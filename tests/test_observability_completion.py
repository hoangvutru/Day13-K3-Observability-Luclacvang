from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.logging_config import add_schema_defaults, scrub_event
from app.main import app


def test_correlation_header_propagates_to_all_request_logs(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "req-deadbeef"},
            json={
                "user_id": "raw-user-must-not-be-logged",
                "session_id": "session-test",
                "feature": "qa",
                "message": "Contact student@example.com or 090 123 4567",
            },
        )

    assert response.headers["x-request-id"] == "req-deadbeef"
    assert float(response.headers["x-response-time-ms"]) >= 0
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    request_records = [record for record in records if record.get("correlation_id") == "req-deadbeef"]
    assert request_records
    assert all(record["user_id_hash"] != "raw-user-must-not-be-logged" for record in request_records)
    raw_log = log_path.read_text(encoding="utf-8")
    assert "student@example.com" not in raw_log
    assert "090 123 4567" not in raw_log
    assert "REDACTED_EMAIL" in raw_log
    assert "REDACTED_PHONE_VN" in raw_log


def test_scrub_event_redacts_nested_values() -> None:
    result = scrub_event(
        None,
        "info",
        {
            "event": "nested_payload",
            "payload": {
                "items": [
                    {"email": "student@example.com"},
                    "card 4111-1111-1111-1111",
                ]
            },
        },
    )
    serialized = json.dumps(result)
    assert "student@example.com" not in serialized
    assert "4111-1111-1111-1111" not in serialized
    assert "REDACTED_EMAIL" in serialized
    assert "REDACTED_CREDIT_CARD" in serialized


def test_background_logs_receive_schema_defaults() -> None:
    result = add_schema_defaults(None, "info", {"event": "background_task"})
    assert result["correlation_id"] == "system-unscoped"
    assert result["service"]
    assert result["env"]


def test_demo_ui_is_served_without_api_keys() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Signal Room" in response.text
    assert 'name="color-scheme" content="light"' in response.text
    assert "Light editorial theme" in response.text
    assert "OPENROUTER_API_KEY" not in response.text
    assert "LANGFUSE_SECRET_KEY" not in response.text
