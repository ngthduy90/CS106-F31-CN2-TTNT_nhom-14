# Phân công việc còn lại

Nhóm 14, đồ án CS106.F31.CN2 đề tài 5.

Phần lập trình đã xong và chạy được đầu-cuối. Bảy gói việc dưới đây là phần **bắt buộc
phải có người kiểm bằng tay**, không phải việc bày ra cho đủ đầu người. Lý do nằm trong
chính runbook của nhóm: runbook 04 §3 ghi *"người phụ trách rà lại từng dòng, không nộp
bản sinh tự động chưa kiểm"*, và runbook 02 yêu cầu duyệt nhãn vàng cùng rà tay các cặp
trùng lặp. Hiện chưa ai làm những việc đó.

Ai nhận gói nào thì ghi tên vào bảng dưới và tick vào ô khi xong.

**Cập nhật 31/08/2026.** Đợt vá theo bản review PR #1 đã sửa 37 chỗ trong mã nguồn, trong
đó có những chỗ làm đổi cách tính số. Vì vậy file này có thêm **gói G** (chạy lại pipeline)
và ba gói cũ đổi điều kiện: gói C không rà được trên mẫu cũ nữa, gói B phải chờ dữ liệu
mới, gói D đổi số lượng mục phải đọc. Chi tiết ghi ngay trong từng gói. Gói A đến F vẫn
độc lập với nhau, chỉ có G chặn trước B, C và E.

## Bảng phân công

| Gói | Việc | Người nhận | Trạng thái |
|---|---|---|---|
| A | Thu thập bù dữ liệu | | chưa nhận |
| B | Rà bộ nhãn vàng 200 tin | | chưa nhận |
| C | Rà 50 cặp trùng lặp | | chưa nhận |
| D | Rà bảng mô tả hàm | | chưa nhận |
| E | Kiểm trích dẫn và chuẩn bị hỏi đáp | | chưa nhận |
| F | Geocoding (tuỳ chọn) | | chưa nhận |
| G | Chạy lại pipeline sau đợt vá review | | chưa nhận |
| | Toàn bộ phần lập trình | Nguyễn Thanh Duy | xong |
| | Vá 37 phát hiện của review PR #1 | Nguyễn Thanh Duy | xong |

Ước lượng công sức:

| Gói | Cần biết code | Thời gian |
|---|---|---|
| A | Không, chỉ chạy lệnh | 30 phút thao tác cộng 3 tới 4 giờ máy chạy |
| B | Không | 3 tới 4 giờ |
| C | Không | 1 giờ |
| D | Có, mức đọc hiểu | 3 tới 4 giờ |
| E | Không | 2 giờ |
| F | Có, mức viết được | 1 ngày |
| G | Không, chỉ chạy lệnh và đọc kết quả | 30 phút thao tác cộng 4 tới 6 giờ máy chạy |

---

## Gói A. Thu thập bù dữ liệu

**Vì sao cần.** Cổng kiểm chất lượng đang đạt 3 trên 6 ngưỡng. Ba ngưỡng chưa đạt đều
do một nguyên nhân duy nhất là số tin thô mới có 2.760 so với mốc 8.000 mà runbook 01 §6
tự đặt ra. Đây là lỗ hổng lớn nhất còn lại của đồ án.

| Kiểm tra | Hiện tại | Ngưỡng |
|---|---:|---:|
| Tổng số tin thô | 2.760 | 8.000 |
| Tin ở 3 quận mục tiêu | 2.760 | 3.000 |
| Tỷ lệ tin có mô tả từ 200 ký tự | 87,8% | 90,0% |

**Cách làm.**

```bash
source .venv/bin/activate
python -m src.crawl.run_chotot --max-per-district 3000
python -m src.crawl.run_mogi   --max-per-district 800
python scripts/fetch-robots.py      # chụp lại robots.txt đúng ngày crawl
make qa
make prep
```

Checkpoint và khử trùng theo mã tin đã có sẵn, nên chạy lại chỉ bổ sung phần còn thiếu,
không tải trùng và không hỏng dữ liệu đã có.

**Đọc kỹ nếu ai đó đã từng thử gói này và thấy không thêm được bao nhiêu tin.** Đến ngày
30/08 crawler có hai lỗi khiến câu trên không đúng: con trỏ resume của Chợ Tốt lưu vị trí
cuối cùng đã quét, nên quận nào đã quét cạn thì lần chạy sau bắt đầu đúng chỗ hết tin và
ghi **0 tin mới vĩnh viễn**; còn mogi resume theo số trang nên bỏ qua trang 1, đúng nơi
tin mới xuất hiện. Cả hai đã sửa: giờ luôn quét từ đầu và dừng khi gặp một chuỗi tin đã
có trong kho, `--no-resume` thì xoá hẳn checkpoint. Nếu trước đây có ai chạy và thấy kết
quả nghèo nàn thì chạy lại, lần này sẽ khác. Đừng sửa `REQUEST_DELAY_SECONDS` trong
`src/config.py` xuống thấp hơn: một request mỗi 1,5 giây là ranh giới nhóm tự đặt và đã
ghi vào phần đạo đức của báo cáo.

Nếu chạy hết mà vẫn chưa đủ 8.000 thì có hai hướng, chọn một rồi ghi lại lựa chọn vào
`reports/tables/qa-gate.md`:

1. Mở nguồn dự phòng alonhadat.com.vn hoặc homedy.com (runbook 01 §2 đã khảo sát sẵn).
2. Nới phạm vi ra toàn bộ quận của TP.HCM thay vì chỉ ba quận mục tiêu.

**Xong khi.**

- [ ] `make qa` báo 6 trên 6 ngưỡng đạt
- [ ] Commit lại `reports/tables/qa-gate.md` và `reports/tables/data-funnel.md`
- [ ] Commit lại ảnh chụp robots.txt trong `docs/robots-snapshots/` với ngày mới
- [ ] Chạy lại `make train` và `make report` để số liệu trong báo cáo khớp dữ liệu mới
- [ ] Báo cho người nhận gói G: nếu A xong sau G thì G phải chạy lại lần nữa

Lưu ý: chạy lại `make train` sẽ đổi mọi con số trong báo cáo và slide. Đó là chuyện bình
thường vì tất cả sinh tự động, nhưng phải chạy `make report` sau đó để bảng biểu cập nhật
theo, và báo cho người phụ trách gói E biết để kiểm lại phần hỏi đáp.

## Gói B. Rà bộ nhãn vàng 200 tin

**Vì sao cần.** Runbook 02 §1 bước 1 yêu cầu lấy mẫu khoảng 200 tin, gán nhãn tay, và
nêu rõ có thể nhờ công cụ gán trước nhưng **người phải duyệt lại**. Hiện nhãn đang lấy tự
động từ các trường có cấu trúc mà người bán điền vào form của sàn, và chưa ai duyệt.

Bảng F1 trong báo cáo dựa hoàn toàn vào bộ nhãn này. Nếu nhãn sai thì con số F1 sai theo,
và đó là bảng thầy dễ hỏi sâu.

**Làm sau gói G.** Bộ trích xuất vừa được sửa ở đúng bốn trường mà gói này rà: số tầng
(trước đây "phòng tắm", "sử dụng lâu dài", "2 mẹ con" đều bị đếm thành tầng), diện tích
("cách chợ 500m" từng thành 500 m²), số phòng ngủ ("1 phòng khách, 2 phòng ngủ" từng ra 1)
và bề rộng hẻm. Rà trước khi chạy lại pipeline là rà trên bảng số cũ, và F1 đo được sẽ
khác con số cuối cùng của báo cáo.

**Cách làm.** Mở `data/interim/gold_200.jsonl`, mỗi dòng một tin gồm văn bản và bốn nhãn.
Với từng tin, đọc phần mô tả rồi đối chiếu bốn trường: diện tích, số phòng ngủ, số nhà
tắm, số tầng.

Ba chỗ cần chú ý nhất:

1. **Diện tích.** Một tin thường có nhiều con số mét vuông khác nhau: kích thước lô, diện
   tích xây dựng, diện tích công nhận trên sổ. Nhãn đúng là diện tích công nhận.
2. **Số tầng.** Cách đếm tiếng Việt cộng dồn thành phần, ví dụ "1 trệt 2 lầu" là 3 tầng.
   Nhưng nhiều tin viết "1 trệt 1 lầu" mà điền số 1 vào form. Đây chính là chỗ F1 đang
   thấp nhất, nên ghi lại cụ thể tin nào mâu thuẫn.
3. **Tin không nêu giá trị trong mô tả.** Nếu mô tả không hề nhắc tới trường đó thì đánh
   dấu riêng, đừng tính là nhãn sai.

**Xong khi.**

- [ ] Có file ghi lại kết quả rà: mã tin, trường nào sai, giá trị đúng là gì
- [ ] Nếu tìm ra nhãn sai thì sửa vào `gold_200.jsonl` rồi chạy
      `python -m src.preprocess.gold --measure` để tính lại F1
- [ ] Commit lại `reports/tables/extraction-quality.md`
- [ ] Viết 3 tới 5 câu nhận xét để chèn vào chương 2 phần chất lượng trích xuất

## Gói C. Rà 50 cặp trùng lặp

**Vì sao cần.** Runbook 02 §3.1 nói đúng chữ *"chỉnh ngưỡng bằng kiểm tay khoảng 50
cặp"*. Ngưỡng cosine 0,85 hiện đang dùng là con số lấy từ runbook, chưa ai xác nhận trên
dữ liệu thật. Khử trùng lặp chạy trước khi chia tập, nên ngưỡng sai sẽ ảnh hưởng thẳng
tới mọi con số trong bảng kết quả.

**Làm sau gói G, và đây là gói đổi nhiều nhất.** File mẫu hiện có sinh từ lần chạy
19/08, còn thuật toán đã đổi hai chỗ làm điểm cosine mang nghĩa khác: TF-IDF trước đây fit
riêng trong từng ô chặn nên cùng một ngưỡng 0,85 nghiêm khắc khác nhau tuỳ ô đông hay
thưa, nay bỏ IDF nên ngưỡng có một nghĩa duy nhất; và ô trên 400 dòng trước đây bị bỏ qua
nguyên khối, nay được chia nhỏ theo bậc giá nên có thêm cặp được đem ra so. Rà 50 cặp
trong file cũ rồi kết luận về ngưỡng là kết luận cho một thuật toán không còn chạy nữa.
Chạy `make prep` trước, file mẫu sẽ được sinh lại.

**Cách làm.** Mở `data/interim/duplicate_pairs_sample.json`, có sẵn 50 cặp kèm điểm
cosine, giá và tiêu đề hai bên. Với từng cặp, quyết định đây là hai bản đăng của cùng một
bất động sản hay hai bất động sản khác nhau.

Cạm bẫy lớn nhất là **chung cư**: nhiều căn trong cùng toà có diện tích, số phòng và mô
tả gần như giống hệt nhau nhưng là hai căn khác nhau. Nếu thấy nhiều cặp chung cư bị gộp
oan thì ngưỡng đang quá lỏng.

**Xong khi.**

- [ ] Có bảng đánh dấu 50 cặp: trùng thật hay nhận nhầm
- [ ] Kết luận rõ ràng: giữ ngưỡng 0,85, hay nới lên, hay siết xuống, kèm lý do
- [ ] Nếu đổi ngưỡng thì sửa `DUPLICATE_TEXT_COSINE` trong `src/config.py`, chạy lại
      `make prep` và `make train`
- [ ] Nếu thấy nhiều cặp lọt vì ô chặn quá lớn thì cân nhắc `DUPLICATE_MAX_BLOCK_SIZE`
      (mới thêm vào `src/config.py`, mặc định 400)
- [ ] Viết vài câu cho chương 2 phần khử trùng lặp, nêu số cặp đã kiểm và kết luận

## Gói D. Rà bảng mô tả hàm

**Vì sao cần.** Đề bài yêu cầu một technical report riêng mô tả hoạt động của từng hàm.
Bảng sinh tự động từ docstring, và runbook 04 §3 ghi rõ không nộp bản sinh tự động chưa
kiểm.

**Con số 164 mục trong bản trước đã cũ.** Đợt vá review thêm nhiều hàm mới (`fit_iqr_bounds`,
`iqr_mask`, `mark_missing`, `GroupMedianImputer`, `scope_iqr`, `group_labels`,
`_phone_windows`, `_best_params_from_e1`, `quality_report`, `_read_searchable_text`) và
viết lại vài chục docstring cũ để giải thích vì sao luật hiện tại như vậy. Chạy lại script
sinh bảng trước, đếm lại số mục, rồi mới ước lượng thời gian và chia việc.

**Cách làm.** Mở `reports/technical-report/02-bang-mo-ta-ham.md`, đọc song song với mã
nguồn trong `src/`. Với mỗi mục, kiểm hai điều: mô tả có đúng việc hàm đang làm không, và
người ngoài đọc có hiểu không.

Sửa ở **docstring trong mã nguồn**, không sửa vào file markdown. File markdown sinh lại
mỗi lần build nên sửa tay sẽ mất.

```bash
# sau khi sửa docstring
python scripts/build-technical-report.py
bash scripts/build-technical-report.sh     # dựng lại bản Word
```

**Xong khi.**

- [ ] Đã đọc hết số mục mà script sinh ra (đếm lại sau khi chạy, không dùng con số cũ)
- [ ] Docstring nào mô tả sai đã sửa trong `src/`
- [ ] Chạy lại script, commit cả docstring lẫn file markdown sinh ra
- [ ] Ghi lại số mục đã phải sửa, để nêu trong phần bàn giao

## Gói E. Kiểm trích dẫn và chuẩn bị hỏi đáp

**Vì sao cần.** Checklist trước khi nộp của runbook 04 §6 có hai mục chưa ai làm: kiểm
lại mọi trích dẫn, và chuẩn bị phần hỏi đáp cho buổi 10.

**Phần 1: trích dẫn.** Mở lại từng URL trong `reports/scientific-report/06-tai-lieu-tham-khao.md`,
xác nhận còn truy cập được và nội dung đúng như mô tả. Hai nghị quyết về sắp xếp đơn vị
hành chính đã được đối chiếu với bản đăng trên cổng thông tin Chính phủ, nhưng phần còn
lại thì chưa ai mở lại lần hai.

**Phần 2: hỏi đáp.** Runbook 04 §4 dự đoán bốn câu thầy sẽ hỏi. Soạn sẵn câu trả lời
ngắn gọn cho từng câu:

1. Vì sao chọn mô hình này mà không phải mô hình khác?
2. Vì sao RMSE và MAE cho kết luận khác nhau?
3. Nhóm xử lý rò rỉ nhãn thế nào?
4. Nguồn dữ liệu có hợp lệ không, có vi phạm gì không?

Ba chỗ trong báo cáo thầy dễ hỏi sâu nhất, nên chuẩn bị kỹ:

- Vì sao nhóm mô hình tuyến tính có R² âm trong khi MdAPE vẫn tốt
- Vì sao khử trùng lặp bắt buộc chạy trước khi chia tập
- Bảng ablation nói lên điều gì, và vì sao mức cải thiện nhỏ hơn độ lệch chuẩn giữa các
  fold lại chỉ được coi là xu hướng chứ chưa phải kết luận chắc

Bốn câu nữa sinh ra từ đợt vá review, đều là chỗ dễ bị hỏi vì báo cáo nói khác bản trước:

- **Vì sao lọc ngoại lai IQR và điền thiếu chuyển vào fit theo từng fold?** Vì trước đó
  chúng chạy trên toàn bảng trước khi chia tập, mà ngưỡng IQR tính trên log(giá/m²) là đại
  lượng dẫn xuất từ nhãn, còn trung vị điền thiếu tính cả trên phần test. Quy tắc chống rò
  rỉ số 3 của chương 3 hứa mọi phép biến đổi chỉ fit trên phần train, giờ mới đúng thật.
- **Vì sao kết luận learning curve là "xấu đi" chứ không phải "đã phẳng"?** Vì bước cuối
  đi từ 13,43% lên 14,20%, tức tăng 0,77 điểm. Bản cũ chỉ có hai nhánh nên xếp ca này vào
  nhánh "phẳng" và in kết luận trái ngược với chính bảng số ngay bên trên. Câu trả lời
  đúng là một bước đi lên cỡ này chưa tách được khỏi dao động giữa các lần lấy mẫu vì mỗi
  tỷ lệ chỉ chạy một lần.
- **Vì sao không gọi tên một mô hình thắng?** Vì LightGBM, XGBoost và CatBoost cách nhau
  chưa tới một độ lệch chuẩn giữa các fold. Báo cáo ghi khoảng 6,32 tới 6,66 điểm cho cả
  nhóm dẫn đầu thay vì 6,66 của riêng LightGBM như bản trước.
- **Vì sao Quận 2 và Quận 9 không còn là hạng mục riêng?** Vì cả hai đã nhập vào TP Thủ
  Đức từ 2021 (Nghị quyết 1111/NQ-UBTVQH14). Để riêng là tách một địa bàn thành ba cột
  one-hot, và E2 chịu ảnh hưởng nặng nhất vì hai thời kỳ ghi tên khác nhau.

**Xong khi.**

- [ ] Mọi URL trong chương 6 đã mở lại, ghi ngày truy cập
- [ ] Có file ghi câu hỏi và câu trả lời đã soạn
- [ ] Đã chạy thử phần hỏi đáp với cả nhóm ít nhất một lần

## Gói F. Geocoding (tuỳ chọn)

**Vì sao cần.** Bước này đã bị cắt theo thứ tự ưu tiên định sẵn của kế hoạch, nhưng
chương 5 của báo cáo xếp đây là phần bổ sung có giá trị rõ nhất còn lại. Khoảng cách tới
trung tâm và cụm toạ độ là thông tin mà biến phân loại theo phường không thay thế được.

Dành cho ai muốn có một phần kỹ thuật riêng để trình bày.

**Cách làm.** Thiết kế đã có sẵn trong runbook 02 §2 phương án 2b:

- Nominatim của OpenStreetMap, tối đa 1 request mỗi giây, bắt buộc cache trên đĩa
- Chỉ geocode các bộ ba (đường, phường, quận) **duy nhất**, không geocode từng dòng
- Địa chỉ không giải được thì lùi về toạ độ tâm phường
- Ghi attribution ODbL vào phần tài liệu tham khảo

Sau khi có toạ độ, thêm hai cột dẫn xuất: khoảng cách tới chợ Bến Thành, và mã cụm toạ
độ. Rồi thêm một dòng vào bảng ablation để đo xem toạ độ đóng góp bao nhiêu.

**Xong khi.**

- [ ] Có file cache toạ độ, ít nhất 80% bộ ba địa chỉ giải được
- [ ] Hai cột dẫn xuất đã vào `data/processed/listings.parquet`
- [ ] Bảng ablation có thêm dòng có toạ độ so với không toạ độ
- [ ] Thêm trích dẫn Nominatim và ODbL vào chương 6

## Gói G. Chạy lại pipeline sau đợt vá review

**Vì sao cần.** Đợt vá theo review PR #1 sửa 37 chỗ, trong đó bảy nhóm thay đổi làm số
liệu dịch: lọc ngoại lai và điền thiếu chuyển sang fit theo fold, khử trùng lặp không còn
bỏ qua ô lớn và ngưỡng cosine đổi nghĩa, phép chia tập giữ nguyên nhóm tin trùng về một
phía, E2 và E3 chạy trên mô hình đã tinh chỉnh thay vì tham số mặc định, bộ trích xuất hết
bịa số tầng và số phòng, giá viết dạng "5.850 tỷ" không còn bị loại âm thầm, Quận 2 và
Quận 9 gộp về Thủ Đức. **Mã nguồn đã đúng, nhưng mọi con số trong `reports/` vẫn là của
lần chạy cũ.** Nộp bài ở trạng thái này là nộp một báo cáo mô tả một pipeline khác với
pipeline trong mã nguồn.

**Cách làm.** Chạy đúng thứ tự, mỗi bước xong mới sang bước sau:

```bash
make prep      # dựng lại listings.parquet, funnel, mẫu 50 cặp trùng
make train     # E1, E2, E3, ablation, SHAP, learning curve
make report    # sinh lại bảng, hình, báo cáo Word, slide
```

`make train` là bước lâu nhất, tính bằng giờ. Chạy khi máy rảnh, đừng chạy ngay trước hạn.

Sau khi chạy xong, đọc lại ba chỗ vì chúng có thể đổi kết luận chứ không chỉ đổi con số:

1. `reports/tables/learning-curve.md`: câu kết luận cuối bảng có ba nhánh (còn giảm,
   đứng yên, xấu đi). Xem nhánh nào được in ra với dữ liệu mới.
2. `reports/tables/e1-results-chotot.md`: nhóm dẫn đầu gồm những mô hình nào, và khoảng
   cách so với baseline môi giới là bao nhiêu. README lấy đúng con số này.
3. `reports/tables/data-funnel.md`: số dòng còn lại sau mỗi bước sẽ khác vì bước IQR
   không còn loại dòng ở tiền xử lý nữa.

**Xong khi.**

- [ ] Ba lệnh trên chạy hết, không lỗi
- [ ] `python scripts/check-reproducibility.py` báo tái lập được
- [ ] Đã đọc lại ba chỗ nêu trên và xác nhận câu chữ trong báo cáo còn khớp với số mới
- [ ] Chụp lại ảnh demo trong `submission/Demo/`: ảnh `demo-02` và `demo-03` hiện tại chụp
      đúng lỗi hiển thị ba quy ước thập phân trong một panel mà đợt vá vừa sửa
- [ ] Chạy `python scripts/assemble-submission.py --check-only --strict-numbers` và rà 14
      con số nó nêu (13 ở README, 1 ở model card): mỗi con số hoặc là làm tròn khác, hoặc
      là mâu thuẫn thật cần sửa
- [ ] Commit toàn bộ `reports/` và `README.md` sinh lại, kèm một câu ghi rõ đây là lần
      chạy sau đợt vá review

---

## Việc chung, không ai được bỏ

**Đọc kỹ chương mình đứng tên và trả lời được câu hỏi về nó.** Buổi 10 thầy hỏi ngẫu
nhiên. Người không giải thích nổi phần mình phụ trách là chỗ mất điểm rõ nhất, và cũng là
chỗ không ai gánh thay được.

Trước buổi bảo vệ, cả nhóm nên ngồi lại một buổi để mỗi người trình bày phần của mình
trong 3 phút và trả lời câu hỏi của những người còn lại.

## Thứ tự ưu tiên

Gói A nên làm trước, vì nếu số liệu đổi thì mọi gói phía sau phải kiểm lại theo. Gói G
chặn trước B, C và E: cả ba đều rà trên dữ liệu hoặc bảng số mà G sinh ra. Gói D và F độc
lập hoàn toàn, làm lúc nào cũng được.

```
A (thu thập)  →  G (chạy lại pipeline)  →  B, C  →  E (hỏi đáp)
D (mô tả hàm)     độc lập
F (geocoding)     độc lập, tuỳ chọn
```

Nếu không ai kịp làm gói A trước hạn thì vẫn phải chạy gói G, vì G không phụ thuộc dữ liệu
mới: nó chỉ đưa các con số về khớp với mã nguồn hiện tại. Ngược lại, làm A sau G thì G
phải chạy lại một lần nữa.

## Trước khi nộp

Người nộp đại diện chạy lệnh cuối cùng này và kiểm đầu ra:

```bash
make report        # sinh lại toàn bộ bảng, hình, báo cáo Word, slide
make submission    # ráp thư mục nộp, quét chéo môn, quét dữ liệu lọt
```

Cả hai phép quét phải sạch, và thư mục nộp phải đủ 7 hạng mục theo runbook 04 §1.

Ba điều kiện bổ sung sau đợt vá review:

- **Gói G phải xong.** Nộp khi `reports/` còn là số của lần chạy cũ nghĩa là nộp một báo
  cáo mô tả pipeline khác với mã nguồn đi kèm.
- **Phép quét nộp bài giờ đọc được cả file Word, PowerPoint và Excel.** Trước đây nó chỉ
  đọc file text nên mù với đúng bốn file thầy sẽ mở. Nếu nó báo có mã môn khác hoặc dữ
  liệu lọt trong các file đó, đấy là phát hiện thật, không phải báo động giả.
- **Chạy thêm `--strict-numbers` một lần.** Nó liệt kê những con số chỉ xuất hiện ở một
  tài liệu mà không thấy trong báo cáo. Không bắt buộc phải sạch, nhưng phải có người đọc
  qua danh sách đó và biết vì sao từng con số lệch.
