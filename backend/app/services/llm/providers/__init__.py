"""LLM provider router."""

import logging

from app.config import settings

from .azure_openai import call_azure_openai
from .gemini import call_gemini
from .groq import call_groq
from .huggingface import call_huggingface
from .ollama import call_ollama
from .openrouter import call_openrouter

logger = logging.getLogger("llm")


def call_llm(system: str, user: str, max_tokens: int = 4000) -> str:
    provider = (settings.LLM_PROVIDER or "gemini").lower().strip()
    logger.info("LLM provider=%s max_tokens=%d user_len=%d", provider, max_tokens, len(user))

    if provider == "groq":
        return call_groq(system, user, max_tokens)
    if provider == "ollama":
        return call_ollama(system, user, max_tokens)
    if provider == "gemini":
        text, _ = call_gemini(system, user, max_tokens)
        return text
    if provider in ("azure_openai", "azure-openai", "azure"):
        return call_azure_openai(system, user, max_tokens)
    if provider in ("openrouter", "open_router"):
        return call_openrouter(system, user, max_tokens)
    if provider in ("huggingface", "hf", "hugging_face"):
        return call_huggingface(system, user, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def call_llm_with_meta(system: str, user: str, max_tokens: int = 4000) -> tuple:
    provider = (settings.LLM_PROVIDER or "gemini").lower().strip()
    logger.info("LLM provider=%s max_tokens=%d user_len=%d", provider, max_tokens, len(user))

    if provider == "gemini":
        return call_gemini(system, user, max_tokens)
    if provider == "groq":
        return call_groq(system, user, max_tokens), ""
    if provider == "ollama":
        return call_ollama(system, user, max_tokens), ""
    if provider in ("azure_openai", "azure-openai", "azure"):
        return call_azure_openai(system, user, max_tokens), ""
    if provider in ("openrouter", "open_router"):
        return call_openrouter(system, user, max_tokens), ""
    if provider in ("huggingface", "hf", "hugging_face"):
        return call_huggingface(system, user, max_tokens), ""
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
