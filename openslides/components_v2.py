"""
Component-based slide assembly system.

Slides are built from composable components:
- Layout components (split, full_width, stacked) define WHERE things go
- Content components (cards, stats, charts) define WHAT fills the spaces
- The theme controls HOW everything looks

Each component is a function that returns an HTML fragment.
Slides are assembled by combining: base + header + headline + layout(content components).
"""
from __future__ import annotations

from .theme import Theme, LightTheme, DarkTheme
from .icons import get_icon_svg, auto_icon


# =============================================================================
# BASE: Every slide starts here
# =============================================================================

def slide_base(theme: Theme, title: str = "Slide") -> str:
    """HTML head with fonts, print CSS, and body open."""
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=1920">
<title>{title}</title>
<link href="{theme.google_fonts_url}" rel="stylesheet">
<style>
@page {{ size: 1920px 1080px; margin: 0; }}
@media print {{ body::before {{ display: none !important; }} * {{ box-shadow: none !important; }} }}
html {{ height: 1080px; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1920px; height: 1080px; overflow: hidden;
  font-family: {theme.body_font_family};
  background: {theme.background}; color: {theme.text_primary};
  padding: 56px 80px 48px; display: flex; flex-direction: column;
  position: relative;
}}
body::before {{
  content: ''; position: absolute; top: -100px; right: 100px;
  width: 700px; height: 700px; pointer-events: none; border-radius: 50%;
  background: radial-gradient(circle, {theme.accent}12 0%, {theme.accent}06 50%, transparent 70%);
}}
</style></head><body>'''


def slide_close() -> str:
    return "\n</body></html>"


# =============================================================================
# HEADER: Logo + section label + recipient
# =============================================================================

def header(theme: Theme, label: str = "", company: str = "", recipient: str = "") -> str:
    right = f'<span style="font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:{theme.text_muted};">{recipient}</span>' if recipient else ""
    return f'''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-shrink:0;">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:24px;height:24px;background:{theme.accent};border-radius:6px;"></div>
    <span style="font-family:{theme.headline_font_family};font-size:22px;font-weight:400;letter-spacing:-0.5px;">{company}</span>
  </div>
  <span style="font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:{theme.text_muted};">{label}</span>
  {right}
</div>'''


# =============================================================================
# HEADLINE: The slide's main message
# =============================================================================

def headline(text: str, theme: Theme, size: int = 56) -> str:
    """Headline with auto-emphasis on the second sentence."""
    display = _auto_emph(text, theme)
    return f'<h1 style="font-family:{theme.headline_font_family};font-size:{size}px;font-weight:400;line-height:1.12;letter-spacing:-0.02em;color:{theme.text_primary};margin-bottom:16px;flex-shrink:0;">{display}</h1>'


def subtitle(text: str, theme: Theme) -> str:
    return f'<p style="font-size:20px;color:{theme.text_secondary};line-height:1.6;max-width:700px;margin-bottom:8px;">{text}</p>'


# =============================================================================
# LAYOUT COMPONENTS: Define spatial structure
# =============================================================================

def split(left: str, right: str, ratio: str = "50_50", theme: Theme | None = None, valign: str = "center") -> str:
    """Two-column layout. ratio: '50_50', '55_45', '45_55', '40_60', '60_40'."""
    ratios = {
        "50_50": ("1", "1"),
        "55_45": ("0 0 55%", "1"),
        "45_55": ("0 0 45%", "1"),
        "40_60": ("0 0 40%", "1"),
        "60_40": ("0 0 60%", "1"),
        "35_65": ("0 0 35%", "1"),
    }
    l_flex, r_flex = ratios.get(ratio, ("1", "1"))
    return f'''<div style="flex:1;display:flex;gap:40px;align-items:{valign};min-height:0;">
  <div style="flex:{l_flex};min-width:0;">{left}</div>
  <div style="flex:{r_flex};min-width:0;">{right}</div>
</div>'''


def full_width(content: str) -> str:
    """Single column, content fills available space."""
    return f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;min-height:0;">{content}</div>'


def stacked(*sections: str) -> str:
    """Vertical sections filling the space."""
    inner = "".join(f'<div style="flex:1;min-height:0;">{s}</div>' for s in sections)
    return f'<div style="flex:1;display:flex;flex-direction:column;gap:24px;min-height:0;">{inner}</div>'


# =============================================================================
# CARD COMPONENTS: Visual containers
# =============================================================================

def dark_card(content: str, theme: Theme) -> str:
    """Dark accent-colored card (green bg for warm tech, navy for consulting)."""
    return f'<div style="background:{theme.accent};border-radius:16px;padding:36px;color:#fff;">{content}</div>'


def surface_card(content: str, theme: Theme) -> str:
    """White/surface card with border."""
    return f'<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:14px;padding:28px;">{content}</div>'


def tinted_card(content: str, theme: Theme) -> str:
    """Accent-tinted background card (green tint for warm tech, blue tint for consulting)."""
    return f'<div style="background:{theme.accent}0a;border-radius:14px;padding:28px;">{content}</div>'


def shadow_card(content: str, theme: Theme) -> str:
    """Borderless card with shadow only (modern minimal style)."""
    return f'<div style="background:{theme.surface};border-radius:14px;padding:28px;box-shadow:0 4px 20px rgba(0,0,0,0.06);">{content}</div>'


# =============================================================================
# CONTENT COMPONENTS: Things that go inside layouts/cards
# =============================================================================

def section_label(text: str, theme: Theme) -> str:
    """Uppercase muted label (e.g., "WHAT YOU WRITE", "CURRENT STAGE")."""
    return f'<div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:{theme.text_muted};margin-bottom:12px;">{text}</div>'


def stat_hero(value: str, label: str, theme: Theme, size: int = 64, color: str = "") -> str:
    """Large stat number with label. The single most impactful component."""
    c = color or theme.accent
    return f'''<div style="display:inline-flex;flex-direction:column;">
  <span style="font-family:{theme.headline_font_family};font-size:{size}px;font-weight:400;color:{c};line-height:1;">{value}</span>
  <span style="font-size:14px;color:{theme.text_muted};margin-top:4px;text-transform:uppercase;letter-spacing:0.05em;">{label}</span>
</div>'''


def stat_row(items: list[dict], theme: Theme) -> str:
    """Row of 2-4 stat numbers. items: [{value, label}]."""
    stats = "".join(
        f'<div style="flex:1;text-align:center;">{stat_hero(s.get("value",""), s.get("label",""), theme, size=48)}</div>'
        for s in items[:4]
    )
    return f'<div style="display:flex;gap:24px;">{stats}</div>'


def blocker_card(icon_name: str, title: str, desc: str, stat_value: str, stat_label: str, theme: Theme) -> str:
    """Problem/blocker card with icon, text, AND a stat on the right. The floom pattern."""
    icon = get_icon_svg(icon_name, theme.text_muted, 24)
    stat = ""
    if stat_value:
        stat = f'''<div style="text-align:right;flex-shrink:0;margin-left:20px;">
  <div style="font-family:{theme.headline_font_family};font-size:32px;color:#ef4444;line-height:1;">{stat_value}</div>
  <div style="font-size:11px;color:{theme.text_muted};text-transform:uppercase;letter-spacing:0.05em;">{stat_label}</div>
</div>'''
    return f'''<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:14px;padding:24px 28px;display:flex;align-items:center;gap:16px;">
  <div style="flex-shrink:0;">{icon}</div>
  <div style="flex:1;">
    <div style="font-size:17px;font-weight:700;color:{theme.text_primary};margin-bottom:2px;">{title}</div>
    <div style="font-size:14px;color:{theme.text_secondary};line-height:1.4;">{desc}</div>
  </div>
  {stat}
</div>'''


def feature_card(icon_name: str, title: str, desc: str, theme: Theme) -> str:
    """Feature/capability card with icon box."""
    icon = get_icon_svg(icon_name, theme.accent, 22)
    return f'''<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:14px;padding:28px;display:flex;gap:16px;align-items:flex-start;">
  <div style="flex-shrink:0;width:44px;height:44px;border-radius:10px;background:{theme.accent}10;display:flex;align-items:center;justify-content:center;">{icon}</div>
  <div>
    <div style="font-size:18px;font-weight:700;color:{theme.text_primary};margin-bottom:4px;">{title}</div>
    <div style="font-size:14px;color:{theme.text_secondary};line-height:1.5;">{desc}</div>
  </div>
</div>'''


def grid(items: list[str], cols: int = 2) -> str:
    """Grid of HTML fragments."""
    inner = "".join(items)
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:16px;">{inner}</div>'


def badge_row(items: list[str], theme: Theme, icon_names: list[str] | None = None) -> str:
    """Row of pill badges. Optionally with icons."""
    icon_names = icon_names or []
    badges = ""
    for i, item in enumerate(items):
        icon_html = ""
        if i < len(icon_names) and icon_names[i]:
            icon_html = get_icon_svg(icon_names[i], theme.accent, 16)
        badges += f'<span style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:{theme.surface};border:1px solid {theme.border};border-radius:20px;font-size:14px;color:{theme.text_secondary};">{icon_html}{item}</span>'
    return f'<div style="display:flex;gap:10px;flex-wrap:wrap;">{badges}</div>'


def metadata_bar(items: list[str], theme: Theme) -> str:
    """Bottom metadata bar with dividers (Pre-Seed | $500K | Name | 2026)."""
    parts = []
    for i, item in enumerate(items):
        parts.append(f'<span style="font-size:14px;font-weight:500;color:{theme.text_muted};">{item}</span>')
        if i < len(items) - 1:
            parts.append(f'<div style="width:1px;height:14px;background:{theme.border};margin:0 24px;"></div>')
    return f'<div style="display:flex;align-items:center;">' + "".join(parts) + '</div>'


def pull_quote(quote: str, author: str, role: str, theme: Theme) -> str:
    """Large testimonial quote."""
    return f'''<div style="padding:32px 0;">
  <div style="font-family:{theme.headline_font_family};font-size:28px;font-style:italic;color:{theme.text_primary};line-height:1.5;margin-bottom:20px;">&ldquo;{quote}&rdquo;</div>
  <div style="font-size:15px;font-weight:600;color:{theme.text_primary};">{author}</div>
  <div style="font-size:14px;color:{theme.text_muted};">{role}</div>
</div>'''


def takeaway_bar(text: str, theme: Theme) -> str:
    """McKinsey-style action title bar. Bold one-sentence summary at top of slide."""
    return f'<div style="background:{theme.accent};color:#fff;padding:16px 28px;border-radius:10px;font-size:18px;font-weight:600;line-height:1.4;margin-bottom:24px;">{text}</div>'


# =============================================================================
# DATA VISUALIZATION COMPONENTS
# =============================================================================

def fund_bars(items: list[dict], theme: Theme) -> str:
    """Allocation bars. items: [{label, amount, percentage, description}]."""
    bars = ""
    for item in items:
        if not isinstance(item, dict):
            continue
        pct = item.get("percentage", 25)
        desc = item.get("description", "")
        desc_html = f'<div style="font-size:13px;color:{theme.text_muted};margin-top:4px;line-height:1.4;">{desc}</div>' if desc else ""
        bars += f'''<div style="margin-bottom:20px;">
  <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
    <span style="font-size:15px;font-weight:600;color:{theme.text_primary};">{item.get("label","")}</span>
    <span style="font-size:15px;color:{theme.accent};font-weight:600;">{item.get("amount","")}</span>
  </div>
  <div style="height:6px;background:{theme.surface};border-radius:3px;overflow:hidden;">
    <div style="height:100%;width:{pct}%;background:{theme.accent};border-radius:3px;"></div>
  </div>
  {desc_html}
</div>'''
    return bars


def milestone_timeline(items: list[dict], theme: Theme, direction: str = "vertical") -> str:
    """Timeline with dots. items: [{date, title, description, status: done|current|upcoming}]."""
    entries = ""
    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status", "upcoming")
        is_done = status in ("done", "current")
        dot_bg = theme.accent if is_done else "transparent"
        dot_border = theme.accent if is_done else theme.text_muted
        opacity = "1" if is_done else "0.5"
        desc = item.get("description", "")
        desc_html = f'<div style="font-size:14px;color:{theme.text_secondary};line-height:1.4;margin-top:2px;">{desc}</div>' if desc else ""
        entries += f'''<div style="display:flex;gap:16px;opacity:{opacity};">
  <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0;">
    <div style="width:12px;height:12px;border-radius:50%;background:{dot_bg};border:2px solid {dot_border};"></div>
    <div style="width:1px;flex:1;background:{theme.border};margin:4px 0;"></div>
  </div>
  <div style="padding-bottom:20px;">
    <div style="font-size:12px;color:{theme.text_muted};text-transform:uppercase;letter-spacing:0.05em;">{item.get("date","")}</div>
    <div style="font-size:16px;font-weight:600;color:{theme.text_primary};">{item.get("title","")}</div>
    {desc_html}
  </div>
</div>'''
    return f'<div>{entries}</div>'


def comparison_table(features: list[str], companies: list[dict], theme: Theme, accent_col: int = 0) -> str:
    """Feature comparison table. companies: [{name, logo_url, checks: [bool]}]."""
    # Header row
    header_cells = f'<div style="flex:2;"></div>'
    for i, co in enumerate(companies):
        is_accent = i == accent_col
        weight = "700" if is_accent else "500"
        color = theme.accent if is_accent else theme.text_primary
        name = co.get("name", "")
        header_cells += f'<div style="flex:1;text-align:center;font-size:15px;font-weight:{weight};color:{color};">{name}</div>'
    header_row = f'<div style="display:flex;padding:12px 0;border-bottom:1px solid {theme.border};">{header_cells}</div>'

    # Feature rows
    rows = ""
    for fi, feat in enumerate(features):
        cells = f'<div style="flex:2;font-size:15px;color:{theme.text_primary};">{feat}</div>'
        for ci, co in enumerate(companies):
            checks = co.get("checks", [])
            val = checks[fi] if fi < len(checks) else False
            is_accent = ci == accent_col
            if val:
                icon = f'<span style="color:{theme.accent};">&#10003;</span>'
            else:
                icon = f'<span style="color:{theme.text_muted};">&#10007;</span>'
            cells += f'<div style="flex:1;text-align:center;font-size:16px;">{icon}</div>'
        rows += f'<div style="display:flex;padding:14px 0;border-bottom:1px solid {theme.border}08;align-items:center;">{cells}</div>'

    return f'<div>{header_row}{rows}</div>'


def accent_callout(text: str, title: str, theme: Theme) -> str:
    """Accent-tinted callout box (green-tinted for warm tech, blue-tinted for consulting)."""
    title_html = f'<div style="font-size:16px;font-weight:700;color:{theme.text_primary};margin-bottom:8px;">{title}</div>' if title else ""
    return f'''<div style="background:{theme.accent}0a;border-radius:14px;padding:28px;">
  {title_html}
  <div style="font-size:15px;color:{theme.text_secondary};line-height:1.6;">{text}</div>
</div>'''


# =============================================================================
# VISUAL COMPONENTS: Rich visuals
# =============================================================================

def code_block(code: str, theme: Theme, title: str = "") -> str:
    """Syntax-highlighted code block. Already built in visuals.py, re-exported here."""
    from .visuals import code_block as _cb
    return _cb(code, theme, title=title)


def browser_mockup(title: str, url: str, fields: list[dict], button: str, theme: Theme) -> str:
    """Browser window mockup. Already built in visuals.py, re-exported here."""
    from .visuals import browser_mockup as _bm
    return _bm(title=title, url=url, fields=fields, button_text=button, theme=theme)


# =============================================================================
# SLIDE ASSEMBLER: Puts it all together
# =============================================================================

def assemble_slide(
    theme: Theme,
    label: str = "",
    company: str = "",
    headline_text: str = "",
    headline_size: int = 56,
    subtitle_text: str = "",
    layout_html: str = "",
    bottom_html: str = "",
    dark: bool = False,
) -> str:
    """
    Assemble a complete slide from components.

    This is the only function that produces a full HTML document.
    Everything else produces fragments.
    """
    # Dark override
    dark_css = ""
    if dark:
        dark_css = f'''<style>
body {{ background: #0a0a0a; color: #e8e8e8; }}
body::before {{ background: radial-gradient(circle, {theme.accent}1a 0%, {theme.accent}08 50%, transparent 70%); }}
h1 {{ color: #e8e8e8; }}
h1 em {{ color: {theme.accent}; }}
</style>'''

    parts = [
        slide_base(theme),
        dark_css,
        header(theme, label, company),
    ]

    if headline_text:
        parts.append(headline(headline_text, theme, headline_size))
    if subtitle_text:
        parts.append(subtitle(subtitle_text, theme))

    parts.append(layout_html)

    if bottom_html:
        parts.append(bottom_html)

    parts.append(slide_close())
    return "\n".join(parts)


# =============================================================================
# HELPERS
# =============================================================================

def _auto_emph(text: str, theme: Theme) -> str:
    """Auto-emphasize the second sentence in a headline."""
    if not text:
        return text
    parts = text.split(". ")
    if len(parts) == 2 and len(parts[1]) > 0:
        return f'{parts[0]}. <em style="color:{theme.accent};font-style:italic;">{parts[1]}</em>'
    if "\n" in text:
        lines = text.split("\n", 1)
        return f'{lines[0]}<br><em style="color:{theme.accent};font-style:italic;">{lines[1]}</em>'
    return text
