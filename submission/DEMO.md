# Demo 5 phút

## Phân vai trình bày

- Lâm Việt Hoàng: API, middleware, correlation ID và observability cho exception.
- Lã Minh Đức: PII redaction và log an toàn.
- Hà Nhật Khánh Duy: metrics và dashboard contract 6 panel.
- Hoàng Tuấn Trung: SLO, alerts và runbook.
- Trần Huy Hoàng: load test, prompt traces và waterfall RAG/LLM.
- Bùi Hữu Nghĩa: challenge root cause, fix, preventive measures và kết luận.

1. Chạy API và mở `/health`: tracing bật, incident đều `false`.
2. Chạy `load_test.py --concurrency 5`, sau đó `validate_logs.py`: chỉ ra correlation, metadata và redaction.
3. Chạy `python scripts/validate_dashboard.py`, rồi đối chiếu 6 panel, đơn vị, time range 60 phút và threshold trong `config/dashboard.yaml`.
4. Mở trace `3735d435...`: so sánh `rag.retrieve` 2500 ms với `llm.generate` ~150 ms; tìm log `req-42c65d4b`.
5. Mở prompt v1/v2 và chạy `manage_prompts.py status`: trạng thái cuối production v1 sau rollback.

## Câu hỏi cần trả lời được

- Correlation ID nối các log trong một request; trace ID nối log với waterfall phân tán.
- P95 là latency mà 95% mẫu không vượt quá, phù hợp phát hiện “đuôi chậm” hơn mean.
- PII phải scrub trước renderer/exporter; hash user ID là một chiều và không log ID thô.
- Prompt label là con trỏ triển khai; version là bản bất biến. Rollback di chuyển label, không sửa lịch sử.
- Alert symptom-based phản ánh ảnh hưởng người dùng; thêm thời gian duy trì và minimum traffic để giảm nhiễu.

### Câu hỏi phần Lâm Việt Hoàng

- Vì sao phải `clear_contextvars()` ở đầu và cuối request? Để worker không giữ metadata của request trước và gắn nhầm vào log request sau.
- Vì sao không tin trực tiếp `x-request-id` từ client? ID sai định dạng hoặc quá dài làm log khó truy vấn và có thể trở thành dữ liệu không kiểm soát; middleware chỉ nhận `req-<8 hex>`.
- Khi endpoint phát sinh lỗi ngoài dự kiến, điều gì còn được giữ lại? Response vẫn có correlation ID và latency; log `request_failed` có cùng ID và error type, còn client chỉ nhận thông báo `500` tổng quát.
