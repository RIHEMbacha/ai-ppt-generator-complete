"""Two-phase presentation pipeline: outline → per-slide HTML."""

import asyncio
import json
import logging
import base64
import re
from typing import List, Optional
import asyncio
import json
import logging
from typing import Any, Dict, List

from .prompts import (
    SINGLE_SLIDE_HTML_SYSTEM,
    SIMPLE_SLIDE_HTML_SYSTEM,
    tone_block,
)
from .constants import SLIDE_WIDTH, SLIDE_HEIGHT


from app.models import OutlineResponse, Presentation, Slide, SlideContent,ImageSelection ,ImageCandidate

from .constants import SLIDE_HEIGHT, SLIDE_WIDTH
from .html_utils import fallback_html, normalize_slide_html, truncate
from .json_utils import extract_json
from .photos import inject_background, resolve_slide_background,rank_images,search_pexels_candidates
from .prompts import (
    OUTLINE_SYSTEM,
    REGEN_SYSTEM,
    SIMPLE_SLIDE_HTML_SYSTEM,
    SINGLE_SLIDE_HTML_SYSTEM,
    resolve_tone,
    tone_block,
)
from .providers import call_llm, call_llm_with_meta

logger = logging.getLogger("llm")


async def generate_outline(
        content: str,
        num_slides: int,
        tone: str
) -> OutlineResponse:

    tone_key = resolve_tone(tone)

    user = (
        f"{tone_block(tone)}\n\n"
        f"Tone requested: {tone}\n"
        f"Resolved tone: {tone_key}\n"
        f"Target number of slides: {num_slides}\n\n"
        "Create the presentation outline based on the source content.\n"
        "Return ONLY valid JSON matching the required schema.\n"
        "Do not add explanations outside the JSON.\n\n"
        "SOURCE CONTENT:\n"
        f"{truncate(content)}\n"
    )

    raw = await asyncio.to_thread(
        call_llm,
        OUTLINE_SYSTEM,
        user,
        8192
    )

    data = extract_json(raw)

    outline = OutlineResponse.model_validate(data)

    for slide in outline.slides:

        query = (slide.image_query or "").strip()

        # This slide doesn't need an image
        if not query:
            continue

        try:
            candidates = await asyncio.to_thread(
                search_pexels_candidates,
                query,
                "landscape",
                5
            )

            candidates = rank_images(
                candidates,
                "landscape"
            )

            slide.image_selection = ImageSelection(
                query=query,
                candidates=[
                    ImageCandidate(
                        url=image["url"],
                        thumbnail_url=image.get("thumbnail_url"),
                        width=image.get("width", 0),
                        height=image.get("height", 0),
                        file_size=image.get("file_size", 0),
                        photographer=image.get(
                            "photographer",
                            ""
                        ),
                        score=image.get(
                            "score",
                            0
                        )
                    )
                    for image in candidates
                ],
                selected_url=None
            )

        except Exception as e:

            logger.warning(
                "Image search failed for slide '%s': %s",
                slide.label,
                e
            )

            slide.image_selection = ImageSelection(
                query=query,
                candidates=[],
                selected_url=None
            )

    # Return the AI outline + photo candidates
    return outline

async def generate_single_slide_html(
        title: str,
        subtitle: str,
        presenters: List[str],
        date: str | None,
        tone: str,
        palette: Dict[str, str],
        slide: Any,
        slide_index: int,
        total_slides: int,
) -> Dict[str, Any]:

    # Convert Pydantic model to dictionary safely.
    if hasattr(slide, "model_dump"):
        slide_data = slide.model_dump()
    elif hasattr(slide, "dict"):
        slide_data = slide.dict()
    elif isinstance(slide, dict):
        slide_data = slide
    else:
        slide_data = {}

    # Selected image from the review screen.
    image_selection = slide_data.get("image_selection") or {}

    selected_image = image_selection.get("selected_url")

    # Keep only useful image information for the LLM.
    image_info = {
        "query": image_selection.get("query", ""),
        "selected_url": selected_image,
    }

    # Remove candidates from the prompt.
    # The LLM only needs the selected image URL.
    slide_for_prompt = {
        "label": slide_data.get("label", "Slide"),
        "objective": slide_data.get("objective", ""),
        "notes": slide_data.get("notes", ""),
        "points": slide_data.get("points", []),
        "stats": slide_data.get("stats", []),
        "chart": slide_data.get("chart"),
        "timeline": slide_data.get("timeline", []),
        "layout_hint": slide_data.get("layout_hint", "content"),
        "image_query": slide_data.get("image_query", ""),
        "image_selection": image_info,
    }

    # Full presentation context.
    presentation_context = {
        "title": title,
        "subtitle": subtitle,
        "presenters": presenters,
        "date": date,
        "tone": tone,
        "palette": palette,
        "slide_number": slide_index + 1,
        "total_slides": total_slides,
    }

    prompt = f"""
PRESENTATION INFORMATION
{json.dumps(presentation_context, ensure_ascii=False, indent=2)}

CURRENT SLIDE CONTENT
{json.dumps(slide_for_prompt, ensure_ascii=False, indent=2)}

==================================================
IMPORTANT
==================================================

The slide above was explicitly reviewed and edited by the user.

You MUST preserve the user's content.

Do NOT:
- invent statistics
- invent chart values
- invent timeline events
- remove meaningful user content
- replace the user's wording unnecessarily
- create information that is not present
- add fake sources

You MAY:
- improve visual hierarchy
- shorten text slightly when necessary for layout
- arrange content professionally
- choose appropriate cards, spacing and typography
- use the selected image if one exists

==================================================
SPECIAL CONTENT
==================================================

If "stats" contains items:
render them as KPI/statistic cards.

If "chart" exists and contains data:
render the chart visually using HTML/CSS.
Do NOT invent data.

If "timeline" contains items:
render the timeline with all meaningful steps.

If "points" contains items:
render the points and their explanations clearly.

If "selected_url" exists:
use that exact image URL.

If no selected image exists:
do not invent an image URL.

==================================================
SLIDE ROLE
==================================================

The layout hint is:

{slide_data.get("layout_hint", "content")}

Respect this layout role.

For a title slide:
- presentation title
- subtitle
- presenters
- date

For an agenda:
- clear numbered agenda items

For big-stats:
- emphasize the statistics

For chart-focus:
- emphasize the chart

For timeline:
- emphasize the timeline

For closing:
- strong conclusion / thank-you

For normal content:
- emphasize the objective and content points.

==================================================
TONE
==================================================

{tone_block(tone)}

==================================================
OUTPUT
==================================================

Return ONLY valid JSON:

{{
  "label": "{slide_data.get("label", "Slide")}",
  "notes": "{slide_data.get("notes", "")}",
  "html": "<div>...</div>"
}}

No markdown.
No explanation.
"""

    # Use your existing LLM provider here.
    result =  call_llm(
        system=SINGLE_SLIDE_HTML_SYSTEM,
        user=prompt,
        max_tokens=5000,
    )

    parsed = extract_json(result)

    return {
        "label": parsed.get(
            "label",
            slide_data.get("label", "Slide"),
        ),
        "notes": parsed.get(
            "notes",
            slide_data.get("notes", ""),
        ),
        "content": slide_data.get("objective", ""),
        "layout_hint": slide_data.get(
            "layout_hint",
            "content",
        ),
        "html": parsed.get("html", ""),
    }



async def generate_html_from_outline(
        title: str,
        subtitle: str,
        tone: str,
        palette: Dict[str, str],
        slides: List[Any],
        presenters: List[str] | None = None,
        date: str | None = None,
):
    """
    Generate HTML for every confirmed slide.

    The frontend sends the complete edited outline:
    - title
    - subtitle
    - presenters
    - date
    - objective
    - points
    - stats
    - chart
    - timeline
    - selected image
    - layout
    """

    presenters = presenters or []

    # Generate each slide independently.
    tasks = [
        generate_single_slide_html(
            title=title,
            subtitle=subtitle,
            presenters=presenters,
            date=date,
            tone=tone,
            palette=palette,
            slide=slide,
            slide_index=index,
            total_slides=len(slides),
        )
        for index, slide in enumerate(slides)
    ]

    generated_slides = await asyncio.gather(*tasks)

    return {
        "title": title or "Presentation",
        "subtitle": subtitle or "",
        "palette": palette or {},
        "slides": generated_slides,
    }
async def regenerate_slide(
    title: str,
    subtitle: str,
    current_html: str,
    instruction: str,
    tone: str,
    palette: Optional[dict] = None,
) -> Slide:
    html_in = (
        current_html if len(current_html) < 8000 else current_html[:8000] + "<!--truncated-->"
    )
    user = (
        f"{tone_block(tone)}\n"
        f"Deck title: {title}\n"
        f"Subtitle: {subtitle}\n"
        f"Tone: {tone}\n"
        f"Instruction: {instruction}\n\n"
        f"Current slide HTML:\n{html_in}\n"
    )
    raw = await asyncio.to_thread(call_llm, REGEN_SYSTEM, user, 8192)
    data = extract_json(raw)
    html = normalize_slide_html(data.get("html") or current_html)
    return Slide(
        html=html,
        label=(data.get("label") or "").strip() or "Slide",
        notes=data.get("notes") or "",
    )
