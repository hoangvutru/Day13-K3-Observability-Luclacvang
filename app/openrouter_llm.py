from __future__ import annotations

import os
from typing import Any

import httpx

from .llm_types import LLMResponse, LLMUsage
from .tracing import observe


class OpenRouterError(RuntimeError):
    """Safe, key-free error raised for OpenRouter request failures."""


class OpenRouterLLM:
    provider_name = "openrouter"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required when OpenRouter is enabled")
        self.model = model or os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self.base_url = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "60"))
        self._client = client

    @observe(
        name="llm.generate",
        as_type="generation",
        capture_input=False,
        capture_output=False,
    )
    def generate(self, prompt: str) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000"),
            "X-OpenRouter-Title": os.getenv(
                "OPENROUTER_APP_TITLE", "Day 13 Observability Demo"
            ),
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": float(os.getenv("OPENROUTER_TEMPERATURE", "0.2")),
            "max_completion_tokens": int(
                os.getenv("OPENROUTER_MAX_COMPLETION_TOKENS", "500")
            ),
            "usage": {"include": True},
        }

        try:
            if self._client is not None:
                response = self._client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions", headers=headers, json=payload
                    )
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            raise OpenRouterError(
                f"OpenRouter returned HTTP {exc.response.status_code}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenRouterError("OpenRouter request failed") from exc

        choices = body.get("choices") or []
        if not choices:
            raise OpenRouterError("OpenRouter returned no completion choice")
        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise OpenRouterError("OpenRouter returned an empty text response")

        usage = body.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        raw_cost = usage.get("cost")
        cost_usd = float(raw_cost) if isinstance(raw_cost, (int, float, str)) else None
        return LLMResponse(
            text=content.strip(),
            usage=LLMUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            model=str(body.get("model") or self.model),
            cost_usd=cost_usd,
            provider=self.provider_name,
        )
