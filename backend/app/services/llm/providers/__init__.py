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
from app.services.session_context import get_session_id
from app.services.session_limits import rate_limiter
logger = logging.getLogger("llm")


def call_llm(system: str, user: str, max_tokens: int = 4000):
    providers = ["azure_openai_5","gemini", "openrouter", "azure_openai", "groq", "huggingface"]

    # Put configured provider first
    configured = (settings.LLM_PROVIDER or "gemini").lower().strip()
    providers.remove(configured)
    providers.insert(0, configured)
    session_id = get_session_id()

    for provider in providers:
        try:
            if provider =='azure_openai_5':
                if not session_id:
                    logger.warning("No session ID available for Azure OpenAI 5")
                    continue
                if not rate_limiter.try_acquire_azure_openai_5(session_id):
                    logger.warning("Azure OpenAI 5 limit reached for session %s",session_id,)
                    continue
                print(session_id)
                text = call_azure_openai(system, user, max_tokens,model='azure_openai_5')
            elif provider == "gemini":
                text, _ = call_gemini(system, user, max_tokens)
            elif provider == "openrouter":
                text = call_openrouter(system, user, max_tokens)
            elif provider == "azure_openai":
                text = call_azure_openai(system, user, max_tokens,model='azure_openai_4')
            elif provider == "groq":
                text = call_groq(system, user, max_tokens)
            elif provider =="huggingface":
                text = call_huggingface(system, user, max_tokens)
            else:
                continue
            logger.info("Provider %s", provider)
            return extract_json(text)

        except Exception as e:
            logger.warning("Provider %s failed: %s", provider, e)
            continue

    raise RuntimeError("All LLM providers failed")