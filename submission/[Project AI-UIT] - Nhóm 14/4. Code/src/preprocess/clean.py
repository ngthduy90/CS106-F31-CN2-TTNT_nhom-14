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


def impute(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Điền trung vị theo (loại nhà × quận), thêm cột `<tên>_missing` cho mỗi trường."""
    frame = frame.copy()
    stats = {}

    for column in IMPUTE_COLUMNS:
        if column not in frame:
            continue
        missing = frame[column].isna()
        frame[f"{column}_missing"] = missing.astype(int)
        stats[column] = int(missing.sum())

        by_group = frame.groupby(["property_type", "district"])[column].transform("median")
        filled = frame[column].fillna(by_group)
        # Nhóm nào không có lấy nổi một giá trị thì lùi về trung vị toàn bộ.
        frame[column] = filled.fillna(frame[column].median())

    for column, default in CATEGORICAL_FILL.items():
        if column in frame:
            frame[column] = frame[column].fillna(default).replace("", default)

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
    remove = np.zeros(len(frame), dtype=bool)
    stats = {}
    for label, mask in checks.items():
        mask = mask.to_numpy()
        stats[label] = int(mask.sum())
        remove |= mask

    return frame[~remove].copy(), stats


def apply_iqr_by_district(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Tầng 2: IQR trên log(giá/m²) theo từng quận, lùi về toàn thành khi quận quá ít tin."""
    frame = frame.copy()
    frame["_log_unit_price"] = np.log(frame["total_price_vnd"] / frame["area_m2"])

    def bounds(series: pd.Series) -> tuple[float, float]:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        spread = q3 - q1
        return q1 - IQR_MULTIPLIER * spread, q3 + IQR_MULTIPLIER * spread

    city_low, city_high = bounds(frame["_log_unit_price"])
    thresholds = {}
    keep = pd.Series(True, index=frame.index)

    for district, group in frame.groupby("district"):
        if len(group) >= MIN_ROWS_PER_DISTRICT:
            low, high = bounds(group["_log_unit_price"])
            basis = "theo quận"
        else:
            low, high = city_low, city_high
            basis = "toàn thành phố"
        thresholds[district] = {
            "cơ sở": basis,
            "n": len(group),
            "giá/m² thấp nhất giữ lại": round(float(np.exp(low)) / 1e6, 2),
            "giá/m² cao nhất giữ lại": round(float(np.exp(high)) / 1e6, 2),
        }
        keep.loc[group.index] = group["_log_unit_price"].between(low, high)

    kept = frame[keep].drop(columns="_log_unit_price")
    return kept, {"đã loại": int((~keep).sum()), "ngưỡng theo quận": thresholds}
