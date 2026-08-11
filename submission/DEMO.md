# Demo 5 phút — Hà Nhật Khánh Duy (Metrics & Dashboard)

## Phần trình bày của tôi

**Nội dung demo**: Metrics module và dashboard contract 6 panel.

### Bước demo

1. **Chạy dashboard validator**:
   ```bash
   python scripts/validate_dashboard.py
   ```
   Kết quả mong đợi: `HỢP LỆ: 6/6 panel có trong dashboard contract.`

2. **Đối chiếu 6 panel trong `config/dashboard.yaml`**:
   - Latency percentiles (P50/P95/P99) — unit: ms, threshold: P95 ≤ 3000.
   - Request traffic — unit: requests/min, threshold: rate ≥ 1.
   - Error rate & breakdown — unit: %, threshold: error_rate_pct ≤ 2.
   - Cost over time — unit: USD, threshold: total ≤ $2.5.
   - Input/output tokens — unit: tokens, threshold: sum ≤ 50,000.
   - Quality proxy — unit: score 0–1, threshold: mean ≥ 0.75.

3. **Giải thích `app/metrics.py`**:
   - Cách `record_request()` thu thập latency, cost, tokens, quality.
   - Cách `snapshot()` tổng hợp và tính `error_rate_pct`.
   - Cách `percentile()` tính P50/P95/P99.

4. **Render dashboard SVG** (nếu có thời gian):
   ```bash
   python scripts/render_dashboard.py
   ```
   Mở file `submission/evidence/dashboard-runtime.svg` để xem 6 panel với dữ liệu thật.

## Câu hỏi cần trả lời được

- **P95 là gì?** P95 là latency mà 95% request nhanh hơn hoặc bằng. Nó phù hợp phát hiện "đuôi chậm" hơn mean vì mean bị kéo bởi outlier, còn P95 phản ánh trải nghiệm thực tế của phần lớn người dùng.
- **Error rate tính thế nào?** `error_count / traffic * 100`. Cần xử lý trường hợp traffic = 0 (trả về 0.0).
- **Tại sao dashboard cần contract?** Để đảm bảo dashboard có đủ chỉ số, đúng nguồn dữ liệu, đúng time range và có threshold rõ ràng. Contract giúp validate tự động và tái tạo được.
- **6 nhóm chỉ số gồm gì?** Latency (performance), Traffic (load), Errors (reliability), Cost (budget), Tokens (usage), Quality (output effectiveness).
- **Thread safety trong metrics?** Dùng `threading.Lock` để đồng bộ truy cập khi nhiều request đồng thời ghi metrics vào các biến toàn cục.
