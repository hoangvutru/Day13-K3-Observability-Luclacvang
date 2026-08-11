from __future__ import annotations

import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import get_langfuse_client, tracing_enabled

configure_logging()
log = get_logger()
agent = LabAgent()


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        correlation_id="system-startup",
        payload={"tracing_enabled": tracing_enabled()},
    )
    yield


app = FastAPI(title="Day 13 Observability Lab", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
STATIC_DIR = Path(__file__).with_name("static")
TRACE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def demo_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "tracing_enabled": tracing_enabled(),
        "llm_provider": agent.provider,
        "model": agent.model,
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "incidents": status(),
    }


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


def _lookup_trace(trace_id: str) -> dict:
    client = get_langfuse_client()
    try:
        trace = client.api.trace.get(trace_id)
    except Exception as exc:  # Langfuse ingestion is eventually consistent.
        status_code = getattr(exc, "status_code", None)
        if status_code == 404 or type(exc).__name__ == "NotFoundError":
            return {"ready": False, "state": "indexing", "trace_id": trace_id}
        log.warning(
            "trace_readiness_check_failed",
            service="api",
            error_type=type(exc).__name__,
        )
        return {"ready": False, "state": "unavailable", "trace_id": trace_id}

    get_trace_url = getattr(client, "get_trace_url", None)
    trace_url = None
    if callable(get_trace_url):
        try:
            trace_url = get_trace_url(trace_id=trace_id)
        except Exception:
            trace_url = None
    return {
        "ready": True,
        "state": "ready",
        "trace_id": trace_id,
        "trace_url": trace_url,
        "observations": len(getattr(trace, "observations", []) or []),
    }


@app.get("/traces/{trace_id}/status")
async def trace_status(trace_id: str) -> dict:
    normalized = trace_id.strip().lower()
    if not TRACE_ID_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid trace ID")
    if not tracing_enabled():
        return {"ready": False, "state": "disabled", "trace_id": normalized}
    return await run_in_threadpool(_lookup_trace, normalized)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        env=os.getenv("APP_ENV", "dev"),
    )
    
    log.info(
        "request_received",
        service="api",
        payload={"message_preview": summarize_text(body.message)},
    )
    try:
        result = await run_in_threadpool(
            agent.run,
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
            correlation_id=request.state.correlation_id,
        )
        if os.getenv("LANGFUSE_FLUSH_EACH_REQUEST", "false").lower() == "true":
            try:
                await run_in_threadpool(get_langfuse_client().flush)
            except Exception as flush_error:  # Observability must not break inference.
                log.warning(
                    "trace_flush_failed",
                    service="api",
                    error_type=type(flush_error).__name__,
                )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
            trace_id=result.trace_id,
            model=result.model,
            provider=result.provider,
            payload={"answer_preview": summarize_text(result.answer)},
        )
        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
            trace_id=result.trace_id,
            trace_url=result.trace_url,
            model=result.model,
            provider=result.provider,
            prompt_name=result.prompt_name,
            prompt_label=result.prompt_label,
            prompt_version=result.prompt_version,
            rag_latency_ms=result.rag_latency_ms,
            llm_latency_ms=result.llm_latency_ms,
        )
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
