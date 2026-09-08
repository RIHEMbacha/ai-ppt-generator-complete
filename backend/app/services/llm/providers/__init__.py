"""LLM provider router."""

import logging
from app.services.llm.json_utils import extract_json

from app.config import settings

from .azure_openai import call_azure_openai
from .gemini import call_gemini
from .groq import call_groq
from .huggingface import call_huggingface
from .ollama import call_ollama
from .openrouter import call_openrouter

logger = logging.getLogger("llm")


def call_llm(system: str, user: str, max_tokens: int = 4000):
    providers = ["gemini", "openrouter", "azure_openai", "groq", "huggingface"]

    # Put configured provider first
    configured = (settings.LLM_PROVIDER or "gemini").lower().strip()
    providers.remove(configured)
    providers.insert(0, configured)

    for provider in providers:
        try:
            if provider == "gemini":
                text, _ = call_gemini(system, user, max_tokens)
            elif provider in ("openrouter", "open_router"):
                text = call_openrouter(system, user, max_tokens)
            elif provider in ("azure_openai", "azure-openai", "azure"):
                text = call_azure_openai(system, user, max_tokens)
            elif provider == "groq":
                text = call_groq(system, user, max_tokens)
            elif provider in ("huggingface", "hf", "hugging_face"):
                text = call_huggingface(system, user, max_tokens)
            else:
                continue
            logger.info("Provider %s: %s", provider)
            return extract_json(text)

        except Exception as e:
            logger.warning("Provider %s failed: %s", provider, e)
            continue

    raise RuntimeError("All LLM providers failed")