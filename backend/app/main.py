"""
AI Presentation Generator – FastAPI backend

Two-phase flow:
  1. POST /api/outline          → content plan (user reviews)
  2. POST /api/generate-html    → HTML for every slide (independent prompts)
"""

import io
import re
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import (
    GenerateOutlineRequest,
    ConfirmOutlineRequest,
    RegenerateSlideRequest,
    ExportRequest,
    OutlineResponse,
    Presentation,
    Slide,
)
from app.services.parser import extract_text
from app.services.llm import (
    generate_outline,
    generate_html_from_outline,
    regenerate_slide,
)
from app.services.exporter import export_presentation

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Presentation Generator",
    description="Two-phase: outline → confirm → per-slide HTML",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "model": (
            settings.GEMINI_MODEL if settings.LLM_PROVIDER == "gemini"
            else settings.GROQ_MODEL if settings.LLM_PROVIDER == "groq"
            else settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama"
            else settings.HF_MODEL
        ),
    }


# ────────────────────────────────────────────────
# Phase 1 – Content outline only
# ────────────────────────────────────────────────

@app.post("/api/outline", response_model=OutlineResponse)
async def api_outline(req: GenerateOutlineRequest):
    """Generate content plan (title, palette, slide briefs). User must confirm."""
    try:
        return await generate_outline(
            content=req.prompt,
            num_slides=req.num_slides,
            tone=req.tone or "professional",
        )
    except Exception as e:
        logger.exception("Outline failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outline/document", response_model=OutlineResponse)
async def api_outline_from_document(
    file: UploadFile = File(...),
    num_slides: int = Form(8),
    tone: str = Form("professional"),
):
    """Same as /api/outline but from an uploaded document."""
    try:
        data = await file.read()
        text = extract_text(file.filename or "file.txt", data)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No extractable text found")
        return await generate_outline(text, num_slides, tone)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document outline failed")
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Phase 2 – Generate HTML (one prompt per slide)
# ────────────────────────────────────────────────

@app.post("/api/generate-html", response_model=Presentation)
async def api_generate_html(req: ConfirmOutlineRequest):
    """
    Generate the final HTML presentation from the
    user-confirmed outline.
    """

    try:

        return await generate_html_from_outline(
            title=req.title,
            subtitle=req.subtitle or "",

            presenters=req.presenters or [],

            date=req.date,

            tone=req.tone or "professional",

            palette=req.palette or {},

            slides=req.slides or [],
        )

    except Exception as e:

        logger.exception(
            "HTML generation failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

# ────────────────────────────────────────────────
# Single-slide regeneration
# ────────────────────────────────────────────────

@app.post("/api/regenerate-slide", response_model=Slide)
async def api_regenerate_slide(req: RegenerateSlideRequest):
    try:
        return await regenerate_slide(
            title=req.title,
            subtitle=req.subtitle or "",
            current_html=req.current_html,
            instruction=req.instruction or "Improve the visual design while keeping the same content.",
            tone=req.tone or "professional",
            palette=req.palette,
        )
    except Exception as e:
        logger.exception("Regenerate failed")
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Export
# ────────────────────────────────────────────────

@app.post("/api/export")
async def api_export(req: ExportRequest):
    try:
        fmt = (req.format or "pptx").lower()
        data = await export_presentation(req.presentation, fmt)
        safe = re.sub(r"[^\w\-]+", "_", (req.presentation.title or "presentation")[:40]).strip("_") or "presentation"
        if fmt == "html":
            media = "text/html"
            filename = f"{safe}.html"
        else:
            media = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            filename = f"{safe}.pptx"
        return StreamingResponse(
            io.BytesIO(data),
            media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.exception("Export failed")
        raise HTTPException(status_code=500, detail=str(e))
