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

# Weak / abstract queries → better visual search terms
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


def _photos_enabled() -> bool:
    val = getattr(settings, "STOCK_PHOTOS", True)
    if isinstance(val, str):
        return val.lower() not in ("0", "false", "no", "off")
    return bool(val)


def _normalize_query(query: str, label: str = "", title: str = "", image_style: str = "photo") -> str:
    q = (query or label or title or "modern office").strip()
    key = q.lower()

    if key in _QUERY_FALLBACKS:
        q = _QUERY_FALLBACKS[key]
    else:
        # Too short / single abstract word
        words = [w for w in re.findall(r"[A-Za-z]+", q) if len(w) > 2]
        if len(words) <= 1:
            q = _QUERY_FALLBACKS.get(key, f"{q} professional workplace")

    # Append transparent/isolated keywords if requested by layout system
    if image_style == "isolated" and "isolated" not in q.lower():
        q += " isolated cutout"

    return q


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


def fetch_as_data_uri(url: str, timeout: float = 15.0):
    try:
        resp = _session().get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SlideBot/1.0)"},
            allow_redirects=True,
        )
        if resp.status_code != 200:
            logger.warning("Photo download HTTP %s", resp.status_code)
            return None
        data = resp.content
        if not data or len(data) < 1000:
            return None
        # Cap ~800KB raw to keep HTML manageable
        if len(data) > 800_000:
            data = data[:800_000]
        ctype = (resp.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip().lower()
        if "png" in ctype:
            mime = "image/png"
        elif "webp" in ctype:
            mime = "image/webp"
        else:
            mime = "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    except Exception as e:
        logger.warning("Photo download failed: %s", e)
        return None


def css_premium_background(palette: dict, layout_hint: str = "") -> str:
    bg = palette.get("bg", "#0f172a")
    surface = palette.get("surface", "#1e293b")
    primary = palette.get("primary", "#38bdf8")
    accent = palette.get("accent", "#38bdf8")
    hint = (layout_hint or "").lower()
    if hint in ("title", "title-slide", "closing", "thank-you", "end"):
        return (
            f"background-color:{bg};"
            f"background-image:"
            f"radial-gradient(ellipse 80% 60% at 20% 20%, {primary}40 0%, transparent 55%),"
            f"radial-gradient(ellipse 70% 50% at 85% 80%, {accent}30 0%, transparent 50%),"
            f"linear-gradient(160deg, {bg} 0%, {surface} 100%);"
        )
    return (
        f"background-color:{bg};"
        f"background-image:"
        f"linear-gradient(165deg, {bg} 0%, {surface} 100%),"
        f"radial-gradient(ellipse at 0% 100%, {accent}20 0%, transparent 45%);"
    )


def resolve_slide_background(
        title: str,
        label: str,
        content: str,
        tone: str,
        layout_hint: str,
        palette: dict,
        image_query: str = "",
        image_spec: dict = None,
):
    if not _photos_enabled():
        return None

    spec = image_spec or {}
    q_input = spec.get("pexels_query") or image_query
    orientation = spec.get("orientation", "landscape")
    image_style = spec.get("image_style", "photo")

    query = _normalize_query(q_input, label, title, image_style=image_style)
    logger.info("Photo query (AI→normalized): '%s'", query)

    url = search_pexels_candidates(query, orientation=orientation)
    source = "pexels"
    if not url:
        url = lorem_flickr_url(query)
        source = "loremflickr"
        logger.info("Fallback Lorem Flickr for '%s'", query)

    data_uri = fetch_as_data_uri(url, timeout=15.0)
    if data_uri:
        logger.info("Photo embedded from %s (%d KB)", source, len(data_uri) // 1024)
        return data_uri

    logger.warning("Embed failed (%s) — remote URL", source)
    return url


def inject_background(html: str, image_url, palette: dict, layout_hint: str = "") -> str:
    """
    Inject photo as a dedicated full-bleed layer (not only CSS background).
    Uses a gradient dynamic overlay mask so text remains clear and readable.
    """
    if not html:
        return html

    if not image_url:
        bg_css = css_premium_background(palette, layout_hint)
        m = re.search(r"(<div\s+[^>]*style\s*=\s*)([\"'])([^\"']*)\2", html, re.I)
        if not m:
            return html
        quote_char = m.group(2)
        style = re.sub(r"background(-color|-image)?\s*:[^;]+;?", "", m.group(3), flags=re.I)
        style = style.rstrip("; ") + ";" + bg_css
        return html[: m.start()] + m.group(1) + quote_char + style + quote_char + html[m.end() :]

    safe = str(image_url).replace('"', "%22")

    # Enhanced Overlay Filter Layer to maintain clear text contrast
    photo_layer = (
        f'<div style="position:absolute;inset:0;z-index:0;pointer-events:none;'
        f'background-image:url(&quot;{safe}&quot;);'
        f'background-size:cover;background-position:center;background-repeat:no-repeat;"></div>'
        f'<div style="position:absolute;inset:0;z-index:0;pointer-events:none;'
        f'background:linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.55) 100%);"></div>'
    )

    # Ensure root is position:relative and content sits above the photo
    m = re.search(r"(<div\s+[^>]*style\s*=\s*)([\"'])([^\"']*)\2(\s*>)", html, re.I)
    if not m:
        return (
            f'<div style="position:relative;overflow:hidden;">'
            f"{photo_layer}<div style=\"position:relative;z-index:1;\">{html}</div></div>"
        )

    quote_char = m.group(2)
    style = m.group(3)
    # Strip conflicting backgrounds from root so photo layer shows through
    style = re.sub(r"background(-color|-image)?\s*:[^;]+;?", "", style, flags=re.I)
    if "position:" not in style.lower():
        style = style.rstrip("; ") + ";position:relative;"
    if "overflow:" not in style.lower():
        style = style.rstrip("; ") + ";overflow:hidden;"
    # Keep a subtle base color in case image fails
    bg = palette.get("bg", "#0f172a")
    style = style.rstrip("; ") + f";background-color:{bg};"

    # Wrap existing inner HTML with z-index:1 so text is above photo
    open_end = m.end()
    after = html[open_end:]
    last_close = after.rfind("</div>")
    if last_close >= 0:
        inner = after[:last_close]
        tail = after[last_close:]
        new_html = (
                html[: m.start()]
                + m.group(1)
                + quote_char
                + style
                + quote_char
                + m.group(4)
                + photo_layer
                + f'<div style="position:relative;z-index:1;width:100%;height:100%;box-sizing:border-box;">'
                + inner
                + "</div>"
                + tail
        )
        return new_html

    return (
            html[: m.start()]
            + m.group(1)
            + quote_char
            + style
            + quote_char
            + m.group(4)
            + photo_layer
            + html[open_end:]
    )