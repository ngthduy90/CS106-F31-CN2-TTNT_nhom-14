# Bảng mô tả hàm

Bảng này sinh tự động từ chữ ký và docstring trong `src/` bằng
`scripts/build-technical-report.py`. Sửa docstring rồi chạy lại script; không
sửa tay file này.

## `src/crawl/chotot.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `parse_ad(raw: dict[str, Any]) -> dict[str, Any]` | Rút gọn tin thô về đúng các trường cần giữ, giá trị để nguyên như API trả. |
| hàm | `fetch_page(session: PoliteSession, area_code: int, offset: int, limit: int = PAGE_SIZE) -> tuple[list[dict[str, Any]], int]` | Một trang tin bán của một quận. Trả về (danh sách tin, tổng số tin của quận). |
| hàm | `iter_district(session: PoliteSession, area_code: int, max_ads: int, start_offset: int = 0, logger = None) -> Iterator[tuple[dict[str, Any], int]]` | Sinh (tin, offset sau khi lấy tin đó) cho tới khi hết trang hoặc đủ max_ads. |
| hàm | `crawl_district(session: PoliteSession, district: str, area_code: int, max_ads: int, resume: bool = True, logger = None) -> dict[str, int]` | Crawl một quận vào kho thô. Trả về thống kê của quận đó. |

## `src/crawl/fetch_hf_dataset.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `write_schema_doc(frame: pd.DataFrame) -> None` | Bảng mô tả trường, dùng thẳng cho chương Dữ liệu của báo cáo. |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/crawl/http.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| lớp | `CrawlError` | Hết số lần thử lại mà vẫn không lấy được trang. |
| lớp | `PoliteSession` | requests.Session có nhịp và có lùi. |
| phương thức | `PoliteSession.__init__(self, delay: float = config.REQUEST_DELAY_SECONDS, timeout: float = config.REQUEST_TIMEOUT_SECONDS, max_retries: int = config.MAX_RETRIES, backoff: float = config.BACKOFF_FACTOR, user_agent: str = config.USER_AGENT, logger = None) -> None` | _(chưa có mô tả)_ |
| phương thức | `PoliteSession.get(self, url: str, **kwargs) -> requests.Response` | GET có nhịp và có lùi. Ném CrawlError khi đã thử hết lượt. |
| phương thức | `PoliteSession.close(self) -> None` | _(chưa có mô tả)_ |

## `src/crawl/mogi.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `listing_id(url: str) -> str \| None` | Mã tin nằm ở đuôi URL dạng `-id22747715`; đây là khoá khử trùng lặp. |
| hàm | `parse_list_page(markup: str) -> list[dict[str, Any]]` | Rút URL tin + vài trường tóm tắt từ một trang danh sách. |
| hàm | `iter_listing_urls(session: PoliteSession, district: str, max_urls: int, start_page: int = 1, logger = None) -> Iterator[tuple[dict[str, Any], int]]` | Sinh (tóm tắt tin, số trang vừa đọc) cho tới khi đủ max_urls hoặc hết trang. |
| hàm | `parse_detail_page(markup: str, url: str) -> dict[str, Any]` | Một tin đầy đủ. Trường nào trang không có thì để trống, không ném lỗi. |
| hàm | `crawl_district(session: PoliteSession, district: str, max_listings: int, resume: bool = True, logger = None) -> dict[str, int]` | Crawl một quận: quét danh sách rồi tải từng trang chi tiết chưa có trong kho. |

## `src/crawl/pii.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `find_phone_spans(text: str) -> list[tuple[int, int]]` | Khoảng [start, end) trong chuỗi GỐC được coi là số điện thoại. |
| hàm | `find_phones(text: str) -> list[str]` | Các đoạn văn bản gốc bị coi là số điện thoại (dùng cho test và QA gate). |
| hàm | `scrub_text(text: str) -> tuple[str, int]` | Thay mọi số điện thoại bằng REDACTION. Trả về (văn bản sạch, số lần xoá). |
| hàm | `scrub_record(record: Any, extra_fields: frozenset[str] \| set[str] = frozenset()) -> tuple[Any, int]` | Bỏ trường cá nhân và xoá số điện thoại trong mọi chuỗi của bản ghi. |
| hàm | `contains_phone(record: Any) -> bool` | True nếu còn bất kỳ chuỗi nào trong bản ghi chứa số điện thoại. |

## `src/crawl/qa_gate.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `collect() -> dict` | Đếm các đại lượng cần cho sáu ngưỡng, quét kho thô đúng một lượt. |
| hàm | `evaluate(stats: dict) -> list[dict]` | _(chưa có mô tả)_ |
| hàm | `render(stats: dict, checks: list[dict]) -> str` | _(chưa có mô tả)_ |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/crawl/run_chotot.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `build_parser() -> argparse.ArgumentParser` | _(chưa có mô tả)_ |
| hàm | `dry_run(logger) -> None` | Hai trang cho quận đầu tiên, chỉ để xác nhận API và bộ parse còn đúng. |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/crawl/run_mogi.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `build_parser() -> argparse.ArgumentParser` | _(chưa có mô tả)_ |
| hàm | `dry_run(logger) -> None` | _(chưa có mô tả)_ |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/crawl/store.py`

_Thu thập dữ liệu và bảo vệ thông tin cá nhân_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `slugify(value: str) -> str` | "Quận 12" → "quan-12". Dùng cho tên file, nên phải không dấu và ổn định. |
| lớp | `RawStore` | Ghi tin thô vào JSONL, tự bỏ tin đã có và tự xoá thông tin cá nhân. |
| phương thức | `RawStore.__init__(self, source: str, partition: str, id_field: str, crawl_day: date \| None = None, root: Path \| None = None) -> None` | _(chưa có mô tả)_ |
| phương thức | `RawStore.append(self, record: dict[str, Any], source_url: str = '') -> bool` | Ghi một tin. Trả về False nếu id đã có trong kho. |
| lớp | `Checkpoint` | Vị trí quét cuối cùng, để chạy lại không phân trang lại từ đầu. |
| phương thức | `Checkpoint.__init__(self, source: str, partition: str, root: Path \| None = None) -> None` | _(chưa có mô tả)_ |
| phương thức | `Checkpoint.get(self, key: str, default: Any = None) -> Any` | _(chưa có mô tả)_ |
| phương thức | `Checkpoint.save(self, **values) -> None` | _(chưa có mô tả)_ |
| phương thức | `Checkpoint.reset(self) -> None` | _(chưa có mô tả)_ |
| hàm | `read_jsonl(path: Path) -> Iterator[dict[str, Any]]` | Đọc từng dòng JSON, bỏ qua dòng hỏng thay vì làm gãy cả lần chạy. |
| hàm | `iter_raw(source: str, root: Path \| None = None) -> Iterator[dict[str, Any]]` | Mọi tin thô của một nguồn, qua mọi ngày crawl. |

## `src/demo/app.py`

_Web app dự báo_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `load_artifacts() -> tuple[dict, dict]` | _(chưa có mô tả)_ |
| hàm | `load_reference() -> pd.DataFrame` | _(chưa có mô tả)_ |
| hàm | `build_input_row(values: dict) -> pd.DataFrame` | Dựng một dòng đúng lược đồ mà `build_feature_frame` mong đợi. |
| hàm | `main() -> None` | _(chưa có mô tả)_ |
| hàm | `render_explanation(pipeline, features: pd.DataFrame) -> None` | Panel giải thích SHAP cho đúng dự báo vừa chạy (T5.2). |

## `src/evaluation/analysis.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `pick_champion(source: str = 'chotot') -> tuple[str, dict]` | Mô hình tốt nhất theo MdAPE trung bình 5 fold, đọc từ kết quả E1 đã lưu. |
| hàm | `error_analysis(frame: pd.DataFrame, estimator, features: pd.DataFrame, test_idx, logger) -> dict` | MdAPE theo quận và theo khoảng giá (T4.10). |
| hàm | `learning_curve(spec, frame: pd.DataFrame, split: dict, best_params: dict, logger) -> dict` | RMSE theo cỡ tập huấn luyện 10%→100% (T4.11). |
| hàm | `shap_and_importance(estimator, features: pd.DataFrame, frame, test_idx, logger) -> None` | SHAP beeswarm + waterfall cho ca sai nặng + permutation importance (T4.9). |
| hàm | `export_champion(spec, frame: pd.DataFrame, best_params: dict, metrics: dict, logger) -> None` | Xuất pipeline vô địch + model card (T4.13). |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/evaluation/metrics.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `median_absolute_percentage_error(y_true, y_pred) -> float` | Trung vị của \|sai số\| / giá thật, tính bằng phần trăm. |
| hàm | `compute_metrics(y_true, y_pred) -> dict[str, float]` | Bộ bốn chỉ số. RMSE/MAE quy ra tỷ đồng để bảng báo cáo đọc được bằng mắt. |

## `src/evaluation/render_figures.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `figure_price_distribution(frame: pd.DataFrame, logger) -> None` | Phân phối giá ở thang gốc và thang log — lý do chọn log làm biến mục tiêu. |
| hàm | `figure_area_distribution(frame: pd.DataFrame, logger) -> None` | _(chưa có mô tả)_ |
| hàm | `figure_count_by_district(frame: pd.DataFrame, logger) -> None` | _(chưa có mô tả)_ |
| hàm | `figure_unit_price_by_quarter(frame: pd.DataFrame, logger) -> None` | Giá/m² trung vị theo quý, tách theo quận — nền cho phần diễn giải trôi giá. |
| hàm | `figure_error_by_slice(logger) -> None` | MdAPE theo quận và theo bin giá — chỗ giám khảo hỏi sâu nhất (T4.10). |
| hàm | `figure_learning_curve(logger) -> None` | RMSE theo cỡ tập huấn luyện — trả lời "crawl thêm có đáng không" (T4.11). |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/evaluation/render_tables.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `render_e1(payload: dict) -> str` | _(chưa có mô tả)_ |
| hàm | `render_e2(payload: dict) -> str` | _(chưa có mô tả)_ |
| hàm | `render_ablation(payload: dict) -> str` | _(chưa có mô tả)_ |
| hàm | `render_e3(payload: dict) -> str` | _(chưa có mô tả)_ |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/evaluation/run_experiments.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `load_frame(sample: int \| None = None) -> pd.DataFrame` | _(chưa có mô tả)_ |
| hàm | `run_e1(frame: pd.DataFrame, specs, logger, search_iterations: int) -> None` | Bảng so sánh chính, chạy RIÊNG trên từng nguồn (runbook 03 §4). |
| hàm | `run_e2(frame: pd.DataFrame, specs, logger, search_iterations: int) -> None` | Trôi giá theo thời gian: huấn luyện trên tin ≤06/2025, kiểm trên tin crawl 2026. |
| hàm | `run_ablation(frame: pd.DataFrame, specs, logger, search_iterations: int) -> None` | Đặc trưng văn bản đáng bao nhiêu MdAPE (runbook 03 §6.1)? |
| hàm | `run_e3(frame: pd.DataFrame, specs, logger) -> None` | Stress test không gian: giữ lần lượt từng phường đông tin làm tập kiểm. |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/evaluation/runner.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `assert_no_leakage(features: pd.DataFrame, text_column: str = 'description_tokens') -> dict` | Danh sách kiểm rò rỉ, chạy trước mỗi job huấn luyện (T7.1). |
| hàm | `build_estimator(spec: ModelSpec, use_text: bool = True, use_flags: bool = True)` | Pipeline hoàn chỉnh cho một mô hình, target đã bọc log/exp. |
| lớp | `ModelResult` | _(chưa có mô tả)_ |
| hàm | `fit_final_model(spec: ModelSpec, frame: pd.DataFrame, best_params: dict, use_text = True, use_flags = True)` | Fit lại mô hình vô địch trên toàn bộ dữ liệu, dùng cho xuất artefact và demo. |
| hàm | `evaluate_model(spec: ModelSpec, frame: pd.DataFrame, split: dict, use_text: bool = True, use_flags: bool = True, search_iterations: int = config.SEARCH_ITERATIONS, logger = None) -> ModelResult` | Chạy 5-fold trên phần train rồi đánh giá lần cuối trên hold-out. |
| hàm | `save_results(name: str, payload: dict) -> None` | _(chưa có mô tả)_ |
| hàm | `results_to_payload(results: list[ModelResult], **extra) -> dict` | _(chưa có mô tả)_ |

## `src/evaluation/splits.py`

_Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `stratum_labels(frame: pd.DataFrame) -> pd.Series` | Nhãn phân tầng = quận × nhóm giá (tứ phân vị). |
| hàm | `make_splits(frame: pd.DataFrame, tag: str, force: bool = False) -> dict` | Hold-out 80/20 + 5-fold trên phần train, lưu ra đĩa và dùng lại. |

## `src/features/build.py`

_Biểu diễn đặc trưng cho mô hình_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| lớp | `AdaptiveSVD` | TruncatedSVD tự hạ số chiều khi từ vựng nhỏ hơn số chiều yêu cầu. |
| phương thức | `AdaptiveSVD.fit_transform(self, X, y = None)` | _(chưa có mô tả)_ |
| phương thức | `AdaptiveSVD.fit(self, X, y = None)` | _(chưa có mô tả)_ |
| hàm | `build_feature_frame(frame: pd.DataFrame) -> pd.DataFrame` | Thêm các cột dẫn xuất rẻ (không cần fit) rồi trả về đúng phần dùng làm X. |
| hàm | `build_pipeline(use_text: bool = True, use_flags: bool = True, svd_components: int = SVD_COMPONENTS)` | ColumnTransformer ba nhánh. Bật/tắt nhánh để chạy ablation mà không đổi code. |

## `src/features/text.py`

_Biểu diễn đặc trưng cho mô hình_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `normalise(text: str \| None) -> str` | Chuẩn hoá nhưng GIỮ dấu câu, vì bộ tách từ cần chúng làm ranh giới. |
| hàm | `tokenize(text: str \| None) -> list[str]` | Chuỗi → danh sách token đã tách từ, bỏ từ dừng và token quá ngắn. |
| hàm | `pretokenize(text: str \| None) -> str` | Token đã tách, nối lại bằng khoảng trắng để TF-IDF chỉ cần `str.split`. |
| hàm | `analyzer(text: str \| None) -> list[str]` | Analyzer cho chuỗi ĐÃ tách từ sẵn bằng `pretokenize`. |
| hàm | `deaccent(text: str) -> str` | _(chưa có mô tả)_ |
| hàm | `extract_flags(text: str \| None) -> dict[str, int]` | 24 cờ nhị phân từ một đoạn mô tả. |

## `src/models/registry.py`

_Danh mục mô hình và baseline_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| lớp | `GroupMedianRegressor` | Baseline "môi giới": trung vị giá/m² của nhóm × diện tích. |
| phương thức | `GroupMedianRegressor.__init__(self, group_columns = ('district', 'ward', 'property_type'), area_column = 'area_m2')` | _(chưa có mô tả)_ |
| phương thức | `GroupMedianRegressor.fit(self, X: pd.DataFrame, y)` | _(chưa có mô tả)_ |
| phương thức | `GroupMedianRegressor.predict(self, X: pd.DataFrame)` | _(chưa có mô tả)_ |
| lớp | `ModelSpec` | _(chưa có mô tả)_ |
| hàm | `build_registry(fast: bool = False) -> list[ModelSpec]` | Danh mục mô hình. `fast=True` rút gọn để chạy thử (smoke test), không để báo cáo. |

## `src/preprocess/address.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `deaccent(text: str) -> str` | _(chưa có mô tả)_ |
| hàm | `normalise_district(text: str \| None) -> str` | Mọi cách viết một quận → một chuỗi chuẩn duy nhất. |
| hàm | `normalise_ward(text: str \| None) -> str` | "13" / "P.13" / "Phường 13" → "Phường 13"; phường có tên giữ nguyên chữ hoa đầu. |
| lớp | `Address` | _(chưa có mô tả)_ |
| phương thức | `Address.resolved(self) -> bool` | _(chưa có mô tả)_ |
| hàm | `parse_address(text: str \| None) -> Address` | Chuỗi địa chỉ tự do → (đường, phường, quận). |
| hàm | `build_ward_mapping(source: str = 'chotot') -> dict` | Dựng bảng ánh xạ từ các cặp (phường mới, phường cũ, quận cũ) trong kho thô. |
| hàm | `save_ward_mapping(source: str = 'chotot') -> dict` | _(chưa có mô tả)_ |
| hàm | `load_ward_mapping() -> dict` | _(chưa có mô tả)_ |
| lớp | `WardResolver` | Quy một địa chỉ về hệ cũ, ưu tiên thông tin sẵn có rồi mới tra bảng. |
| phương thức | `WardResolver.__init__(self, table: dict \| None = None) -> None` | _(chưa có mô tả)_ |
| phương thức | `WardResolver.resolve(self, ward_old: str \| None = None, ward_new: str \| None = None, district: str \| None = None) -> tuple[str, str, str]` | Trả về (phường cũ, quận cũ, nguồn đơn vị) — nguồn để báo cáo minh bạch. |
| phương thức | `WardResolver.unmapped_rate(self) -> float` | _(chưa có mô tả)_ |

## `src/preprocess/clean.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `drop_missing_labels(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]` | Loại dòng thiếu giá hoặc diện tích. Không impute nhãn, không impute diện tích. |
| hàm | `impute(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]` | Điền trung vị theo (loại nhà × quận), thêm cột `<tên>_missing` cho mỗi trường. |
| hàm | `apply_hard_rules(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]` | Tầng 1: miền hợp lệ khai báo sẵn trong config. |
| hàm | `apply_iqr_by_district(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]` | Tầng 2: IQR trên log(giá/m²) theo từng quận, lùi về toàn thành khi quận quá ít tin. |

## `src/preprocess/dedup.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `find_duplicate_groups(frame: pd.DataFrame, text_threshold: float = config.DUPLICATE_TEXT_COSINE, price_tolerance: float = config.DUPLICATE_PRICE_TOLERANCE, max_block_size: int = 400) -> tuple[list[list[int]], list[dict]]` | Các nhóm dòng được coi là cùng một bất động sản, kèm mẫu cặp để rà tay. |
| hàm | `deduplicate(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]` | Bỏ bản đăng lại, giữ bản mới nhất (hoà thì giữ bản mô tả dài nhất). |

## `src/preprocess/extract.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `strip_accents(text: str) -> str` | Bỏ dấu và quy các biến thể ký tự lạ về ASCII trước khi chạy luật. |
| hàm | `extract_dimensions(flat: str) -> tuple[float \| None, float \| None]` | (chiều ngang, chiều dài) tính bằng mét, từ cách viết kích thước. |
| hàm | `extract_area(flat: str) -> float \| None` | Diện tích m², chấm điểm theo ngữ cảnh quanh từng con số. |
| hàm | `extract_bedrooms(flat: str) -> int \| None` | _(chưa có mô tả)_ |
| hàm | `extract_bathrooms(flat: str) -> int \| None` | _(chưa có mô tả)_ |
| hàm | `extract_floors(flat: str) -> int \| None` | Số tầng, cộng dồn theo cách người Việt mô tả nhà phố. |
| hàm | `extract_frontage(flat: str) -> float \| None` | _(chưa có mô tả)_ |
| hàm | `extract_alley_width(flat: str) -> float \| None` | _(chưa có mô tả)_ |
| hàm | `extract_position(flat: str) -> str` | "mặt tiền" / "hẻm" / "không rõ" — biến phân loại, không phải số đo. |
| hàm | `extract_legal(flat: str) -> str` | _(chưa có mô tả)_ |
| hàm | `extract_direction(flat: str) -> str` | Hướng ghép ("Đông Nam") phải thử trước hướng đơn, nếu không "Đông" nuốt mất. |
| lớp | `Extracted` | _(chưa có mô tả)_ |
| phương thức | `Extracted.as_dict(self) -> dict[str, object]` | _(chưa có mô tả)_ |
| hàm | `extract_all(text: str \| None) -> Extracted` | Chạy trọn bộ luật trên một đoạn văn bản (tiêu đề + mô tả nối lại). |

## `src/preprocess/gold.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `build(size: int, seed: int = config.SEED) -> int` | Lấy mẫu ngẫu nhiên các tin có đủ trường có cấu trúc, ghi ra bộ nhãn vàng. |
| hàm | `measure() -> dict[str, dict[str, float]]` | Precision / recall / F1 từng trường trên phần nhãn verbatim. |
| hàm | `error_breakdown() -> dict[str, dict[str, int]]` | Phân loại lỗi còn lại: bỏ sót, lệch đúng 1 đơn vị, lệch khác. |
| hàm | `write_report(results: dict[str, dict[str, float]], n_rows: int) -> None` | _(chưa có mô tả)_ |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/preprocess/leakage.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `strip_price_mentions(text: str \| None) -> str` | Thay mọi cụm tiền bằng một placeholder duy nhất. |
| hàm | `count_money_tokens(text: str \| None) -> int` | _(chưa có mô tả)_ |
| hàm | `verify_no_money_tokens(feature_names) -> list[str]` | Các đặc trưng TF-IDF còn mang hình dạng tiền tệ. Rỗng nghĩa là đã sạch. |

## `src/preprocess/load.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `load_all(hf_limit: int \| None = 40000) -> pd.DataFrame` | Bảng gộp của cả ba nguồn, theo đúng thứ tự cột của SCHEMA. |

## `src/preprocess/price.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| lớp | `ParsedPrice` | Kết quả parse một chuỗi giá. |
| phương thức | `ParsedPrice.ok(self) -> bool` | _(chưa có mô tả)_ |
| hàm | `parse_price(text: str \| None, area_m2: float \| None = None) -> ParsedPrice` | Chuỗi giá → tổng giá VND. Cần `area_m2` khi tin chỉ ghi đơn giá theo m². |
| hàm | `normalise_numeric_price(value: float \| int \| str \| None) -> float \| None` | Giá do API/dataset trả về dạng số. Giá 0/1 là quy ước "không công bố". |
| hàm | `cross_check(total_vnd: float \| None, unit_vnd_per_m2: float \| None, area_m2: float \| None, tolerance: float = config.PRICE_CROSS_CHECK_TOLERANCE) -> tuple[bool, float \| None]` | Tin ghi cả tổng giá lẫn đơn giá thì hai con số phải khớp. |
| hàm | `looks_like_rental(title: str \| None, total_vnd: float \| None = None) -> bool` | Tin cho thuê lọt vào danh mục bán: nhận ra bằng TIÊU ĐỀ hoặc bằng giá quá thấp. |

## `src/preprocess/run_pipeline.py`

_Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| lớp | `Funnel` | Ghi lại số dòng qua từng bước, tách theo nguồn. |
| phương thức | `Funnel.__init__(self) -> None` | _(chưa có mô tả)_ |
| phương thức | `Funnel.record(self, name: str, frame: pd.DataFrame, note: str = '') -> None` | _(chưa có mô tả)_ |
| phương thức | `Funnel.to_markdown(self) -> str` | _(chưa có mô tả)_ |
| hàm | `main() -> None` | _(chưa có mô tả)_ |

## `src/utils/logging_setup.py`

_Ghi nhật ký và run manifest_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| hàm | `get_logger(step: str, level: int = logging.INFO) -> logging.Logger` | Return a logger that writes to the console and to a per-step log file. |

## `src/utils/run_manifest.py`

_Ghi nhật ký và run manifest_

| Loại | Chữ ký | Mô tả |
|---|---|---|
| lớp | `RunManifest` | Collects run metadata, then writes it as JSON. |
| phương thức | `RunManifest.count(self, key: str, value: int) -> None` | _(chưa có mô tả)_ |
| phương thức | `RunManifest.note(self, message: str) -> None` | _(chưa có mô tả)_ |
| phương thức | `RunManifest.path(self) -> Path` | _(chưa có mô tả)_ |
| phương thức | `RunManifest.write(self) -> Path` | _(chưa có mô tả)_ |

---

Tổng cộng 158 hàm, lớp và phương thức công khai trong 32 tệp mã nguồn.
