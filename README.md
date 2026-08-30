# Dự báo giá nhà TP.HCM từ dữ liệu rao vặt

Đồ án môn **Trí tuệ nhân tạo**, lớp CS106.F31.CN2, đề tài 5. **Nhóm 14**.

Thu thập tin rao bất động sản TP.HCM, trích đặc trưng định lượng từ mô tả tự do, chuẩn
hoá địa chỉ qua đợt sáp nhập hành chính 2025, rồi so sánh 12 mô hình hồi quy trên cùng
một bộ fold. Kèm web app dự báo có giải thích từng ca.

## Kết quả chính

Bảng đầy đủ nằm ở [`reports/tables/`](reports/tables/). Các con số dưới đây sinh tự
động từ `reports/results/*.json` bằng `scripts/update-readme-metrics.py`, không gõ tay.

<!-- metrics:start -->

Trên 2.326 tin Chợ Tốt, 5-fold, cùng bộ fold và cùng ngân sách tinh chỉnh cho mọi mô hình:

| | MdAPE (%) | RMSE (tỷ) | R² |
|---|---:|---:|---:|
| **LightGBM** | 13,88 ± 1,15 | 3,92 | 0,698 |
| **XGBoost** | 14,00 ± 1,07 | 3,79 | 0,716 |
| **CatBoost** | 14,21 ± 1,19 | 3,86 | 0,708 |
| Trung vị giá/m² theo nhóm | 20,53 ± 1,39 | 3,80 | 0,706 |
| Dummy (trung vị) | 34,65 ± 2,09 | 7,25 | -0,053 |

Nhóm dẫn đầu hơn baseline kiểu môi giới 6,32–6,66 điểm phần trăm MdAPE. Các mô
hình in đậm cách nhau chưa tới một độ lệch chuẩn giữa các fold, nên bảng không
chọn ra một mô hình thắng.

<!-- metrics:end -->

| Thí nghiệm | Nội dung | Bảng |
|---|---|---|
| E1 | So sánh 12 mô hình, hold-out 80/20 + 5-fold, chạy riêng từng nguồn | [`e1-results-chotot.md`](reports/tables/e1-results-chotot.md) |
| E2 | Huấn luyện trên tin ≤06/2025, kiểm trên tin crawl 08/2026, đo trôi giá theo thời gian | [`e2-results.md`](reports/tables/e2-results.md) |
| E3 | Giữ lần lượt từng phường làm tập kiểm, đo khả năng tổng quát sang khu vực chưa thấy | [`e3-results.md`](reports/tables/e3-results.md) |
| Ablation | Mô tả rao vặt đáng bao nhiêu phần trăm sai số | [`ablation.md`](reports/tables/ablation.md) |

Chất lượng trích xuất từ văn bản: [`extraction-quality.md`](reports/tables/extraction-quality.md).
Dòng dữ liệu qua từng bước làm sạch: [`data-funnel.md`](reports/tables/data-funnel.md).

## Dữ liệu

| Vai trò | Nguồn | Ghi chú |
|---|---|---|
| Nguồn B (hiện tại) | Chợ Tốt (API công khai) + mogi.vn (HTML) | Crawl 08/2026, ưu tiên Tân Bình, Tân Phú, Quận 12 |
| Nguồn A (lịch sử) | Hugging Face `tinixai/vietnam-real-estates` | Lát cắt TP.HCM, license CC BY-NC 4.0 |

Kho dữ liệu thô **không** nằm trong repo: tin rao có thể còn dấu vết người bán, và bộ
lịch sử có license cấm tái phân phối. Chạy `make crawl` để dựng lại từ đầu.

## Bốn quyết định đáng nói

**Xoá số điện thoại ngay lúc ghi file.** Người rao né bộ lọc của sàn bằng chữ số
Unicode, emoji, chữ cái thay số, số viết bằng chữ, ký tự vô hình. Bộ lọc quy mọi biến
thể về một chuỗi chỉ-để-dò nhưng giữ bản đồ vị trí ngược về văn bản gốc, nên chỉ đúng
đoạn số điện thoại bị xoá. 14 kiểu nguỵ trang được phủ bằng test; 0 số sót lại trong
kho thô.

**Bảng ánh xạ phường mới → cũ dựng từ chính dữ liệu.** API Chợ Tốt trả cả tên phường
theo hệ cũ lẫn hệ mới cho cùng một tin, nên mỗi tin là một cặp ánh xạ do sàn khẳng
định. Không phải tải bảng ngoài, có ngày chốt rõ ràng, và lộ ra đúng cạm bẫy đã lường
trước: 14 trong 16 phường mới gộp từ nhiều phường cũ, tỷ lệ đa số thấp nhất chỉ 0,45.

**Chống rò rỉ nhãn được kiểm chứ không được tin.** Danh sách kiểm chạy trước mỗi lần
huấn luyện, và nó bắt được hai lỗi thật: bước tách từ *tái tạo* cụm tiền sau khi đã lọc
(bỏ dấu phẩy thập phân biến "5,85" thành "585" nằm cạnh chữ "tỷ" còn sót), và một đơn
giá theo m² lọt qua dưới dạng "110 triệum2", thứ nhân với diện tích ra thẳng nhãn.

**Baseline "môi giới" là mốc đáng quan tâm nhất.** Trung vị giá/m² theo (quận, phường,
loại nhà) nhân diện tích chính là cách một người môi giới định giá trong đầu. Nếu
LightGBM chỉ nhỉnh hơn cách tính đó vài phần trăm thì giá trị nằm ở dữ liệu địa bàn chứ
không nằm ở mô hình. Đó là kết luận đáng viết hơn bất kỳ con số R² nào.

## Cấu trúc thư mục

```
src/
├── config.py            # đường dẫn, mã vùng, ngưỡng, seed (không module nào hardcode)
├── crawl/               # client Chợ Tốt, mogi, tải bộ HF, xoá PII, kho JSONL, QA gate
├── preprocess/          # giá, trích đặc trưng, địa chỉ, khử trùng lặp, làm sạch, chống rò rỉ
├── features/            # tách từ tiếng Việt, cờ văn bản, ColumnTransformer ba nhánh
├── models/              # danh mục 12 mô hình + baseline theo nhóm
├── evaluation/          # chia tập, chạy thí nghiệm, chỉ số, bảng, hình, phân tích
└── demo/                # web app Streamlit
reports/                 # báo cáo, slide, bảng, hình, kết quả JSON
docs/                    # dataset card, model card, hướng dẫn, ảnh chụp robots.txt
tests/                   # gồm test chống rò rỉ nhãn, chạy trước mỗi lần huấn luyện
```

## Chạy thử

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make all        # hoặc từng bước: make crawl / prep / train / report / demo
```

**Thu thập thêm dữ liệu.** Mặc định các script crawl lấy ít, đủ để kiểm pipeline chạy
đúng. Muốn đạt mốc 8.000 tin của đề thì tăng hạn mức rồi chạy lại; nhờ checkpoint và
khử trùng theo mã tin, lần chạy sau chỉ bổ sung phần còn thiếu:

```bash
python -m src.crawl.run_chotot --max-per-district 3000
python -m src.crawl.run_mogi   --max-per-district 800
make qa                                    # chấm lại theo 6 ngưỡng
```

Chi tiết từng lệnh, bộ số mẫu cho demo và chỗ đọc kết quả:
[`docs/huong-dan-su-dung.md`](docs/huong-dan-su-dung.md).

## Ranh giới đã tự đặt

- Tôn trọng `robots.txt` từng trang; bản chụp có ngày giờ trong
  [`docs/robots-snapshots/`](docs/robots-snapshots/).
- Không vượt anti-bot chủ động. Các trang dựng Cloudflare bị loại khỏi danh sách nguồn
  ngay từ đầu chứ không tìm cách đi vòng.
- 1 request mỗi 1,5 giây, lùi luỹ tiến khi máy chủ báo bận, User-Agent khai báo rõ.
- Không thu thập và không lưu thông tin người bán.

## Thành viên

Danh sách chính thức nằm ở `config/thanh-vien.yaml`; trang bìa báo cáo, file Excel bài
nộp và bảng phân công ở slide đều sinh từ đó.

Việc còn lại và ai nhận gói nào: [`docs/phan-cong.md`](docs/phan-cong.md).
