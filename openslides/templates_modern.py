"""
Modern slide templates.
High-quality HTML renderers for the pitch deck design system.
Warm background, DM Serif Display headlines, Plus Jakarta Sans body, emerald accent.
"""
from __future__ import annotations
from typing import Optional
from .theme import Theme, LightTheme, DarkTheme
from .icons import auto_icon, get_icon_svg


def _base(theme: Theme, title: str = "Slide") -> str:
    """Common HTML head with theme fonts and print-safe CSS."""
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
  padding: 64px 80px; display: flex; flex-direction: column;
  position: relative;
}}
body::before {{
  content: ''; position: absolute; top: -100px; right: 100px;
  width: 700px; height: 700px; pointer-events: none; border-radius: 50%;
  background: radial-gradient(circle, {theme.accent}14 0%, {theme.accent}08 50%, transparent 70%);
}}
.logo {{ display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }}
.logo-dot {{ width: 24px; height: 24px; background: {theme.accent}; border-radius: 6px; }}
.logo-text {{ font-family: {theme.headline_font_family}; font-size: 22px; font-weight: 400; letter-spacing: -0.5px; }}
.section-label {{ font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: {theme.text_muted}; }}
h1 {{
  font-family: {theme.headline_font_family}; font-size: 56px; font-weight: 400;
  line-height: 1.12; letter-spacing: -0.02em; color: {theme.text_primary}; margin-bottom: 24px;
}}
h1 em {{ color: {theme.accent}; font-style: italic; }}
.subtitle {{ font-size: 20px; color: {theme.text_secondary}; line-height: 1.6; max-width: 700px; }}
</style>'''


def _close() -> str:
    return "\n</body></html>"


def _header(theme: Theme, label: str = "", company: str = "") -> str:
    return f'''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-shrink:0;">
  <div class="logo">
    <div class="logo-dot"></div>
    <span class="logo-text">{company}</span>
  </div>
  <span class="section-label">{label}</span>
</div>'''


def render_title(
    company_name: str,
    headline: str,
    subheadline: str,
    bottom_items: list[str] | None = None,
    theme: Theme | None = None,
    **_,
) -> str:
    """Dark title slide with left-aligned headline."""
    theme = theme or DarkTheme()
    bottom_items = bottom_items or []
    bottom_html = "".join(
        f'<span style="font-size:14px;font-weight:500;color:{theme.text_muted};">{item}</span>'
        + (f'<div style="width:1px;height:14px;background:{theme.border};margin:0 24px;"></div>' if i < len(bottom_items) - 1 else "")
        for i, item in enumerate(bottom_items)
    )

    return f'''{_base(theme, company_name)}
<style>
body {{ background: #0a0a0a; color: #e8e8e8; justify-content: space-between; }}
body::before {{ background: radial-gradient(circle, {theme.accent}1a 0%, {theme.accent}08 50%, transparent 70%); }}
.logo-text {{ color: #e8e8e8; }}
h1 {{ font-size: 76px; color: #e8e8e8; max-width: 900px; }}
h1 em {{ color: {theme.accent}; }}
.subtitle {{ color: #999; }}
</style>
</head><body>
<div class="logo">
  <div class="logo-dot"></div>
  <span class="logo-text">{company_name}</span>
</div>
<div style="flex:1;display:flex;align-items:center;">
  <div>
    <h1>{_emph(headline, theme)}</h1>
    <p class="subtitle">{subheadline}</p>
  </div>
</div>
<div style="display:flex;align-items:center;gap:0;">
  {bottom_html}
</div>
{_close()}'''


def render_problem(
    headline: str,
    story_html: str = "",
    blocker_list: list[str] | None = None,
    label: str = "Problem",
    theme: Theme | None = None,
    **_,
) -> str:
    """Problem slide with story and blocker cards."""
    theme = theme or LightTheme()
    blockers = blocker_list or []
    blocker_html = ""
    if blockers:
        cards = "".join(
            f'<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:12px;'
            f'padding:20px 24px;display:flex;gap:14px;align-items:flex-start;">'
            f'{auto_icon(b, theme.text_muted, 20)}'
            f'<span style="font-size:16px;color:{theme.text_secondary};line-height:1.5;">{b}</span>'
            f'</div>'
            for b in blockers
        )
        blocker_html = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:40px;">{cards}</div>'

    return f'''{_base(theme, "Problem")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;">
  <div style="font-size:20px;color:{theme.text_secondary};line-height:1.8;max-width:900px;">{story_html}</div>
  {blocker_html}
</div>
{_close()}'''


def render_solution(
    headline: str,
    subheadline: str,
    features: list[dict] | None = None,
    label: str = "Solution",
    theme: Theme | None = None,
    **_,
) -> str:
    """Solution slide: headline + subtitle on top, feature cards with icons filling the space below."""
    theme = theme or LightTheme()
    features = features or []

    # Two-row layout: 3 features top, remaining below. Or 2x2. Adapt to count.
    count = len(features)
    if count <= 3:
        cols = count or 2
    elif count == 4:
        cols = 2
    else:
        cols = 3

    feat_cards = ""
    for f in features[:6]:
        title = f.get("title", "") if isinstance(f, dict) else str(f)
        desc = f.get("description", "") if isinstance(f, dict) else ""
        feat_cards += (
            f'<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:14px;padding:28px 32px;'
            f'display:flex;gap:20px;align-items:flex-start;">'
            f'<div style="flex-shrink:0;width:44px;height:44px;border-radius:10px;background:{theme.accent}10;'
            f'display:flex;align-items:center;justify-content:center;">{auto_icon(title, theme.accent, 22)}</div>'
            f'<div>'
            f'<div style="font-size:18px;font-weight:700;color:{theme.text_primary};margin-bottom:4px;">{title}</div>'
            f'<div style="font-size:14px;color:{theme.text_secondary};line-height:1.5;">{desc}</div>'
            f'</div></div>'
        )

    return f'''{_base(theme, "Solution")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<p class="subtitle" style="margin-bottom:8px;">{subheadline}</p>
<div style="flex:1;display:flex;align-items:center;">
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:16px;width:100%;">
    {feat_cards}
  </div>
</div>
{_close()}'''


def render_market(
    headline: str,
    tam: dict | None = None,
    sam: dict | None = None,
    som: dict | None = None,
    segments: list[dict] | None = None,
    label: str = "Market",
    theme: Theme | None = None,
    **_,
) -> str:
    """Market slide with TAM/SAM/SOM boxes."""
    theme = theme or LightTheme()
    tam = tam or {}
    sam = sam or {}
    som = som or {}

    def _market_box(data: dict, accent: bool = False) -> str:
        bg = f"{theme.accent}" if accent else theme.surface
        text = "#fff" if accent else theme.text_primary
        desc_color = "rgba(255,255,255,0.8)" if accent else theme.text_secondary
        return (
            f'<div style="background:{bg};border-radius:16px;padding:40px;text-align:center;'
            f'{"" if accent else f"border:1px solid {theme.border};"}flex:1;">'
            f'<div style="font-family:{theme.headline_font_family};font-size:48px;font-weight:400;color:{text};">'
            f'{data.get("value", "")}</div>'
            f'<div style="font-size:14px;color:{desc_color};margin-top:8px;">{data.get("description", "")}</div>'
            f'</div>'
        )

    seg_html = ""
    if segments:
        for seg in segments[:2]:
            if isinstance(seg, dict):
                items = seg.get("items", [])
                if isinstance(items, list):
                    item_tags = "".join(f'<span style="background:{theme.surface};border:1px solid {theme.border};'
                                       f'border-radius:20px;padding:6px 16px;font-size:14px;color:{theme.text_secondary};">'
                                       f'{it}</span>' for it in items[:5] if isinstance(it, str))
                    seg_html += f'<div style="margin-top:12px;"><div style="font-size:14px;font-weight:600;color:{theme.text_muted};margin-bottom:8px;">{seg.get("title","")}</div><div style="display:flex;gap:8px;flex-wrap:wrap;">{item_tags}</div></div>'

    return f'''{_base(theme, "Market")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;">
  <div style="display:flex;gap:24px;margin-bottom:40px;">
    {_market_box(tam, accent=True)}
    {_market_box(sam)}
    {_market_box(som)}
  </div>
  {seg_html}
</div>
{_close()}'''


def render_team_ask(
    founder_name: str = "",
    founder_title: str = "",
    bio_items: list[dict] | None = None,
    ask_amount: str = "",
    ask_uses: list[str] | None = None,
    contact_info: dict | None = None,
    theme: Theme | None = None,
    **_,
) -> str:
    """Team + Ask slide, dark themed."""
    theme = theme or DarkTheme()
    bio_items = bio_items or []
    ask_uses = ask_uses or []
    contact_info = contact_info or {}

    bio_html = "".join(
        f'<div style="margin-bottom:16px;">'
        f'<div style="font-size:18px;font-weight:700;color:#e8e8e8;">{b.get("company", "")}</div>'
        f'<div style="font-size:15px;color:#999;margin-top:4px;">{b.get("detail", "")}</div>'
        f'</div>'
        for b in bio_items
    )

    uses_html = "".join(
        f'<li style="font-size:16px;color:#999;margin-bottom:8px;">{u}</li>'
        for u in ask_uses
    )

    contact_html = ""
    if contact_info:
        items = []
        for k, v in contact_info.items():
            items.append(f'<span style="font-size:14px;color:#777;">{k}: {v}</span>')
        contact_html = '<div style="display:flex;gap:24px;margin-top:24px;">' + "".join(items) + '</div>'

    return f'''{_base(theme, "Team")}
<style>
body {{ background: #0a0a0a; color: #e8e8e8; }}
body::before {{ background: radial-gradient(circle, {theme.accent}12 0%, transparent 60%); }}
.logo-text {{ color: #e8e8e8; }}
h1 {{ color: #e8e8e8; }}
</style>
</head><body>
{_header(theme, "Team & Ask")}
<div style="flex:1;display:flex;gap:80px;align-items:center;">
  <div style="flex:1;">
    <div style="font-family:{theme.headline_font_family};font-size:36px;color:#e8e8e8;margin-bottom:8px;">{founder_name}</div>
    <div style="font-size:18px;color:#777;margin-bottom:32px;">{founder_title}</div>
    {bio_html}
    {contact_html}
  </div>
  <div style="flex:1;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:48px;">
    <div style="font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:#777;margin-bottom:16px;">The Ask</div>
    <div style="font-family:{theme.headline_font_family};font-size:56px;color:{theme.accent};margin-bottom:24px;">{ask_amount}</div>
    <ul style="list-style:none;padding:0;">{uses_html}</ul>
  </div>
</div>
{_close()}'''


def render_traction(
    headline: str,
    status_box: dict | None = None,
    milestones: list[dict] | None = None,
    label: str = "Traction",
    theme: Theme | None = None,
    **_,
) -> str:
    """Traction slide with status box and timeline."""
    theme = theme or LightTheme()
    status_box = status_box or {}
    milestones = milestones or []

    status_html = ""
    if status_box:
        stage = status_box.get("stage", status_box.get("title", ""))
        desc = status_box.get("description", "")
        status_html = (
            f'<div style="background:{theme.accent};border-radius:16px;padding:40px;color:#fff;margin-bottom:32px;">'
            f'<div style="font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;opacity:0.7;margin-bottom:8px;">Current Stage</div>'
            f'<div style="font-family:{theme.headline_font_family};font-size:36px;margin-bottom:12px;">{stage}</div>'
            f'<div style="font-size:16px;opacity:0.85;line-height:1.5;">{desc}</div>'
            f'</div>'
        )

    ms_html = ""
    if milestones:
        items = ""
        for m in milestones:
            if isinstance(m, dict):
                status = m.get("status", "upcoming")
                dot_color = theme.accent if status == "done" else (theme.text_muted if status == "upcoming" else theme.accent)
                opacity = "1" if status != "upcoming" else "0.5"
                items += (
                    f'<div style="display:flex;gap:16px;align-items:flex-start;opacity:{opacity};">'
                    f'<div style="width:12px;height:12px;border-radius:50%;background:{dot_color};margin-top:4px;flex-shrink:0;"></div>'
                    f'<div><div style="font-size:13px;color:{theme.text_muted};">{m.get("date", "")}</div>'
                    f'<div style="font-size:17px;color:{theme.text_primary};font-weight:500;">{m.get("title", "")}</div></div>'
                    f'</div>'
                )
        ms_html = f'<div style="display:flex;flex-direction:column;gap:20px;">{items}</div>'

    return f'''{_base(theme, "Traction")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;gap:48px;align-items:center;">
  <div style="flex:1;">{status_html}</div>
  <div style="flex:1;">{ms_html}</div>
</div>
{_close()}'''


def render_comparison(
    headline: str,
    columns: list[dict] | None = None,
    highlight_column: int = 0,
    label: str = "Competition",
    theme: Theme | None = None,
    **_,
) -> str:
    """Comparison slide with column cards."""
    theme = theme or LightTheme()
    columns = columns or []

    col_html = ""
    for i, col in enumerate(columns[:4]):
        if not isinstance(col, dict):
            continue
        is_highlight = i == highlight_column
        bg = theme.accent if is_highlight else theme.surface
        text = "#fff" if is_highlight else theme.text_primary
        items_html = ""
        for item in col.get("items", [])[:6]:
            if isinstance(item, dict):
                good = item.get("good", False)
                icon = "+" if good else "-"
                icon_color = "#10b981" if good else "#ef4444"
                if is_highlight:
                    icon_color = "#fff" if good else "rgba(255,255,255,0.4)"
                items_html += (
                    f'<div style="display:flex;gap:8px;margin-bottom:8px;font-size:15px;color:{"rgba(255,255,255,0.85)" if is_highlight else theme.text_secondary};">'
                    f'<span style="color:{icon_color};font-weight:700;">{icon}</span> {item.get("text", "")}'
                    f'</div>'
                )
        col_html += (
            f'<div style="background:{bg};border-radius:16px;padding:32px;flex:1;'
            f'{"" if is_highlight else f"border:1px solid {theme.border};"}{"box-shadow:0 8px 32px rgba(0,0,0,0.12);" if is_highlight else ""}">'
            f'<div style="font-size:20px;font-weight:700;color:{text};margin-bottom:20px;">{col.get("name", "")}</div>'
            f'{items_html}'
            f'</div>'
        )

    return f'''{_base(theme, "Competition")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;gap:24px;align-items:flex-start;padding-top:24px;">
  {col_html}
</div>
{_close()}'''


def render_funds(
    headline: str,
    subheadline: str = "",
    fund_items: list[dict] | None = None,
    milestones: list[dict] | None = None,
    label: str = "The Ask",
    theme: Theme | None = None,
    **_,
) -> str:
    """Funds / Ask slide with allocation bars and milestones."""
    theme = theme or LightTheme()
    fund_items = fund_items or []
    milestones = milestones or []

    bars_html = ""
    for f in fund_items:
        if isinstance(f, dict):
            pct = f.get("percentage", 25)
            bars_html += (
                f'<div style="margin-bottom:16px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:15px;margin-bottom:6px;">'
                f'<span style="color:{theme.text_primary};font-weight:600;">{f.get("label", "")}</span>'
                f'<span style="color:{theme.text_muted};">{f.get("amount", "")}</span></div>'
                f'<div style="height:8px;background:{theme.surface};border-radius:4px;overflow:hidden;">'
                f'<div style="height:100%;width:{pct}%;background:{theme.accent};border-radius:4px;"></div></div></div>'
            )

    ms_html = ""
    for m in milestones:
        if isinstance(m, dict):
            ms_html += (
                f'<div style="display:flex;gap:16px;margin-bottom:12px;">'
                f'<span style="font-size:14px;font-weight:600;color:{theme.accent};min-width:60px;">{m.get("month", "")}</span>'
                f'<span style="font-size:15px;color:{theme.text_secondary};">{m.get("text", "")}</span></div>'
            )

    return f'''{_base(theme, "The Ask")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<p class="subtitle">{subheadline}</p>
<div style="flex:1;display:flex;gap:80px;align-items:center;">
  <div style="flex:1;">{bars_html}</div>
  <div style="flex:1;">{ms_html}</div>
</div>
{_close()}'''


def _emph(text: str, theme: Theme) -> str:
    """Make the last phrase italic+accent if the headline has a period or is multi-sentence."""
    if not text:
        return text
    # If there's a period mid-sentence, emphasize the second part
    parts = text.split(". ")
    if len(parts) == 2:
        return f'{parts[0]}. <em>{parts[1]}</em>'
    # If there's a line break, emphasize the second line
    if "\n" in text:
        lines = text.split("\n", 1)
        return f'{lines[0]}<br><em>{lines[1]}</em>'
    return text


def render_validation(
    headline: str,
    quotes: list[dict] | None = None,
    bottom_stat: dict | str | None = None,
    label: str = "Validation",
    theme: Theme | None = None,
    **_,
) -> str:
    """Validation slide with quote cards."""
    theme = theme or LightTheme()
    quotes = quotes or []

    cards = ""
    for q in quotes[:4]:
        if isinstance(q, dict):
            quote_text = q.get("quote", str(q))
            author = q.get("author", "")
            role = q.get("role", "")
            emphasis = q.get("emphasis", [])
            display_text = quote_text
            for emp in (emphasis if isinstance(emphasis, list) else []):
                if isinstance(emp, str) and emp in display_text:
                    display_text = display_text.replace(emp, f'<strong style="color:{theme.accent};">{emp}</strong>')
            cards += (
                f'<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:14px;padding:32px;">'
                f'<div style="font-size:17px;color:{theme.text_secondary};line-height:1.6;margin-bottom:16px;">&ldquo;{display_text}&rdquo;</div>'
                f'<div style="font-size:14px;font-weight:600;color:{theme.text_primary};">{author}</div>'
                f'<div style="font-size:13px;color:{theme.text_muted};">{role}</div>'
                f'</div>'
            )
        elif isinstance(q, str):
            cards += (
                f'<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:14px;padding:32px;">'
                f'<div style="font-size:17px;color:{theme.text_secondary};line-height:1.6;">&ldquo;{q}&rdquo;</div></div>'
            )

    cols = 2 if len(quotes) <= 4 else 3

    stat_html = ""
    if isinstance(bottom_stat, dict):
        stat_html = (
            f'<div style="margin-top:32px;display:flex;align-items:baseline;gap:12px;">'
            f'<span style="font-family:{theme.headline_font_family};font-size:36px;color:{theme.accent};">{bottom_stat.get("number", "")}</span>'
            f'<span style="font-size:16px;color:{theme.text_muted};">{bottom_stat.get("text", "")}</span></div>'
        )

    return f'''{_base(theme, "Validation")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;">
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:20px;">{cards}</div>
  {stat_html}
</div>
{_close()}'''


def render_demo(
    headline: str,
    flow_items: list[str] | None = None,
    label: str = "Product",
    theme: Theme | None = None,
    **_,
) -> str:
    """Demo/product slide with flow steps."""
    theme = theme or LightTheme()
    flow_items = flow_items or []

    steps = ""
    for i, item in enumerate(flow_items):
        text = item if isinstance(item, str) else str(item)
        steps += (
            f'<div style="display:flex;align-items:center;gap:20px;">'
            f'<div style="width:48px;height:48px;border-radius:50%;background:{theme.accent};color:#fff;'
            f'display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;flex-shrink:0;">{i+1}</div>'
            f'<div style="font-size:20px;color:{theme.text_primary};font-weight:500;">{text}</div>'
            f'</div>'
        )
        if i < len(flow_items) - 1:
            steps += f'<div style="width:2px;height:24px;background:{theme.border};margin-left:23px;"></div>'

    return f'''{_base(theme, "Product")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;align-items:center;justify-content:center;">
  <div style="display:flex;flex-direction:column;gap:8px;">{steps}</div>
</div>
{_close()}'''


def render_pricing(
    headline: str,
    tiers: list[dict] | None = None,
    unit_economics: dict | None = None,
    label: str = "Business Model",
    theme: Theme | None = None,
    **_,
) -> str:
    """Pricing slide with tier cards."""
    theme = theme or LightTheme()
    tiers = tiers or []

    cards = ""
    for i, tier in enumerate(tiers[:4]):
        if not isinstance(tier, dict):
            continue
        is_primary = i == 1 and len(tiers) >= 3  # middle tier highlighted
        bg = theme.accent if is_primary else theme.surface
        text = "#fff" if is_primary else theme.text_primary
        price_color = "#fff" if is_primary else theme.accent
        feat_color = "rgba(255,255,255,0.8)" if is_primary else theme.text_secondary

        features_html = ""
        for feat in tier.get("features", [])[:5]:
            f_text = feat if isinstance(feat, str) else str(feat)
            features_html += f'<div style="font-size:14px;color:{feat_color};margin-bottom:6px;">+ {f_text}</div>'

        period = tier.get("period", "month")
        cards += (
            f'<div style="background:{bg};border-radius:16px;padding:36px;flex:1;'
            f'{"" if is_primary else f"border:1px solid {theme.border};"}text-align:center;">'
            f'<div style="font-size:18px;font-weight:700;color:{text};margin-bottom:16px;">{tier.get("name", "")}</div>'
            f'<div style="font-family:{theme.headline_font_family};font-size:40px;color:{price_color};margin-bottom:4px;">{tier.get("price", "")}</div>'
            f'<div style="font-size:13px;color:{feat_color};margin-bottom:24px;">/{period}</div>'
            f'<div style="text-align:left;">{features_html}</div>'
            f'</div>'
        )

    return f'''{_base(theme, "Pricing")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;gap:24px;align-items:center;">
  {cards}
</div>
{_close()}'''


def render_content(
    headline: str,
    content_html: str = "",
    label: str = "",
    theme: Theme | None = None,
    **_,
) -> str:
    """Generic content slide."""
    theme = theme or LightTheme()
    return f'''{_base(theme, "Slide")}
</head><body>
{_header(theme, label)}
<h1>{_emph(headline, theme)}</h1>
<div style="flex:1;display:flex;align-items:center;">
  <div style="font-size:20px;color:{theme.text_secondary};line-height:1.8;max-width:1000px;">{content_html}</div>
</div>
{_close()}'''


# Registry mapping slide types to modern renderers
MODERN_RENDERERS = {
    "title": render_title,
    "problem": render_problem,
    "solution": render_solution,
    "market": render_market,
    "comparison": render_comparison,
    "traction": render_traction,
    "funds": render_funds,
    "team_ask": render_team_ask,
    "validation": render_validation,
    "demo": render_demo,
    "pricing": render_pricing,
    "content": render_content,
}
