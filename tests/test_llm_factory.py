from __future__ import annotations

from app.llm_factory import build_llm
from app.mock_llm import FakeLLM


def test_factory_uses_openrouter_when_provider_and_key_are_set(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "must-not-be-used")

    llm = build_llm()

    assert llm.provider_name == "openrouter"
    assert llm.model == "openrouter/free"


def test_factory_uses_mock_in_keyless_auto_mode(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    llm = build_llm()

    assert llm.provider_name == "fake"


def test_mock_llm_answers_the_question_using_retrieved_context() -> None:
    prompt = (
        "Feature=qa\n"
        "Docs=Refunds are available within 7 days with proof of purchase.\n"
        "Question=What is your refund policy?"
    )

    response = FakeLLM.generate.__wrapped__(FakeLLM(), prompt)

    assert response.text == "Refunds are available within 7 days with proof of purchase."
    assert "Starter answer" not in response.text
