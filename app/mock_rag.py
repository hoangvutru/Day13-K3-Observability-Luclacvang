from __future__ import annotations

import os
import time

from .incidents import STATE
from .tracing import observe

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, traces localize them, logs explain root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}
DEMO_ERROR_TRIGGER = "Trigger a vector store failure for the observability demo."


class DemoVectorStoreError(RuntimeError):
    """Intentional, safe failure used to demonstrate error observability."""


@observe(name="rag.retrieve", as_type="span", capture_input=False, capture_output=False)
def retrieve(message: str) -> list[str]:
    demo_trigger_enabled = (
        os.getenv("APP_ENV", "dev").lower() != "production"
        and os.getenv("ENABLE_DEMO_ERROR_TRIGGER", "true").lower() == "true"
    )
    if demo_trigger_enabled and message.strip().casefold() == DEMO_ERROR_TRIGGER.casefold():
        raise DemoVectorStoreError("Intentional vector store failure")
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    lowered = message.lower()
    for key, docs in CORPUS.items():
        if key in lowered:
            return docs
    return ["No domain document matched. Use general fallback answer."]
