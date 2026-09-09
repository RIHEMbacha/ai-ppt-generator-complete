"""
Stock photos for slides — Pexels (primary) + Lorem Flickr (fallback).
AI provides image specifications in the outline; this module fetches existing photos.
No Unsplash. No AI image generation.
"""

import base64
import logging
import re
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter, Retry

from app.config import settings

logger = logging.getLogger("llm")

_QUERY_FALLBACKS = {
    "closing": "business handshake success",
    "closing & call to action": "team celebrating success office",
    "call to action": "startup team collaboration",
    "thank you": "audience applause conference",
    "title": "modern office skyline",
    "title slide": "modern office skyline",
    "agenda": "notebook planning desk",
    "plan": "roadmap strategy whiteboard",
    "roadmap": "highway road journey aerial",
    "enterprise blueprint": "architecture blueprint building",
    "conclusion": "mountain peak sunrise",
    "takeaways": "checklist notebook desk",
    "introduction": "open book light window",
}


def _session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=2, backoff_factor=0.8, status_forcelist=[500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def search_pexels_candidates(
        query: str,
        orientation: str = "landscape",
        per_page: int = 5,
):
    key = getattr(settings, "PEXELS_API_KEY", None)

    if not key:
        logger.warning(
            "PEXELS_API_KEY not configured"
        )
        return []

    q = (query or "").strip()

    if not q:
        return []

    try:

        resp = _session().get(
            "https://api.pexels.com/v1/search",
            params={
                "query": q,
                "per_page": per_page,
                "orientation": orientation,
            },
            headers={
                "Authorization": key
            },
            timeout=12,
        )

        if resp.status_code != 200:
            logger.warning(
                "Pexels HTTP %s",
                resp.status_code
            )
            return []

        photos = (
                         resp.json() or {}
                 ).get("photos") or []

        candidates = []

        for photo in photos:

            src = photo.get("src") or {}

            original = src.get("original")
            large = (
                    src.get("large2x")
                    or src.get("large")
            )

            if not large:
                continue

            candidates.append({
                "url": large,

                "thumbnail_url": (
                        src.get("medium")
                        or src.get("small")
                        or large
                ),

                "width": int(
                    photo.get("width") or 0
                ),

                "height": int(
                    photo.get("height") or 0
                ),

                "photographer": (
                        photo.get("photographer")
                        or ""
                ),

                "photographer_url": (
                        photo.get("photographer_url")
                        or ""
                ),

                "original_url": original or large,

                "id": photo.get("id"),
            })

        return candidates[:per_page]

    except Exception as e:

        logger.warning(
            "Pexels candidate search failed: %s",
            e
        )

        return []

def score_image(
        image: dict,
        target_orientation: str = "landscape",
) -> float:

    width = image.get("width") or 0
    height = image.get("height") or 0

    if width <= 0 or height <= 0:
        return 0.0

    megapixels = (
                         width * height
                 ) / 1_000_000

    resolution_score = min(
        megapixels / 8.0,
        1.0
    )

    ratio = width / height

    if target_orientation == "landscape":

        orientation_score = (
            1.0
            if ratio >= 1.45
            else 0.6
        )

    elif target_orientation == "portrait":

        orientation_score = (
            1.0
            if ratio <= 0.8
            else 0.6
        )

    else:

        orientation_score = (
            1.0
            if 0.85 <= ratio <= 1.15
            else 0.6
        )


    size_score = min(
        width / 2400,
        1.0
    )
    composition_score = 1.0

    if target_orientation == "landscape":

        if ratio >= 1.6:
            composition_score = 1.0
        elif ratio >= 1.3:
            composition_score = 0.8
        else:
            composition_score = 0.5

    score = (
            resolution_score * 0.40
            + orientation_score * 0.25
            + size_score * 0.20
            + composition_score * 0.15
    )

    return round(
        score * 100,
        2
    )

def rank_images(
        candidates: list,
        orientation: str = "landscape",
):
    for image in candidates:

        image["score"] = score_image(
            image,
            orientation
        )

    return sorted(
        candidates,
        key=lambda x: x.get("score", 0),
        reverse=True
    )

def lorem_flickr_url(query: str, width: int = 1280, height: int = 720) -> str:
    tags = re.sub(r"[^a-zA-Z0-9\s]", " ", query or "office")
    tags = ",".join(t for t in tags.lower().split() if len(t) > 2)[:60] or "office,business"
    seed = abs(hash(query or "office")) % 100000
    return f"https://loremflickr.com/{width}/{height}/{quote(tags)}?lock={seed}"


