from __future__ import annotations

from .mock_llm import FakeLLM


def build_llm(*, model: str | None = None) -> FakeLLM:
    """Build the local mock LLM used by every app environment."""
    return FakeLLM(model=model or "fake-observability-llm")
