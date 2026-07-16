from __future__ import annotations

import os

from backend.services.groq_service import GroqLLMProvider
from backend.services.llm_provider import BaseLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """Factory for selecting the active model provider by environment variable."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower().strip()

    if provider == "groq":
        return GroqLLMProvider()

    raise ValueError(
        f"Unsupported LLM_PROVIDER '{provider}'. Supported values: groq"
    )
