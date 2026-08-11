from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .llm_factory import build_llm
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .prompt_management import resolve_prompt
from .tracing import get_langfuse_client, observe, tracing_enabled
from .logging_config import get_logger


log = get_logger()


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float
    trace_id: str | None = None
    trace_url: str | None = None
    model: str = "unknown"
    provider: str = "unknown"
    prompt_name: str = "unknown"
    prompt_label: str = "unknown"
    prompt_version: str = "unknown"
    prompt_source: str = "unknown"
    doc_count: int = 0
    rag_latency_ms: int = 0
    llm_latency_ms: int = 0
    llm_offset_ms: int = 0


class LabAgent:
    def __init__(self, model: str | None = None) -> None:
        self.llm = build_llm(model=model)
        self.model = self.llm.model
        self.provider = self.llm.provider_name

    @observe(as_type="generation", capture_input=False, capture_output=False)
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        correlation_id: str | None = None,
    ) -> AgentResult:
        started = time.perf_counter()
        rag_started = time.perf_counter()
        docs = retrieve(message)
        rag_latency_ms = int((time.perf_counter() - rag_started) * 1000)
        log.info(
            "rag_completed",
            service="agent",
            tool_name="vector_store",
            latency_ms=rag_latency_ms,
            payload={"doc_count": len(docs)},
        )
        langfuse_client = get_langfuse_client()
        prompt = resolve_prompt(
            langfuse_client,
            feature=feature,
            docs=docs,
            message=message,
            enabled=tracing_enabled(),
        )
        llm_started = time.perf_counter()
        llm_offset_ms = int((llm_started - started) * 1000)
        response = self.llm.generate(prompt.text)
        llm_latency_ms = int((time.perf_counter() - llm_started) * 1000)
        log.info(
            "llm_completed",
            service="agent",
            tool_name=f"{response.provider}_llm",
            latency_ms=llm_latency_ms,
            model=response.model,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
        )
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = (
            response.cost_usd
            if response.cost_usd is not None
            else self._estimate_cost(
                response.usage.input_tokens, response.usage.output_tokens
            )
            if response.provider == "fake"
            else 0.0
        )

        trace_metadata = {
            "prompt_name": prompt.name,
            "prompt_label": prompt.label,
            "prompt_version": prompt.version,
            "prompt_source": prompt.source,
        }
        if correlation_id:
            trace_metadata["correlation_id"] = correlation_id

        langfuse_client.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["lab", feature, response.model, response.provider],
            metadata=trace_metadata,
        )
        langfuse_client.update_current_generation(
            model=response.model,
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
                "prompt_fetch_error": prompt.fetch_error,
                "llm_provider": response.provider,
                "resolved_model": response.model,
                "rag_latency_ms": rag_latency_ms,
                "llm_latency_ms": llm_latency_ms,
            },
            usage_details={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            cost_details={"total": cost_usd},
            prompt=prompt.managed_prompt,
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        get_trace_id = getattr(langfuse_client, "get_current_trace_id", None)
        trace_id = get_trace_id() if callable(get_trace_id) else None
        get_trace_url = getattr(langfuse_client, "get_trace_url", None)
        trace_url = None
        if trace_id and tracing_enabled() and callable(get_trace_url):
            try:
                trace_url = get_trace_url(trace_id=trace_id)
            except Exception as exc:  # Trace UI availability must not break inference.
                log.warning(
                    "trace_url_unavailable",
                    service="agent",
                    error_type=type(exc).__name__,
                )
        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
            trace_id=trace_id,
            trace_url=trace_url,
            model=response.model,
            provider=response.provider,
            prompt_name=prompt.name,
            prompt_label=prompt.label,
            prompt_version=prompt.version,
            prompt_source=prompt.source,
            doc_count=len(docs),
            rag_latency_ms=rag_latency_ms,
            llm_latency_ms=llm_latency_ms,
            llm_offset_ms=llm_offset_ms,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
