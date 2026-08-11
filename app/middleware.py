from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


REQUEST_ID_PATTERN = re.compile(r"req-[0-9a-f]{8}", re.IGNORECASE)


def resolve_correlation_id(supplied_id: str | None) -> str:
    candidate = (supplied_id or "").strip()
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate.lower()
    return f"req-{uuid.uuid4().hex[:8]}"


def observability_response_headers(correlation_id: str, started_at: float) -> dict[str, str]:
    elapsed_ms = max(0.0, (time.perf_counter() - started_at) * 1000)
    return {
        "x-request-id": correlation_id,
        "x-response-time-ms": f"{elapsed_ms:.2f}",
    }


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Context variables can survive worker reuse, so every request starts clean.
        clear_contextvars()

        correlation_id = resolve_correlation_id(request.headers.get("x-request-id"))
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id
        request.state.request_started_at = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers.update(
                observability_response_headers(
                    correlation_id,
                    request.state.request_started_at,
                )
            )
            return response
        finally:
            # Avoid retaining request metadata outside this request lifecycle.
            clear_contextvars()
