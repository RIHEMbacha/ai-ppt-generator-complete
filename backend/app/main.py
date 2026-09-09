import sys
import asyncio
import uuid

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )
import io
import re
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request

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
from app.services.parser import extract_document_assets
from app.services.llm import (
    generate_outline,
    generate_outline_from_document,
    generate_html_from_outline,
    regenerate_slide,
)
from app.services.exporter import export_presentation
from app.services.session_context import (
    set_session_id,
    get_session_id,
)

from app.services.session_limits import (
    rate_limiter,
    MAX_AZURE_OPENAI_5_REQUESTS,
)
logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI Presentation Generator",
    description="Two-phase: outline → confirm → per-slide HTML",
    version="2.0.0",
)
@app.middleware("http")
async def session_middleware(request: Request, call_next):

    session_id = request.cookies.get("presentation_session_id")

    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info("NEW SESSION: %s", session_id)
    else:
        logger.info("EXISTING SESSION: %s", session_id)

    set_session_id(session_id)

    response = await call_next(request)

    response.set_cookie(
        key="presentation_session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return response
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    session_id = get_session_id()
    print(session_id)
    if not session_id:

        return {
            "status": "ok",
            "provider": settings.LLM_PROVIDER,
            "azure_openai_5": {
                "used": 0,
                "limit": MAX_AZURE_OPENAI_5_REQUESTS,
                "remaining": MAX_AZURE_OPENAI_5_REQUESTS,
            }
        }

    used = rate_limiter.get_count(
        session_id
    )

    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "azure_openai_5": {
            "used": used,
            "limit": MAX_AZURE_OPENAI_5_REQUESTS,
            "remaining": max(
                0,
                MAX_AZURE_OPENAI_5_REQUESTS - used,
                ),
        }
    }

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
        text, document_images = extract_document_assets(
            file_bytes=data,
            filename=file.filename or "file.txt",
        )
        if not text.strip():
            raise HTTPException(status_code=400, detail="No extractable text found")
        return await generate_outline_from_document(
            content=text,
            num_slides=num_slides,
            tone=tone,
            document_images=document_images,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document outline failed")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/export")
async def api_export(req: ExportRequest):
    try:
        fmt = (req.format or "pptx").lower()

        if fmt not in {"pdf", "pptx"}:
            raise HTTPException(
                status_code=400,
                detail="Only PDF and PPTX exports are supported.",
            )

        data = await export_presentation(
            req.presentation,
            fmt,
        )

        safe = (
                re.sub(
                    r"[^\w\-]+",
                    "_",
                    (req.presentation.title or "presentation")[:40],
                )
                .strip("_")
                or "presentation"
        )

        if fmt == "pdf":
            media_type = "application/pdf"
            filename = f"{safe}.pdf"

        else:
            media_type = (
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            )
            filename = f"{safe}.pptx"

        return StreamingResponse(
            io.BytesIO(data),
            media_type=media_type,
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"'
            },
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Export failed")

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
