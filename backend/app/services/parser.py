"""
Document parsing utility service to extract raw text content
from uploaded text, PDF, or Word documents (.pdf, .docx, .txt).
"""

import base64
import io
import logging
import zipfile
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger("parser")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes using PyPDF2 or pdfplumber if available."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)
        return "\n".join(text)
    except ImportError:
        logger.warning("PyPDF2 not installed. Unable to parse PDF.")
        return ""
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from Word (.docx) file bytes using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])
    except ImportError:
        logger.warning("python-docx not installed. Unable to parse DOCX.")
        return ""
    except Exception as e:
        logger.error(f"Failed to parse DOCX: {e}")
        return ""


def extract_text(file_bytes: bytes, filename: str = "") -> str:
    """
    Main parser entrypoint called by app/main.py.
    Extracts plain text content from uploaded file bytes based on file extension.
    """
    if not file_bytes:
        return ""

    filename_lower = (filename or "").lower()

    if filename_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith(".docx") or filename_lower.endswith(".doc"):
        return extract_text_from_docx(file_bytes)
    else:
        # Default text decoding (.txt, .md, plain text)
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore")


def _detect_mime_from_bytes(data: bytes) -> str:
    if not data:
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return "image/webp"
    return "image/jpeg"


def _mime_from_filename(name: str) -> str:
    ext = Path(name or "").suffix.lower()
    if ext == ".png":
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".gif":
        return "image/gif"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"


def _to_data_uri(image_bytes: bytes, mime: str, max_bytes: int = 600_000) -> str:
    if not image_bytes:
        return ""
    payload = image_bytes[:max_bytes]
    return f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"


def extract_images_from_docx(file_bytes: bytes, max_images: int = 8) -> List[str]:
    """
    Extract embedded images from DOCX as data URIs (word/media/*).
    """
    out: List[str] = []
    if not file_bytes:
        return out
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            media_files = sorted(
                name for name in zf.namelist()
                if name.lower().startswith("word/media/")
            )
            for name in media_files:
                if len(out) >= max_images:
                    break
                data = zf.read(name)
                if not data:
                    continue
                mime = _mime_from_filename(name) or _detect_mime_from_bytes(data)
                uri = _to_data_uri(data, mime)
                if uri:
                    out.append(uri)
    except Exception as e:
        logger.warning("Failed to extract DOCX images: %s", e)
    return out


def extract_images_from_pdf(file_bytes: bytes, max_images: int = 8) -> List[str]:
    """
    Best-effort PDF image extraction through PyPDF2 page.images (if available).
    """
    out: List[str] = []
    if not file_bytes:
        return out
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            if len(out) >= max_images:
                break
            page_images = getattr(page, "images", None) or []
            for image in page_images:
                if len(out) >= max_images:
                    break
                data = getattr(image, "data", b"")
                name = getattr(image, "name", "")
                if not data:
                    continue
                mime = _mime_from_filename(name) or _detect_mime_from_bytes(data)
                uri = _to_data_uri(data, mime)
                if uri:
                    out.append(uri)
    except ImportError:
        logger.warning("PyPDF2 not installed. Unable to extract PDF images.")
    except Exception as e:
        logger.warning("Failed to extract PDF images: %s", e)
    return out


def extract_document_images(file_bytes: bytes, filename: str = "", max_images: int = 8) -> List[str]:
    filename_lower = (filename or "").lower()
    if filename_lower.endswith(".docx"):
        return extract_images_from_docx(file_bytes, max_images=max_images)
    if filename_lower.endswith(".pdf"):
        return extract_images_from_pdf(file_bytes, max_images=max_images)
    return []


def extract_document_assets(
        file_bytes: bytes,
        filename: str = "",
        max_images: int = 8
) -> Tuple[str, List[str]]:
    """
    Extract both text and reusable document images from an uploaded file.
    """
    text = extract_text(file_bytes=file_bytes, filename=filename)
    images = extract_document_images(file_bytes=file_bytes, filename=filename, max_images=max_images)
    return text, images