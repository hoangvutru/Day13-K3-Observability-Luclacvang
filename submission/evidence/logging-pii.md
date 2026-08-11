# Evidence — correlation ID, metadata và PII redaction

Các dòng dưới đây được trích từ `data/logs.jsonl` sau lượt chạy chính thức. Không chứa PII nguyên văn.

## Correlation và metadata

```json
{"event":"request_received","correlation_id":"req-00fed000","user_id_hash":"a757d68204ad","session_id":"pii-s1","feature":"qa","model":"claude-sonnet-4-5","env":"dev","payload":{"message_preview":"Email [REDACTED_EMAIL] and phone [REDACTED_PHONE_VN]"}}
```

Response trả cùng `x-request-id=req-00fed000`; các event `rag_completed`, `llm_completed` và `response_sent` của request dùng cùng correlation ID.

## Redaction cases

```json
{"correlation_id":"req-00fed001","payload":{"message_preview":"Test card [REDACTED_CREDIT_CARD] and CCCD [REDACTED_CCCD]"}}
{"correlation_id":"req-00fed002","payload":{"message_preview":"[REDACTED_PASSPORT]; address supplied"}}
```

Scrubber chạy trước JSON renderer/file processor và đệ quy qua dictionary/list/tuple, nên cả payload lồng nhau và exception detail đều được xử lý trước khi ghi file.
