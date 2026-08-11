# Challenge investigation — day13-k3-observability-v1

## Metrics → Traces → Logs

- Baseline (13 request): P50 `155 ms`, P95 `893 ms`, error `0%`, quality `0.8692`.
- Sau bật challenge `rag_slow` (18 request tích lũy): P50 `865 ms`, P95 `2656 ms`, error `0%`, quality `0.8667`.
- P95 vượt ngưỡng challenge `2000 ms`; không có tăng error hoặc giảm quality đáng kể, nên triệu chứng là latency.
- Trace chính: [`3735d4355029f97df3a7e3404c15933b`](https://cloud.langfuse.com/project/cmso2fnd803s7ad0cpj2r3l76/traces/3735d4355029f97df3a7e3404c15933b).
- Correlation ID: `req-42c65d4b`.

Log chứng minh:

```json
{"ts":"2026-08-11T03:08:03.978063Z","event":"rag_completed","correlation_id":"req-42c65d4b","feature":"refund","tool_name":"vector_store","latency_ms":2500}
{"ts":"2026-08-11T03:08:04.134358Z","event":"response_sent","correlation_id":"req-42c65d4b","trace_id":"3735d4355029f97df3a7e3404c15933b","latency_ms":2656}
```

Kết luận: `rag.retrieve` chiếm 2500/2656 ms (~94% total), trong khi request thành công và LLM chỉ khoảng 150 ms. Root cause là độ trễ vector store/RAG được inject bởi challenge, không phải LLM, prompt hay lỗi API.

- Fix đã thực hiện: tắt `rag_slow` bằng endpoint control; `/health` xác nhận tất cả incident flag về `false`.
- Preventive measures: alert P95 > 3000 ms/10 phút; span riêng cho dependency; timeout/circuit breaker và fallback cache cho retrieval; canary + rollback cho thay đổi dependency.
