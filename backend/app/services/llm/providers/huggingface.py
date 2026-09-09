

from __future__ import annotations

import logging
from typing import Any, List, cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from app.config import settings

logger = logging.getLogger("llm")

HF_ROUTER_BASE = "https://router.huggingface.co/v1"


def call_huggingface(system: str, user: str, max_tokens: int = 4096) -> str:
    if not settings.HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is not set in .env\n"
            "Create a token with Inference Providers permission:\n"
        )

    token = settings.HF_TOKEN.strip()
    model = settings.HF_MODEL

    provider = (getattr(settings, "HF_PROVIDER", None) or "").strip()
    if provider and ":" not in model and provider.lower() not in ("auto", "none"):
        model = f"{model}:{provider}"

    max_tok = min(int(max_tokens), 4096)

    client = OpenAI(
        base_url=HF_ROUTER_BASE,
        api_key=token,
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=cast(
                Any,
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            ),
            max_tokens=max_tok,
            temperature=0.5,
        )
    except Exception as e:
        msg = str(e).lower()
        raise RuntimeError(f"HF chat completion failed: {msg}") from e

    try:
        text = completion.choices[0].message.content or ""
        print(text)
    except Exception:
        text = str(completion)
    logger.info("HF Inference Providers model=%s len=%d", model, len(text))
    return text