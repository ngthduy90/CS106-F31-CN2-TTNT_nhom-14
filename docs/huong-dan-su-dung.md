# Hướng dẫn sử dụng

Đồ án môn Trí tuệ nhân tạo (CS106.F31.CN2) — Nhóm 14
Đề tài 5: dự báo giá nhà từ dữ liệu rao vặt bất động sản TP.HCM

## 1. Cài đặt

Yêu cầu Python 3.11 (các thư viện trong `requirements.txt` được ghim theo phiên bản đã
kiểm trên 3.11; bản 3.12 trở lên có thể vướng `underthesea`).

```bash
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Kiểm tra nhanh:

```bash
pytest -q                          # phải xanh toàn bộ, gồm cả test chống rò rỉ nhãn
```

## 2. Chạy toàn bộ pipeline

```bash
make all
```

Lệnh này chạy tuần tự: thu thập dữ liệu → cổng kiểm chất lượng → tiền xử lý → dựng đặc
trưng → huấn luyện và thí nghiệm → sinh bảng biểu và báo cáo.

Chạy từng bước khi cần:

| Lệnh | Việc |
|---|---|
| `make crawl` | Thu thập tin từ Chợ Tốt, mogi.vn và tải bộ dữ liệu lịch sử |
| `make qa` | Chấm kho dữ liệu thô theo 6 ngưỡng chất lượng |
| `make prep` | Làm sạch, trích đặc trưng, chuẩn hoá địa chỉ, khử trùng lặp |
| `make train` | Chạy E1, E2, E3 và ablation |
| `make report` | Sinh lại mọi bảng, hình, và bản Word của báo cáo |
| `make demo` | Mở web app dự báo |
| `make test` | Chạy kiểm thử |

## 3. Thu thập dữ liệu

Mặc định các script crawl lấy ÍT, đủ để kiểm pipeline chạy đúng:

```bash
python -m src.crawl.run_chotot --dry-run                 # xem thử, không ghi file
python -m src.crawl.run_chotot --max-per-district 800    # mặc định 300
python -m src.crawl.run_mogi   --max-per-district 120
python -m src.crawl.fetch_hf_dataset --max-shards 3
```

Muốn đạt mốc 8.000 tin của đề thì tăng `--max-per-district` rồi chạy lại. Script ghi
checkpoint và khử trùng theo mã tin, nên **chạy lại chỉ bổ sung phần còn thiếu**, không
tải lại từ đầu và không tạo bản trùng.

Tốc độ được giới hạn ở 1 request mỗi 1,5 giây kèm lùi luỹ tiến khi máy chủ báo bận. Đừng
sửa `REQUEST_DELAY_SECONDS` trong `src/config.py` xuống thấp hơn.

## 4. Web app dự báo

```bash
make demo
# hoặc: streamlit run src/demo/app.py
```

App cần file `models/champion.joblib`. Nếu chưa có, chạy trước:

```bash
python -m src.evaluation.run_experiments
python -m src.evaluation.analysis
```

Cách dùng: chọn quận, phường, loại bất động sản, nhập diện tích và các thông số, dán mô
tả tin rao rồi bấm **Dự báo giá**. App trả về một khoảng giá kèm biểu đồ giải thích cho
biết đặc trưng nào đẩy dự báo lên hay xuống.

Bộ số mẫu để thử:

| Trường | Giá trị |
|---|---|
| Quận / phường | Tân Bình / Phường 13 |
| Loại | Nhà phố liền kề |
| Diện tích | 64 m² |
| Số tầng / phòng ngủ / nhà tắm | 3 / 3 / 3 |
| Mặt tiền / hẻm | 4 m / 5 m |
| Vị trí, pháp lý | hẻm, sổ hồng riêng |
| Mô tả | "Nhà đẹp hẻm xe hơi, sổ hồng riêng, full nội thất, gần chợ và trường học, vào ở ngay." |

## 5. Đọc kết quả ở đâu

| Nội dung | Đường dẫn |
|---|---|
| Bảng so sánh mô hình | `reports/tables/e1-results-*.md` |
| Chuyển giao theo thời gian | `reports/tables/e2-results.md` |
| Ablation đặc trưng văn bản | `reports/tables/ablation.md` |
| Chất lượng trích xuất từ văn bản | `reports/tables/extraction-quality.md` |
| Data funnel | `reports/tables/data-funnel.md` |
| Hình vẽ | `reports/figures/` |
| Kết quả thô dạng JSON | `reports/results/` |

Mọi bảng markdown đều **sinh lại được** từ các file JSON trong `reports/results/` bằng
`python -m src.evaluation.render_tables`. Không sửa tay các file bảng: lần chạy sau sẽ
ghi đè.

## 6. Những điều cần biết trước khi dùng con số

- Mô hình học từ **giá rao**, không phải giá giao dịch. Giá giao dịch thực tế thường
  thấp hơn, nhưng nhóm không có dữ liệu để đo khoảng cách đó nên không suy đoán.
- Chỉ áp dụng cho TP.HCM, dày nhất ở Tân Bình, Tân Phú và Quận 12.
- Địa danh dùng **hệ quy chiếu cũ** (quận + phường trước sáp nhập 01/07/2025). Tin theo
  phường mới được ánh xạ ngược về hệ cũ; bảng ánh xạ và ngày chốt nằm trong
  `data/external/ward_mapping_new_to_old.json`.
- Kho dữ liệu thô không được đưa lên GitHub: tin rao có thể còn dấu vết người bán, và
  bộ dữ liệu lịch sử có license cấm tái phân phối.
