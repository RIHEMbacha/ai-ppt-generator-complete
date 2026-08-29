"""HTML utilities for slide generation."""

import re
from typing import Dict, Any

from .constants import SLIDE_WIDTH, SLIDE_HEIGHT


def normalize_slide_html(html: str) -> str:
    """Normalize HTML: ensure root div, remove bad tags."""
    if not html:
        return f'<div style="width:{SLIDE_WIDTH}px;height:{SLIDE_HEIGHT}px;box-sizing:border-box;overflow:hidden;padding:48px;display:flex;align-items:center;justify-content:center;"></div>'

    html = html.strip()

    # Remove markdown fence
    html = re.sub(r'^```html?\n', '', html)
    html = re.sub(r'\n```$', '', html)

    # Ensure root div has required styles
    if not html.startswith('<div'):
        html = f'<div style="width:{SLIDE_WIDTH}px;height:{SLIDE_HEIGHT}px;box-sizing:border-box;overflow:hidden;padding:48px;">{html}</div>'

    # Check root div has required dimensions
    if 'width:' not in html[:200] or f'{SLIDE_WIDTH}px' not in html[:500]:
        html = html.replace(
            '<div',
            f'<div style="width:{SLIDE_WIDTH}px;height:{SLIDE_HEIGHT}px;box-sizing:border-box;overflow:hidden;"',
            1
        )

    return html


def truncate(text: str, max_chars: int = 6000) -> str:
    """Truncate text for LLM context."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[...truncated {len(text) - max_chars} chars]"


def fallback_html(slide: Dict[str, Any], palette: Dict[str, str]) -> str:
    """
    Generate minimal fallback HTML when LLM fails.
    Simplified structure with good contrast for photo backgrounds.
    """
    label = slide.get("label", "Slide")
    content = slide.get("content", "")
    layout_hint = slide.get("layout_hint", "content")

    bg = palette.get("bg", "#0f172a")
    text = palette.get("text", "#f8fafc")
    primary = palette.get("primary", "#38bdf8")

    # Use semi-transparent cards for photo compatibility
    card_bg = "rgba(255, 255, 255, 0.08)"
