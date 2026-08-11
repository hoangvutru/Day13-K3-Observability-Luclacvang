# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Lục Lạc Vàng (K3)
- Repository URL: https://github.com/hoangvutru/Day13-K3-Observability-Luclacvang
- Commit SHA cuối: dùng SHA của repository HEAD khi nộp; commit triển khai cụ thể được ghi ở mục 7.
- Thành viên/vai trò: HuyHoangTran — Logging & PII; Tracing & Prompt Version; Dashboard/SLO/Alert; Incident/Report/Demo.

## 2. Kết quả kỹ thuật

- `validate_logs.py`: **100/100** (85 records, 22 correlation ID, 0 thiếu schema/enrichment, 0 PII leak).
- Tổng số traces: **ít nhất 17 trace thật** (12 trace prompt/rollback và 5 trace challenge).
- Số PII leak còn lại: **0**.
- Dashboard: [`evidence/dashboard-runtime.svg`](evidence/dashboard-runtime.svg), nguồn chuẩn `data/logs.jsonl`.
- Test: **25 passed**.

## 3. Logging và tracing

- Correlation/metadata/PII: [`evidence/logging-pii.md`](evidence/logging-pii.md).
- Validation: [`evidence/validation-results.md`](evidence/validation-results.md).
- Trace waterfall tiêu biểu: [`3735d4355029f97df3a7e3404c15933b`](https://cloud.langfuse.com/project/cmso2fnd803s7ad0cpj2r3l76/traces/3735d4355029f97df3a7e3404c15933b).
- Span đáng chú ý: `rag.retrieve=2500 ms`, chiếm khoảng 94% request `2656 ms`; `llm.generate` khoảng 150 ms.

## 4. Prompt versioning

- Prompt name: `day13-chat`.
- Baseline: v1, label `baseline`; candidate: v2, label `candidate`.
- Trace baseline: `0203530208148c7d03ef7d8da14eb214`; trace candidate: `8606d1477904dc77aeda215c89feee49`.
- Đã promote production lên v2 (`53e7478...`) rồi rollback production về v1 (`6d6f30c...`).
- Inventory và link kiểm chứng: [`evidence/langfuse-prompts-traces.md`](evidence/langfuse-prompts-traces.md).

## 5. Dashboard, SLO và alerts

- Validator: **HỢP LỆ 6/6 panel**.
- Dashboard runtime: [`evidence/dashboard-runtime.svg`](evidence/dashboard-runtime.svg), time range 60 phút, refresh 30 giây, đủ unit và threshold.
- SLO chính: P95 ≤ 3000 ms với target 99.5%/28 ngày; P95 nhạy với tail latency và sát trải nghiệm người dùng.
- SLO bổ sung: error ≤ 2%, daily cost ≤ $2.5, quality mean ≥ 0.75.
- Ba alert symptom-based có duration/minimum traffic/owner tại [`../config/alert_rules.yaml`](../config/alert_rules.yaml); runbook tại [`../docs/alerts.md`](../docs/alerts.md).

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`; affected feature: `refund`; scenario release: `rag_slow`.
- Metrics: P95 tăng `893 → 2656 ms`, vượt threshold 2000 ms; error vẫn 0%.
- Trace: `3735d4355029f97df3a7e3404c15933b`; correlation: `req-42c65d4b`.
- Root cause: span/log `rag.retrieve`/`vector_store` mất 2500 ms; không phải LLM.
- Fix: disable flag challenge, xác minh health trở về bình thường.
- Prevention: latency alert, dependency span, timeout/circuit breaker, retrieval fallback/cache và canary.
- Toàn bộ bằng chứng: [`evidence/challenge-investigation.md`](evidence/challenge-investigation.md).

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| HuyHoangTran | Hoàn thiện toàn bộ logging, PII, trace/prompt, metrics, dashboard, SLO/alerts, challenge và report | Commit triển khai Day 13 trong repository HEAD | Phân biệt metrics/trace/log; percentile; redaction trước export; prompt label/version và rollback; alert dựa trên symptom |

Automation bonus: `scripts/manage_prompts.py` quản lý prompt/rollback idempotent và `scripts/render_dashboard.py` tái tạo dashboard evidence trực tiếp từ log chuẩn.
