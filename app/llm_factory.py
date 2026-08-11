from __future__ import annotations

import os
from typing import Any

from .mock_llm import FakeLLM
from .openrouter_llm import OpenRouterLLM


def build_llm(*, model: str | None = None) -> Any:
    """Use OpenRouter for real demos, with an explicit mock option for tests."""
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    has_openrouter_key = bool(os.getenv("OPENROUTER_API_KEY"))
    if provider == "openrouter" or (provider == "auto" and has_openrouter_key):
        return OpenRouterLLM(model=model)
    if provider in {"auto", "fake"}:
        return FakeLLM(model=model or "fake-observability-llm")
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
