# Dự báo giá nhà TP.HCM từ tin rao vặt

Đồ án cuối kỳ môn Trí tuệ nhân tạo (CS106.F31.CN2), đề tài 5. Hệ thống học từ các mẩu
tin rao bán nhà, trích đặc trưng định lượng từ mô tả tự do, rồi dự báo tổng giá bán.

**Trạng thái**: đang triển khai. Các con số kết quả trong README này được sinh tự động
từ `reports/tables/`; phần nào còn ghi "đang cập nhật" nghĩa là thí nghiệm chưa chạy xong.

## Bài toán

Nhập một tin rao (địa chỉ, diện tích, số tầng, mặt tiền, mô tả tự do), hệ thống trả về
giá bán dự báo. Bài toán hồi quy, huấn luyện trên log(giá) vì phân phối giá lệch phải
nặng, báo cáo sai số trên thang tỷ đồng.

## Dữ liệu

| Nguồn | Vai trò | Ghi chú |
|---|---|---|
| Chợ Tốt (API JSON công khai) | Nguồn crawl chính | Tin đang rao 2026, có sẵn mô tả và phường |
| mogi.vn | Nguồn crawl thứ hai | Đa dạng nguồn, tránh học lệch theo một sàn |
| `tinixai/vietnam-real-estates` (Hugging Face) | Nguồn lịch sử | Tin rao tới ~06/2025, license CC BY-NC 4.0 |

Quy tắc thu thập: tôn trọng robots.txt từng trang, 1 request mỗi 1–2 giây, không vượt
anti-bot chủ động, không thu thập và không lưu thông tin cá nhân người đăng tin (kể cả
số điện thoại lẫn trong mô tả). Kho dữ liệu thô không được đẩy lên GitHub.

## Kết quả chính

Đang cập nhật (bảng sinh từ `reports/tables/e1-results.md` sau khi chạy `make train`).

## Cấu trúc thư mục

```
src/
  config.py          tham số dùng chung: đường dẫn, mã vùng, ngưỡng QA, seed
  utils/             logging, run manifest (mọi lần chạy ghi lại tham số + số dòng)
  crawl/             script thu thập + QA gate
  preprocess/        làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ, khử trùng lặp
  features/          TF-IDF + SVD, cờ văn bản, ColumnTransformer
  models/            danh mục mô hình, tinh chỉnh tham số
  evaluation/        thí nghiệm E1/E2/E3, metric, SHAP, biểu đồ
  demo/              web app Streamlit
reports/
  scientific-report/ báo cáo khoa học (Markdown -> Word)
  technical-report/  tài liệu mô tả hàm
  slides/            slide thuyết trình
  figures/ tables/   hình và bảng sinh tự động
data/                không đẩy lên git (xem .gitignore)
tests/               kiểm thử, bắt buộc có test chống leakage
```

## Cài đặt và chạy

```bash
python -m venv .venv && source .venv/bin/activate
make setup          # cài thư viện
make crawl          # thu thập dữ liệu (mất khoảng 2-3 giờ)
make qa             # kiểm tra chất lượng kho thô
make prep           # làm sạch + trích đặc trưng
make features       # dựng pipeline đặc trưng
make train          # chạy toàn bộ thí nghiệm
make demo           # mở web app dự báo
```

Yêu cầu Python 3.11. Nếu không muốn crawl lại, xem `docs/dataset-card.md` để tải bộ dữ
liệu đã làm sạch.

## Nguyên tắc chống rò rỉ dữ liệu

Ba luật áp dụng trước mọi lần huấn luyện, có kiểm thử tự động trong `tests/`:

1. Xoá mọi cụm giá khỏi mô tả trước khi vector hoá.
2. Không đưa giá/m² hay bất kỳ đại lượng dẫn xuất từ nhãn vào đặc trưng.
3. Khử trùng lặp trước khi chia tập; mọi phép biến đổi fit trên train, áp sang test.

## Thành viên nhóm

Đang cập nhật.

## Tài liệu tham khảo

Xem phần Tài liệu tham khảo trong báo cáo khoa học (`reports/scientific-report/`).
