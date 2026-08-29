"""Export Presentation → PPTX or simple HTML."""

import io
import re
from typing import List

from app.models import Presentation, Slide


async def export_presentation(pres: Presentation, fmt: str = "pptx") -> bytes:
    fmt = (fmt or "pptx").lower()
    if fmt == "html":
        return _export_html(pres)
    return _export_pptx(pres)


def _export_html(pres: Presentation) -> bytes:
    slides_html = []
    for i, s in enumerate(pres.slides):
        slides_html.append(
            f'<section class="slide" id="slide-{i+1}">\n{s.html}\n</section>'
        )
    body = "\n".join(slides_html)
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{_esc(pres.title)}</title>
<style>
  body {{ margin:0; background:#111; font-family:system-ui,sans-serif; }}
  .slide {{ margin:24px auto; box-shadow:0 8px 32px rgba(0,0,0,.4); }}
  @media print {{ .slide {{ page-break-after:always; margin:0; box-shadow:none; }} }}
</style>
</head>
<body>
{body}
</body>
</html>"""
    return doc.encode("utf-8")


def _export_pptx(pres: Presentation) -> bytes:
    """
    Lightweight PPTX export.
    Each slide is rendered as a single full-bleed image placeholder is not used;
    instead we put the HTML content as notes and a simple title box.
    For true visual fidelity the frontend should screenshot the HTML slides
    and embed images; this keeps the dependency light.
    """
    try:
        from pptx import Presentation as PptxPresentation
        from pptx.util import Inches, Pt, Emu
        from pptx.dml.color import RgbColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        raise RuntimeError("python-pptx is required for PPTX export. pip install python-pptx")

    prs = PptxPresentation()
    prs.slide_width = Inches(13.333)   # 16:9
    prs.slide_height = Inches(7.5)

    blank = prs.slide_layouts[6]  # blank

    for s in pres.slides:
        slide = prs.slides.add_slide(blank)

        # Title shape
        left = Inches(0.7)
        top = Inches(0.5)
        width = Inches(12)
        height = Inches(1.2)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = s.label or "Slide"
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = RgbColor(0x0F, 0x17, 0x2A)

        # Body from content or notes
        body_text = (s.content or s.notes or "").strip()
        if body_text:
            body_box = slide.shapes.add_textbox(Inches(0.7), Inches(2.0), Inches(12), Inches(4.5))
            btf = body_box.text_frame
            btf.word_wrap = True
            bp = btf.paragraphs[0]
            bp.text = body_text[:2000]
            bp.font.size = Pt(16)
            bp.font.color.rgb = RgbColor(0x33, 0x33, 0x33)

        # Speaker notes
        if s.notes:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = s.notes

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def _esc(t: str) -> str:
    return (
        (t or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
