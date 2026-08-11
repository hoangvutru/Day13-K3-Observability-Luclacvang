from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app import main as main_module
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
    assert "waitForTrace" in response.text
    assert "/traces/${encodeURIComponent(traceId)}/status" in response.text
    assert "OPENROUTER_API_KEY" not in response.text
    assert "LANGFUSE_SECRET_KEY" not in response.text


class _ReadyTrace:
    observations = [object(), object(), object()]


class _ReadyTraceApi:
    class _TraceResource:
        @staticmethod
        def get(trace_id: str):
            assert trace_id == "a" * 32
            return _ReadyTrace()

    trace = _TraceResource()

    @staticmethod
    def get_trace_url(*, trace_id: str) -> str:
        return f"https://langfuse.test/traces/{trace_id}"

    api = type("Api", (), {"trace": trace})()


def test_trace_status_only_reports_ready_after_langfuse_lookup(monkeypatch) -> None:
    client = _ReadyTraceApi()
    monkeypatch.setattr(main_module, "tracing_enabled", lambda: True)
    monkeypatch.setattr(main_module, "get_langfuse_client", lambda: client)

    with TestClient(app) as test_client:
        response = test_client.get(f"/traces/{'a' * 32}/status")

    assert response.status_code == 200
    assert response.json() == {
        "ready": True,
        "state": "ready",
        "trace_id": "a" * 32,
        "trace_url": f"https://langfuse.test/traces/{'a' * 32}",
        "observations": 3,
    }


def test_trace_status_reports_eventual_consistency_as_indexing(monkeypatch) -> None:
    class PendingError(Exception):
        status_code = 404

    class PendingClient:
        api = type(
            "Api",
            (),
            {"trace": type("TraceResource", (), {"get": lambda self, _: (_ for _ in ()).throw(PendingError())})()},
        )()

    monkeypatch.setattr(main_module, "tracing_enabled", lambda: True)
    monkeypatch.setattr(main_module, "get_langfuse_client", lambda: PendingClient())

    with TestClient(app) as test_client:
        response = test_client.get(f"/traces/{'b' * 32}/status")

    assert response.status_code == 200
    assert response.json()["ready"] is False
    assert response.json()["state"] == "indexing"


def test_trace_status_rejects_invalid_id() -> None:
    with TestClient(app) as test_client:
        response = test_client.get("/traces/not-a-trace/status")

    assert response.status_code == 400
