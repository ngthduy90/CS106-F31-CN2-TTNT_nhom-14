"""T3.2 và T3.4 — dựng pipeline đặc trưng ba nhánh.

Mọi bước biến đổi nằm TRONG pipeline sklearn, không có bước nào chạy trước khi chia
tập. Đây không phải chuyện gọn code mà là chuyện đúng sai: trung vị dùng để điền, từ
vựng TF-IDF, trục SVD đều là thống kê học từ dữ liệu; tính chúng trên toàn bộ dữ liệu
rồi mới chia tập nghĩa là tập test đã rò rỉ vào tập train.

Ba nhánh (runbook 03 §3):

- **Số**: điền trung vị + chuẩn hoá thang. Chuẩn hoá là bắt buộc cho Ridge/Lasso/KNN/
  MLP; cây và boosting không cần nhưng cũng không bị hại.
- **Phân loại**: one-hot, gộp mức hiếm. Tên đường có hàng nghìn mức nên bị chặn ở
  `MAX_STREET_LEVELS` mức phổ biến nhất, phần còn lại dồn vào "khác" — không chặn thì
  one-hot phình ra vài nghìn cột gần như toàn số 0.
- **Văn bản**: TF-IDF 1–2 gram trên mô tả ĐÃ XOÁ GIÁ, rồi TruncatedSVD. Cây học rất
  kém trên vài nghìn cột thưa, nên SVD không phải để cho đẹp mà để nhánh boosting dùng
  được văn bản.

`build_feature_frame` chỉ tạo cột, không fit gì; `build_pipeline` mới là thứ được fit
trong từng fold.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config
from src.features.text import TEXT_FLAGS, analyzer, extract_flags, pretokenize

class AdaptiveSVD(TruncatedSVD):
    """TruncatedSVD tự hạ số chiều khi từ vựng nhỏ hơn số chiều yêu cầu.

    TruncatedSVD gốc ném lỗi nếu n_components > số cột đầu vào. Chuyện đó xảy ra thật:
    trên một fold nhỏ hoặc trên tập mẫu dùng để chạy thử, TF-IDF với min_df=5 có thể
    chỉ còn vài chục từ. Vỡ pipeline vì lý do đó là vô nghĩa, nên lớp này hạ số chiều
    xuống mức khả thi và ghi lại con số đã dùng.
    """

    def fit_transform(self, X, y=None):
        self.n_components = max(1, min(self.n_components, X.shape[1] - 1))
        return super().fit_transform(X, y)

    def fit(self, X, y=None):
        self.n_components = max(1, min(self.n_components, X.shape[1] - 1))
        return super().fit(X, y)


NUMERIC_FEATURES = [
    "area_m2",
    "bedrooms",
    "bathrooms",
    "floors",
    "frontage_m",
    "alley_width_m",
    "bedrooms_missing",
    "bathrooms_missing",
    "floors_missing",
    "frontage_m_missing",
    "alley_width_m_missing",
    "description_length",
    "listing_year",
    "listing_month",
    "listing_quarter_index",
]

CATEGORICAL_FEATURES = ["district", "ward", "property_type", "legal_status", "direction", "position"]
TEXT_FEATURE = "description_tokens"
FLAG_FEATURES = list(TEXT_FLAGS)

MAX_STREET_LEVELS = 100
TFIDF_MAX_FEATURES = 8_000
SVD_COMPONENTS = 120

# Cột không bao giờ được vào X. Kiểm ở đây một lần thay vì tin vào việc nhớ.
BANNED = set(config.LEAKAGE_BLOCKLIST) | {"total_price_vnd", "price_per_m2", "description", "title"}

BASE_QUARTER = pd.Timestamp("2025-01-01")


def build_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Thêm các cột dẫn xuất rẻ (không cần fit) rồi trả về đúng phần dùng làm X."""
    out = frame.copy()

    published = pd.to_datetime(out["published_at"], errors="coerce", utc=True)
    out["listing_year"] = published.dt.year
    out["listing_month"] = published.dt.month
    # Chỉ số quý liên tục để mô hình bắt được xu hướng thời gian theo một chiều duy nhất.
    out["listing_quarter_index"] = (
        (published.dt.year - BASE_QUARTER.year) * 4 + published.dt.quarter - 1
    )
    out["description_length"] = out["description"].fillna("").str.len()

    flags = pd.DataFrame(
        [extract_flags(text) for text in out["description_clean"].fillna("")], index=out.index
    )
    if TEXT_FEATURE not in out:
        out[TEXT_FEATURE] = out["description_clean"].fillna("").map(pretokenize)
    out = pd.concat([out, flags], axis=1)

    for column in NUMERIC_FEATURES:
        if column not in out:
            out[column] = np.nan

    columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + FLAG_FEATURES + [TEXT_FEATURE]
    leaked = BANNED & set(columns)
    if leaked:
        raise ValueError(f"cột rò rỉ nhãn lọt vào X: {sorted(leaked)}")

    out[TEXT_FEATURE] = out[TEXT_FEATURE].fillna("")
    return out[columns]


def build_pipeline(use_text: bool = True, use_flags: bool = True, svd_components: int = SVD_COMPONENTS):
    """ColumnTransformer ba nhánh. Bật/tắt nhánh để chạy ablation mà không đổi code."""
    numeric = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="constant", fill_value="không rõ")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10, sparse_output=False),
            ),
        ]
    )

    branches = [
        ("numeric", numeric, NUMERIC_FEATURES),
        ("categorical", categorical, CATEGORICAL_FEATURES),
    ]
    if use_flags:
        branches.append(("flags", "passthrough", FLAG_FEATURES))
    if use_text:
        text = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer=analyzer,
                        ngram_range=(1, 1),
                        min_df=5,
                        max_features=TFIDF_MAX_FEATURES,
                        sublinear_tf=True,
                    ),
                ),
                ("svd", AdaptiveSVD(n_components=svd_components, random_state=config.SEED)),
            ]
        )
        branches.append(("text", text, TEXT_FEATURE))

    return ColumnTransformer(branches, remainder="drop", verbose_feature_names_out=False)


def main() -> None:
    """Kiểm nhanh tầng đặc trưng: dựng bảng, fit pipeline, in kích thước ma trận.

    `make features` gọi hàm này. Nó không sinh ra artefact nào — mục đích là phát hiện
    sớm lỗi cấu hình cột (thiếu cột, cột lẫn kiểu, cột nhãn lọt vào X) ngay sau bước
    tiền xử lý, thay vì để lỗi đó nổ ra giữa một lần chạy huấn luyện dài.
    """
    import pandas as pd

    from src.utils.logging_setup import get_logger

    logger = get_logger("features")
    frame = pd.read_parquet(config.DATA_PROCESSED / "listings.parquet")
    features = build_feature_frame(frame)
    logger.info("bảng đặc trưng: %d dòng × %d cột", *features.shape)

    pipeline = build_pipeline()
    matrix = pipeline.fit_transform(features)
    logger.info("ma trận sau ColumnTransformer: %d dòng × %d cột", *matrix.shape)
    logger.info(
        "nhánh: %s",
        ", ".join(name for name, _, _ in pipeline.transformers),
    )


if __name__ == "__main__":
    main()
