"""Ollama local provider."""

import requests
from requests.adapters import HTTPAdapter, Retry

from app.config import settings


def _session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=2, backoff_factor=1.0, status_forcelist=[500, 502, 503, 504])
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def call_ollama(system: str, user: str, max_tokens: int = 4096) -> str:
    resp = _session().post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.5, "num_predict": max_tokens},
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]
