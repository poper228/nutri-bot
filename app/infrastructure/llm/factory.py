from functools import lru_cache

from app.core.config import get_settings
from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.llm.gemini import GeminiProvider
from app.infrastructure.llm.groq_provider import GroqProvider


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        return GeminiProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_model,
        )
    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        return GroqProvider(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.groq_model,
        )
    raise NotImplementedError(f"LLM provider '{settings.llm_provider}' is not implemented")
