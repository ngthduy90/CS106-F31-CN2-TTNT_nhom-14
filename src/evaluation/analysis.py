"""T4.9–T4.13 — phân tích lỗi, SHAP, đường cong học, xuất mô hình vô địch.

    python -m src.evaluation.analysis
"""

from __future__ import annotations

import argparse
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import joblib  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from src import config  # noqa: E402
from src.evaluation.metrics import compute_metrics  # noqa: E402
from src.evaluation.runner import RESULTS_DIR, build_estimator, _coerce  # noqa: E402
from src.evaluation.splits import make_splits  # noqa: E402
from src.features.build import build_feature_frame  # noqa: E402
from src.models.registry import build_registry  # noqa: E402
from src.utils.logging_setup import get_logger  # noqa: E402

MODEL_DIR = config.ROOT / "models"
PRICE_BIN_LABELS = ["dưới 2 tỷ", "2–5 tỷ", "5–10 tỷ", "trên 10 tỷ"]


def pick_champion(source: str = "chotot") -> tuple[str, dict]:
    """Mô hình tốt nhất theo MdAPE trung bình 5 fold, đọc từ kết quả E1 đã lưu.

    Chọn theo MdAPE chứ không theo R²: phân phối giá lệch phải nặng nên R² bị vài căn
    dị biệt kéo đi, còn MdAPE nói đúng cái người mua nhà quan tâm — sai bao nhiêu phần
    trăm ở một căn điển hình.
    """
    payload = json.loads((RESULTS_DIR / f"e1_{source}.json").read_text(encoding="utf-8"))
    candidates = [m for m in payload["models"] if not m["tier"].startswith("0")]
    best = min(candidates, key=lambda m: m["cv_mean"]["MdAPE (%)"])
    return best["name"], best


def error_analysis(frame: pd.DataFrame, estimator, features: pd.DataFrame, test_idx, logger) -> dict:
    """MdAPE theo quận và theo khoảng giá (T4.10)."""
    truth = frame["total_price_vnd"].to_numpy(dtype="float64")[test_idx]
    prediction = estimator.predict(features.iloc[test_idx])
    subset = frame.iloc[test_idx].copy()
    subset["_truth"] = truth
    subset["_pred"] = prediction
    subset["_ape"] = np.abs(prediction - truth) / truth * 100

    by_district = (
        subset.groupby("district")
        .agg(n=("_ape", "size"), mdape=("_ape", "median"))
        .query("n >= 20")
        .sort_values("mdape", ascending=False)
        .reset_index()
    )
    subset["_bin"] = pd.cut(
        subset["_truth"], bins=config.PRICE_BINS_VND, labels=PRICE_BIN_LABELS
    )
    by_bin = (
        subset.groupby("_bin", observed=False)
        .agg(n=("_ape", "size"), mdape=("_ape", "median"))
        .reset_index()
    )

    payload = {
        "by_district": [
            {"district": r["district"], "n": int(r["n"]), "MdAPE (%)": float(r["mdape"])}
            for _, r in by_district.iterrows()
        ],
        "by_price_bin": [
            {"bin": str(r["_bin"]), "n": int(r["n"]), "MdAPE (%)": float(r["mdape"])}
            for _, r in by_bin.iterrows()
            if r["n"] > 0
        ],
        "overall": compute_metrics(truth, prediction),
    }
    (RESULTS_DIR / "error_analysis.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("phân tích lỗi: %d quận, %d khoảng giá",
                len(payload["by_district"]), len(payload["by_price_bin"]))
    return payload


def learning_curve(spec, frame: pd.DataFrame, split: dict, best_params: dict, logger) -> dict:
    """RMSE theo cỡ tập huấn luyện 10%→100% (T4.11).

    Đường còn dốc ở mốc 100% nghĩa là crawl thêm vẫn còn cải thiện; đường đã phẳng
    nghĩa là nút thắt nằm ở đặc trưng chứ không ở số lượng tin. Đó là câu trả lời trực
    tiếp cho phần hướng phát triển.
    """
    features = build_feature_frame(frame)
    target = frame["total_price_vnd"].to_numpy(dtype="float64")
    train_idx = np.array(split["train"])
    test_idx = np.array(split["test"])
    rng = np.random.default_rng(config.SEED)

    points = []
    for fraction in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0):
        size = max(50, int(len(train_idx) * fraction))
        subset = rng.choice(train_idx, size=size, replace=False)
        estimator = build_estimator(spec)
        if best_params:
            estimator.set_params(**{k: _coerce(v) for k, v in best_params.items()})
        estimator.fit(features.iloc[subset], target[subset])
        metrics = compute_metrics(target[test_idx], estimator.predict(features.iloc[test_idx]))
        points.append({"fraction": fraction, "n_train": size, **metrics})
        logger.info("learning curve %3.0f%% (n=%5d) → RMSE %.3f | MdAPE %.1f%%",
                    fraction * 100, size, metrics["RMSE (tỷ)"], metrics["MdAPE (%)"])

    payload = {"model": spec.name, "points": points}
    (RESULTS_DIR / "learning_curve.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def shap_and_importance(estimator, features: pd.DataFrame, frame, test_idx, logger) -> None:
    """SHAP beeswarm + waterfall cho ca sai nặng + permutation importance (T4.9).

    Dùng kèm permutation importance chứ không chỉ impurity importance: impurity
    importance thiên vị biến có nhiều mức (đường phố, phường), nên đọc một mình sẽ dẫn
    tới kết luận sai về biến nào thật sự quan trọng.
    """
    try:
        import shap
    except ImportError:
        logger.warning("chưa cài shap, bỏ qua")
        return

    sample_idx = test_idx[: min(400, len(test_idx))]
    X = features.iloc[sample_idx]
    transformer = estimator.named_steps["features"]
    matrix = transformer.transform(X)
    names = list(transformer.get_feature_names_out())
    model = estimator.named_steps["model"].regressor_

    try:
        explainer = shap.Explainer(model, matrix, feature_names=names)
        values = explainer(matrix, check_additivity=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("không dựng được SHAP: %s", exc)
        return

    config.FIGURES.mkdir(parents=True, exist_ok=True)

    plt.figure()
    shap.plots.beeswarm(values, max_display=18, show=False)
    plt.title("SHAP — ảnh hưởng của từng đặc trưng lên log(giá)")
    plt.tight_layout()
    plt.savefig(config.FIGURES / "ket-qua-03-shap-beeswarm.png", dpi=140, bbox_inches="tight")
    plt.close()

    truth = frame["total_price_vnd"].to_numpy(dtype="float64")[sample_idx]
    prediction = estimator.predict(X)
    worst = np.argsort(-np.abs(prediction - truth) / truth)[:3]

    for rank, position in enumerate(worst, start=1):
        plt.figure()
        shap.plots.waterfall(values[position], max_display=12, show=False)
        plt.title(f"Ca sai nặng #{rank}: thật {truth[position]/1e9:.2f} tỷ, "
                  f"dự báo {prediction[position]/1e9:.2f} tỷ")
        plt.tight_layout()
        plt.savefig(config.FIGURES / f"ket-qua-04-shap-waterfall-{rank}.png", dpi=140,
                    bbox_inches="tight")
        plt.close()

    result = permutation_importance(
        estimator, X, truth, n_repeats=5, random_state=config.SEED,
        scoring="neg_median_absolute_error",
    )
    order = np.argsort(-result.importances_mean)[:20]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([X.columns[i] for i in order][::-1],
            result.importances_mean[order][::-1], color="#0891B2")
    ax.set_title("Permutation importance (trên cột đầu vào)")
    ax.set_xlabel("Mức xấu đi của sai số khi xáo trộn cột")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "ket-qua-05-permutation-importance.png", dpi=140,
                bbox_inches="tight")
    plt.close(fig)
    logger.info("đã sinh hình SHAP và permutation importance")


def export_champion(spec, frame: pd.DataFrame, best_params: dict, metrics: dict, logger) -> None:
    """Xuất pipeline vô địch + model card (T4.13)."""
    features = build_feature_frame(frame)
    target = frame["total_price_vnd"].to_numpy(dtype="float64")
    estimator = build_estimator(spec)
    if best_params:
        estimator.set_params(**{k: _coerce(v) for k, v in best_params.items()})
    estimator.fit(features, target)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": estimator,
            "model_name": spec.name,
            "feature_columns": list(features.columns),
            "seed": config.SEED,
            "trained_rows": len(frame),
        },
        MODEL_DIR / "champion.joblib",
    )

    card = [
        f"# Model card — {spec.name}",
        "",
        "## Dùng để làm gì",
        "",
        "Ước lượng tổng giá rao của nhà ở riêng lẻ và căn hộ tại TP.HCM từ các thuộc",
        "tính cơ bản và mô tả tự do của tin rao. Đây là mô hình học từ GIÁ RAO, không",
        "phải giá giao dịch: dùng nó để tham khảo mặt bằng rao bán, không dùng để định",
        "giá tài sản thế chấp hay ra quyết định tài chính.",
        "",
        "## Dữ liệu huấn luyện",
        "",
        f"- Số dòng: {len(frame):,}".replace(",", "."),
        f"- Nguồn: {', '.join(sorted(frame['source'].unique()))}",
        f"- Khoảng thời gian: {pd.to_datetime(frame['published_at'], errors='coerce', utc=True).min():%m/%Y}"
        f" – {pd.to_datetime(frame['published_at'], errors='coerce', utc=True).max():%m/%Y}",
        f"- Địa bàn: TP.HCM, dày nhất ở {', '.join(config.TARGET_DISTRICTS)}",
        "",
        "## Kết quả (5-fold trên nguồn Chợ Tốt)",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---:|",
    ]
    for key, value in metrics.items():
        card.append(f"| {key} | {value:.3f} |".replace(".", ","))

    card += [
        "",
        "## Hạn chế đã biết",
        "",
        "- Học từ giá rao; giá giao dịch thực tế thường thấp hơn nhưng nhóm không có dữ",
        "  liệu để đo khoảng cách đó.",
        "- Chỉ phủ TP.HCM, và dày nhất ở ba quận mục tiêu. Đưa sang tỉnh khác thì không",
        "  còn giá trị.",
        "- Tin rao có nhiễu: cùng một căn có thể được mô tả bằng hai bộ số khác nhau",
        "  (xem bảng chất lượng trích xuất).",
        "- Không dùng được cho bất động sản đặc thù: đất nền diện tích lớn, nhà xưởng,",
        "  khách sạn — chúng đã bị loại ở bước làm sạch.",
        "",
        f"Seed: {config.SEED}. Tham số tốt nhất: `{best_params or 'mặc định'}`.",
    ]
    (config.DOCS / "model-card.md").write_text("\n".join(card) + "\n", encoding="utf-8")
    logger.info("mô hình → %s", MODEL_DIR / "champion.joblib")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phân tích sau huấn luyện và xuất mô hình")
    parser.add_argument("--source", default="chotot")
    parser.add_argument("--skip-shap", action="store_true")
    args = parser.parse_args()

    logger = get_logger("analysis")
    frame = pd.read_parquet(config.DATA_PROCESSED / "listings.parquet")
    subset = frame[frame["source"] == args.source].reset_index(drop=True)

    name, record = pick_champion(args.source)
    spec = next(s for s in build_registry() if s.name == name)
    logger.info("mô hình vô địch: %s (MdAPE %.2f%%)", name, record["cv_mean"]["MdAPE (%)"])

    split = make_splits(subset, f"e1_{args.source}")
    features = build_feature_frame(subset)
    target = subset["total_price_vnd"].to_numpy(dtype="float64")

    estimator = build_estimator(spec)
    if record["best_params"]:
        estimator.set_params(**{k: _coerce(v) for k, v in record["best_params"].items()})
    estimator.fit(features.iloc[split["train"]], target[split["train"]])

    test_idx = np.array(split["test"])
    error_analysis(subset, estimator, features, test_idx, logger)
    learning_curve(spec, subset, split, record["best_params"], logger)
    if not args.skip_shap:
        shap_and_importance(estimator, features, subset, test_idx, logger)
    export_champion(spec, subset, record["best_params"], record["cv_mean"], logger)


if __name__ == "__main__":
    main()
