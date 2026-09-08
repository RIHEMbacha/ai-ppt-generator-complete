
import json
import re

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


def _is_unsupported_version(resp: requests.Response) -> bool:
    text = _error_text(resp).lower()
    return "api version not supported" in text or "unsupported api-version" in text


def _candidate_versions(configured: str, endpoint: str) -> list[str]:
    versions = []
    for value in [configured, "v1", "2024-06-01", "2024-10-21"]:
        v = (value or "").strip()
        if v and v not in versions:
            versions.append(v)
    if "services.ai.azure.com" in endpoint.lower() and "v1" not in versions:
        versions.insert(0, "v1")
    return versions


def _make_url(endpoint: str, deployment: str, api_version: str) -> str:
    return (
        f"{endpoint.rstrip('/')}/openai/v1/chat/completions"
    )


def call_azure_openai(system: str, user: str, max_tokens: int = 4096) -> str:
    endpoint = (settings.AZURE_OPENAI_ENDPOINT or "").strip().rstrip("/")
    api_key = (settings.AZURE_OPENAI_API_KEY or "").strip()
    deployment = (settings.AZURE_OPENAI_DEPLOYMENT or "").strip()
    api_version = (settings.AZURE_OPENAI_API_VERSION or "").strip()

    if not endpoint:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT is not set")
    if not api_key:
        raise RuntimeError("AZURE_OPENAI_API_KEY is not set")
    if not deployment:
        raise RuntimeError("AZURE_OPENAI_DEPLOYMENT is not set")
    if not api_version:
        raise RuntimeError("AZURE_OPENAI_API_VERSION is not set")

    payload = {
        "model": deployment,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    last_resp = None
    for version in _candidate_versions(api_version, endpoint):
        resp = _session().post(
            _make_url(endpoint, deployment, version),
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )
        last_resp = resp
        if resp.status_code == 413:
            raise InternalServerError("Azure OpenAI 413 – payload too large.")
        if resp.status_code == 429:
            raise InternalServerError("Azure OpenAI rate limit (429).")
        if resp.status_code >= 400 and _is_unsupported_version(resp):
            continue
        if resp.status_code >= 400:
            raise InternalServerError(f"Azure OpenAI HTTP {resp.status_code}: {_error_text(resp)}")
        return resp.json()["choices"][0]["message"]["content"]

    if last_resp is not None:
        raise InternalServerError(f"Azure OpenAI HTTP {last_resp.status_code}: {_error_text(last_resp)}")
    raise InternalServerError("Azure OpenAI request failed")
