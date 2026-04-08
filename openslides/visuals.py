"""
Visual components for slides.
Code blocks, browser mockups, charts, stat badges.
Reusable HTML snippets embedded in slide templates.
"""
from __future__ import annotations
import html as html_module
from .theme import Theme, LightTheme
from .icons import get_icon_svg


def code_block(
    code: str,
    theme: Theme | None = None,
    language: str = "python",
    title: str = "",
    width: str = "100%",
) -> str:
    """Syntax-highlighted code block with dark green background."""
    theme = theme or LightTheme()
    escaped = html_module.escape(code)

    # Basic Python syntax highlighting via CSS
    keywords = ["from", "import", "def", "return", "class", "if", "else", "for", "in", "async", "await", "with", "as", "yield", "None", "True", "False"]
    decorators_pattern = "@\\w+"
    strings_css = "color: #a5d6a7;"  # light green for strings
    keyword_css = "color: #81c784;"  # green for keywords
    comment_css = "color: #6a9955;"  # muted green for comments

    # Simple keyword highlighting
    for kw in keywords:
        escaped = escaped.replace(f'{kw} ', f'<span style="{keyword_css}">{kw}</span> ')
        escaped = escaped.replace(f'{kw}\n', f'<span style="{keyword_css}">{kw}</span>\n')

    # Highlight @decorators
    import re
    escaped = re.sub(r'(@\w+)', f'<span style="color:#4db6ac;">\\1</span>', escaped)

    # Highlight strings
    escaped = re.sub(r'(&quot;[^&]*&quot;|&#x27;[^&]*&#x27;)', f'<span style="{strings_css}">\\1</span>', escaped)
    escaped = re.sub(r'("[^"]*")', f'<span style="{strings_css}">\\1</span>', escaped)

    # Highlight comments
    escaped = re.sub(r'(#[^\n]*)', f'<span style="{comment_css}">\\1</span>', escaped)

    title_html = f'<div style="font-size:13px;color:rgba(255,255,255,0.4);margin-bottom:12px;">{title}</div>' if title else ""

    return f'''<div style="background:#064E3B;border-radius:14px;padding:32px;font-family:'JetBrains Mono',monospace;font-size:15px;line-height:1.7;color:#e8e8e8;width:{width};overflow:hidden;">
{title_html}<pre style="margin:0;white-space:pre-wrap;">{escaped}</pre></div>'''


def browser_mockup(
    title: str = "My App",
    url: str = "my-app.example.com",
    fields: list[dict] | None = None,
    button_text: str = "Submit",
    badge_text: str = "Live",
    theme: Theme | None = None,
    width: str = "100%",
) -> str:
    """Browser window mockup with form fields and CTA button."""
    theme = theme or LightTheme()
    fields = fields or []

    fields_html = ""
    for field in fields[:4]:
        label = field.get("label", "")
        value = field.get("value", "")
        fields_html += f'''<div style="margin-bottom:16px;">
<div style="font-size:13px;color:{theme.text_muted};margin-bottom:6px;">{label}</div>
<div style="padding:12px 16px;border:1px solid {theme.border};border-radius:8px;font-size:15px;color:{theme.text_primary};background:{theme.background};">{value}</div>
</div>'''

    return f'''<div style="background:{theme.surface};border:1px solid {theme.border};border-radius:16px;overflow:hidden;width:{width};box-shadow:0 8px 32px rgba(0,0,0,0.08);">
<div style="height:40px;background:{theme.background};border-bottom:1px solid {theme.border};display:flex;align-items:center;padding:0 16px;gap:8px;">
<div style="width:10px;height:10px;border-radius:50%;background:#ff5f57;"></div>
<div style="width:10px;height:10px;border-radius:50%;background:#febc2e;"></div>
<div style="width:10px;height:10px;border-radius:50%;background:#28c840;"></div>
<div style="margin-left:12px;padding:4px 14px;background:{theme.surface};border-radius:6px;font-size:12px;color:{theme.text_muted};font-family:monospace;">{url}</div>
</div>
<div style="padding:32px;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
<span style="font-size:22px;font-weight:700;color:{theme.text_primary};">{title}</span>
<span style="font-size:12px;padding:3px 10px;background:rgba(5,150,105,0.1);color:{theme.accent};border-radius:12px;font-weight:600;">{badge_text}</span>
</div>
{fields_html}
<div style="padding:14px 0;background:{theme.accent};border-radius:10px;text-align:center;color:#fff;font-size:16px;font-weight:600;margin-top:8px;">{button_text}</div>
</div>
</div>'''


def stat_badge(
    value: str,
    label: str = "",
    theme: Theme | None = None,
) -> str:
    """Large stat number with label."""
    theme = theme or LightTheme()
    return f'''<div style="display:inline-flex;align-items:baseline;gap:12px;">
<span style="font-family:{theme.headline_font_family};font-size:64px;font-weight:400;color:{theme.accent};">{value}</span>
<span style="font-size:18px;color:{theme.text_muted};">{label}</span>
</div>'''


def output_badges(
    items: list[str] | None = None,
    theme: Theme | None = None,
) -> str:
    """Row of output type badges (Live URL, Web UI, REST API, MCP)."""
    theme = theme or LightTheme()
    items = items or ["Live URL", "Web UI", "REST API", "MCP"]
    badges = ""
    for item in items:
        icon = get_icon_svg(
            {"Live URL": "link", "Web UI": "layout", "REST API": "code", "MCP": "wifi"}.get(item, "star"),
            theme.accent, 16,
        )
        badges += f'''<span style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:{theme.surface};border:1px solid {theme.border};border-radius:20px;font-size:14px;color:{theme.text_secondary};">{icon}{item}</span>'''
    return f'<div style="display:flex;gap:10px;flex-wrap:wrap;">{badges}</div>'


def deploy_command(
    command: str = "$ openslides deploy",
    stat_value: str = "<60s",
    theme: Theme | None = None,
) -> str:
    """Deploy command badge with stat."""
    theme = theme or LightTheme()
    return f'''<div style="display:inline-flex;align-items:center;gap:16px;">
<span style="padding:8px 20px;background:#064E3B;border-radius:8px;font-family:monospace;font-size:15px;color:#e8e8e8;">{command}</span>
<span style="font-family:{theme.headline_font_family};font-size:48px;color:{theme.accent};">{stat_value}</span>
</div>'''
