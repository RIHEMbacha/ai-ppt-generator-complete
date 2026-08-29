"""OpenRouter provider (OpenAI-compatible chat API)."""

import json

import requests
from requests.adapters import HTTPAdapter, Retry
from werkzeug.exceptions import InternalServerError

from app.config import settings


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


def _error_text(resp: requests.Response) -> str:
    try:
        data = resp.json()
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                return str(err.get("message") or json.dumps(err))
            return json.dumps(data)
    except Exception:
        pass
    return (resp.text or "").strip()[:500]


def call_openrouter(system: str, user: str, max_tokens: int = 4000) -> str:
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    model = (settings.OPENROUTER_MODEL or "").strip()
    if not model:
        raise RuntimeError("OPENROUTER_MODEL is not set")
    if "rerank" in model.lower():
        raise RuntimeError(
            f"OPENROUTER_MODEL '{model}' is a rerank model and cannot be used with "
            "chat/completions. Choose a chat model (e.g. openai/gpt-4o)."
        )

    resp = _session().post(
        f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "ai-ppt-generator",
        },
        json={
            "model": model,
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
        raise InternalServerError("OpenRouter 413 – payload too large.")
    if resp.status_code == 429:
        raise InternalServerError("OpenRouter rate limit (429).")
    if resp.status_code >= 400:
        raise InternalServerError(f"OpenRouter HTTP {resp.status_code}: {_error_text(resp)}")

    return resp.json()["choices"][0]["message"]["content"]
