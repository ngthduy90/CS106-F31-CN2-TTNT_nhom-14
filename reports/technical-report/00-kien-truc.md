# Technical report — kiến trúc mã nguồn và luồng chạy

Đồ án CS106.F31.CN2 — Nhóm 14 — Đề tài 5: dự báo giá nhà từ dữ liệu rao vặt

Tài liệu này mô tả *mã nguồn*: các module ghép với nhau ra sao, dữ liệu đi qua đâu, và
vì sao ranh giới giữa chúng được đặt ở chỗ đó. Bảng liệt kê từng hàm nằm ở
[`02-bang-mo-ta-ham.md`](02-bang-mo-ta-ham.md), sinh tự động từ docstring.

## 1. Nguyên tắc chung

Ba nguyên tắc chi phối toàn bộ cách chia module:

**Hằng số chỉ có một chỗ.** `src/config.py` giữ mọi đường dẫn, mã vùng, ngưỡng chất
lượng, miền giá trị hợp lệ và seed. Không module nào được viết cứng một đường dẫn hay
một ngưỡng. Nhờ vậy báo cáo trích được đúng con số mà code đã chạy, và đổi một ngưỡng
là đổi cho cả pipeline chứ không phải đi sửa bảy chỗ.

**Dữ liệu thô là bất biến.** `data/raw/` chỉ được ghi thêm, không bao giờ sửa. Mọi biến
đổi xảy ra ở bước sau và ghi ra thư mục khác (`interim/`, `processed/`). Khi một con số
trong báo cáo trông lạ, luôn lần ngược được về đúng dòng JSON gốc.

**Mỗi bước để lại dấu vết.** Mọi script chạm vào dữ liệu đều ghi một run manifest JSON:
tham số, số dòng vào ra, thời gian chạy, mã commit git. Bảng data funnel trong báo cáo
lắp từ chính các file này.

## 2. Bốn tầng

```
src/
├── config.py          hằng số dùng chung
├── utils/             nhật ký + run manifest
├── crawl/             tầng 1 — thu thập
├── preprocess/        tầng 2 — làm sạch và chuẩn hoá
├── features/          tầng 3 — biểu diễn
├── models/            danh mục mô hình
├── evaluation/        tầng 4 — thí nghiệm và báo cáo kết quả
└── demo/              web app
```

### Tầng 1 — thu thập (`src/crawl/`)

`http.py` giữ một `PoliteSession` duy nhất: 1 request mỗi 1,5 giây, lùi luỹ tiến khi
gặp 429/403, User-Agent khai báo rõ. Đặt ràng buộc ở một chỗ thay vì để mỗi crawler tự
lo nghĩa là chỉ cần đọc một file là biết dự án đối xử với máy chủ bên kia thế nào.

`store.py` là kho JSONL bất biến, một file mỗi quận mỗi ngày crawl, khử trùng theo mã
tin do sàn cấp, kèm checkpoint để chạy lại chỉ bổ sung phần còn thiếu.

`pii.py` chạy **tại thời điểm ghi file**, không phải ở bước tiền xử lý. Đặt ở đây vì
một khi số điện thoại đã nằm trong `data/raw/` thì nó nằm đó vĩnh viễn: file thô không
được sửa. Bộ lọc quy mọi biến thể nguỵ trang (chữ số Unicode, emoji, chữ cái thay số,
số viết bằng chữ, ký tự vô hình) về một chuỗi chỉ-để-dò, nhưng giữ bản đồ vị trí ngược
về văn bản gốc để chỉ đúng đoạn số điện thoại bị xoá.

`chotot.py` và `mogi.py` là hai client cụ thể; `fetch_hf_dataset.py` tải bộ lịch sử
theo từng shard rồi xoá shard sau khi lọc, giữ đỉnh dung lượng đĩa ở một shard thay vì
1,67 GB. `qa_gate.py` chấm kho thô theo sáu ngưỡng và buộc ghi lại một quyết định khi
chưa đạt.

### Tầng 2 — làm sạch (`src/preprocess/`)

Thứ tự các bước không tuỳ tiện:

1. `price.py` chạy **trước tiên**. Giá là nhãn; một lỗi ở đây làm sai thẳng mục tiêu
   huấn luyện chứ không chỉ bẩn một đặc trưng.
2. `extract.py` rút bảy trường định lượng từ mô tả tự do bằng regex. `gold.py` đo chất
   lượng bộ luật đó trên một bộ nhãn vàng độc lập.
3. `address.py` quy mọi cách viết địa danh về hệ quy chiếu cũ, và dựng bảng ánh xạ
   phường mới → cũ từ chính dữ liệu crawl.
4. `dedup.py` chạy **trước khi chia tập**, không phải sau: một căn nhà nằm ở cả train
   lẫn test là mô hình được xem trước đáp án.
5. `clean.py` xử lý giá trị thiếu và ngoại lai hai tầng.
6. `leakage.py` xoá dấu vết giá khỏi văn bản, và cung cấp phép kiểm ngược để xác nhận
   không còn token tiền nào sống sót.

`run_pipeline.py` xâu chuỗi cả sáu và ghi bảng data funnel.

### Tầng 3 — biểu diễn (`src/features/`)

`text.py` tách từ tiếng Việt (underthesea, lùi về pyvi rồi khoảng trắng), giữ danh sách
dừng riêng cho tin rao, và định nghĩa 24 cờ nhị phân thủ công.

Việc tách từ nằm ở bước tiền xử lý chứ không nằm trong analyzer của TF-IDF. Đây là
quyết định về hiệu năng có hệ quả lớn: để trong analyzer thì bộ tách từ chạy lại toàn
bộ tập dữ liệu ở mỗi lần fit — tức là mỗi fold nhân mỗi cấu hình tìm kiếm, hàng trăm
lần cho cùng một kết quả.

`build.py` lắp `ColumnTransformer` ba nhánh (số / phân loại / văn bản). **Mọi bước fit
nằm trong pipeline**, không có bước nào chạy trước khi chia tập.

### Tầng 4 — thí nghiệm (`src/evaluation/`)

`splits.py` tính phép chia một lần, phân tầng theo (quận × nhóm giá), lưu ra đĩa kèm mã
băm của bộ id. Mọi mô hình đo trên cùng bộ fold; dữ liệu đổi thì mã băm đổi và phép
chia được tính lại chứ không âm thầm dùng lại phép chia cũ.

`runner.py` bọc mô hình bằng `TransformedTargetRegressor` trên log(giá) và chạy danh
sách kiểm rò rỉ trước mỗi job. `run_experiments.py` chạy E1, E2, E3 và ablation;
`analysis.py` làm phân tích lỗi, SHAP, đường cong học và xuất mô hình vô địch;
`render_tables.py` và `render_figures.py` sinh lại toàn bộ bảng biểu từ kết quả JSON.

## 3. Luồng chạy đầu-cuối

```
make crawl
  run_chotot ─┐
  run_mogi   ─┼─→ data/raw/<nguồn>/<ngày>/<quận>.jsonl   (đã xoá PII lúc ghi)
  fetch_hf   ─┘   data/external/hf_hcmc_listings.parquet

make qa
  qa_gate → reports/tables/qa-gate.md

make prep
  load → giá → lọc tin thuê → luật cứng → khử trùng lặp → IQR theo quận
       → điền thiếu → xoá giá khỏi văn bản → tách từ
  → data/processed/listings.parquet
  → reports/tables/data-funnel.md

make train
  splits (một lần, lưu ra đĩa)
  → E1 từng nguồn · E2 chuyển giao thời gian · E3 theo phường · ablation
  → reports/results/*.json

make report
  render_tables + render_figures + analysis → bảng, hình, models/champion.joblib
  build-docx.sh → báo cáo Word

make demo
  Streamlit đọc models/champion.joblib
```

## 4. Môi trường

- Python 3.11.11
- Thư viện và phiên bản: xem `requirements.txt`
- Seed cố định `SEED = 42` trong `src/config.py`, dùng cho chia tập, tìm kiếm siêu tham
  số và mọi mô hình có yếu tố ngẫu nhiên
- Kiểm thử: `pytest -q`, gồm bộ test chống rò rỉ nhãn chạy trước mỗi lần huấn luyện
