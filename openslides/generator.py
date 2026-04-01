"""
Deck Generator
Orchestrates content generation from prompt + brand context via LLM.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .theme import Theme, LightTheme, DarkTheme
from .prompts import SLIDE_SCHEMAS
from .components import SlideBuilder


@dataclass
class BrandContext:
    """Scraped/provided brand information."""
    company_name: str = ""
    domain: str = ""
    tagline: str = ""
    description: str = ""
    logo_url: str = ""
    colors: dict = field(default_factory=dict)
    fonts: dict = field(default_factory=dict)
    team: list[dict] = field(default_factory=list)
    pricing: list[dict] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    og_image: str = ""


class DeckGenerator:
    """
    Generates slide deck content from prompt + brand context.

    Usage:
        gen = DeckGenerator()
        config = gen.generate(
            prompt="Raising $200K pre-seed for AI deploy platform",
            brand=BrandContext(company_name="floom", domain="floom.dev"),
            audience="vc",
        )
        # config is a dict ready for SlideBuilder
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    def generate(
        self,
        prompt: str,
        brand: BrandContext | None = None,
        audience: str = "vc",
        deck_type: str = "pitch",
        model: str = "gemini-3.1-pro-preview",
    ) -> dict:
        """
        Generate slide config from prompt.

        Returns dict with "slides" key, ready for SlideBuilder.
        """
        from .prompts import get_deck_prompt

        full_prompt = get_deck_prompt(
            brief=prompt,
            brand_context=self._brand_to_dict(brand) if brand else None,
            audience=audience,
            deck_type=deck_type,
        )

        response_text = self._call_llm(full_prompt, model)
        config = self._parse_response(response_text)

        # Normalize: if slides have content at root level, nest into "content"
        # Detect by checking for any known content field at root level
        _content_indicators = {"headline", "story_html", "founder_name", "company_name", "subheadline", "features", "tam", "quotes", "tiers", "flow_items", "columns", "fund_items"}
        for slide in config.get("slides", []):
            if "content" not in slide and (set(slide.keys()) & _content_indicators):
                slide_type = slide.pop("type", "content")
                theme_val = slide.pop("theme", None)
                new_slide = {"type": slide_type, "content": dict(slide)}
                if theme_val:
                    new_slide["theme"] = theme_val
                slide.clear()
                slide.update(new_slide)

        # Normalize common LLM output issues
        self._normalize_config(config)

        # Validate and auto-fix
        from .content_validator import validate_deck, apply_fixes
        result = validate_deck(config)
        if result.auto_fixes:
            config = apply_fixes(config, result.auto_fixes)

        # Inject company name from brand if missing
        if brand and brand.company_name:
            for slide in config.get("slides", []):
                content = slide.get("content", {})
                if slide.get("type") == "title" and not content.get("company_name"):
                    content["company_name"] = brand.company_name

        return config

    def generate_partial(
        self,
        prompt: str,
        previous_config: dict,
        slide_indices: list[int],
        brand: BrandContext | None = None,
        audience: str = "vc",
        model: str = "gemini-3.1-pro-preview",
    ) -> dict:
        """
        Regenerate specific slides while keeping the rest.

        Args:
            prompt: refinement instruction
            previous_config: full deck config from previous generation
            slide_indices: 0-based indices of slides to regenerate
        """
        from .prompts import get_refinement_prompt

        slides = previous_config.get("slides", [])
        new_config = {"slides": list(slides)}  # copy

        for idx in slide_indices:
            if idx < 0 or idx >= len(slides):
                continue
            slide = slides[idx]
            refine_prompt = get_refinement_prompt(
                slide_type=slide["type"],
                current_content=slide.get("content", {}),
            )
            full_prompt = f"{refine_prompt}\n\nUser refinement request: {prompt}"
            response_text = self._call_llm(full_prompt, model)
            try:
                new_content = self._parse_response(response_text)
                # Response might be just the content dict or a full slide
                if "content" in new_content:
                    new_config["slides"][idx] = new_content
                elif "type" not in new_content:
                    new_config["slides"][idx]["content"] = new_content
            except ValueError:
                pass  # keep original slide on parse failure

        return new_config

    def render(self, config: dict, theme: Theme | None = None) -> list[str]:
        """
        Render slide config to list of HTML strings.

        Args:
            config: deck config with "slides" key
            theme: theme to use (defaults to LightTheme)
        """
        theme = theme or LightTheme()
        from .assembler import assemble_deck
        return assemble_deck(config, theme)

    def _render_modern(self, config: dict, theme: Theme) -> list[str]:
        """Render using modern templates, fall back to v1 for unsupported types."""
        from .templates_modern import MODERN_RENDERERS
        from .components import SlideBuilder

        slides = []
        for slide_cfg in config.get("slides", []):
            slide_type = slide_cfg.get("type", "content")
            content = slide_cfg.get("content", {})

            # Pick dark/light theme per slide
            slide_theme = theme
            if slide_cfg.get("theme") == "dark" or SLIDE_SCHEMAS.get(slide_type, {}).get("theme") == "dark":
                slide_theme = DarkTheme()
                # Preserve custom fonts from base theme
                slide_theme.headline_font_family = theme.headline_font_family
                slide_theme.body_font_family = theme.body_font_family
                if hasattr(theme, "mono_font_family"):
                    slide_theme.mono_font_family = theme.mono_font_family
                slide_theme.accent = theme.accent
                slide_theme.accent_secondary = theme.accent_secondary

            # Try modern renderer first
            renderer = MODERN_RENDERERS.get(slide_type)
            if renderer:
                try:
                    html = renderer(theme=slide_theme, **content)
                    slides.append(html)
                    continue
                except (TypeError, KeyError, AttributeError):
                    pass

            # Fall back to v1 renderer
            try:
                builder = SlideBuilder(theme=slide_theme)
                builder._theme_externally_set = True
                content_copy = dict(content)
                content_copy["theme"] = slide_theme
                builder.add_slide(slide_type, content_copy)
                slides.extend(builder.build())
            except Exception:
                # Last resort: generic content slide
                from .templates_modern import render_content
                slides.append(render_content(
                    headline=content.get("headline", slide_type.replace("_", " ").title()),
                    content_html=f"<p>{content.get('subheadline', content.get('story_html', ''))}</p>",
                    label=slide_type.replace("_", " ").title(),
                    theme=slide_theme,
                ))

        return slides

    def _call_llm(self, prompt: str, model: str) -> str:
        """Call Gemini API. Tries JSON mode first, falls back to plain text."""
        from google import genai
        from google.genai.types import GenerateContentConfig

        client = genai.Client(api_key=self._api_key)

        # Try with JSON mode
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=16384,
                ),
            )
            if response.text:
                return response.text
        except Exception:
            pass

        # Fallback: plain text mode (more reliable for complex prompts)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(max_output_tokens=16384),
        )
        return response.text or ""

    def _parse_response(self, response: str) -> dict:
        """Extract JSON from LLM response. Handles object or array."""
        # Try direct parse first (Gemini JSON mode returns clean JSON)
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return {"slides": data}
            return data
        except json.JSONDecodeError:
            pass

        # Try markdown code fence
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    return {"slides": data}
                return data
            except json.JSONDecodeError:
                pass

        # Try raw JSON object or array
        for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
            match = re.search(pattern, response)
            if match:
                try:
                    data = json.loads(match.group())
                    if isinstance(data, list):
                        return {"slides": data}
                    return data
                except json.JSONDecodeError:
                    pass

        raise ValueError("No valid JSON found in LLM response")

    @staticmethod
    def _normalize_config(config: dict):
        """Fix common LLM output format issues in-place."""
        for slide in config.get("slides", []):
            content = slide.get("content", {})

            # segments: list of strings -> list of dicts
            segs = content.get("segments")
            if isinstance(segs, list) and segs and isinstance(segs[0], str):
                content["segments"] = [{"title": s, "items": []} for s in segs]

            # features: list of strings -> list of dicts
            feats = content.get("features")
            if isinstance(feats, list) and feats and isinstance(feats[0], str):
                content["features"] = [{"title": f, "description": ""} for f in feats]

            # quotes: list of strings -> list of dicts
            quotes = content.get("quotes")
            if isinstance(quotes, list) and quotes and isinstance(quotes[0], str):
                content["quotes"] = [{"quote": q, "author": "", "role": ""} for q in quotes]

            # bio_items: list of strings -> list of dicts
            bios = content.get("bio_items")
            if isinstance(bios, list) and bios and isinstance(bios[0], str):
                content["bio_items"] = [{"company": b, "detail": ""} for b in bios]

            # flow_items: ensure list of strings
            flow = content.get("flow_items")
            if isinstance(flow, list) and flow and isinstance(flow[0], dict):
                content["flow_items"] = [f.get("title", str(f)) for f in flow]

            # tiers: list of strings -> list of dicts
            tiers = content.get("tiers")
            if isinstance(tiers, list) and tiers and isinstance(tiers[0], str):
                content["tiers"] = [{"name": t, "price": "", "period": "month", "features": []} for t in tiers]

            # fund_items: list of strings -> list of dicts
            funds = content.get("fund_items")
            if isinstance(funds, list) and funds and isinstance(funds[0], str):
                content["fund_items"] = [{"label": f, "amount": "", "percentage": 25} for f in funds]

            # milestones: list of strings -> list of dicts
            ms = content.get("milestones")
            if isinstance(ms, list) and ms and isinstance(ms[0], str):
                content["milestones"] = [{"date": "", "title": m, "status": "upcoming"} for m in ms]

            # columns (comparison): list of strings -> list of dicts
            cols = content.get("columns")
            if isinstance(cols, list) and cols and isinstance(cols[0], str):
                content["columns"] = [{"name": c, "items": []} for c in cols]

            # ask_uses: ensure list of strings
            uses = content.get("ask_uses")
            if isinstance(uses, list) and uses and isinstance(uses[0], dict):
                content["ask_uses"] = [u.get("text", str(u)) for u in uses]

    @staticmethod
    def _brand_to_dict(brand: BrandContext) -> dict:
        """Convert BrandContext to dict for prompt injection."""
        d = {}
        if brand.company_name:
            d["company_name"] = brand.company_name
        if brand.domain:
            d["domain"] = brand.domain
        if brand.tagline:
            d["tagline"] = brand.tagline
        if brand.description:
            d["description"] = brand.description
        if brand.team:
            d["team"] = brand.team
        if brand.pricing:
            d["pricing"] = brand.pricing
        if brand.features:
            d["features"] = brand.features
        return d
