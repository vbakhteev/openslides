"""
Slide Assembler
Converts slide config + theme into assembled HTML using components_v2.
Each slide type has an assembly recipe that picks layout + components.
"""
from __future__ import annotations

from .theme import Theme, LightTheme, DarkTheme
from .prompts import SLIDE_SCHEMAS
from . import components_v2 as C


def assemble_deck(config: dict, theme: Theme) -> list[str]:
    """Assemble a full deck from config. Returns list of HTML strings."""
    slides = []
    company = ""

    # Extract company name from title slide
    for s in config.get("slides", []):
        if s.get("type") == "title":
            company = s.get("content", {}).get("company_name", "")
            break

    for slide_cfg in config.get("slides", []):
        slide_type = slide_cfg.get("type", "content")
        content = slide_cfg.get("content", {})
        is_dark = slide_cfg.get("theme") == "dark" or SLIDE_SCHEMAS.get(slide_type, {}).get("theme") == "dark"

        # Build dark theme variant preserving custom fonts
        slide_theme = theme
        if is_dark:
            slide_theme = DarkTheme()
            slide_theme.headline_font_family = theme.headline_font_family
            slide_theme.body_font_family = theme.body_font_family
            slide_theme.accent = theme.accent
            slide_theme.accent_secondary = theme.accent_secondary

        assembler = ASSEMBLERS.get(slide_type, _assemble_generic)
        try:
            html = assembler(content, slide_theme, company, is_dark)
        except Exception:
            html = _assemble_generic(content, slide_theme, company, is_dark)

        slides.append(html)

    return slides


# =============================================================================
# ASSEMBLER RECIPES: One per slide type
# =============================================================================

def _assemble_title(content: dict, theme: Theme, company: str, dark: bool) -> str:
    bottom = content.get("bottom_items", [])
    bottom_html = C.metadata_bar(bottom, theme) if bottom else ""

    return C.assemble_slide(
        theme=theme,
        company=company,
        headline_text=content.get("headline", ""),
        headline_size=76,
        subtitle_text=content.get("subheadline", ""),
        layout_html=C.full_width(""),  # flex spacer
        bottom_html=bottom_html,
        dark=dark,
    )


def _assemble_problem(content: dict, theme: Theme, company: str, dark: bool) -> str:
    # Left: dark quote card or stat hero
    story = content.get("story_html", "")
    left_content = f'<div style="font-size:18px;color:{theme.text_secondary};line-height:1.7;">{story}</div>'
    left = C.dark_card(left_content, theme) if story else ""

    # Right: blocker cards with stats
    blockers = content.get("blocker_list", [])
    cards = []
    for b in blockers[:4]:
        if isinstance(b, dict):
            cards.append(C.blocker_card(
                icon_name=b.get("icon", "alert-triangle"),
                title=b.get("title", str(b)),
                desc=b.get("description", ""),
                stat_value=b.get("stat_value", ""),
                stat_label=b.get("stat_label", ""),
                theme=theme,
            ))
        else:
            cards.append(C.blocker_card(
                icon_name="alert-triangle",
                title=str(b),
                desc="",
                stat_value="",
                stat_label="",
                theme=theme,
            ))
    right = "".join(cards) if cards else ""

    layout = C.split(left, f'<div style="display:flex;flex-direction:column;gap:16px;">{right}</div>', "40_60", valign="flex-start") if left and right else C.full_width(left + right)

    return C.assemble_slide(
        theme=theme,
        label=content.get("label", "Problem"),
        company=company,
        headline_text=content.get("headline", ""),
        layout_html=layout,
        dark=dark,
    )


def _assemble_solution(content: dict, theme: Theme, company: str, dark: bool) -> str:
    features = content.get("features", [])
    cols = min(len(features), 3) if features else 2
    if len(features) == 4:
        cols = 2

    cards = []
    for f in features[:6]:
        if isinstance(f, dict):
            cards.append(C.feature_card(
                icon_name=f.get("icon", "") or "star",
                title=f.get("title", ""),
                desc=f.get("description", ""),
                theme=theme,
            ))
        else:
            cards.append(C.feature_card("star", str(f), "", theme))

    return C.assemble_slide(
        theme=theme,
        label=content.get("label", "Solution"),
        company=company,
        headline_text=content.get("headline", ""),
        subtitle_text=content.get("subheadline", ""),
        layout_html=C.full_width(C.grid(cards, cols)),
        dark=dark,
    )


def _assemble_market(content: dict, theme: Theme, company: str, dark: bool) -> str:
    tam = content.get("tam", {})
    sam = content.get("sam", {})
    som = content.get("som", {})

    # TAM/SAM/SOM as stat boxes
    def _market_box(data: dict, accent: bool = False) -> str:
        bg = theme.accent if accent else theme.surface
        text_c = "#fff" if accent else theme.text_primary
        desc_c = "rgba(255,255,255,0.8)" if accent else theme.text_secondary
        border = "" if accent else f"border:1px solid {theme.border};"
        val = data.get("value", "") if isinstance(data, dict) else str(data)
        desc = data.get("description", "") if isinstance(data, dict) else ""
        return (
            f'<div style="background:{bg};{border}border-radius:16px;padding:36px;text-align:center;flex:1;">'
            f'<div style="font-family:{theme.headline_font_family};font-size:44px;color:{text_c};">{val}</div>'
            f'<div style="font-size:13px;color:{desc_c};margin-top:8px;">{desc}</div>'
            f'</div>'
        )

    boxes = f'<div style="display:flex;gap:20px;">{_market_box(tam, accent=True)}{_market_box(sam)}{_market_box(som)}</div>'

    # Segments
    segments = content.get("segments", [])
    seg_html = ""
    for seg in segments[:2]:
        if isinstance(seg, dict):
            items = seg.get("items", [])
            pills = "".join(
                f'<span style="background:{theme.surface};border:1px solid {theme.border};border-radius:20px;padding:6px 16px;font-size:13px;color:{theme.text_secondary};">{it}</span>'
                for it in items[:5] if isinstance(it, str)
            )
            seg_html += f'<div style="margin-top:16px;"><div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:{theme.text_muted};margin-bottom:8px;">{seg.get("title","")}</div><div style="display:flex;gap:8px;flex-wrap:wrap;">{pills}</div></div>'

    return C.assemble_slide(
        theme=theme,
        label=content.get("label", "Market"),
        company=company,
        headline_text=content.get("headline", ""),
        layout_html=C.full_width(f'{boxes}<div style="margin-top:24px;">{seg_html}</div>'),
        dark=dark,
    )


def _assemble_comparison(content: dict, theme: Theme, company: str, dark: bool) -> str:
    columns = content.get("columns", [])

    # Build comparison table from column data
    if not columns or not isinstance(columns[0], dict):
        return _assemble_generic(content, theme, company, dark)

    # Extract features from first column's items
    all_features = []
    for col in columns:
        for item in col.get("items", []):
            if isinstance(item, dict):
                text = item.get("text", "")
                if text and text not in all_features:
                    all_features.append(text)

    # Build companies with check arrays
    companies = []
    for col in columns:
        checks = []
        col_items_text = [it.get("text", "") if isinstance(it, dict) else str(it) for it in col.get("items", [])]
        col_items_good = [it.get("good", False) if isinstance(it, dict) else False for it in col.get("items", [])]
        for feat in all_features:
            if feat in col_items_text:
                idx = col_items_text.index(feat)
                checks.append(col_items_good[idx])
            else:
                checks.append(False)
        companies.append({"name": col.get("name", ""), "checks": checks})

    table = C.comparison_table(all_features, companies, theme, accent_col=content.get("highlight_column", 0))

    return C.assemble_slide(
        theme=theme,
        label=content.get("label", "Competition"),
        company=company,
        headline_text=content.get("headline", ""),
        layout_html=C.full_width(table),
        dark=dark,
    )


def _assemble_traction(content: dict, theme: Theme, company: str, dark: bool) -> str:
    # Left: status card
    status = content.get("status_box", {})
    left = ""
    if isinstance(status, dict) and status:
        stage = status.get("stage", status.get("title", ""))
        desc = status.get("description", "")
        left = C.dark_card(
            f'{C.section_label("Current Stage", Theme(text_muted="rgba(255,255,255,0.6)"))}'
            f'<div style="font-family:{theme.headline_font_family};font-size:36px;margin-bottom:8px;">{stage}</div>'
            f'<div style="font-size:15px;opacity:0.85;line-height:1.5;">{desc}</div>',
            theme,
        )

    # Right: milestones
    milestones = content.get("milestones", [])
    right = C.milestone_timeline(milestones, theme) if milestones else ""

    if left and right:
        layout = C.split(left, right, "50_50", valign="flex-start")
    else:
        layout = C.full_width(left or right)

    return C.assemble_slide(
        theme=theme,
        label=content.get("label", "Traction"),
        company=company,
        headline_text=content.get("headline", ""),
        layout_html=layout,
        dark=dark,
    )


def _assemble_funds(content: dict, theme: Theme, company: str, dark: bool) -> str:
    # Left: ask card + fund bars
    fund_items = content.get("fund_items", [])
    left = C.fund_bars(fund_items, theme)

    # Right: milestones
    milestones = content.get("milestones", [])
    right = ""
    if milestones:
        right = f'{C.section_label("Milestones", theme)}{C.milestone_timeline(milestones, theme)}'

    if left and right:
        layout = C.split(left, right, "50_50", valign="flex-start")
    else:
        layout = C.full_width(left or right)

    return C.assemble_slide(
        theme=theme,
        label=content.get("label", "The Ask"),
        company=company,
        headline_text=content.get("headline", ""),
        subtitle_text=content.get("subheadline", ""),
        layout_html=layout,
        dark=dark,
    )


def _assemble_team_ask(content: dict, theme: Theme, company: str, dark: bool) -> str:
    # Left: founder info
    name = content.get("founder_name", "")
    title = content.get("founder_title", "")
    bios = content.get("bio_items", [])

    bio_html = ""
    for b in bios:
        if isinstance(b, dict):
            bio_html += f'''<div style="margin-bottom:16px;">
  <div style="font-size:17px;font-weight:700;color:{"#e8e8e8" if dark else theme.text_primary};">{b.get("company","")}</div>
  <div style="font-size:14px;color:{"#999" if dark else theme.text_secondary};margin-top:4px;line-height:1.4;">{b.get("detail","")}</div>
</div>'''

    contact = content.get("contact_info", {})
    contact_html = ""
    if isinstance(contact, dict):
        items = [f'{k}: {v}' for k, v in contact.items()]
        contact_html = f'<div style="display:flex;gap:24px;margin-top:20px;">' + "".join(
            f'<span style="font-size:13px;color:{"#666" if dark else theme.text_muted};">{it}</span>' for it in items
        ) + '</div>'

    left = f'''<div style="font-family:{theme.headline_font_family};font-size:36px;color:{"#e8e8e8" if dark else theme.text_primary};margin-bottom:8px;">{name}</div>
<div style="font-size:17px;color:{"#777" if dark else theme.text_muted};margin-bottom:28px;">{title}</div>
{bio_html}
{contact_html}'''

    # Right: ask card
    ask = content.get("ask_amount", "")
    uses = content.get("ask_uses", [])
    uses_html = "".join(f'<div style="font-size:15px;color:{"#999" if dark else theme.text_secondary};margin-bottom:8px;">{u}</div>' for u in uses if isinstance(u, str))

    right_inner = f'''{C.section_label("The Ask", Theme(text_muted="rgba(255,255,255,0.5)") if dark else theme)}
<div style="font-family:{theme.headline_font_family};font-size:56px;color:{theme.accent};margin-bottom:20px;">{ask}</div>
{uses_html}'''

    if dark:
        right = f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px;">{right_inner}</div>'
    else:
        right = C.surface_card(right_inner, theme)

    layout = C.split(left, right, "50_50")

    return C.assemble_slide(
        theme=theme,
        company=company,
        label="Team & Ask",
        headline_text="",
        layout_html=layout,
        dark=dark,
    )


def _assemble_generic(content: dict, theme: Theme, company: str, dark: bool) -> str:
    """Fallback for any slide type without a specific assembler."""
    body = content.get("content_html", content.get("story_html", content.get("subheadline", "")))
    return C.assemble_slide(
        theme=theme,
        label=content.get("label", ""),
        company=company,
        headline_text=content.get("headline", ""),
        subtitle_text="",
        layout_html=C.full_width(f'<div style="font-size:20px;color:{theme.text_secondary};line-height:1.8;max-width:900px;">{body}</div>'),
        dark=dark,
    )


# Registry
ASSEMBLERS = {
    "title": _assemble_title,
    "problem": _assemble_problem,
    "solution": _assemble_solution,
    "market": _assemble_market,
    "comparison": _assemble_comparison,
    "traction": _assemble_traction,
    "funds": _assemble_funds,
    "team_ask": _assemble_team_ask,
}
