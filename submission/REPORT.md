# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Lục Lạc Vàng (K3)
- Repository URL: https://github.com/hoangvutru/Day13-K3-Observability-Luclacvang
- Commit SHA cuối: dùng SHA của repository HEAD khi nộp; commit triển khai cụ thể được ghi ở mục 7.

| Thành viên | MSSV | Vai trò | Phạm vi phụ trách |
|---|---|---|---|
| Lâm Việt Hoàng | 2A202601067 | Logging & PII — API/Middleware | CP1 correlation ID, request context, response headers và global exception handler |
| Lã Minh Đức | 2A202601261 | B — Security Engineer | CP1 PII scrubbing, regex patterns và kiểm chứng log không lộ PII |
| Hà Nhật Khánh Duy | 2A202602031 | C — Metrics & Dashboard | CP1/CP2 `error_rate_pct` và dashboard 6 nhóm chỉ số |
| Hoàng Tuấn Trung | 2A202601807 | D — SRE & Alerts Engineer | CP2 SLO, alert rules và alert runbook |
| Trần Huy Hoàng | 2A202601709 | E1 — QA & Tracing | Load test, test hồi quy và trace cho RAG/LLM |
| Bùi Hữu Nghĩa | 2A202601880 | E2 — Chief Investigator, Report & Demo | Điều tra challenge CP3, evidence, báo cáo và demo nhóm |

## 2. Kết quả kỹ thuật

- `validate_logs.py`: **100/100** (85 records, 22 correlation ID, 0 thiếu schema/enrichment, 0 PII leak).
- Tổng số traces: **ít nhất 17 trace thật** (12 trace prompt/rollback và 5 trace challenge).
- Số PII leak còn lại: **0**.
- Dashboard contract dùng nguồn chuẩn `data/logs.jsonl`; validator và thông số runtime được lưu tại [`evidence/validation-results.md`](evidence/validation-results.md).
- Test: **27 passed**.

## 3. Logging và tracing

- Correlation/metadata/PII: [`evidence/logging-pii.md`](evidence/logging-pii.md).
- Validation: [`evidence/validation-results.md`](evidence/validation-results.md).
- Danh sách observations/traces trực tiếp trên Langfuse: [`evidence/langfuse-trace-list.png`](evidence/langfuse-trace-list.png).
- Trace waterfall trực tiếp trên Langfuse: [`evidence/langfuse-trace-waterfall.png`](evidence/langfuse-trace-waterfall.png).
- Trace waterfall tiêu biểu: [`3735d4355029f97df3a7e3404c15933b`](https://cloud.langfuse.com/project/cmso2fnd803s7ad0cpj2r3l76/traces/3735d4355029f97df3a7e3404c15933b).
- Span đáng chú ý: `rag.retrieve=2500 ms`, chiếm khoảng 94% request `2656 ms`; `llm.generate` khoảng 150 ms.

## 4. Prompt versioning

- Prompt name: `day13-chat`.
- Baseline: v1, label `baseline`; candidate: v2, label `candidate`.
- Trace baseline: `0203530208148c7d03ef7d8da14eb214`; trace candidate: `8606d1477904dc77aeda215c89feee49`.
- Đã promote production lên v2 (`53e7478...`) rồi rollback production về v1 (`6d6f30c...`).
- Inventory và link kiểm chứng: [`evidence/langfuse-prompts-traces.md`](evidence/langfuse-prompts-traces.md).
- Screenshot trace production v1 có metadata `prompt_name`, `prompt_label`, `prompt_version`: [`evidence/langfuse-trace-waterfall.png`](evidence/langfuse-trace-waterfall.png).

## 5. Dashboard, SLO và alerts

- Validator: **HỢP LỆ 6/6 panel**.
- Dashboard contract: time range 60 phút, refresh 30 giây, đủ unit và threshold; kết quả validator nằm trong [`evidence/validation-results.md`](evidence/validation-results.md).
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
- Screenshot waterfall challenge: [`evidence/langfuse-trace-waterfall.png`](evidence/langfuse-trace-waterfall.png).
- Toàn bộ bằng chứng: [`evidence/challenge-investigation.md`](evidence/challenge-investigation.md).

## 7. Đóng góp cá nhân

| Thành viên | Phần việc/evidence | Commit/PR | Điều đã học |
|---|---|---|---|
| Lâm Việt Hoàng | `app/middleware.py`, `app/main.py`, correlation/response headers, global exception flow và regression tests | `606cc4c` | Context isolation, correlation ID xuyên suốt request và observability cho lỗi `500` |
| Lã Minh Đức | `app/pii.py`, `app/logging_config.py`, kiểm chứng redaction | `d98ea81`, `9a14d03` | Redaction phải chạy trước renderer/exporter; không log định danh thô |
| Hà Nhật Khánh Duy | `app/metrics.py`, `config/dashboard.yaml`, dashboard validator | `9a14d03` (commit tích hợp nhóm) | P50/P95/P99, error rate, cost/token và quality proxy |
| Hoàng Tuấn Trung | `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md` | `9a14d03` (commit tích hợp nhóm) | Alert symptom-based, duration/minimum traffic và runbook |
| Trần Huy Hoàng | Load/challenge test, RAG/LLM spans, tests và prompt trace linkage | `9a14d03` | Metrics phát hiện, trace khoanh vùng và log chứng minh root cause |
| Bùi Hữu Nghĩa | `challenge-investigation.md`, `REPORT.md`, `DEMO.md` và screenshots | `9e0c5d4` (commit evidence nhóm) | Điều tra Metrics → Traces → Logs và trình bày evidence kiểm chứng được |

### Chi tiết đóng góp — Lâm Việt Hoàng

- Chuẩn hóa `x-request-id`: chỉ chấp nhận `req-<8 ký tự hex>`, chuyển về chữ thường và sinh ID mới khi header thiếu hoặc sai định dạng.
- Xóa/bind `structlog.contextvars` theo vòng đời từng request; lưu correlation ID và thời điểm bắt đầu trong `request.state`.
- Dùng chung logic tạo `x-request-id` và `x-response-time-ms` cho response thành công lẫn lỗi ngoài dự kiến.
- Bổ sung global exception handler: ghi `request_failed` với correlation ID/error type, trả thông báo `500` tổng quát để không lộ chi tiết nội bộ.
- Bổ sung regression tests cho request ID normalization/generation và exception response/log propagation. Kiểm chứng: `27 passed`, log validator `100/100`, dashboard validator `6/6`.

Automation bonus: `scripts/manage_prompts.py` quản lý prompt/rollback idempotent và `scripts/render_dashboard.py` tái tạo dashboard evidence trực tiếp từ log chuẩn.
