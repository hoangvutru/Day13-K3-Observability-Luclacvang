# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: Latency spike trên API chat
- Severity: high
- SLI/SLO liên quan: p95 latency của event `response_sent`
- Điều kiện và thời gian duy trì: p95 latency > 2000 ms trong 5 phút liên tục
- Ảnh hưởng tới người dùng: Trải nghiệm chậm, phản hồi không kịp thời cho request chat
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `latency` trên dashboard, xác định khoảng thời gian tăng cao.
  2. Tìm trace có `response_sent` latency cao bằng correlation ID và prompt metadata.
  3. So sánh với logs `request_received`/`response_sent` để xác định bước xử lý chậm.
- Mitigation tạm thời: tắt incident practice nếu có, giảm tải traffic hoặc khởi động lại service phụ trợ.
- Owner: observability-team

## Alert 2

- Tên: Tăng lỗi API
- Severity: medium
- SLI/SLO liên quan: error rate của các request chat
- Điều kiện và thời gian duy trì: error rate > 2% trong 5 phút
- Ảnh hưởng tới người dùng: Nhiều request chat bị thất bại, trải nghiệm AI không ổn định
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `errors` trên dashboard để xác nhận xu hướng tăng.
  2. Mở trace `request_failed` và xác định `error_type` cùng correlation ID.
  3. Kiểm tra logs liên quan cùng request để tìm chi tiết nguyên nhân.
- Mitigation tạm thời: giới hạn input nếu cần, hoặc rollback thay đổi gần nhất.
- Owner: api-reliability-team

## Alert 3

- Tên: Giảm chất lượng kết quả AI
- Severity: medium
- SLI/SLO liên quan: mean quality_score của `response_sent`
- Điều kiện và thời gian duy trì: quality_score trung bình < 0.75 trong 5 phút
- Ảnh hưởng tới người dùng: Câu trả lời kém chính xác, độ tin cậy thấp
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `quality` trên dashboard để xác nhận xu hướng giảm.
  2. Mở trace và kiểm tra prompt version/label để xác định phiên bản prompt đang dùng.
  3. Xem logs và trace metadata để kiểm tra xem liệu `docs` hoặc prompt input có bị lỗi.
- Mitigation tạm thời: chuyển prompt sang phiên bản baseline hoặc tạm dừng thay đổi prompt mới.
- Owner: ai-quality-team
