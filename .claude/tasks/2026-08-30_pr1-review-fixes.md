# Áp bản review PR #1 (NaR-1.naes → PR-1.md)

Nguồn: `~/Downloads/PR-1.md`, giải mã từ `/Volumes/USR_18T_01/UIT_eLearning/NaR-1.naes`
(review PR #1 tại head 7ce21eb). Repo: nhánh `develop`, sạch trước khi bắt đầu.
Chủ nhân yêu cầu: thực hiện luôn các sửa đổi.

## Quy tắc khi làm

- Mỗi mục sửa xong chạy `python -m pytest -q` (78 test) trước khi tick.
- KHÔNG chạy lại `make train` (tốn hàng giờ, đổi số headline đã nộp). Ghi lại
  mục nào làm số trong `reports/` lệch để hỏi chủ nhân sau.
- `make report`/`render_tables` chỉ chạy khi mục đó yêu cầu và không cần train lại.

## Critical (4)

- [x] C1 `src/crawl/pii.py:117-120` — bỏ nhánh 9 chữ số không hint (đang xoá nhầm giá 850.000.000)
- [x] C2 `src/crawl/pii.py:90` — `_DIGIT_RUN` nuốt cụm số liền kề → SĐT lọt; quét cửa sổ con trong run
- [ ] C3 `src/crawl/chotot.py:141` — con trỏ resume theo offset làm quận đã cạn đứng im vĩnh viễn
- [x] C4 `src/preprocess/extract.py:160-162` — "tắm/lâu/mẹ" bỏ dấu bị đếm thành tầng (+ siết `gold.py:63`)

## Warning (12)

- [x] C5 `address.py:142` — `P.13`/`P13` bị loại; "Xa lộ" bị nhận thành phường
- [x] C6 `address.py:107-109` — `normalise_ward` không có đường thất bại → "Phường không rõ"
- [ ] C7 `dedup.py:74` — ô > 400 dòng bị bỏ im lặng, không vào funnel
- [ ] C8 `run_pipeline.py:111` — IQR + impute chạy trước khi chia tập (trái quy tắc 3 của báo cáo)
- [ ] C9 `run_experiments.py:112` — `run_e2` nhận `search_iterations` rồi bỏ không dùng
- [ ] C10 `run_experiments.py:253` — E3 fit champion bằng tham số mặc định, không dùng `best_params`
- [ ] C11 `splits.py:33` — fingerprint băm id đã sort nên bất biến với thứ tự dòng
- [ ] C12 `render_tables.py:459-477` — kết luận learning curve thiếu nhánh "xấu đi"
- [ ] C13 `demo/app.py:83` — demo thiếu lượt `strip_price_mentions` sau `pretokenize`
- [ ] C14 `scripts/check-reproducibility.py:46-49` — không nhìn `returncode`, crash vẫn báo PASS
- [x] C15 `price.py:159-163` — "5.850 tỷ" đọc thành 5.850 nghìn tỷ rồi bị loại âm thầm
- [ ] C16 `fetch_hf_dataset.py:155` — "12" vs "Quận 12" nên `isin` trượt cả một quận mục tiêu

## Suggestion (1)

- [ ] C17 `runner.py:123` — `Pipeline(memory=...)` + `n_jobs` cho search (giảm ~120 lần fit transformer)

## Ghi chú thêm (20 mục trong review)

- [ ] N1 `qa_gate.py:85` — gate PII dùng chính detector của scrubber → luôn 0
- [ ] N2 `http.py:82` — `raise_for_status()` ngoài `try` → 4xx thoát ra sai kiểu; `mogi.py:94` chưa guard
- [ ] N3 `store.py:99-110` — checkpoint ghi không atomic
- [ ] N4 `mogi.py:207,209` — resume bỏ trang 1, `seen_before` đóng băng; `chotot.py:123` đếm sai `max_ads`
- [ ] N5 `fetch_hf_dataset.py:89,126-152` — `unlink` không xoá blob HF; `--max-shards` mặc định 3 cắt timeline
- [ ] N6 `runner.py:117-133` — tuning không nested (cột CV lạc quan một chiều)
- [ ] N7 `registry.py:17` — "ngân sách tinh chỉnh giống nhau" thực ra là min(40, |grid|)
- [ ] N8 `run_experiments.py:84-87` — artifact `--fast` bị tái dùng âm thầm cho champion/ablation
- [ ] N9 `dedup.py:81-86` — TF-IDF fit riêng từng ô làm ngưỡng 0,85 đổi nghĩa theo mật độ
- [ ] N10 `clean.py:102-115,73-77` + `price.py:77` — band toàn thành phố cho quận nhỏ; funnel đếm đúp
- [ ] N11 `extract.py:60,113,127,221-222` — "m" trần thành diện tích; "phòng" thành phòng ngủ; hẻm
- [x] N12 `pii.py:126-131,51` — homoglyph chỉ chạy một lượt; danh sách ký tự vô hình hardcode
- [ ] N13 `scripts/assemble-submission.py:46,51,180,194-203` — mù với docx/pptx/xlsx, không thể fail
- [ ] N14 `demo/app.py:166-173` — ba quy ước thập phân trong một panel
- [ ] N15 `scripts/update-readme-metrics.py:60-66` + `render_tables.py:136-145` — 6,66 là của riêng LightGBM
- [ ] N16 `address.py:169-181,91` — `majority_share`/`unmapped_rate` ghi ra nhưng không ai đọc; Quận 2/9
- [ ] N17 `render_tables.py:88-90` — mô tả split đọc từ config sống thay vì payload của run
- [ ] N18 `features/text.py:117` + `leakage.py:37-41` — `ban_gap` khớp "gặp"; checker yếu hơn stripper
- [ ] N19 `dedup.py:150` — `duplicate_group` đã có nhưng splits chưa group-aware
- [ ] N20 `tests/` — chưa phủ crawl/store/address/extract

## Mục làm số trong reports/ lệch (cần quyết định chạy lại)

- C1/C2 (pii): kho thô đổi → phải crawl lại mới thấy tác dụng; số hiện tại KHÔNG đổi.
- C4 (floors) + siết `gold.py`: recall trích xuất trong `extraction-quality.md` sẽ dịch.
- C15 (giá "X.850 tỷ"): thêm tin được giữ lại → funnel và mọi số E1/E2/E3 dịch nhẹ.
- C5/C6 (địa chỉ): cột phường của nhánh mogi đổi → dataset-card, dedup, `unmapped_rate`.
