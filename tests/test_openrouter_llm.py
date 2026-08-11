from __future__ import annotations

import json

import httpx
import pytest

from app.openrouter_llm import OpenRouterError, OpenRouterLLM


def test_openrouter_maps_completion_usage_and_cost_without_exposing_key() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "google/gemini-test",
                "choices": [{"message": {"content": "A traced answer."}}],
                "usage": {
                    "prompt_tokens": 21,
                    "completion_tokens": 8,
                    "cost": 0.000012,
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    llm = OpenRouterLLM(api_key="test-secret", model="openrouter/free", client=client)
    result = OpenRouterLLM.generate.__wrapped__(llm, "Explain tracing")

    assert captured["authorization"] == "Bearer test-secret"
    assert captured["payload"]["model"] == "openrouter/free"
    assert captured["payload"]["usage"] == {"include": True}
    assert result.text == "A traced answer."
    assert result.model == "google/gemini-test"
    assert result.provider == "openrouter"
    assert result.usage.input_tokens == 21
    assert result.usage.output_tokens == 8
    assert result.cost_usd == 0.000012


def test_openrouter_rejects_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        OpenRouterLLM()


def test_openrouter_raises_safe_error_without_response_body() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(401, json={"error": {"message": "secret detail"}})
        )
    )
    llm = OpenRouterLLM(api_key="test-secret", client=client)
    with pytest.raises(OpenRouterError, match="HTTP 401") as caught:
        OpenRouterLLM.generate.__wrapped__(llm, "hello")
    assert "secret detail" not in str(caught.value)
