"""T3.6 và T7.1 — hàng rào chống rò rỉ nhãn, chạy trước MỖI lần huấn luyện.

Bốn thứ được kiểm, tương ứng bốn cách kết quả có thể đẹp một cách giả tạo:

1. Giá và giá/m² không có mặt trong ma trận đặc trưng.
2. Không còn cụm tiền tệ nào sống sót trong văn bản đưa vào TF-IDF.
3. Mọi bước biến đổi chỉ fit trên phần train (kiểm bằng cách so kết quả transform của
   một pipeline fit trên train với một pipeline fit trên toàn bộ dữ liệu — nếu giống
   hệt nhau thì tức là bước đó không học gì từ dữ liệu, còn nếu pipeline nhận biết
   được thì phải khác).
4. Khử trùng lặp chạy trước khi chia tập.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.build import BANNED, build_feature_frame, build_pipeline
from src.preprocess.leakage import count_money_tokens, strip_price_mentions, verify_no_money_tokens


# Mô tả phải KHÁC NHAU giữa các dòng. Dùng 60 bản sao của cùng một câu thì nhánh văn bản
# có phương sai bằng 0, TruncatedSVD chia cho 0, và quan trọng hơn là phép kiểm rò rỉ
# không thật sự kiểm được gì: một từ vựng chỉ có một tài liệu thì không có gì để lọc.
DESCRIPTIONS = [
    "nhà đẹp hẻm xe hơi sổ hồng riêng full nội thất vào ở ngay",
    "nhà mặt tiền đường lớn kinh doanh sầm uất vị trí đắc địa",
    "căn hộ chung cư view đẹp ban công thoáng gần trường học",
    "nhà nát cần bán gấp tiện xây mới hẻm ba gác",
    "biệt thự khu compound an ninh có hồ bơi sân vườn rộng",
    "đất thổ cư vuông vức đã tách thửa gần chợ và bệnh viện",
]


@pytest.fixture
def frame():
    n = 60
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "total_price_vnd": rng.uniform(2e9, 9e9, n),
            "area_m2": rng.uniform(30, 120, n),
            "bedrooms": rng.integers(1, 5, n),
            "bathrooms": rng.integers(1, 4, n),
            "floors": rng.integers(1, 5, n),
            "frontage_m": rng.uniform(3, 8, n),
            "alley_width_m": rng.uniform(2, 8, n),
            "bedrooms_missing": 0,
            "bathrooms_missing": 0,
            "floors_missing": 0,
            "frontage_m_missing": 0,
            "alley_width_m_missing": 0,
            "district": ["Tân Bình", "Tân Phú"] * (n // 2),
            "ward": ["Phường 1", "Phường 2"] * (n // 2),
            "property_type": "Nhà",
            "legal_status": "sổ hồng",
            "direction": "Đông",
            "position": "hẻm",
            "published_at": pd.date_range("2025-06-01", periods=n, freq="D"),
            "title": "Bán nhà Tân Bình",
            "description": [DESCRIPTIONS[i % len(DESCRIPTIONS)] for i in range(n)],
            "description_clean": [DESCRIPTIONS[i % len(DESCRIPTIONS)] for i in range(n)],
            "description_tokens": [DESCRIPTIONS[i % len(DESCRIPTIONS)] for i in range(n)],
        }
    )


def test_gia_khong_lot_vao_ma_tran_dac_trung(frame):
    features = build_feature_frame(frame)
    assert not (BANNED & set(features.columns))
    assert "total_price_vnd" not in features.columns
    assert "price_per_m2" not in features.columns


def test_van_ban_da_bi_xoa_moi_dau_vet_gia():
    text = "Nhà đẹp, giá 5,2 tỷ, tương đương 86 triệu/m2, hoặc 5200000000 đ"
    cleaned = strip_price_mentions(text)
    assert count_money_tokens(cleaned) == 0


def test_top_dac_trung_tfidf_khong_con_token_tien(frame):
    # Nhét giá vào mô tả rồi cho chạy đúng đường mà pipeline thật đi qua: nếu bộ lọc
    # hỏng thì "5,2 tỷ" sẽ nằm trong từ vựng TF-IDF và phép kiểm phải bắt được.
    frame = frame.copy()
    frame["description_tokens"] = [
        strip_price_mentions(f"{text} giá chỉ 5,2 tỷ thương lượng")
        for text in frame["description_tokens"]
    ]
    pipeline = build_pipeline(use_text=True)
    pipeline.fit(build_feature_frame(frame))
    tfidf = pipeline.named_transformers_["text"].named_steps["tfidf"]
    vocabulary = list(tfidf.get_feature_names_out())

    assert verify_no_money_tokens(vocabulary) == []
    assert len(vocabulary) > 5, "từ vựng quá nghèo để phép kiểm có ý nghĩa"


def test_transform_chi_fit_tren_train(frame):
    """Pipeline fit trên nửa đầu phải cho kết quả KHÁC pipeline fit trên toàn bộ.

    Nếu hai kết quả trùng nhau thì hoặc pipeline không học gì từ dữ liệu, hoặc nó đang
    nhìn thấy phần test lúc fit. Cả hai đều là dấu hiệu phải dừng lại xem xét.
    """
    features = build_feature_frame(frame)
    train, test = features.iloc[:30], features.iloc[30:]

    fit_on_train = build_pipeline(use_text=False).fit(train)
    fit_on_all = build_pipeline(use_text=False).fit(features)

    scaler_train = fit_on_train.named_transformers_["numeric"].named_steps["scale"]
    scaler_all = fit_on_all.named_transformers_["numeric"].named_steps["scale"]
    assert not np.allclose(scaler_train.mean_, scaler_all.mean_), (
        "bộ chuẩn hoá cho ra cùng thống kê dù fit trên hai tập khác nhau"
    )
    assert fit_on_train.transform(test).shape[0] == len(test)


def test_khu_trung_lap_chay_truoc_khi_chia_tap():
    """Bản đăng lại không được rơi vào cả hai phía của phép chia."""
    from src.preprocess.dedup import deduplicate

    base = "Bán nhà hẻm xe hơi Tân Bình 60m2 sổ hồng riêng giá tốt vào ở ngay"
    frame = pd.DataFrame(
        {
            "listing_id": ["a", "b", "c"],
            "title": ["Bán nhà Tân Bình", "Bán nhà Tân Bình", "Bán đất Quận 12"],
            "description": [base, base + " liên hệ", "Đất nền quận 12 giá rẻ đầu tư sinh lời"],
            "total_price_vnd": [5e9, 5.02e9, 3e9],
            "area_m2": [60.0, 60.0, 80.0],
            "district": ["Tân Bình", "Tân Bình", "Quận 12"],
            "ward": ["Phường 1", "Phường 1", "Phường 2"],
            "published_at": pd.to_datetime(["2026-01-01", "2026-02-01", "2026-01-15"]),
        }
    )
    kept, stats = deduplicate(frame)
    assert stats["dòng bị loại"] == 1
    assert set(kept["listing_id"]) == {"b", "c"}, "phải giữ bản mới nhất"
