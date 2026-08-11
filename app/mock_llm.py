from __future__ import annotations

import random
import time

from .incidents import STATE
from .llm_types import LLMResponse, LLMUsage
from .tracing import observe

class FakeLLM:
    provider_name = "fake"

    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    @observe(name="llm.generate", as_type="generation", capture_input=False, capture_output=False)
    def generate(self, prompt: str) -> LLMResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
        answer = (
            "Starter answer. Teams should improve this output logic and add better quality checks. "
            "Use retrieved context and keep responses concise."
        )
        return LLMResponse(
            text=answer,
            usage=LLMUsage(input_tokens, output_tokens),
            model=self.model,
            provider=self.provider_name,
        )
