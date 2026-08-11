# Demo 5 phút

1. Chạy API và mở `/health`: tracing bật, incident đều `false`.
2. Chạy `load_test.py --concurrency 5`, sau đó `validate_logs.py`: chỉ ra correlation, metadata và redaction.
3. Mở `dashboard-runtime.svg`: đọc 6 panel, đơn vị, 60 phút và threshold.
4. Mở trace `3735d435...`: so sánh `rag.retrieve` 2500 ms với `llm.generate` ~150 ms; tìm log `req-42c65d4b`.
5. Mở prompt v1/v2 và chạy `manage_prompts.py status`: trạng thái cuối production v1 sau rollback.

## Câu hỏi cần trả lời được

- Correlation ID nối các log trong một request; trace ID nối log với waterfall phân tán.
- P95 là latency mà 95% mẫu không vượt quá, phù hợp phát hiện “đuôi chậm” hơn mean.
- PII phải scrub trước renderer/exporter; hash user ID là một chiều và không log ID thô.
- Prompt label là con trỏ triển khai; version là bản bất biến. Rollback di chuyển label, không sửa lịch sử.
- Alert symptom-based phản ánh ảnh hưởng người dùng; thêm thời gian duy trì và minimum traffic để giảm nhiễu.
