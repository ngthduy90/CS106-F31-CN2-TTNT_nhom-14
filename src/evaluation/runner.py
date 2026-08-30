"""Bộ chạy thí nghiệm dùng chung cho E1, E2, E3 và ablation.

Mọi mô hình đi qua đúng một đường: ColumnTransformer → TransformedTargetRegressor trên
log(giá). Bọc target bằng `TransformedTargetRegressor` thay vì tự log rồi tự exp là có
chủ đích: cách tự làm rất dễ quên exp ngược ở một nhánh nào đó và báo cáo ra một con số
RMSE đo trên thang log, nhìn thì đẹp mà vô nghĩa.

Trước MỖI lần huấn luyện, `assert_no_leakage` chạy lại danh sách kiểm rò rỉ (T7.1) và
kết quả được lưu cạnh file kết quả. Chạy một lần lúc đầu rồi tin mãi là cách một cột
giá lọt vào X ở lần sửa thứ mười mà không ai biết.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline

from src import config
from src.evaluation.metrics import compute_metrics
from src.features.build import BANNED, GroupMedianImputer, build_feature_frame, build_pipeline
from src.models.registry import ModelSpec
from src.preprocess.clean import fit_iqr_bounds, iqr_mask
from src.preprocess.leakage import count_money_tokens

RESULTS_DIR = config.REPORTS / "results"


def assert_no_leakage(features: pd.DataFrame, text_column: str = "description_tokens") -> dict:
    """Danh sách kiểm rò rỉ, chạy trước mỗi job huấn luyện (T7.1)."""
    banned_present = sorted(BANNED & set(features.columns))
    money_rows = 0
    if text_column in features:
        money_rows = int(sum(count_money_tokens(t) > 0 for t in features[text_column].head(2_000)))

    checklist = {
        "cột nhãn trong X": banned_present,
        "dòng còn cụm tiền trong văn bản (mẫu 2.000)": money_rows,
        "số cột đặc trưng": features.shape[1],
        "số dòng": len(features),
    }
    if banned_present:
        raise AssertionError(f"rò rỉ nhãn: {banned_present}")
    if money_rows:
        raise AssertionError(f"{money_rows} dòng còn cụm tiền trong văn bản đưa vào TF-IDF")
    return checklist


def build_estimator(spec: ModelSpec, use_text: bool = True, use_flags: bool = True):
    """Pipeline hoàn chỉnh cho một mô hình, target đã bọc log/exp."""
    if spec.needs_raw_frame:
        return spec.estimator

    # memory=<cachedir>: không tham số search nào chạm nhánh đặc trưng, nên cả 40 ứng
    # viên của một fold dùng chung đúng một trạng thái transformer. Cache lại thì số lần
    # fit TF-IDF + SVD cho mỗi mô hình rơi từ ~120 về 3 — đây là chi phí lặp lớn nhất.
    return Pipeline(
        [
            # Điền thiếu theo (loại nhà × quận) nằm TRONG pipeline nên fit theo fold.
            ("group_impute", GroupMedianImputer()),
            ("features", build_pipeline(use_text=use_text, use_flags=use_flags)),
            (
                "model",
                TransformedTargetRegressor(
                    regressor=spec.estimator, func=np.log, inverse_func=np.exp
                ),
            ),
        ],
        memory=str(config.CACHE / "pipeline"),
    )


def scope_iqr(frame: pd.DataFrame, train_rows, eval_rows) -> tuple[np.ndarray, np.ndarray]:
    """Ngưỡng IQR học từ PHẦN TRAIN rồi áp cho cả hai phía.

    Chạy IQR trên toàn bảng trước khi chia tập (cách cũ, ở run_pipeline) nghĩa là tập
    kiểm được lọc inlier bằng ngưỡng mà chính nhãn của nó góp phần đặt, nên số công bố
    lạc quan hơn dữ liệu triển khai thật. Học ngưỡng trên train rồi áp cho cả hai phía
    giữ được tính so sánh được của tập kiểm mà không còn nhìn trộm nhãn.
    """
    train_rows = np.asarray(train_rows)
    eval_rows = np.asarray(eval_rows)
    fitted = fit_iqr_bounds(frame.iloc[train_rows])
    return train_rows[iqr_mask(frame.iloc[train_rows], fitted)], eval_rows[
        iqr_mask(frame.iloc[eval_rows], fitted)
    ]


@dataclass
class ModelResult:
    name: str
    tier: str
    cv_mean: dict[str, float] = field(default_factory=dict)
    cv_std: dict[str, float] = field(default_factory=dict)
    holdout: dict[str, float] = field(default_factory=dict)
    best_params: dict[str, Any] = field(default_factory=dict)
    fit_seconds: float = 0.0
    notes: str = ""
    # Ngân sách rút THẬT (min(ngân sách yêu cầu, kích thước lưới)) — "ngân sách giống
    # nhau" chỉ đúng với mô hình có lưới lớn hơn ngân sách.
    search_budget: int = 0


def _prepare(frame: pd.DataFrame, spec: ModelSpec) -> pd.DataFrame:
    """Baseline theo nhóm cần bảng thô; các mô hình khác nhận ma trận đặc trưng."""
    if spec.needs_raw_frame:
        return frame[["district", "ward", "property_type", "area_m2"]].copy()
    return build_feature_frame(frame)


def fit_final_model(spec: ModelSpec, frame: pd.DataFrame, best_params: dict, use_text=True, use_flags=True):
    """Fit lại mô hình vô địch trên toàn bộ dữ liệu, dùng cho xuất artefact và demo."""
    # Artefact cuối cùng: fit trên toàn bộ bảng được giao, ngưỡng IQR học từ chính nó
    # (không có tập kiểm nào ở đây nên không có gì để nhìn trộm).
    rows, _ = scope_iqr(frame, np.arange(len(frame)), np.arange(len(frame)))
    frame = frame.iloc[rows].reset_index(drop=True)
    features = _prepare(frame, spec)
    target = frame["total_price_vnd"].to_numpy(dtype="float64")
    estimator = build_estimator(spec, use_text, use_flags)
    if best_params:
        estimator.set_params(**{k: _coerce(v) for k, v in best_params.items()})
    return estimator.fit(features, target)


def evaluate_model(
    spec: ModelSpec,
    frame: pd.DataFrame,
    split: dict,
    use_text: bool = True,
    use_flags: bool = True,
    search_iterations: int = config.SEARCH_ITERATIONS,
    logger=None,
) -> ModelResult:
    """Chạy 5-fold trên phần train rồi đánh giá lần cuối trên hold-out."""
    started = time.time()
    features = _prepare(frame, spec)
    target = frame["total_price_vnd"].to_numpy(dtype="float64")
    train_idx, test_idx = split["train"], split["test"]

    # Tinh chỉnh MỘT LẦN trên phần train với 3-fold nội bộ, rồi dùng lại cấu hình đó
    # cho cả 5 fold ngoài. Chạy search lại trong từng fold tốn gấp 5 lần mà không đo
    # thêm được gì: cái cần đo là mô hình đã tinh chỉnh ổn định đến đâu giữa các fold,
    # chứ không phải bộ tìm kiếm dao động đến đâu.
    best_params: dict[str, Any] = {}
    if spec.param_distributions and not spec.needs_raw_frame:
        search = RandomizedSearchCV(
            build_estimator(spec, use_text, use_flags),
            spec.param_distributions,
            n_iter=search_iterations,
            cv=3,
            random_state=config.SEED,
            scoring="neg_mean_absolute_error",
            n_jobs=spec.search_n_jobs,
            error_score="raise",
        )
        tuning_rows, _ = scope_iqr(frame, train_idx, train_idx)
        search.fit(features.iloc[tuning_rows], target[tuning_rows])
        best_params = {k: str(v) for k, v in search.best_params_.items()}

    def make_fitted():
        estimator = build_estimator(spec, use_text, use_flags)
        if best_params:
            estimator.set_params(**{k: _coerce(v) for k, v in best_params.items()})
        return estimator

    fold_metrics: list[dict[str, float]] = []
    for fold in split["folds"]:
        fold_train, fold_valid = scope_iqr(frame, fold["train"], fold["valid"])
        fitted = make_fitted().fit(features.iloc[fold_train], target[fold_train])
        prediction = fitted.predict(features.iloc[fold_valid])
        fold_metrics.append(compute_metrics(target[fold_valid], prediction))

    table = pd.DataFrame(fold_metrics)

    # Mô hình cuối: fit lại trên toàn bộ phần train, đo trên hold-out chưa từng chạm.
    final_train, final_test = scope_iqr(frame, train_idx, test_idx)
    final = make_fitted().fit(features.iloc[final_train], target[final_train])
    holdout = compute_metrics(target[final_test], final.predict(features.iloc[final_test]))

    result = ModelResult(
        name=spec.name,
        tier=spec.tier,
        cv_mean=table.mean().to_dict(),
        cv_std=table.std().to_dict(),
        holdout=holdout,
        best_params=best_params,
        fit_seconds=round(time.time() - started, 1),
        notes=spec.notes,
        search_budget=spec.search_budget(search_iterations) if spec.param_distributions else 0,
    )
    if logger:
        logger.info(
            "%-28s MdAPE %.1f%% ±%.1f | RMSE %.2f tỷ | R² %.3f | %.0fs",
            spec.name,
            result.cv_mean["MdAPE (%)"],
            result.cv_std["MdAPE (%)"],
            result.cv_mean["RMSE (tỷ)"],
            result.cv_mean["R²"],
            result.fit_seconds,
        )
    return result


def _coerce(value: str):
    """RandomizedSearch trả tham số đã ép sang chuỗi khi lưu; đưa lại đúng kiểu."""
    for cast in (int, float):
        try:
            return cast(value)
        except (TypeError, ValueError):
            continue
    if value in ("None", "none"):
        return None
    if value in ("True", "False"):
        return value == "True"
    if value.startswith("(") and value.endswith(")"):
        return tuple(int(part) for part in value.strip("()").rstrip(",").split(",") if part.strip())
    return value


def save_results(name: str, payload: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def results_to_payload(results: list[ModelResult], **extra) -> dict:
    return {"models": [asdict(r) for r in results], **extra}
