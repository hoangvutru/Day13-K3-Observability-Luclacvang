from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class LLMResponse:
    text: str
    usage: LLMUsage
    model: str
    cost_usd: float | None = None
    provider: str = "unknown"
