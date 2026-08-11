from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config, main as main_module
from app.logging_config import add_schema_defaults, scrub_event
from app.main import app
from app.middleware import resolve_correlation_id


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


def test_request_id_is_normalized_or_replaced() -> None:
    assert resolve_correlation_id("  REQ-DEADBEEF ") == "req-deadbeef"
    assert re.fullmatch(r"req-[0-9a-f]{8}", resolve_correlation_id("invalid-id"))
    assert re.fullmatch(r"req-[0-9a-f]{8}", resolve_correlation_id(None))


def test_unhandled_exception_keeps_observability_context(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    def fail_snapshot() -> dict:
        raise RuntimeError("metrics backend unavailable")

    monkeypatch.setattr(main_module, "snapshot", fail_snapshot)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/metrics",
            headers={"x-request-id": "req-cafebabe"},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["x-request-id"] == "req-cafebabe"
    assert float(response.headers["x-response-time-ms"]) >= 0

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    error_record = next(record for record in records if record["event"] == "request_failed")
    assert error_record["correlation_id"] == "req-cafebabe"
    assert error_record["error_type"] == "RuntimeError"
    assert error_record["payload"]["path"] == "/metrics"


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
