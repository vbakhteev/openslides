"""OpenSlides - Prompt + URL -> branded pitch deck."""
from __future__ import annotations

from .theme import Theme, DarkTheme, LightTheme
from .logos import LogoResult, resolve_logo, resolve_logos
from .generator import DeckGenerator, BrandContext
from .main import generate_deck

__version__ = "2.0.0"
__all__ = [
    "Theme",
    "DarkTheme",
    "LightTheme",
    "LogoResult",
    "resolve_logo",
    "resolve_logos",
    "DeckGenerator",
    "BrandContext",
    "generate_deck",
]
