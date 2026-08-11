from __future__ import annotations

import os
from typing import Any

from .mock_llm import FakeLLM
from .openrouter_llm import OpenRouterLLM


def build_llm(*, model: str | None = None) -> Any:
    """Select OpenRouter for real demos and FakeLLM for keyless tests/practice."""
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    has_openrouter_key = bool(os.getenv("OPENROUTER_API_KEY"))
    if provider == "openrouter" or (provider == "auto" and has_openrouter_key):
        return OpenRouterLLM(model=model)
    if provider not in {"auto", "fake"}:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
    return FakeLLM(model=model or "fake-observability-llm")
