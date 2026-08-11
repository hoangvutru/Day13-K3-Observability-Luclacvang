from __future__ import annotations

import random
import re
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
        answer = self._answer_from_prompt(prompt)
        return LLMResponse(
            text=answer,
            usage=LLMUsage(input_tokens, output_tokens),
            model=self.model,
            provider=self.provider_name,
        )

    def _answer_from_prompt(self, prompt: str) -> str:
        """Return a useful deterministic answer from the local RAG prompt."""
        question_match = re.search(r"^Question=(.*)$", prompt, flags=re.MULTILINE)
        question = question_match.group(1).strip() if question_match else prompt.strip()
        normalized = question.casefold()

        if "refund" in normalized:
            return "Refunds are available within 7 days with proof of purchase."
        if (
            "metric" in normalized
            and "trace" in normalized
            and "log" in normalized
        ):
            return "Metrics detect incidents, traces localize them, and logs explain the root cause."
        if (
            "pii" in normalized
            or "sensitive" in normalized
            or "credit card" in normalized
            or ("log" in normalized and ("should" in normalized or "appear" in normalized))
        ):
            return "Do not expose PII or other sensitive information in application logs; use sanitized summaries only."
        if "latency" in normalized or "bottleneck" in normalized:
            return "Compare RAG retrieval latency with llm.generate latency, then use the trace and correlation ID to locate the slow span."
        if "alert" in normalized:
            return "Design alerts around user-impacting symptoms, with a threshold, a duration window, and a minimum traffic requirement."

        docs_match = re.search(r"^Docs=(.*?)(?=^Question=|\Z)", prompt, flags=re.MULTILINE | re.DOTALL)
        docs = docs_match.group(1).strip() if docs_match else ""
        if docs and not docs.casefold().startswith("no domain document matched"):
            return f"Based on the retrieved context: {docs}"
        return "I could not find a matching domain document. Please provide more context so I can answer accurately."
