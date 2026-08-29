"""
Document parsing utility service to extract raw text content
from uploaded text, PDF, or Word documents (.pdf, .docx, .txt).
"""

import io
import logging

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