"""
Generate all 10 test decks using the Gemini renderer.
Run after every change to check quality across the board.

Usage: GEMINI_API_KEY=... python tests/generate_all_v2.py
"""
import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("GEMINI_API_KEY", "REDACTED_GEMINI_KEY")

from test_prompts import TEST_PROMPTS
from openslides.renderer import render_deck
from openslides.scraper import scrape_brand
from openslides.theme import Theme, LightTheme

OUT_DIR = Path.home() / ".openslides" / "test-suite-v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = []

for tp in TEST_PROMPTS:
    deck_id = tp["id"]
    deck_dir = OUT_DIR / deck_id
    deck_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Generating: {deck_id}")
    print(f"{'='*60}")

    # Theme
    if tp["theme_override"]:
        theme = Theme.from_brand(tp["theme_override"])
    elif tp["url"]:
        brand = scrape_brand(tp["url"])
        theme = Theme.from_brand(brand)
    else:
        theme = LightTheme()

    # Brand context
    brand_context = None
    if tp["url"]:
        brand = scrape_brand(tp["url"])
        brand_context = {
            "company_name": brand.company_name,
            "description": brand.description[:200] if brand.description else "",
            "domain": brand.domain,
        }

    t0 = time.time()
    try:
        slides = render_deck(
            brief=tp["prompt"],
            theme=theme,
            brand_context=brand_context,
            audience=tp["audience"],
            style="warm-tech",
            model="gemini-3-flash-preview",
        )
        elapsed = time.time() - t0

        print(f"  {len(slides)} slides in {elapsed:.1f}s")

        # Save slides
        for i, html in enumerate(slides, 1):
            (deck_dir / f"slide-{i:02d}.html").write_text(html)

        # Viewer
        viewer = [
            '<!DOCTYPE html><html><head><meta charset="UTF-8">',
            f'<title>{deck_id}</title>',
            '<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#1a1a1a;padding:20px}',
            'h2{text-align:center;padding:20px;font-family:sans-serif;color:#999}',
            '.sf{width:1920px;height:1080px;margin:20px auto;box-shadow:0 4px 40px rgba(0,0,0,.3);border-radius:8px;overflow:hidden}',
            '.sf iframe{width:1920px;height:1080px;border:none}</style></head><body>',
            f'<h2>{deck_id}</h2>',
        ]
        for i in range(1, len(slides) + 1):
            viewer.append(f'<div class="sf"><iframe src="slide-{i:02d}.html"></iframe></div>')
        viewer.append('</body></html>')
        (deck_dir / "deck.html").write_text("\n".join(viewer))

        results.append({"id": deck_id, "slides": len(slides), "time": round(elapsed, 1), "status": "ok"})

    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FAILED: {e}")
        results.append({"id": deck_id, "slides": 0, "time": round(elapsed, 1), "status": f"error: {str(e)[:80]}"})

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
ok = sum(1 for r in results if r["status"] == "ok")
print(f"{ok}/{len(results)} decks generated\n")
for r in results:
    status = "OK" if r["status"] == "ok" else "FAIL"
    print(f"  [{status}] {r['id']}: {r['slides']} slides, {r['time']}s")

# Master viewer with thumbnail strips
master = [
    '<!DOCTYPE html><html><head><meta charset="UTF-8">',
    '<title>OpenSlides v2 Test Suite (Gemini Renderer)</title>',
    '<style>',
    '*{margin:0;padding:0;box-sizing:border-box}',
    'body{background:#0a0a0a;color:#fff;font-family:system-ui,sans-serif;padding:40px}',
    'h1{text-align:center;margin-bottom:40px;font-size:28px;color:#e8e8e8}',
    '.deck{margin-bottom:48px}',
    '.deck h2{font-size:18px;margin-bottom:12px;color:#777}',
    '.deck h2 span{color:#059669;font-size:14px}',
    '.slides{display:flex;gap:8px;overflow-x:auto;padding-bottom:8px}',
    '.slide-thumb{flex-shrink:0;width:384px;height:216px;border-radius:6px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.4)}',
    '.slide-thumb iframe{width:1920px;height:1080px;border:none;transform:scale(0.2);transform-origin:top left;pointer-events:none}',
    '</style></head><body>',
    '<h1>OpenSlides v2 - Gemini Renderer - 10 Decks</h1>',
]

for r in results:
    if r["status"] != "ok":
        continue
    deck_id = r["id"]
    master.append(f'<div class="deck">')
    master.append(f'<h2>{deck_id} <span>({r["slides"]} slides, {r["time"]}s)</span></h2>')
    master.append(f'<div class="slides">')
    for i in range(1, r["slides"] + 1):
        master.append(f'<div class="slide-thumb"><iframe src="{deck_id}/slide-{i:02d}.html"></iframe></div>')
    master.append('</div></div>')

master.append('</body></html>')
(OUT_DIR / "index.html").write_text("\n".join(master))

print(f"\nMaster viewer: {OUT_DIR / 'index.html'}")
(OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
