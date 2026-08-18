"""Chạy toàn bộ thí nghiệm: E1, E2, E3, ablation (T4.5–T4.8).

    python -m src.evaluation.run_experiments --fast          # 5 mô hình, chạy thử
    python -m src.evaluation.run_experiments                 # đủ danh mục
    python -m src.evaluation.run_experiments --only e2

Kết quả ghi ra `reports/results/*.json`. Bảng markdown do `render_tables.py` sinh lại
từ các file này, nên bảng trong báo cáo luôn khớp với lần chạy gần nhất và không bao
giờ được gõ tay.
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from src import config
from src.evaluation.metrics import compute_metrics
from src.evaluation.runner import (
    RESULTS_DIR,
    assert_no_leakage,
    build_estimator,
    evaluate_model,
    results_to_payload,
    save_results,
)
from src.evaluation.splits import make_splits
from src.features.build import build_feature_frame
from src.models.registry import build_registry
from src.utils.logging_setup import get_logger
from src.utils.run_manifest import RunManifest

PROCESSED = config.DATA_PROCESSED / "listings.parquet"


def load_frame(sample: int | None = None) -> pd.DataFrame:
    frame = pd.read_parquet(PROCESSED)
    if sample and len(frame) > sample:
        frame = frame.sample(sample, random_state=config.SEED).reset_index(drop=True)
    return frame


def _cap(subset: pd.DataFrame, max_rows: int | None) -> pd.DataFrame:
    """Giới hạn số dòng của một nguồn cho E1, lấy mẫu phân tầng theo quận.

    Nguồn lịch sử có hơn 30.000 dòng, gấp mười ba lần nguồn crawl. Chạy hết trên nguồn
    đó tốn hàng giờ mà không đổi được kết luận: E1 so các mô hình VỚI NHAU trên cùng một
    tập, và mức phân giải của phép so đã bão hoà từ vài nghìn dòng. Quan trọng hơn, hai
    bảng E1 chỉ đọc cạnh nhau được khi cỡ tập không lệch quá xa — chênh mười ba lần thì
    khác biệt giữa hai bảng một phần là khác biệt về lượng dữ liệu.

    Lấy mẫu phân tầng theo quận để không làm méo phân bố địa bàn.
    """
    if not max_rows or len(subset) <= max_rows:
        return subset

    fraction = max_rows / len(subset)
    # Vòng lặp tường minh thay cho `groupby.apply`: pandas 2.2 cảnh báo rằng apply đang
    # thao tác cả trên cột dùng để nhóm và sẽ đổi hành vi ở bản sau. Viết thẳng ra thì
    # vừa hết cảnh báo vừa đọc rõ đang lấy bao nhiêu dòng mỗi quận.
    parts = [
        group.sample(max(1, int(round(len(group) * fraction))), random_state=config.SEED)
        for _, group in subset.groupby("district", sort=True)
    ]
    return pd.concat(parts).reset_index(drop=True)


def run_e1(frame: pd.DataFrame, specs, logger, search_iterations: int,
           max_rows: int | None = None, force: bool = False) -> None:
    """Bảng so sánh chính, chạy RIÊNG trên từng nguồn (runbook 03 §4).

    Không trộn hai nguồn làm thí nghiệm chính: hai nguồn phủ thời kỳ và địa bàn khác
    nhau, nên cờ nguồn sẽ lẫn với địa bàn và với năm. Chạy song song từng nguồn giữ
    cho mỗi con số chỉ nói về đúng một thứ.
    """
    for source, label in (("chotot", "Nguồn B — Chợ Tốt 2026"), ("hf", "Nguồn A — bộ lịch sử")):
        subset = _cap(frame[frame["source"] == source].reset_index(drop=True), max_rows)
        if len(subset) < 500:
            logger.warning("%s chỉ có %d dòng, bỏ qua E1", source, len(subset))
            continue

        target = RESULTS_DIR / f"e1_{source}.json"
        if target.exists() and not force:
            logger.info("đã có %s, bỏ qua (dùng --force để chạy lại)", target.name)
            continue

        logger.info("=== E1 · %s · %d dòng ===", label, len(subset))
        checklist = assert_no_leakage(build_feature_frame(subset))
        split = make_splits(subset, f"e1_{source}")

        results = [
            evaluate_model(spec, subset, split, search_iterations=search_iterations, logger=logger)
            for spec in specs
        ]
        save_results(
            f"e1_{source}",
            results_to_payload(
                results,
                experiment="E1",
                source=source,
                label=label,
                n_rows=len(subset),
                leakage_checklist=checklist,
                search_iterations=search_iterations,
                seed=config.SEED,
            ),
        )


def run_e2(frame: pd.DataFrame, specs, logger, search_iterations: int) -> None:
    """Trôi giá theo thời gian: huấn luyện trên tin ≤06/2025, kiểm trên tin crawl 2026.

    Kèm hai mốc đối chứng để con số chênh lệch đọc được:
    - **Cùng thời kỳ**: train 2026 → test 2026 (đã có ở E1 nguồn B).
    - **Cùng nguồn, khác thời kỳ**: không có ở đây, vì bộ lịch sử đã bị cắt tại mốc.

    Sau khi thay nguồn A bằng bộ Hugging Face, cả hai phía đều là GIÁ RAO, nên chênh
    lệch đo được là trôi giá theo thời gian thuần tuý, không lẫn khoảng cách giữa giá
    rao và giá giao dịch như thiết kế ban đầu.
    """
    train_frame = frame[frame["source"] == "hf"].reset_index(drop=True)
    # Tập kiểm CHỈ lấy Chợ Tốt, không gộp mogi. Lý do: con số của E2 chỉ có nghĩa khi
    # đặt cạnh bảng E1 nguồn Chợ Tốt, mà bảng đó đo trên đúng tập Chợ Tốt. Thêm mogi vào
    # thì chênh lệch giữa hai bảng vừa mang thay đổi nguồn huấn luyện, vừa mang thay đổi
    # thành phần tập kiểm, và không tách được hai thứ đó ra.
    test_frame = frame[frame["source"] == "chotot"].reset_index(drop=True)

    if len(train_frame) < 500 or len(test_frame) < 200:
        logger.warning("không đủ dữ liệu cho E2")
        return

    logger.info("=== E2 · train %d dòng HF (≤%s) → test %d dòng Chợ Tốt 2026 ===",
                len(train_frame), config.HF_CUTOFF, len(test_frame))

    train_features = build_feature_frame(train_frame)
    test_features = build_feature_frame(test_frame)
    assert_no_leakage(train_features)
    assert_no_leakage(test_features)

    train_target = train_frame["total_price_vnd"].to_numpy(dtype="float64")
    test_target = test_frame["total_price_vnd"].to_numpy(dtype="float64")

    rows = []
    for spec in specs:
        if spec.needs_raw_frame:
            estimator = build_estimator(spec)
            estimator.fit(
                train_frame[["district", "ward", "property_type", "area_m2"]], train_target
            )
            prediction = estimator.predict(
                test_frame[["district", "ward", "property_type", "area_m2"]]
            )
        else:
            estimator = build_estimator(spec)
            estimator.fit(train_features, train_target)
            prediction = estimator.predict(test_features)

        metrics = compute_metrics(test_target, prediction)
        rows.append({"name": spec.name, "tier": spec.tier, "transfer": metrics})
        logger.info("%-28s chuyển giao: MdAPE %.1f%% | R² %.3f",
                    spec.name, metrics["MdAPE (%)"], metrics["R²"])

    save_results(
        "e2",
        {
            "experiment": "E2",
            "train_rows": len(train_frame),
            "test_rows": len(test_frame),
            "cutoff": config.HF_CUTOFF,
            "test_source": "chotot",
            "models": rows,
        },
    )


def _champion_from_e1(specs, source: str, logger):
    """Mô hình có MdAPE thấp nhất trong bảng E1 (bỏ qua tầng mốc)."""
    path = RESULTS_DIR / f"e1_{source}.json"
    if not path.exists():
        logger.warning("chưa có %s, ablation lùi về Random Forest", path.name)
        return next((s for s in specs if s.name == "Random Forest"), None)

    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = [m for m in payload["models"] if not m["tier"].startswith("0")]
    best = min(candidates, key=lambda m: m["cv_mean"]["MdAPE (%)"])
    logger.info("ablation dùng mô hình vô địch E1: %s (MdAPE %.2f%%)",
                best["name"], best["cv_mean"]["MdAPE (%)"])
    return next((s for s in specs if s.name == best["name"]), None)


def run_ablation(frame: pd.DataFrame, specs, logger, search_iterations: int) -> None:
    """Đặc trưng văn bản đáng bao nhiêu MdAPE (runbook 03 §6.1)?

    Ba cấu hình trên CÙNG một bộ fold và cùng một mô hình: chỉ bảng / bảng + TF-IDF+SVD
    / bảng + cờ thủ công / cả hai. Khác biệt duy nhất giữa các dòng là nhánh văn bản,
    nên chênh lệch đọc thẳng ra được là đóng góp của mô tả.
    """
    subset = frame[frame["source"] == "chotot"].reset_index(drop=True)
    if len(subset) < 500:
        return

    # Ablation phải chạy trên ĐÚNG mô hình tốt nhất của E1, không phải trên một mô hình
    # chọn sẵn theo thứ tự khai báo. Nếu không, bảng ablation đo đóng góp của văn bản
    # với một mô hình khác mô hình mà báo cáo kết luận, và hai chỗ không khớp nhau.
    champion = _champion_from_e1(specs, "chotot", logger)
    if champion is None:
        return

    split = make_splits(subset, "e1_chotot")
    configurations = [
        ("Chỉ đặc trưng bảng", False, False),
        ("Bảng + cờ văn bản thủ công", False, True),
        ("Bảng + TF-IDF/SVD", True, False),
        ("Bảng + TF-IDF/SVD + cờ", True, True),
    ]

    rows = []
    for label, use_text, use_flags in configurations:
        result = evaluate_model(
            champion, subset, split,
            use_text=use_text, use_flags=use_flags,
            search_iterations=max(8, search_iterations // 3), logger=None,
        )
        rows.append({"configuration": label, "cv_mean": result.cv_mean, "cv_std": result.cv_std})
        logger.info("ablation %-32s MdAPE %.2f%%", label, result.cv_mean["MdAPE (%)"])

    save_results("ablation", {"experiment": "Ablation", "model": champion.name, "rows": rows})


def run_e3(frame: pd.DataFrame, specs, logger) -> None:
    """Stress test không gian: giữ lần lượt từng phường đông tin làm tập kiểm.

    Đây là phép đo khả năng tổng quát sang khu vực CHƯA TỪNG THẤY. Kết quả tệ hơn E1 là
    phát hiện chứ không phải thất bại: nó cho biết mô hình đang dựa vào địa bàn nhiều
    đến mức nào.
    """
    subset = frame[frame["source"] == "chotot"].reset_index(drop=True)
    champion = _champion_from_e1(specs, "chotot", logger)
    if champion is None or len(subset) < 500:
        return

    top_wards = subset["ward"].value_counts().head(5).index.tolist()
    features = build_feature_frame(subset)
    target = subset["total_price_vnd"].to_numpy(dtype="float64")

    rows = []
    for ward in top_wards:
        held_out = subset["ward"] == ward
        if held_out.sum() < 20 or (~held_out).sum() < 200:
            continue
        estimator = build_estimator(champion)
        estimator.fit(features[~held_out], target[~held_out.to_numpy()])
        metrics = compute_metrics(target[held_out.to_numpy()], estimator.predict(features[held_out]))
        rows.append({"ward": ward, "n_test": int(held_out.sum()), "metrics": metrics})
        logger.info("E3 giữ %-24s n=%3d → MdAPE %.1f%%", ward, int(held_out.sum()), metrics["MdAPE (%)"])

    save_results("e3", {"experiment": "E3", "model": champion.name, "rows": rows})


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy thí nghiệm E1/E2/E3 và ablation")
    parser.add_argument("--fast", action="store_true", help="rút gọn danh mục mô hình")
    parser.add_argument("--sample", type=int, default=None, help="lấy mẫu N dòng để chạy nhanh")
    parser.add_argument("--search-iterations", type=int, default=config.SEARCH_ITERATIONS)
    parser.add_argument(
        "--e1-max-rows",
        type=int,
        default=6_000,
        help="giới hạn số dòng mỗi nguồn cho E1 (lấy mẫu phân tầng theo quận); 0 = không giới hạn",
    )
    parser.add_argument("--only", nargs="*", default=None, choices=["e1", "e2", "e3", "ablation"])
    parser.add_argument(
        "--force",
        action="store_true",
        help="chạy lại cả những thí nghiệm đã có file kết quả",
    )
    args = parser.parse_args()

    logger = get_logger("experiments")
    frame = load_frame(sample=args.sample)
    specs = build_registry(fast=args.fast)
    wanted = set(args.only or ["e1", "e2", "e3", "ablation"])

    logger.info("%d dòng, %d mô hình, ngân sách search %d cấu hình",
                len(frame), len(specs), args.search_iterations)

    params = {
        "n_rows": len(frame),
        "models": [s.name for s in specs],
        "search_iterations": args.search_iterations,
        "e1_max_rows": args.e1_max_rows,
        "experiments": sorted(wanted),
    }
    with RunManifest("experiments", params=params) as manifest:
        if "e1" in wanted:
            run_e1(frame, specs, logger, args.search_iterations, args.e1_max_rows or None,
                   force=args.force)
        if "e2" in wanted:
            run_e2(frame, specs, logger, args.search_iterations)
        if "ablation" in wanted:
            run_ablation(frame, specs, logger, args.search_iterations)
        if "e3" in wanted:
            run_e3(frame, specs, logger)
        manifest.count("result_files", len(list(RESULTS_DIR.glob("*.json"))))

    logger.info("kết quả → %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
