"""
Generate all 10 test decks and create a comparison viewer.
Run after every engine change to check for improvement across the board.

Usage: GEMINI_API_KEY=... python tests/generate_all.py
"""
import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
if not os.environ.get("GEMINI_API_KEY"):
    print("Set GEMINI_API_KEY env var first"); sys.exit(1)

from test_prompts import TEST_PROMPTS
from openslides.generator import DeckGenerator
from openslides.scraper import scrape_brand
from openslides.theme import Theme, LightTheme

OUT_DIR = Path.home() / ".openslides" / "test-suite"
OUT_DIR.mkdir(parents=True, exist_ok=True)

gen = DeckGenerator(api_key=os.environ["GEMINI_API_KEY"])
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
    brand = None
    if tp["url"]:
        brand = scrape_brand(tp["url"])

    # Generate
    t0 = time.time()
    try:
        config = gen.generate(
            prompt=tp["prompt"],
            brand=brand,
            audience=tp["audience"],
            model="gemini-3-flash-preview",
        )
        elapsed = time.time() - t0

        slides = config.get("slides", [])
        print(f"  {len(slides)} slides in {elapsed:.1f}s:")
        for i, s in enumerate(slides):
            h = s.get("content", {}).get("headline", "?")[:50]
            print(f"    {i+1}. [{s.get('type')}] {h}")

        # Render
        html_slides = gen.render(config, theme=theme)

        # Save
        for i, html in enumerate(html_slides, 1):
            (deck_dir / f"slide-{i:02d}.html").write_text(html)

        # Save config
        (deck_dir / "config.json").write_text(json.dumps(config, indent=2))

        # Create viewer
        viewer = [
            '<!DOCTYPE html><html><head><meta charset="UTF-8">',
            f'<title>{deck_id}</title>',
            '<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#e8e8e6}',
            'h2{text-align:center;padding:20px;font-family:sans-serif;color:#333}',
            '.sf{width:1920px;height:1080px;margin:20px auto;box-shadow:0 4px 40px rgba(0,0,0,.15)}',
            '.sf iframe{width:1920px;height:1080px;border:none}</style></head><body>',
            f'<h2>{deck_id}</h2>',
        ]
        for i in range(1, len(html_slides) + 1):
            viewer.append(f'<div class="sf"><iframe src="slide-{i:02d}.html"></iframe></div>')
        viewer.append('</body></html>')
        (deck_dir / "deck.html").write_text("\n".join(viewer))

        results.append({
            "id": deck_id,
            "slides": len(html_slides),
            "time": round(elapsed, 1),
            "status": "ok",
        })

    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FAILED: {e}")
        results.append({
            "id": deck_id,
            "slides": 0,
            "time": round(elapsed, 1),
            "status": f"error: {str(e)[:80]}",
        })

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
ok = sum(1 for r in results if r["status"] == "ok")
print(f"{ok}/{len(results)} decks generated successfully\n")
for r in results:
    status = "OK" if r["status"] == "ok" else "FAIL"
    print(f"  [{status}] {r['id']}: {r['slides']} slides, {r['time']}s")

# Build master comparison viewer (all decks on one page)
master = [
    '<!DOCTYPE html><html><head><meta charset="UTF-8">',
    '<title>OpenSlides Test Suite</title>',
    '<style>',
    '*{margin:0;padding:0;box-sizing:border-box}',
    'body{background:#1a1a1a;color:#fff;font-family:sans-serif;padding:40px}',
    'h1{text-align:center;margin-bottom:40px;font-size:28px}',
    '.deck{margin-bottom:60px}',
    '.deck h2{font-size:20px;margin-bottom:16px;color:#999}',
    '.deck h2 span{color:#059669}',
    '.slides{display:flex;gap:12px;overflow-x:auto;padding-bottom:12px}',
    '.slide-thumb{flex-shrink:0;width:384px;height:216px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.3)}',
    '.slide-thumb iframe{width:1920px;height:1080px;border:none;transform:scale(0.2);transform-origin:top left;pointer-events:none}',
    '</style></head><body>',
    '<h1>OpenSlides Test Suite - 10 Decks</h1>',
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
print(f"Individual decks: {OUT_DIR}/{{deck_id}}/deck.html")

# Save results
(OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
