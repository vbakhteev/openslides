"""
OpenSlides Main Entry Point
Prompt + URL -> base64-encoded PDF pitch deck.
"""
from __future__ import annotations

import base64
import sys
import tempfile
from pathlib import Path


def generate_deck(prompt: str, company_url: str | None = None) -> str:
    """
    Generate a branded pitch deck and return the PDF as a base64-encoded string.

    Args:
        prompt: what the deck is about
        company_url: company website to scrape brand from

    Returns:
        Base64-encoded PDF string
    """
    from .generator import DeckGenerator, BrandContext
    from .theme import Theme, LightTheme
    from .scraper import scrape_brand

    # --- Step 1: Brand context ---
    brand = BrandContext()
    if company_url:
        print(f"Scraping brand from {company_url}...", file=sys.stderr)
        brand = scrape_brand(company_url)

    # --- Step 2: Theme ---
    theme = LightTheme()
    if brand.colors or brand.fonts:
        theme = Theme.from_brand(brand)

    # --- Step 3: Generate content ---
    gen = DeckGenerator()
    print("Generating pitch deck...", file=sys.stderr)
    config = gen.generate(prompt=prompt, brand=brand, audience="vc", deck_type="pitch")

    # --- Step 4: Render HTML ---
    print("Rendering slides...", file=sys.stderr)
    html_slides = gen.render(config, theme=theme)

    # --- Step 5: Export PDF ---
    print("Exporting PDF...", file=sys.stderr)
    from .export import export_pdf_sync

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "deck.pdf"
        export_pdf_sync(html_slides, pdf_path)
        pdf_bytes = pdf_path.read_bytes()

    pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")
    print(f"Done: {len(html_slides)} slides, {len(pdf_bytes)} bytes", file=sys.stderr)
    return pdf_base64


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OpenSlides - Prompt + URL -> PDF pitch deck")
    parser.add_argument("prompt", help="What the deck is about")
    parser.add_argument("--url", help="Company URL to scrape brand from")
    args = parser.parse_args()

    result = generate_deck(prompt=args.prompt, company_url=args.url)
    print(result)
