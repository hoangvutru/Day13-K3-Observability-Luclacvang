# Alert runbooks

All alerts are based on user-facing symptoms or SLOs. Start every investigation
with the dashboard, use a trace to isolate the slow or failing operation, then
use the matching correlation ID to confirm the root cause in JSON logs.

## Alert 1

- Name: High chat latency
- Severity: warning
- SLI/SLO: `latency_p95_ms`, objective 3000 ms
- Trigger: P95 `response_sent.latency_ms` exceeds 3000 ms for 10 minutes.
- User impact: chat responses are slow and may time out.
- First checks: inspect the latency panel; open a slow trace; filter logs by its correlation ID.
- Temporary mitigation: disable the active incident, reduce load, or use a retrieval fallback.
- Owner: platform-observability

## Alert 2

- Name: Elevated chat error rate
- Severity: critical
- SLI/SLO: `error_rate_pct`, objective at most 2%
- Trigger: `request_failed / request_received` exceeds 2% for 5 minutes.
- User impact: users do not receive a chat response.
- First checks: inspect the error breakdown; open a recent failed trace; compare `error_type` and correlation ID in logs.
- Temporary mitigation: disable the failing dependency or incident, apply bounded retries, and return a safe fallback.
- Owner: api-oncall

## Alert 3

- Name: Quality proxy degradation
- Severity: warning
- SLI/SLO: `quality_score_avg`, objective at least 0.75
- Trigger: mean `response_sent.quality_score` is below 0.75 for 15 minutes.
- User impact: answers may lack retrieved context or be unhelpful.
- First checks: inspect the quality panel; compare prompt label/version in traces; check retrieved-document count and redacted log previews.
- Temporary mitigation: roll back the production prompt label to the stable version and check the retrieval corpus.
- Owner: ai-product
