# OpenSlides Demo: Floom Pitch Deck

## The Prompt

```
Raise $500K pre-seed for Floom, an AI-powered platform that turns Python scripts into live apps with UI, API, and MCP — no frontend code needed. Vibecoders write the logic, Floom handles everything else.
```

## Parameters

| Field | Value |
|---|---|
| `prompt` | See above |
| `company_url` | https://floom.dev |
| `audience` | vc |
| `deck_type` | pitch |
| `format` | pdf |

## CLI Command (internal)

```bash
cd ~/openslides-v2 && PYTHONPATH=. python3 -c "
from openslides.main import generate_deck
result = generate_deck(
    prompt='Raise \$500K pre-seed for Floom, an AI-powered platform that turns Python scripts into live apps with UI, API, and MCP — no frontend code needed. Vibecoders write the logic, Floom handles everything else.',
    company_url='https://floom.dev',
    audience='vc',
    format='pdf',
    output_dir='examples/floom-demo'
)
print('PDF:', result.pdf_path)
"
```
