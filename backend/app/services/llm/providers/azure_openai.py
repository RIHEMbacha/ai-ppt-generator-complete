import logging
import json
import re

import requests
from requests.adapters import HTTPAdapter, Retry
from werkzeug.exceptions import InternalServerError

from app.config import settings

logger = logging.getLogger("llm")

def _session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def _make_url(endpoint: str) -> str:
    return (
        f"{endpoint.rstrip('/')}/openai/v1/chat/completions"
    )


def call_azure_openai(system: str, user: str, max_tokens: int = 4096,model:str='azure_openai_5') -> str:
    endpoint = settings.AZURE_OPENAI_ENDPOINT.strip()
    api_key = settings.AZURE_OPENAI_API_KEY .strip()
    deployment = (settings.AZURE_OPENAI_model5 if model == "azure_openai_5" else settings.AZURE_OPENAI_model4).strip()

    if not endpoint or not api_key or  not deployment:
        logger.error(" azure credentials  is missing ")
        raise InternalServerError("internal server")


    payload = {
        "model": deployment,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    try:
        resp = _session().post(
            _make_url(endpoint),
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        if resp.status_code == 413:
            raise InternalServerError("Azure OpenAI 413 – payload too large.")

        if resp.status_code == 429:
            raise InternalServerError("Azure OpenAI rate limit (429).")

        if resp.status_code >= 400:
            raise Exception(
                f"Azure OpenAI HTTP {resp.status_code}: {resp.text}"
            )

        return resp.json()["choices"][0]["message"]["content"]

    except requests.RequestException as e:
        logger.exception("Azure OpenAI request failed: %s", e)
        raise InternalServerError("Azure OpenAI request failed.")