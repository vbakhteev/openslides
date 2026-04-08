"""floom app wrapper for OpenSlides."""
import base64
from pathlib import Path

from floom import app, context
from openslides.main import generate_deck
from openslides.logos import resolve_logo as _resolve_logo
from openslides.versions import load_deck
from openslides.generator import DeckGenerator


@app.action
def generate(
    prompt: str,
    company_url: str = None,
    audience: str = "vc",
    deck_type: str = "pitch",
) -> dict:
    """Generate a branded pitch deck from a prompt and optional company URL."""
    result = generate_deck(
        prompt=prompt,
        company_url=company_url,
        deck_type=deck_type,
        audience=audience,
        api_key=context.get_secret("GEMINI_API_KEY"),
    )

    output = {
        "deck_id": result.deck_id,
        "slide_count": len(result.html_slides),
        "slides": result.html_slides,
    }

    # Always return PDF as base64
    if result.pdf_path:
        pdf_file = Path(result.pdf_path)
        if pdf_file.exists():
            pdf_bytes = pdf_file.read_bytes()
            output["pdf_base64"] = base64.b64encode(pdf_bytes).decode("ascii")
            output["pdf_size_bytes"] = len(pdf_bytes)

    return output


@app.action
def iterate(deck_id: str, prompt: str, slide_indices: list[int]) -> dict:
    """Regenerate specific slides from a previous deck."""
    result = generate_deck(
        prompt=prompt,
        previous_deck_id=deck_id,
        slides_to_regenerate=slide_indices,
        api_key=context.get_secret("GEMINI_API_KEY"),
    )

    output = {
        "deck_id": result.deck_id,
        "slide_count": len(result.html_slides),
    }

    if result.pdf_path:
        pdf_file = Path(result.pdf_path)
        if pdf_file.exists():
            pdf_bytes = pdf_file.read_bytes()
            output["pdf_base64"] = base64.b64encode(pdf_bytes).decode("ascii")
            output["pdf_size_bytes"] = len(pdf_bytes)

    return output


@app.action
def resolve_logo(name: str) -> dict:
    """Find the best logo for a company name or domain."""
    logo = _resolve_logo(name)
    if logo:
        return {"url": logo.url, "format": logo.format, "provider": logo.provider}
    return {"url": "", "format": "", "provider": "none"}
