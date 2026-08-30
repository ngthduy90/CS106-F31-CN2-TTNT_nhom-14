"""T4.3 — chia tập một lần, dùng lại cho MỌI mô hình.

Điều kiện so sánh công bằng của runbook 03 §5: mọi mô hình phải đo trên cùng một bộ
fold. Nếu mỗi mô hình tự chia tập theo seed riêng thì chênh lệch giữa hai dòng trong
bảng kết quả một phần là chênh lệch giữa hai phép chia, không đọc được gì.

Vì thế phép chia được tính một lần rồi GHI RA ĐĨA kèm mã băm của dữ liệu. Lần chạy sau
đọc lại đúng phép chia đó; dữ liệu đổi thì mã băm đổi và phép chia được tính lại, chứ
không âm thầm dùng phép chia cũ trên dữ liệu mới.

Phân tầng theo (quận × nhóm giá) chứ không chỉ theo một trong hai: chia ngẫu nhiên
thuần có thể dồn phần lớn nhà trên 10 tỷ vào một phía, và khi đó chênh lệch giữa các
mô hình bị lẫn với chênh lệch giữa hai phân phối giá.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, train_test_split

from src import config

SPLIT_DIR = config.DATA_PROCESSED / "splits"
MIN_STRATUM = 10  # tầng ít hơn ngần này thì gộp vào "khác"


def _fingerprint(frame: pd.DataFrame) -> str:
    """Mã băm của bộ id, để phép chia lưu trên đĩa luôn khớp với dữ liệu đang dùng.

    CỐ Ý không sort: split lưu trên đĩa là CHỈ SỐ VỊ TRÍ, nên cùng tập id mà khác thứ
    tự dòng (đổi keep-first của dedup, đổi thứ tự concat nguồn, ghi lại parquet) là một
    phân hoạch khác hẳn. Băm trên bộ id đã sort thì hash vẫn khớp và split cũ được tái
    dùng trong khi nó đang trỏ vào những tin khác — đúng kịch bản module này sinh ra để
    chặn.
    """
    joined = "|".join(frame["listing_id"].astype(str))
    return hashlib.sha256(joined.encode()).hexdigest()[:16]


def group_labels(frame: pd.DataFrame) -> np.ndarray:
    """Khoá nhóm để cả một nhóm tin trùng luôn nằm về CÙNG một phía của phép chia.

    `duplicate_group` được dedup tính và lưu từ đầu nhưng chưa ai tiêu thụ. Nối nó vào
    đây đóng hẳn lớp rủi ro twin-listing (mô hình xem trước đáp án qua một bản đăng lại)
    thay vì chỉ giảm nó bằng cách loại bớt bản trùng. Dòng không thuộc nhóm nào đứng
    riêng thành nhóm một phần tử, nên hành vi không đổi khi cột này vắng mặt.
    """
    if "duplicate_group" in frame.columns:
        groups = frame["duplicate_group"].astype("object")
    else:
        groups = pd.Series(pd.NA, index=frame.index, dtype="object")
    fallback = "single:" + frame["listing_id"].astype(str)
    return groups.where(groups.notna(), fallback).astype(str).to_numpy()


def stratum_labels(frame: pd.DataFrame) -> pd.Series:
    """Nhãn phân tầng = quận × nhóm giá (tứ phân vị)."""
    price_bin = pd.qcut(frame["total_price_vnd"], q=4, labels=False, duplicates="drop")
    labels = frame["district"].astype(str) + "|" + price_bin.astype(str)
    counts = labels.value_counts()
    rare = counts[counts < MIN_STRATUM].index
    return labels.where(~labels.isin(rare), "khác")


def make_splits(frame: pd.DataFrame, tag: str, force: bool = False) -> dict:
    """Hold-out 80/20 + 5-fold trên phần train, lưu ra đĩa và dùng lại."""
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    path = SPLIT_DIR / f"{tag}.json"
    fingerprint = _fingerprint(frame)

    if path.exists() and not force:
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("fingerprint") == fingerprint:
            return saved

    strata = stratum_labels(frame)
    groups = group_labels(frame)
    indices = np.arange(len(frame))

    # Hold-out được cắt ở mức NHÓM: cắt ở mức dòng thì hai bản đăng lại của cùng một
    # bất động sản rơi hai phía và mô hình được xem trước đáp án.
    unique_groups, first_position = np.unique(groups, return_index=True)
    group_strata = pd.Series(strata.to_numpy()[first_position])
    lone = group_strata.value_counts()
    group_strata = group_strata.where(~group_strata.isin(lone[lone < 2].index), "khác")

    train_groups, _test_groups = train_test_split(
        unique_groups,
        test_size=config.HOLDOUT_TEST_SIZE,
        random_state=config.SEED,
        stratify=group_strata,
    )
    in_train = np.isin(groups, train_groups)
    train_idx, test_idx = indices[in_train], indices[~in_train]

    train_strata = strata.iloc[train_idx]
    # Tầng còn quá ít sau khi cắt hold-out thì gộp lại, nếu không splitter sẽ vỡ.
    counts = train_strata.value_counts()
    thin = counts[counts < config.CV_FOLDS].index
    train_strata = train_strata.where(~train_strata.isin(thin), "khác")

    folds = []
    splitter = StratifiedGroupKFold(
        n_splits=config.CV_FOLDS, shuffle=True, random_state=config.SEED
    )
    for fold_train, fold_valid in splitter.split(train_idx, train_strata, groups[train_idx]):
        folds.append(
            {
                "train": train_idx[fold_train].tolist(),
                "valid": train_idx[fold_valid].tolist(),
            }
        )

    payload = {
        "tag": tag,
        "fingerprint": fingerprint,
        "n_rows": len(frame),
        "seed": config.SEED,
        "test_size": config.HOLDOUT_TEST_SIZE,
        "n_folds": config.CV_FOLDS,
        "n_groups": int(len(unique_groups)),
        "group_aware": True,
        "train": train_idx.tolist(),
        "test": test_idx.tolist(),
        "folds": folds,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload
