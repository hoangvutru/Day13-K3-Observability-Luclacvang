from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def test_chat_response_log_exposes_quality_for_dashboard(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]
    local_trace = response.json()["local_trace"]
    assert local_trace["status"] == "completed"
    assert [item["name"] for item in local_trace["observations"]] == [
        "run",
        "rag.retrieve",
        "llm.generate",
    ]
    assert [item["event"] for item in local_trace["logs"]] == [
        "request_received",
        "rag_completed",
        "llm_completed",
        "response_sent",
    ]
    assert "user_id" not in json.dumps(local_trace)


def test_demo_failure_returns_correlated_error_trace(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ENABLE_DEMO_ERROR_TRIGGER", "true")

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "must-not-be-returned",
                "session_id": "error-demo",
                "feature": "qa",
                "message": "Trigger a vector store failure for the observability demo.",
            },
        )

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "DemoVectorStoreError"
    assert payload["correlation_id"].startswith("req-")
    assert payload["local_trace"]["status"] == "error"
    assert [item["name"] for item in payload["local_trace"]["observations"]] == [
        "run",
        "rag.retrieve",
    ]
    assert payload["local_trace"]["logs"][-1]["event"] == "request_failed"
    assert "must-not-be-returned" not in json.dumps(payload)
