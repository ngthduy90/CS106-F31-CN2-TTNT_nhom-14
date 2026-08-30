"""T2.10 và T2.11 — giá trị thiếu và ngoại lai.

**Giá trị thiếu.** Thiếu giá hoặc diện tích thì loại dòng: giá là nhãn (impute nhãn là
bịa dữ liệu) và diện tích là biến giải thích mạnh nhất, đoán nó ra thì phần lớn tín
hiệu còn lại là do mình tự tạo. Các trường còn lại được điền bằng trung vị theo nhóm
(loại nhà × quận) KÈM CỘT CHỈ BÁO: việc người bán không ghi số tầng tự nó đã là thông
tin, xoá dấu vết đó đi là mất một biến.

**Ngoại lai, hai tầng.** Tầng 1 là luật cứng theo miền hợp lệ trong `config`. Tầng 2 là
IQR trên log(giá/m²) tính THEO TỪNG QUẬN: 300 triệu/m² là bình thường ở Quận 1 nhưng vô
lý ở Củ Chi, nên một ngưỡng chung cho cả thành phố sẽ cắt oan quận đắt và bỏ sót quận
rẻ. Quận có ít hơn `MIN_ROWS_PER_DISTRICT` tin thì dùng ngưỡng toàn thành phố, vì IQR
trên vài chục điểm còn nhiễu hơn cái nó định lọc.

Mọi ngưỡng tầng 2 đều TÍNH TỪ DỮ LIỆU, không lấy từ trí nhớ (runbook 03 §7.1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config

MIN_ROWS_PER_DISTRICT = 60
IQR_MULTIPLIER = 1.5

IMPUTE_COLUMNS = ["bedrooms", "bathrooms", "floors", "frontage_m", "alley_width_m"]
CATEGORICAL_FILL = {"legal_status": "không rõ", "direction": "không rõ", "position": "không rõ"}


def drop_missing_labels(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Loại dòng thiếu giá hoặc diện tích. Không impute nhãn, không impute diện tích."""
    before = len(frame)
    kept = frame[frame["total_price_vnd"].notna() & frame["area_m2"].notna()].copy()
    return kept, {
        "thiếu giá": int(frame["total_price_vnd"].isna().sum()),
        "thiếu diện tích": int(frame["area_m2"].isna().sum()),
        "còn lại": len(kept),
        "đã loại": before - len(kept),
    }


def mark_missing(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Cột chỉ báo `<tên>_missing` + điền hạng mục mặc định. KHÔNG tính trung vị.

    Hai việc này thuần theo DÒNG nên không rò rỉ gì và ở lại tiền xử lý. Phần điền số
    theo trung vị (loại nhà × quận) đã chuyển vào pipeline (`GroupMedianImputer`) để fit
    theo từng fold, đúng như quy tắc chống rò rỉ số 3 của báo cáo.
    """
    frame = frame.copy()
    stats = {}

    for column in IMPUTE_COLUMNS:
        if column not in frame:
            continue
        missing = frame[column].isna()
        frame[f"{column}_missing"] = missing.astype(int)
        stats[column] = int(missing.sum())

    for column, default in CATEGORICAL_FILL.items():
        if column in frame:
            frame[column] = frame[column].fillna(default).replace("", default)

    return frame, stats


def impute(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Điền trung vị theo (loại nhà × quận) trên CẢ bảng — chỉ dùng cho EDA.

    Luồng huấn luyện KHÔNG gọi hàm này: trung vị tính trên cả phần test là rò rỉ.
    """
    frame, stats = mark_missing(frame)

    for column in IMPUTE_COLUMNS:
        if column not in frame:
            continue
        by_group = frame.groupby(["property_type", "district"])[column].transform("median")
        filled = frame[column].fillna(by_group)
        # Nhóm nào không có lấy nổi một giá trị thì lùi về trung vị toàn bộ.
        frame[column] = filled.fillna(frame[column].median())

    return frame, stats


def apply_hard_rules(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Tầng 1: miền hợp lệ khai báo sẵn trong config."""
    area_low, area_high = config.VALID_AREA_M2
    price_low, price_high = config.VALID_TOTAL_PRICE_VND

    checks = {
        "diện tích ngoài khoảng": ~frame["area_m2"].between(area_low, area_high),
        "giá ngoài khoảng": ~frame["total_price_vnd"].between(price_low, price_high),
        "tin cho thuê": frame["is_rental"].fillna(False).astype(bool),
    }
    # Một dòng có thể trượt nhiều luật cùng lúc (giá dưới sàn của tin BÁN thường chính
    # là một tin CHO THUÊ), nên cộng các con số này lại sẽ lớn hơn số dòng thật sự bị
    # loại — funnel từng ghi 4.041 trong khi delta chỉ là 3.627. Mỗi dòng vì thế được
    # tính cho ĐÚNG MỘT lý do, theo thứ tự khai báo, và tổng được ghi ra tường minh.
    remove = np.zeros(len(frame), dtype=bool)
    stats = {}
    for label, mask in checks.items():
        mask = mask.to_numpy()
        stats[label] = int((mask & ~remove).sum())
        remove |= mask
    stats["tổng dòng bị loại"] = int(remove.sum())

    return frame[~remove].copy(), stats


# Quận rơi về band toàn thành phố mà giữ lại dưới ngần này thì band đó SAI với quận đó
# (quận rẻ bị cắt mất phần dưới), và phải nói ra thay vì lặng lẽ loại tin.
MIN_DISTRICT_KEEP_SHARE = 0.80


def fit_iqr_bounds(frame: pd.DataFrame) -> dict:
    """Học ngưỡng IQR trên log(giá/m²) theo từng quận. CHỈ nhìn dữ liệu được truyền vào.

    Tách khỏi phần áp dụng để ngưỡng có thể học từ phần TRAIN của từng fold rồi áp cho
    cả hai phía: quy tắc chống rò rỉ số 3 của báo cáo hứa đúng điều đó, còn chạy trên
    toàn bảng trước khi chia tập thì tập test được lọc bằng ngưỡng mà nhãn của chính nó
    góp phần đặt.
    """
    log_unit = np.log(frame["total_price_vnd"] / frame["area_m2"])

    def bounds(series: pd.Series) -> tuple[float, float]:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        spread = q3 - q1
        return q1 - IQR_MULTIPLIER * spread, q3 + IQR_MULTIPLIER * spread

    city = bounds(log_unit)
    per_district: dict[str, tuple[float, float]] = {}
    info: dict[str, dict] = {}

    for district, positions in frame.groupby("district").groups.items():
        group = log_unit.loc[positions]
        if len(group) >= MIN_ROWS_PER_DISTRICT:
            low, high = bounds(group)
            basis = "theo quận"
        else:
            low, high = city
            basis = "toàn thành phố"
        per_district[district] = (float(low), float(high))
        keep_share = float(group.between(low, high).mean()) if len(group) else 1.0
        entry = {
            "cơ sở": basis,
            "n": int(len(group)),
            "tỷ lệ giữ lại": round(keep_share, 3),
            "giá/m² thấp nhất giữ lại": round(float(np.exp(low)) / 1e6, 2),
            "giá/m² cao nhất giữ lại": round(float(np.exp(high)) / 1e6, 2),
        }
        if basis == "toàn thành phố" and keep_share < MIN_DISTRICT_KEEP_SHARE:
            entry["cảnh báo"] = (
                f"band toàn thành phố loại {1 - keep_share:.0%} tin của quận này — "
                "nhiều khả năng đây là quận rẻ chứ không phải quận nhiều tin lỗi"
            )
        info[district] = entry

    return {"city": city, "per_district": per_district, "info": info}


def iqr_mask(frame: pd.DataFrame, fitted: dict) -> np.ndarray:
    """Mặt nạ giữ lại theo ngưỡng ĐÃ HỌC (mảng numpy, so theo vị trí dòng)."""
    log_unit = np.log(frame["total_price_vnd"] / frame["area_m2"]).to_numpy(dtype="float64")
    city_low, city_high = fitted["city"]
    per_district = fitted["per_district"]
    lows = frame["district"].map(lambda d: per_district.get(d, (city_low, city_high))[0])
    highs = frame["district"].map(lambda d: per_district.get(d, (city_low, city_high))[1])
    return (log_unit >= lows.to_numpy(dtype="float64")) & (
        log_unit <= highs.to_numpy(dtype="float64")
    )


def apply_iqr_by_district(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Fit + áp ngưỡng trên CÙNG một bảng.

    Dùng cho EDA và cho bảng ngưỡng trong báo cáo. KHÔNG dùng trong luồng huấn luyện:
    ở đó ngưỡng phải học từ phần train của từng fold (xem `fit_iqr_bounds`).
    """
    fitted = fit_iqr_bounds(frame)
    keep = iqr_mask(frame, fitted)
    kept = frame[keep].copy()
    return kept, {"đã loại": int((~keep).sum()), "ngưỡng theo quận": fitted["info"]}
