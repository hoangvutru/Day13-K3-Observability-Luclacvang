# Evidence — Langfuse prompt versions và traces

- Project: `cmso2fnd803s7ad0cpj2r3l76`
- Prompt: `day13-chat`
- Baseline: version 1, labels `baseline`, `production` (trạng thái cuối)
- Candidate: version 2, label `candidate`
- Công cụ tái tạo/rollback: `python scripts/manage_prompts.py {bootstrap|promote|rollback|status}`

## Trace inventory

| Label | Version | Trace ID | Correlation ID |
|---|---:|---|---|
| baseline | 1 | `0203530208148c7d03ef7d8da14eb214` | `req-00989680` |
| baseline | 1 | `73c4dd9d536fdfc426808163faca0e8f` | `req-00989681` |
| baseline | 1 | `f1fd4853f32a3fb0d956b44b0d2ad1aa` | `req-00989682` |
| baseline | 1 | `50d4fad5bb03adf890bda448e6112019` | `req-00989683` |
| baseline | 1 | `a6a9ad9d8c619cf55161fc5a904881a7` | `req-00989684` |
| candidate | 2 | `8606d1477904dc77aeda215c89feee49` | `req-00989685` |
| candidate | 2 | `022c67aea17b7099423d67a5cbb2e293` | `req-00989686` |
| candidate | 2 | `26132ba6bf5b15dd068117363db05e20` | `req-00989687` |
| candidate | 2 | `2ae0b9eb2fa0dc7c47cafb3ac84d0a2c` | `req-00989688` |
| candidate | 2 | `a096ae59a88071fb6b87eee80903191c` | `req-00989689` |

## Promote và rollback thật

1. `manage_prompts.py promote` chuyển `production` sang v2; trace xác minh: [`53e7478db6f2cc75d11bdbe4a3379f74`](https://cloud.langfuse.com/project/cmso2fnd803s7ad0cpj2r3l76/traces/53e7478db6f2cc75d11bdbe4a3379f74), correlation `req-00abc002`.
2. `manage_prompts.py rollback` đưa `production` về v1; trace xác minh: [`6d6f30cbdf90b8c193528b559a624b25`](https://cloud.langfuse.com/project/cmso2fnd803s7ad0cpj2r3l76/traces/6d6f30cbdf90b8c193528b559a624b25), correlation `req-00abc001`.
3. Trạng thái cuối đã gọi API kiểm tra: `baseline=v1; candidate=v2; production=v1`.

Trace waterfall gồm generation `LabAgent.run`, span con `rag.retrieve` và generation con `llm.generate`; input/output capture bị tắt để tránh đưa PII vào trace.
