# Báo cáo Day 13 Observability — Hà Nhật Khánh Duy

## 1. Thông tin cá nhân

- Họ tên: Hà Nhật Khánh Duy
- MSSV: 2A202602031
- Nhóm: Lục Lạc Vàng (K3)
- Vai trò: C — Metrics & Dashboard
- Repository URL: https://github.com/hoangvutru/Day13-K3-Observability-Luclacvang
- Commit SHA: `9a14d03` (commit tích hợp nhóm)

## 2. Phạm vi phụ trách

- **CP1**: Triển khai `error_rate_pct` trong module metrics — tính tỷ lệ lỗi phần trăm từ error count / traffic.
- **CP2**: Thiết kế và hoàn thiện dashboard contract 6 nhóm chỉ số theo `config/dashboard.yaml`, đảm bảo validator `scripts/validate_dashboard.py` báo hợp lệ 6/6 panel.

## 3. Các file đã triển khai

### 3.1. `app/metrics.py`

Module thu thập và tổng hợp metrics runtime:

- **Dữ liệu thu thập**: latency (ms), cost (USD), tokens in/out, quality score, error count, traffic count.
- **Thread-safe**: sử dụng `threading.Lock` để đồng bộ truy cập dữ liệu giữa các request đồng thời.
- **Hàm chính**:
  - `record_request(latency_ms, cost_usd, tokens_in, tokens_out, quality_score)`: ghi nhận metrics mỗi request thành công.
  - `record_error(error_type)`: đếm lỗi theo loại.
  - `percentile(values, p)`: tính percentile (P50, P95, P99) — sắp xếp danh sách rồi lấy phần tử tại vị trí tương ứng.
  - `snapshot()`: trả về dict tổng hợp toàn bộ metrics tại thời điểm gọi.
- **`error_rate_pct`**: công thức `(error_count / traffic) * 100`, trả về `0.0` nếu chưa có traffic. Đây là chỉ số cốt lõi cho panel Error rate trên dashboard.

### 3.2. `config/dashboard.yaml`

Dashboard contract định nghĩa 6 panel bắt buộc:

| Panel ID  | Title                    | Source           | Unit                | Threshold                |
| --------- | ------------------------ | ---------------- | ------------------- | ------------------------ |
| latency   | Latency percentiles      | data/logs.jsonl  | ms                  | P95 ≤ 3000               |
| traffic   | Request traffic          | data/logs.jsonl  | requests_per_minute | rate_per_minute ≥ 1      |
| errors    | Error rate and breakdown | data/logs.jsonl  | percent             | error_rate_pct ≤ 2       |
| cost      | Cost over time           | data/logs.jsonl  | usd                 | total ≤ $2.5             |
| tokens    | Input and output tokens  | data/logs.jsonl  | tokens              | sum_by_field ≤ 50,000    |
| quality   | Quality proxy            | data/logs.jsonl  | score_0_to_1        | mean ≥ 0.75              |

Cấu hình chung:
- `schema_version: 1`
- `time_range_minutes: 60`
- `refresh_seconds: 30`
- Mỗi panel có đầy đủ: `title`, `source`, `events`, `fields`, `aggregations`, `query`, `unit`, `threshold`.

### 3.3. `scripts/validate_dashboard.py` (dashboard validator)

Script kiểm tra tính hợp lệ của dashboard contract:

- Kiểm tra `schema_version == 1`, `time_range_minutes == 60`, `refresh_seconds` trong khoảng 15–30.
- Kiểm tra đủ 6 panel ID: `latency`, `traffic`, `errors`, `cost`, `tokens`, `quality`.
- Kiểm tra mỗi panel có đủ các trường bắt buộc: `title`, `source`, `events`, `fields`, `aggregations`, `query`, `unit`, `threshold`.
- Kiểm tra threshold hợp lệ: `aggregation` thuộc danh sách aggregations của panel, `operator` là `lte` hoặc `gte`, `value` là số.

### 3.4. `scripts/render_dashboard.py` (bonus automation)

Script tự động tạo file SVG dashboard từ `data/logs.jsonl`:

- Đọc log records trong 60 phút gần nhất.
- Tính toán metrics thật: P50/P95/P99, error rate, total cost, tokens in/out, quality mean.
- Render 6 panel với thanh progress bar và trạng thái healthy/unhealthy dựa trên threshold từ `config/dashboard.yaml`.
- Output: `submission/evidence/dashboard-runtime.svg`.

## 4. Kết quả đạt được

### Dashboard validator
```text
HỢP LỆ: 6/6 panel có trong dashboard contract.
```

### Log validator (kết quả nhóm)
```text
Total log records analyzed: 85
Estimated Score: 100/100
```

### Automated tests
```text
32 passed in 2.02s
```

Có thể tái tạo bằng:
```bash
python scripts/validate_dashboard.py
python scripts/validate_logs.py
python -m pytest -q
```

## 5. Evidence liên quan

- Kết quả validator đầy đủ: [`evidence/validation-results.md`](evidence/validation-results.md).
- Dashboard contract: [`config/dashboard.yaml`](../config/dashboard.yaml).
- Metrics module: [`app/metrics.py`](../app/metrics.py).

## 6. Điều đã học

- **Percentile (P50/P95/P99)**: P95 là giá trị mà 95% request có latency thấp hơn hoặc bằng. So với mean, P95 nhạy hơn với "đuôi chậm" (tail latency), phản ánh chính xác hơn trải nghiệm người dùng thực tế. P50 cho biết trải nghiệm "thông thường", P99 cho biết worst case.
- **Error rate**: Tính bằng tỷ lệ phần trăm request lỗi trên tổng traffic. Cần guard `if traffic == 0` để tránh chia cho 0. Threshold ≤ 2% là mức chấp nhận được cho SLO.
- **Dashboard contract**: Dashboard không phải chỉ là hình ảnh — nó cần contract rõ ràng: nguồn dữ liệu (`data/logs.jsonl`), time range, refresh interval, unit cho mỗi panel, và threshold để phân biệt healthy/unhealthy.
- **6 nhóm chỉ số cần thiết cho Observability AI**: latency (performance), traffic (load), errors (reliability), cost (budget), tokens (usage), quality (output effectiveness). Đây là bộ chỉ số tối thiểu để quan sát một hệ thống AI.
- **Thread safety**: Khi nhiều request đồng thời cập nhật metrics, cần dùng Lock để tránh race condition trên các biến toàn cục.
