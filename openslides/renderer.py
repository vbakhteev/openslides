"""
Gemini HTML Renderer v2
Multi-turn per-slide generation with style routing and tools injection.

Architecture:
1. Python resolves tools (logos, brand, theme)
2. Gemini generates deck outline (slide types + key messages)
3. For each slide: Gemini generates HTML with matched reference template + injected tools
4. Python post-processes (theme injection, export)
"""
from __future__ import annotations

import os
from pathlib import Path

from .theme import Theme, LightTheme


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Industry -> style mapping for auto-routing
STYLE_ROUTES: dict[str, str] = {
    "saas": "warm-tech",
    "devtools": "warm-tech",
    "ai": "warm-tech",
    "developer": "warm-tech",
    "consulting": "consulting",
    "b2b services": "consulting",
    "strategy": "consulting",
    "enterprise": "consulting",
    "consumer": "consumer",
    "dtc": "consumer",
    "lifestyle": "consumer",
    "fitness": "consumer",
    "food": "consumer",
    "fintech": "warm-tech",
    "healthcare": "warm-tech",
    "climate": "warm-tech",
    "marketplace": "consumer",
    "agency": "consulting",
    "edtech": "warm-tech",
}


def render_deck(
    brief: str,
    theme: Theme,
    brand_context: dict | None = None,
    audience: str = "vc",
    style: str | None = None,
    slide_types: list[str] | None = None,
    logos: dict[str, str] | None = None,
    api_key: str | None = None,
    model: str = "gemini-3-flash-preview",
) -> list[str]:
    """
    Generate a full deck via multi-turn Gemini calls.

    Step 1: Generate outline (slide types + key messages)
    Step 2: For each slide, generate HTML with matched reference template

    Args:
        brief: company/product description
        theme: visual theme tokens
        brand_context: scraped brand info (company_name, description, domain)
        audience: vc/angel/ff/customer
        style: template style (auto-detected if None)
        slide_types: override slide sequence
        logos: pre-resolved logo URLs {name: url}
        api_key: Gemini API key
        model: Gemini model ID
    """
    from google import genai
    from google.genai.types import GenerateContentConfig

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Auto-detect style from brief if not provided
    if not style:
        style = _detect_style(brief)

    # Load templates for the style
    templates = _load_templates(style)

    # Step 1: Generate outline
    default_types = ["title", "problem", "solution", "market", "competition", "traction", "funds", "team_ask"]
    types = slide_types or default_types

    outline = _generate_outline(client, model, brief, audience, types)

    # Step 2: Generate each slide individually
    slides = []
    company = brand_context.get("company_name", "") if brand_context else ""

    for i, slide_info in enumerate(outline):
        slide_type = slide_info.get("type", types[i] if i < len(types) else "content")
        key_message = slide_info.get("message", "")

        # Find the best reference template for this slide type
        reference = _find_best_template(templates, slide_type)

        # Build per-slide prompt with tools
        prompt = _build_slide_prompt(
            slide_type=slide_type,
            key_message=key_message,
            brief=brief,
            theme=theme,
            brand_context=brand_context,
            audience=audience,
            reference_html=reference,
            logos=logos,
            slide_number=i + 1,
            total_slides=len(outline),
            company=company,
        )

        # Generate
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=GenerateContentConfig(max_output_tokens=16384),
            )
            html = _extract_html(response.text or "")
            html = _inject_theme(html, theme)
            slides.append(html)
            print(f"  Slide {i+1}/{len(outline)}: {slide_type} ({len(html)} chars)")
        except Exception as e:
            print(f"  Slide {i+1}/{len(outline)}: {slide_type} FAILED: {e}")
            slides.append(_fallback_slide(slide_type, key_message, theme, company))

    return slides


def render_single_slide(
    slide_type: str,
    content_brief: str,
    theme: Theme,
    style: str = "warm-tech",
    reference_html: str | None = None,
    logos: dict[str, str] | None = None,
    api_key: str | None = None,
    model: str = "gemini-3-flash-preview",
) -> str:
    """Generate a single slide. Useful for iteration."""
    from google import genai
    from google.genai.types import GenerateContentConfig

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    if not reference_html:
        templates = _load_templates(style)
        reference_html = _find_best_template(templates, slide_type)

    prompt = _build_slide_prompt(
        slide_type=slide_type,
        key_message=content_brief,
        brief=content_brief,
        theme=theme,
        reference_html=reference_html,
        logos=logos,
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=GenerateContentConfig(max_output_tokens=16384),
    )

    html = _extract_html(response.text or "")
    return _inject_theme(html, theme)


# =============================================================================
# OUTLINE GENERATION
# =============================================================================

def _generate_outline(client, model: str, brief: str, audience: str, slide_types: list[str]) -> list[dict]:
    """Step 1: Generate deck outline with key messages per slide."""
    from google.genai.types import GenerateContentConfig

    prompt = f"""You are a pitch deck strategist. Given this brief, generate a slide-by-slide outline.

Brief: {brief}
Audience: {audience}
Slides needed: {', '.join(slide_types)}

For each slide, provide:
- type: the slide type
- message: the ONE key message for this slide (a punchy headline, max 10 words)

Return a JSON array. Example:
[
  {{"type": "title", "message": "The Production Layer for AI Scripts"}},
  {{"type": "problem", "message": "Scripts die on localhost. 99% never reach a user."}},
  ...
]

Return ONLY the JSON array. No commentary."""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=2048,
            ),
        )
        import json
        data = json.loads(response.text or "[]")
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # Fallback: generate outline from slide_types
    return [{"type": t, "message": ""} for t in slide_types]


# =============================================================================
# PER-SLIDE PROMPT
# =============================================================================

def _build_slide_prompt(
    slide_type: str,
    key_message: str,
    brief: str,
    theme: Theme,
    brand_context: dict | None = None,
    audience: str = "vc",
    reference_html: str = "",
    logos: dict[str, str] | None = None,
    slide_number: int = 1,
    total_slides: int = 8,
    company: str = "",
) -> str:
    """Build prompt for a single slide with all context injected."""

    # Truncate reference if too long
    ref = reference_html
    if len(ref) > 10000:
        ref = ref[:10000] + "\n<!-- truncated -->"

    # Brand block
    brand_block = ""
    if brand_context:
        parts = [f"- {k}: {v}" for k, v in brand_context.items() if v]
        if parts:
            brand_block = "\n## Company Info\n" + "\n".join(parts)

    # Logos block
    logo_block = ""
    if logos:
        parts = [f"- {name}: {url}" for name, url in logos.items()]
        logo_block = "\n## Available Logo URLs (use as <img src>)\n" + "\n".join(parts)

    # Theme block
    theme_block = f"""## Theme
- Background: {theme.background}
- Text: {theme.text_primary} / {theme.text_secondary} / {theme.text_muted}
- Accent: {theme.accent}
- Surface: {theme.surface}
- Border: {theme.border}
- Headline font: {theme.headline_font_family}
- Body font: {theme.body_font_family}
- Google Fonts: {theme.google_fonts_url}"""

    return f"""You are a pitch deck designer. Generate slide {slide_number} of {total_slides}.

## Slide Type: {slide_type}
## Key Message: {key_message}
## Company: {company}

## Reference Template (match this visual quality and layout structure)
```html
{ref}
```

{theme_block}
{brand_block}
{logo_block}

## Full Brief
{brief}

## Rules
1. Generate a COMPLETE self-contained HTML file (1920x1080px).
2. Match the reference template's visual quality: split layouts, dark accent cards, stat numbers, icons, proper spacing.
3. Adapt ALL content for the company and slide type. Do NOT copy the reference content.
4. Use the theme colors and fonts from the tokens above.
5. Include @page {{ size: 1920px 1080px; margin: 0; }} in CSS.
6. Fill the ENTIRE slide. No dead space. Use the full 1920x1080 canvas.
7. If logo URLs are provided, embed them as <img src="URL"> with proper sizing (24-48px height).
8. Headlines max 10 words, with key phrase in italic + accent color.
9. ONLY use numbers and stats that are in the brief or can be reasonably inferred. Do NOT invent fake metrics.
10. For team slides: use text-based layouts (name, role, credentials, badges). Do NOT generate or reference avatar images, illustrations, or placeholder photos. Use initials in styled circles if you need a visual anchor.
11. Every slide must use the full 1080px height. If content is short, increase padding, use larger fonts, or add supporting visual elements.
12. Use inline SVG icons from Lucide (24x24 viewBox, stroke-based) for visual richness. Do not reference external icon CDNs.
13. Return ONLY the HTML. No markdown fences. No commentary."""


# =============================================================================
# STYLE ROUTING
# =============================================================================

def _detect_style(brief: str) -> str:
    """Auto-detect the best template style from the brief."""
    lower = brief.lower()
    for keyword, style in STYLE_ROUTES.items():
        if keyword in lower:
            return style
    return "warm-tech"  # default


# =============================================================================
# TEMPLATE LOADING
# =============================================================================

def _load_templates(style: str) -> dict[str, str]:
    """Load reference templates for a style."""
    style_dir = TEMPLATE_DIR / style
    if not style_dir.exists():
        style_dir = TEMPLATE_DIR / "warm-tech"

    templates = {}
    for f in sorted(style_dir.glob("*.html")):
        templates[f.stem] = f.read_text()
    return templates


def _find_best_template(templates: dict[str, str], slide_type: str) -> str:
    """Find the best matching template for a slide type."""
    type_map = {
        "title": ["slide-01-title", "slide-01"],
        "market": ["slide-02-market", "slide-02"],
        "problem": ["slide-03-problem", "slide-03", "slide-02"],
        "solution": ["slide-04-solution", "slide-04", "slide-03"],
        "business": ["slide-06-business", "slide-05"],
        "competition": ["slide-07-competition", "slide-06", "slide-04"],
        "traction": ["slide-07-traction", "slide-07", "slide-05"],
        "gtm": ["slide-08-gtm", "slide-06"],
        "team": ["slide-08-team", "slide-09", "slide-08"],
        "team_ask": ["slide-08-team", "slide-09", "slide-10"],
        "ask": ["slide-09-ask", "slide-10", "slide-08"],
        "funds": ["slide-09-ask", "slide-10", "slide-07"],
        "closing": ["slide-12-closing", "slide-10"],
    }

    candidates = type_map.get(slide_type, [])
    for key in candidates:
        if key in templates:
            return templates[key]

    # Fallback: first template
    return next(iter(templates.values()), "")


# =============================================================================
# HELPERS
# =============================================================================

def _extract_html(text: str) -> str:
    """Extract HTML from Gemini response."""
    import re
    match = re.search(r"```html?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()

    text = text.strip()
    if text.startswith("<!") or text.startswith("<html"):
        return text
    return text


def _inject_theme(html: str, theme: Theme) -> str:
    """Ensure Google Fonts link is present."""
    if "fonts.googleapis.com" not in html and "<head>" in html:
        html = html.replace("<head>", f'<head>\n<link href="{theme.google_fonts_url}" rel="stylesheet">')
    return html


def _fallback_slide(slide_type: str, message: str, theme: Theme, company: str) -> str:
    """Minimal fallback if Gemini call fails."""
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="{theme.google_fonts_url}" rel="stylesheet">
<style>
@page {{ size: 1920px 1080px; margin: 0; }}
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ width:1920px;height:1080px;font-family:{theme.body_font_family};background:{theme.background};color:{theme.text_primary};padding:80px;display:flex;flex-direction:column;justify-content:center; }}
h1 {{ font-family:{theme.headline_font_family};font-size:64px;margin-bottom:24px; }}
</style></head><body>
<div style="font-size:14px;color:{theme.text_muted};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:32px;">{company} / {slide_type}</div>
<h1>{message or slide_type.replace("_", " ").title()}</h1>
</body></html>'''
