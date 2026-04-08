"""
System prompts for deck generation.
Few-shot approach: show what great looks like, not just describe it.
"""
from __future__ import annotations

import json

SLIDE_SCHEMAS: dict[str, dict] = {
    "title": {
        "required": ["company_name", "headline", "subheadline"],
        "optional": ["bottom_items"],
        "theme": "dark",
    },
    "problem": {
        "required": ["headline", "story_html"],
        "optional": ["blocker_list", "label"],
        "theme": "light",
    },
    "solution": {
        "required": ["headline", "subheadline", "features"],
        "optional": ["label"],
        "theme": "light",
    },
    "market": {
        "required": ["headline", "tam", "sam", "som"],
        "optional": ["segments", "label"],
        "theme": "light",
    },
    "comparison": {
        "required": ["headline", "columns"],
        "optional": ["highlight_column", "label"],
        "theme": "light",
    },
    "traction": {
        "required": ["headline"],
        "optional": ["status_box", "milestones", "label"],
        "theme": "light",
    },
    "funds": {
        "required": ["headline", "subheadline", "fund_items"],
        "optional": ["milestones", "label"],
        "theme": "light",
    },
    "team_ask": {
        "required": ["founder_name", "founder_title", "bio_items", "ask_amount", "ask_uses"],
        "optional": ["contact_info"],
        "theme": "dark",
    },
    "validation": {
        "required": ["headline", "quotes"],
        "optional": ["bottom_stat", "label"],
        "theme": "light",
    },
    "demo": {
        "required": ["headline", "flow_items"],
        "optional": ["label"],
        "theme": "light",
    },
    "pricing": {
        "required": ["headline", "tiers"],
        "optional": ["unit_economics", "label"],
        "theme": "light",
    },
}

# --- Few-shot example: a real, high-quality pitch deck ---
# This is the quality bar. Every generated deck should match this level.

_EXAMPLE_DECK = [
    {
        "type": "title",
        "company_name": "acme",
        "headline": "The Production Layer for AI Scripts",
        "subheadline": "AI writes the code. We ship it.",
        "bottom_items": ["Pre-Seed", "$200K SAFE", "Federico De Ponte", "2026"]
    },
    {
        "type": "problem",
        "headline": "Millions of Useful Tools Get Built Every Day. They Die on Localhost.",
        "label": "Problem",
        "story_html": "<p>16M developers now use AI coding tools. They can build anything in hours. But <strong>less than 1% of these scripts ever reach a user</strong>.</p><p>The gap between 'it works on my machine' and 'anyone can use it' kills 99% of AI-generated tools. No deployment path. No UI. No API. Just code trapped in a terminal.</p>",
        "blocker_list": [
            "No deployment path for scripts",
            "No auto-generated UI for end users",
            "No API or integration layer",
            "Security, auth, and scaling are unsolved"
        ]
    },
    {
        "type": "solution",
        "headline": "Write a Function. Get an App.",
        "subheadline": "One command deploys any Python script as a production app with UI, API, and shareable link. Under 60 seconds.",
        "label": "Solution",
        "features": [
            {"title": "Live URL", "description": "Instant shareable link for anyone"},
            {"title": "Web UI", "description": "Auto-generated interface from your function signature"},
            {"title": "REST API", "description": "Programmatic access for integrations"},
            {"title": "MCP Server", "description": "AI agents can discover and use your tool"}
        ]
    },
    {
        "type": "market",
        "headline": "A $24B Market. No Production Layer Exists Yet.",
        "label": "Market",
        "tam": {"value": "$24B", "description": "AI-assisted developer tools (2026)"},
        "sam": {"value": "$4.8B", "description": "Script deployment and hosting"},
        "som": {"value": "$120M", "description": "Vibecoder deployment tools"},
        "segments": [
            {"title": "Vibecoders", "items": ["ChatGPT power users building tools", "Cursor/Copilot developers", "Non-technical builders who can prompt but not deploy"]}
        ]
    },
    {
        "type": "comparison",
        "headline": "Not a Hosting Platform. A New Abstraction.",
        "label": "Competition",
        "columns": [
            {"name": "acme", "items": [
                {"text": "One-command deploy from script", "good": True},
                {"text": "Auto-generated UI", "good": True},
                {"text": "MCP server built-in", "good": True},
                {"text": "AI-agent native distribution", "good": True}
            ]},
            {"name": "Replit", "items": [
                {"text": "Full IDE, steep learning curve", "good": False},
                {"text": "Manual UI building", "good": False},
                {"text": "No MCP support", "good": False},
                {"text": "Developer-focused only", "good": False}
            ]},
            {"name": "Railway", "items": [
                {"text": "Docker-based, requires config", "good": False},
                {"text": "No UI generation", "good": False},
                {"text": "No MCP support", "good": False},
                {"text": "Infrastructure-focused", "good": False}
            ]}
        ],
        "highlight_column": 0
    },
    {
        "type": "traction",
        "headline": "Built the Prototype Solo. Ready for First Users.",
        "label": "Status",
        "status_box": {
            "stage": "Prototype",
            "description": "Core engine built. Control plane, runner, UI, CLI all functional.",
            "metrics": {"code_coverage": "1,300+ tests", "ai_tokens": "50B+ tokens used in development"}
        },
        "milestones": [
            {"date": "Q1 2026", "title": "Prototype complete", "status": "done"},
            {"date": "Q2 2026", "title": "Private beta (50 users)", "status": "current"},
            {"date": "Q3 2026", "title": "Public launch", "status": "upcoming"},
            {"date": "Q4 2026", "title": "1,000 deployed apps", "status": "upcoming"}
        ]
    },
    {
        "type": "funds",
        "headline": "Raising $200K to Go from Prototype to Product.",
        "subheadline": "Friends & Family Round. SAFE, $8M cap, MFN.",
        "label": "The Ask",
        "fund_items": [
            {"label": "Engineering", "amount": "$80K", "percentage": 40},
            {"label": "Infrastructure", "amount": "$50K", "percentage": 25},
            {"label": "Go-to-Market", "amount": "$40K", "percentage": 20},
            {"label": "Runway Buffer", "amount": "$30K", "percentage": 15}
        ],
        "milestones": [
            {"month": "M1-3", "text": "Private beta, 50 users"},
            {"month": "M4-6", "text": "Public launch, 500 users"},
            {"month": "M7-9", "text": "Revenue, seed-ready metrics"}
        ]
    },
    {
        "type": "team_ask",
        "founder_name": "Federico De Ponte",
        "founder_title": "Founder & CEO",
        "bio_items": [
            {"company": "SCAILE", "detail": "Co-founded AI visibility engine. Scaled to $600K ARR, team of 10. Raised $500K total."},
            {"company": "advisupply consulting", "detail": "At 20, led 27 consultants. Scaled to 6-figure revenue in under 2 years."}
        ],
        "ask_amount": "$200K",
        "ask_uses": ["MVP launch and private beta", "First 100 deployed apps", "3-month runway to seed metrics"],
        "contact_info": {"email": "fede@acme.com", "linkedin": "linkedin.com/in/federicodeponte"}
    }
]

_AUDIENCE_LENS: dict[str, str] = {
    "vc": (
        "Target: venture capital investors. "
        "Emphasize defensible moat, market size with bottoms-up math, "
        "unit economics, growth metrics, clear path to 10x returns. "
        "Hard numbers over adjectives. Show why this is a $1B+ opportunity."
    ),
    "angel": (
        "Target: angel investors. "
        "Lead with the founder story and personal conviction. "
        "Emphasize vision, early signal, why this team will win. "
        "Angels invest in people; make the narrative personal and compelling."
    ),
    "ff": (
        "Target: friends and family. "
        "Build trust and clarity. Explain the business simply, no jargon. "
        "Emphasize what the money will be used for, the timeline, "
        "and why you are the right person. Transparency matters most."
    ),
    "customer": (
        "Target: potential customers. "
        "Lead with their pain, show the solution in action, prove value. "
        "Include social proof, pricing clarity, clear next step. "
        "No fundraising language; focus on their ROI."
    ),
}

_DECK_STRUCTURES: dict[str, dict] = {
    "pitch": {
        "slide_count": "8-11",
        "sequence": ["title", "problem", "solution", "market", "comparison", "traction", "funds", "team_ask"],
        "optional_inserts": ["validation", "demo", "pricing"],
    },
    "sales": {
        "slide_count": "7-9",
        "sequence": ["title", "problem", "solution", "demo", "comparison", "pricing", "team_ask"],
    },
    "update": {
        "slide_count": "8-10",
        "sequence": ["title", "traction", "problem", "solution", "market", "funds", "team_ask"],
    },
    "general": {
        "slide_count": "6-15",
        "sequence": [],
    },
}


def get_deck_prompt(
    brief: str,
    brand_context: dict | None = None,
    audience: str = "vc",
    deck_type: str = "pitch",
) -> str:
    """Build the full prompt for deck generation. Uses few-shot example."""
    audience_lens = _AUDIENCE_LENS.get(audience, _AUDIENCE_LENS["vc"])
    structure = _DECK_STRUCTURES.get(deck_type, _DECK_STRUCTURES["pitch"])

    brand_block = ""
    if brand_context:
        parts = []
        for key in ["company_name", "description", "domain", "team", "pricing", "features"]:
            val = brand_context.get(key)
            if val:
                parts.append(f"- {key}: {val}")
        if parts:
            brand_block = "\n## Company Context\n" + "\n".join(parts)

    sequence_str = " -> ".join(structure["sequence"]) if structure["sequence"] else "flexible"
    optional = ", ".join(structure.get("optional_inserts", []))

    example_json = json.dumps(_EXAMPLE_DECK, indent=2)

    return f"""You are an expert pitch deck writer. Your job: generate specific, punchy, memorable slide content.

## Quality Standard
Study this example deck carefully. Match this quality level:
- Headlines are short, specific, and position the company clearly
- Every claim has a number or concrete detail
- Problem slides tell a story with emotional stakes
- Solution slides show the "aha moment" in one sentence
- No generic phrases like "revolutionary", "cutting-edge", "transform"
- No filler. Every word earns its place.

## Example (this is what great looks like)
```json
{example_json}
```

## Your Task
Generate a {deck_type} deck for the brief below. {audience_lens}

Slide sequence: {sequence_str}
{"Optional additions if relevant: " + optional if optional else ""}
Target: {structure['slide_count']} slides.
{brand_block}

## Content Rules
1. Headlines: max 10 words. Specific, not generic. "A $24B Market" not "A Massive Opportunity".
2. Story: every problem slide needs a narrative with stakes, not a list of complaints.
3. Numbers: use specific figures. "$600K ARR" not "significant revenue". "16M developers" not "millions".
4. Solution: lead with the user's action, not the technology. "Write a function. Get an app." not "Our platform leverages..."
5. Comparison: be honest about trade-offs. Don't claim you're better at everything.
6. team_ask bio_items: each bio_item needs "company" and "detail" keys. Detail must include a specific metric.
7. fund_items: each needs "label", "amount", "percentage" keys. Percentages must sum to 100.
8. All nested objects use the exact key names from the example.
9. TAM > SAM > SOM, always.
10. No "[INFERRED]" tags. If you lack info, make a credible specific estimate.

## Output
Return ONLY a JSON array of slide objects. No commentary, no markdown fences. Match the example format exactly.

## Brief
{brief}"""


def get_refinement_prompt(slide_type: str, current_content: dict) -> str:
    """Prompt for refining a single slide."""
    content_str = json.dumps(current_content, indent=2)
    return f"""Improve this {slide_type} slide. Make it more specific, more memorable, and punchier.

Current content:
```json
{content_str}
```

Rules:
- Replace generic language with specific claims and numbers
- Headlines under 10 words
- If the headline doesn't make you stop and pay attention, rewrite it
- Keep the same JSON structure. Return ONLY the improved JSON object."""
