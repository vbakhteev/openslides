"""
Gemini HTML Renderer
Generates slide HTML directly via Gemini, using template library as reference.
This replaces the Python assembler/template system.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .theme import Theme, LightTheme


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def render_deck(
    brief: str,
    theme: Theme,
    brand_context: dict | None = None,
    audience: str = "vc",
    style: str = "warm-tech",
    slide_types: list[str] | None = None,
    api_key: str | None = None,
    model: str = "gemini-3-flash-preview",
) -> list[str]:
    """
    Generate a full deck of HTML slides via Gemini.

    This is the core function. Gemini receives:
    1. Reference templates (real HTML from the template library)
    2. Theme tokens (colors, fonts)
    3. Company brief + brand context
    4. Instructions to generate each slide

    Returns: list of HTML strings, one per slide.
    """
    from google import genai
    from google.genai.types import GenerateContentConfig

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Load reference templates for the style
    templates = _load_templates(style)

    # Build the prompt
    prompt = _build_prompt(brief, theme, brand_context, audience, templates, slide_types)

    # Call Gemini
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=GenerateContentConfig(max_output_tokens=65536),
    )

    text = response.text or ""

    # Parse: Gemini returns slides separated by a delimiter
    slides = _parse_slides(text)

    # Inject theme if needed (replace CSS vars)
    slides = [_inject_theme(s, theme) for s in slides]

    return slides


def render_single_slide(
    slide_type: str,
    content_brief: str,
    theme: Theme,
    style: str = "warm-tech",
    reference_html: str | None = None,
    api_key: str | None = None,
    model: str = "gemini-3-flash-preview",
) -> str:
    """
    Generate a single slide. Useful for iteration (regenerate slide 3 only).

    If reference_html is provided, Gemini adapts it. Otherwise uses template library.
    """
    from google import genai
    from google.genai.types import GenerateContentConfig

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Get reference template
    if not reference_html:
        templates = _load_templates(style)
        reference_html = _find_best_template(templates, slide_type)

    prompt = f"""You are a pitch deck designer. Generate a single HTML slide (1920x1080px).

REFERENCE TEMPLATE (adapt this structure, keep the CSS quality):
```html
{reference_html}
```

THEME TOKENS:
- Background: {theme.background}
- Text primary: {theme.text_primary}
- Text secondary: {theme.text_secondary}
- Text muted: {theme.text_muted}
- Accent: {theme.accent}
- Surface: {theme.surface}
- Border: {theme.border}
- Headline font: {theme.headline_font_family}
- Body font: {theme.body_font_family}
- Google Fonts URL: {theme.google_fonts_url}

SLIDE TYPE: {slide_type}
CONTENT: {content_brief}

Rules:
1. Keep the EXACT same CSS structure, layout patterns, and visual quality as the reference.
2. Replace ALL content (text, numbers, labels) with content relevant to the brief.
3. Adapt the theme colors/fonts to match the THEME TOKENS above.
4. The slide must be a complete, self-contained HTML file (1920x1080).
5. Use the Google Fonts URL from the theme tokens.
6. Return ONLY the HTML. No markdown fences. No commentary."""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=GenerateContentConfig(max_output_tokens=16384),
    )

    html = _extract_html(response.text or "")
    return _inject_theme(html, theme)


def _load_templates(style: str) -> dict[str, str]:
    """Load reference templates for a style."""
    style_dir = TEMPLATE_DIR / style
    if not style_dir.exists():
        style_dir = TEMPLATE_DIR / "warm-tech"  # fallback

    templates = {}
    for f in sorted(style_dir.glob("*.html")):
        # Map filename to slide type
        name = f.stem  # e.g., "slide-03-problem"
        templates[name] = f.read_text()

    return templates


def _find_best_template(templates: dict[str, str], slide_type: str) -> str:
    """Find the best matching template for a slide type."""
    type_map = {
        "title": "slide-01-title",
        "market": "slide-02-market",
        "problem": "slide-03-problem",
        "solution": "slide-04-solution",
        "business": "slide-06-business",
        "competition": "slide-07-competition",
        "traction": "slide-07-traction",
        "gtm": "slide-08-gtm",
        "team": "slide-08-team",
        "team_ask": "slide-08-team",
        "ask": "slide-09-ask",
        "funds": "slide-09-ask",
        "closing": "slide-12-closing",
    }

    key = type_map.get(slide_type, "")
    if key and key in templates:
        return templates[key]

    # Fallback: return the problem template (most versatile)
    for k, v in templates.items():
        if "problem" in k:
            return v

    # Last resort: return first template
    return next(iter(templates.values()), "")


def _build_prompt(
    brief: str,
    theme: Theme,
    brand_context: dict | None,
    audience: str,
    templates: dict[str, str],
    slide_types: list[str] | None,
) -> str:
    """Build the full prompt for deck generation."""

    # Pick 3-4 reference templates (can't fit all 11 in one prompt)
    ref_slides = {}
    priority = ["slide-03-problem", "slide-04-solution", "slide-09-ask", "slide-07-competition"]
    for key in priority:
        if key in templates:
            ref_slides[key] = templates[key]
        if len(ref_slides) >= 3:
            break

    # Build reference block
    ref_block = ""
    for name, html in ref_slides.items():
        # Truncate very long templates
        if len(html) > 8000:
            html = html[:8000] + "\n<!-- ... truncated ... -->"
        ref_block += f"\n### Reference: {name}\n```html\n{html}\n```\n"

    # Brand context block
    brand_block = ""
    if brand_context:
        brand_block = "\n## Company Context\n"
        for k, v in brand_context.items():
            if v:
                brand_block += f"- {k}: {v}\n"

    # Slide sequence
    default_types = ["title", "problem", "solution", "market", "competition", "traction", "funds", "team_ask"]
    types = slide_types or default_types

    audience_desc = {
        "vc": "venture capital investors (emphasize moat, metrics, 10x returns)",
        "angel": "angel investors (emphasize founder story, vision, early signal)",
        "ff": "friends and family (emphasize trust, clarity, use of funds)",
        "customer": "potential customers (emphasize value prop, ROI, social proof)",
    }.get(audience, "investors")

    return f"""You are an expert pitch deck designer. Generate a complete {len(types)}-slide HTML pitch deck.

## Quality Standard
Study these reference slides carefully. Match this EXACT level of visual quality:
- Split layouts (40/60, 50/50) that fill the full 1920x1080 space
- Dark accent cards with white text for emphasis
- Surface cards with icons, titles, descriptions, AND stat numbers
- DM Serif Display for headlines with italic accent on key phrases
- Subtle emerald radial gradient in the background
- No dead space. Every slide must fill the canvas.
{ref_block}

## Theme Tokens
- Background: {theme.background}
- Text primary: {theme.text_primary}
- Text secondary: {theme.text_secondary}
- Text muted: {theme.text_muted}
- Accent: {theme.accent}
- Accent secondary: {theme.accent_secondary}
- Surface: {theme.surface}
- Border: {theme.border}
- Dark card bg: Use a dark shade of the accent color
- Headline font: {theme.headline_font_family}
- Body font: {theme.body_font_family}
- Google Fonts: {theme.google_fonts_url}
{brand_block}

## Audience
This deck targets {audience_desc}.

## Slides to Generate
Generate these {len(types)} slides in order: {', '.join(types)}

## Rules
1. Each slide is a COMPLETE, self-contained HTML file (1920x1080).
2. Use @page {{ size: 1920px 1080px; margin: 0; }} in every slide.
3. Every slide must use the theme tokens above for colors and fonts.
4. Headlines: DM Serif Display (or theme headline font), max 10 words, with italic+accent on the key phrase.
5. Content must be SPECIFIC to the brief. Real numbers, real claims, no generic filler.
6. Separate each slide with the delimiter: ===SLIDE_BREAK===
7. No markdown fences around the HTML. Just raw HTML separated by the delimiter.
8. Match the reference templates' visual density. No empty slides. Fill the space.

## Brief
{brief}"""


def _parse_slides(text: str) -> list[str]:
    """Parse Gemini output into individual slides."""
    # Try delimiter-based split
    if "===SLIDE_BREAK===" in text:
        parts = text.split("===SLIDE_BREAK===")
        return [_extract_html(p) for p in parts if p.strip()]

    # Try splitting on <!DOCTYPE
    if text.count("<!DOCTYPE") > 1:
        parts = text.split("<!DOCTYPE")
        slides = []
        for p in parts:
            if p.strip():
                html = "<!DOCTYPE" + p
                slides.append(_extract_html(html))
        return slides

    # Single slide
    return [_extract_html(text)]


def _extract_html(text: str) -> str:
    """Extract HTML from text that might have markdown fences."""
    import re
    # Remove markdown code fences
    match = re.search(r"```html?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()

    # If it starts with <!DOCTYPE or <html, it's already HTML
    text = text.strip()
    if text.startswith("<!") or text.startswith("<html"):
        return text

    return text


def _inject_theme(html: str, theme: Theme) -> str:
    """Ensure the HTML uses the correct theme Google Fonts URL."""
    # If no Google Fonts link, add one
    if "fonts.googleapis.com" not in html and "<head>" in html:
        font_link = f'<link href="{theme.google_fonts_url}" rel="stylesheet">'
        html = html.replace("<head>", f"<head>\n{font_link}")
    return html
