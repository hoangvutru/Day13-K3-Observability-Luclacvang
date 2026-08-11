# Alert và Runbook

Mỗi alert dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High user-facing latency
- Severity: critical
- SLI/SLO liên quan: `latency_p95_ms <= 3000`, target 99.5% trong cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: P95 lớn hơn 3000 ms liên tục 10 phút.
- Ảnh hưởng tới người dùng: phần lớn request chậm, có nguy cơ timeout ở client.
- Ba bước kiểm tra đầu tiên:
  1. Khoanh vùng feature và thời gian tăng P95 trên dashboard.
  2. Mở trace chậm, so sánh duration của `rag.retrieve` và `llm.generate`.
  3. Tìm log cùng correlation ID; kiểm tra `rag_completed.latency_ms`, `llm_completed.latency_ms` và incident control events.
- Mitigation tạm thời: rollback thay đổi mới nhất; tắt incident/test flag; bypass RAG bằng fallback đã kiểm thử nếu vector store là nút thắt.
- Owner: `ai-platform-oncall`

## Alert 2

- Tên: Elevated request error rate
- Severity: critical
- SLI/SLO liên quan: `error_rate_pct <= 2`, target 99% trong cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: error rate lớn hơn 2% trong 5 phút, tối thiểu 20 request để tránh nhiễu mẫu nhỏ.
- Ảnh hưởng tới người dùng: request `/chat` trả 5xx và không có câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xem breakdown `error_type` và feature bị ảnh hưởng.
  2. Mở trace lỗi để xác định span đầu tiên báo exception.
  3. Tìm `request_failed` cùng correlation ID và đối chiếu dependency health.
- Mitigation tạm thời: tắt feature/incident flag gây lỗi, chuyển sang fallback local, hoặc rollback phiên bản vừa triển khai.
- Owner: `ai-platform-oncall`

## Alert 3

- Tên: Quality proxy degradation
- Severity: warning
- SLI/SLO liên quan: `quality_score_avg >= 0.75`, target 95% trong cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: quality trung bình dưới 0.75 trong 15 phút, tối thiểu 20 response.
- Ảnh hưởng tới người dùng: câu trả lời vẫn thành công nhưng kém liên quan hoặc thiếu ngữ cảnh.
- Ba bước kiểm tra đầu tiên:
  1. Phân đoạn quality theo feature, model và prompt version.
  2. So sánh trace baseline/candidate và tài liệu trả về từ `rag.retrieve`.
  3. Kiểm tra prompt label/version trong trace metadata và log correlation tương ứng.
- Mitigation tạm thời: rollback label `production` về prompt baseline đã xác minh.
- Owner: `ai-quality-oncall`
