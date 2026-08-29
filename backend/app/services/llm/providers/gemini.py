"""Google Gemini provider (google-genai SDK)."""

import logging

from google import genai
from google.genai import types

from app.config import settings
from werkzeug.exceptions import InternalServerError

logger = logging.getLogger("llm")


def get_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def call_gemini(system: str, user: str, max_tokens: int = 8192) -> tuple:
    model = settings.GEMINI_MODEL
    client = get_client()

    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0.5,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=user,
            config=config,
        )

    except Exception as e:
        msg = str(e).lower()
        if "mime" in msg or "response_mime" in msg:
            logger.warning("Retrying Gemini without response_mime_type")

            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.5,
                max_output_tokens=max_tokens,
            )
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user,
                    config=config,
                )
            except Exception as e2:
                raise InternalServerError(f"Gemini SDK error: {e2}") from e2
        else:
            raise InternalServerError( f"Gemini SDK error: {e}") from e

    if response is None:
        raise InternalServerError("Gemini returned no response")

    text = getattr(response, "text", None)

    if not text:
        try:
            for part in response.candidates[0].content.parts:
                if getattr(part, "text", None):
                    text = part.text
                    break
        except Exception:
            pass

    finish = "STOP"

    try:
        reason = response.candidates[0].finish_reason
        if reason:
            finish = str(reason).split(".")[-1].upper()
    except Exception:
        pass

    logger.info(
        "Gemini(SDK) finishReason=%s len=%d",
        finish,
        len(text or ""),
    )

    return text, finish