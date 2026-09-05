"""
LLM service package – two-phase presentation generation.

Public API (same as the old monolithic llm.py):
  - generate_outline
  - generate_outline_from_document
  - generate_html_from_outline
  - regenerate_slide
"""

from .pipeline import (
    generate_html_from_outline,
    generate_outline,
    generate_outline_from_document,
    regenerate_slide,
)

__all__ = [
    "generate_outline",
    "generate_outline_from_document",
    "generate_html_from_outline",
    "regenerate_slide",
]
