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

    # Step 1: Pick slide sequence based on style
    default_sequences = {
        "warm-tech": ["title", "problem", "solution", "market", "competition", "traction", "funds", "team_ask"],
        "consulting": ["title", "situation", "methodology", "case_study", "market", "team_credentials", "implementation", "investment"],
        "consumer": ["title", "problem", "solution", "social_proof", "market", "traction", "business_model", "team_ask"],
    }
    types = slide_types or default_sequences.get(style, default_sequences["warm-tech"])

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

    # Consulting slide type descriptions
    type_descriptions = {
        "situation": "Current state analysis: what's happening in the market/client's world",
        "methodology": "Your approach: numbered steps, framework, process",
        "case_study": "Client success story with specific ROI metrics",
        "team_credentials": "Team qualifications, notable alumni, relevant experience",
        "implementation": "Timeline, phases, deliverables, milestones",
        "investment": "Engagement terms, pricing, expected ROI",
        "social_proof": "Testimonials, ratings, community metrics, press mentions",
        "business_model": "Revenue model, pricing tiers, unit economics",
    }
    type_hints = "\n".join(f"- {t}: {type_descriptions.get(t, t)}" for t in slide_types)

    prompt = f"""You are a presentation strategist. Given this brief, generate a slide-by-slide outline.

Brief: {brief}
Audience: {audience}
Slides needed (in order):
{type_hints}

For each slide, provide:
- type: the slide type (exactly as listed above)
- message: the ONE key message for this slide (a punchy headline, max 10 words)

The message should be specific to the company, not generic. Use real numbers from the brief.

Return a JSON array. Example:
[
  {{"type": "title", "message": "Eliminating $562B in Retail Food Waste"}},
  {{"type": "situation", "message": "Mid-market retailers hemorrhaging margin to spoilage."}},
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

    # Style-specific instructions
    style_instructions = ""
    if any(t in slide_type for t in ["situation", "methodology", "case_study", "team_credentials", "implementation", "investment"]):
        style_instructions = """
## Consulting Deck Style
This is a CONSULTING deck, NOT a startup pitch deck. Key differences:
- Use structured data tables, frameworks, and process diagrams
- Takeaway bar at top of content: one bold sentence summarizing the slide's conclusion
- No app mockups, no code blocks, no product screenshots
- Use numbered process steps (01, 02, 03) for methodology
- Client case studies show ROI metrics and implementation details
- Conservative serif headlines, data-dense layouts
- Bottom of every slide: source citation or exhibit label"""
    elif any(t in slide_type for t in ["social_proof", "business_model"]):
        style_instructions = """
## Consumer/DTC Deck Style
- Emphasize social proof: user testimonials, ratings, community metrics
- Use emotional language and lifestyle-oriented visuals
- Product screenshots or lifestyle imagery as visual anchors
- Bright accent colors, playful but professional"""

    return f"""You are a presentation designer. Generate slide {slide_number} of {total_slides}.

## Slide Type: {slide_type}
## Key Message: {key_message}
## Company: {company}
{style_instructions}

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
2. Match the reference template's visual quality. Adapt the LAYOUT for this slide type (not every slide should use the same split pattern).
3. Adapt ALL content for the company and slide type. Do NOT copy the reference content.
4. Use the theme colors and fonts from the tokens above.
5. CSS MUST include: @page {{ size: 1920px 1080px; margin: 0; }}. Body: display:flex; flex-direction:column; padding: 56px 80px 40px (SMALL bottom padding). The main content container MUST use flex:1 to stretch to the bottom.
6. CRITICAL: NO visible empty space at the bottom of the slide. The content must visually reach the bottom edge. If the main content is short, add a bottom bar with stats, a source citation, or increase card sizes. Test: if you drew a line at y=1040px, content should be there.
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
    import re
    lower = brief.lower()
    # Check longer keywords first (more specific matches)
    sorted_routes = sorted(STYLE_ROUTES.items(), key=lambda x: -len(x[0]))
    for keyword, style in sorted_routes:
        # Word boundary match to avoid "ai" matching in "retailers"
        if re.search(r'\b' + re.escape(keyword) + r'\b', lower):
            return style
    return "warm-tech"


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
    """Find the best matching template for a slide type.
    Handles both naming conventions:
    - warm-tech: slide-03-problem, slide-04-solution
    - consulting/consumer: slide-01, slide-02, ..., slide-10
    """
    # Map slide types to candidate template names (both conventions)
    type_map = {
        # Pitch deck types
        "title": ["slide-01-title", "slide-01"],
        "problem": ["slide-03-problem", "slide-02", "slide-03"],
        "solution": ["slide-04-solution", "slide-03", "slide-04"],
        "market": ["slide-02-market", "slide-04", "slide-05"],
        "competition": ["slide-07-competition", "slide-04", "slide-06"],
        "traction": ["slide-07-traction", "slide-05", "slide-07"],
        "funds": ["slide-09-ask", "slide-07", "slide-10"],
        "team_ask": ["slide-08-team", "slide-10", "slide-09"],
        "business": ["slide-06-business", "slide-05", "slide-06"],
        "gtm": ["slide-08-gtm", "slide-06"],
        "closing": ["slide-12-closing", "slide-10"],
        # Consulting-specific types (map to consulting template positions)
        "situation": ["slide-02", "slide-03-problem", "slide-03"],
        "methodology": ["slide-03", "slide-04-solution", "slide-04"],
        "case_study": ["slide-05", "slide-04", "slide-07-traction"],
        "team_credentials": ["slide-09", "slide-08-team", "slide-10"],
        "implementation": ["slide-06", "slide-07", "slide-08-gtm"],
        "investment": ["slide-07", "slide-09-ask", "slide-10"],
        # Consumer-specific types
        "social_proof": ["slide-03", "slide-05", "slide-07-traction"],
        "business_model": ["slide-06", "slide-05", "slide-06-business"],
    }

    candidates = type_map.get(slide_type, [])
    for key in candidates:
        if key in templates:
            return templates[key]

    # Fallback: try to match by position (slide-N where N = slide index)
    keys = sorted(templates.keys())
    if keys:
        # Return a middle template (likely content-heavy, good reference)
        mid = len(keys) // 3
        return templates[keys[mid]]

    return ""


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
