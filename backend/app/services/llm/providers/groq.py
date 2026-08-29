"""Groq provider (OpenAI-compatible chat API)."""

import requests
from requests.adapters import HTTPAdapter, Retry

from app.config import settings
from werkzeug.exceptions import InternalServerError


def _session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def call_groq(system: str, user: str, max_tokens: int = 4096) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")
    resp = _session().post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.5,
            "max_tokens": max_tokens,
        },
        timeout=120,
    )
    if resp.status_code == 413:
        raise InternalServerError("Groq 413 – payload too large.")
    if resp.status_code == 429:
        raise InternalServerError("Groq rate limit (429).")
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
