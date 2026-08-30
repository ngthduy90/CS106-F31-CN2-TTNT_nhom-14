"""Chạy trọn bộ tiền xử lý và sinh bảng data funnel (T2.12).

    python -m src.preprocess.run_pipeline
    python -m src.preprocess.run_pipeline --hf-limit 20000

Bảng funnel không phải để trang trí: nó là bằng chứng cho mọi con số "còn lại N dòng"
trong báo cáo, và là chỗ duy nhất nói rõ dữ liệu mất đi ở đâu. Mỗi bước ghi số dòng
vào, số dòng ra, và lý do loại.
"""

from __future__ import annotations

import argparse

import pandas as pd

from src import config
from src.preprocess import clean, dedup
from src.preprocess.address import WardResolver, save_ward_mapping
from src.preprocess.leakage import strip_price_mentions
from src.preprocess.load import load_all
from src.utils.logging_setup import get_logger
from src.utils.run_manifest import RunManifest

OUTPUT = config.DATA_PROCESSED / "listings.parquet"
FUNNEL_PATH = config.TABLES / "data-funnel.md"


def _vi(value: int, signed: bool = False) -> str:
    """Số theo cách viết Việt Nam: dấu chấm phân nghìn."""
    text = f"{abs(value):,}".replace(",", ".")
    if signed:
        return f"+{text}" if value >= 0 else f"-{text}"
    return f"-{text}" if value < 0 else text


class Funnel:
    """Ghi lại số dòng qua từng bước, tách theo nguồn."""

    def __init__(self) -> None:
        self.steps: list[dict] = []

    def record(self, name: str, frame: pd.DataFrame, note: str = "") -> None:
        counts = frame["source"].value_counts().to_dict()
        self.steps.append(
            {
                "bước": name,
                "tổng": len(frame),
                "chotot": counts.get("chotot", 0),
                "mogi": counts.get("mogi", 0),
                "hf": counts.get("hf", 0),
                "ghi chú": note,
            }
        )

    def to_markdown(self) -> str:
        lines = [
            "# Data funnel: số dòng còn lại sau từng bước",
            "",
            "| Bước | Tổng | Chợ Tốt | mogi | HF (lịch sử) | Ghi chú |",
            "|---|---:|---:|---:|---:|---|",
        ]
        previous = None
        for step in self.steps:
            delta = "" if previous is None else f" ({_vi(step['tổng'] - previous, signed=True)})"
            # Dấu chấm phân nghìn chỉ áp cho ô số; ghi chú giữ nguyên dấu phẩy của nó.
            numbers = " | ".join(
                _vi(step[key]) for key in ("tổng", "chotot", "mogi", "hf")
            )
            lines.append(f"| {step['bước']} | {_vi(step['tổng'])}{delta} | " +
                         " | ".join(_vi(step[key]) for key in ("chotot", "mogi", "hf")) +
                         f" | {step['ghi chú']} |")
            previous = step["tổng"]
        return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Tiền xử lý ba nguồn thành bảng sẵn cho mô hình")
    parser.add_argument("--hf-limit", type=int, default=40_000)
    args = parser.parse_args()
    logger = get_logger("preprocess")

    with RunManifest("preprocess", params={"hf_limit": args.hf_limit}) as manifest:
        save_ward_mapping()
        funnel = Funnel()

        resolver = WardResolver()
        frame = load_all(hf_limit=args.hf_limit, resolver=resolver)
        funnel.record("Gộp ba nguồn", frame, "sau khử trùng theo id ngay lúc crawl")

        frame, price_stats = clean.drop_missing_labels(frame)
        funnel.record(
            "Loại dòng thiếu giá hoặc diện tích",
            frame,
            f"thiếu giá {price_stats['thiếu giá']}, thiếu diện tích {price_stats['thiếu diện tích']}",
        )

        frame, hard_stats = clean.apply_hard_rules(frame)
        funnel.record(
            "Luật cứng miền hợp lệ + lọc tin cho thuê",
            frame,
            ", ".join(f"{k}: {v}" for k, v in hard_stats.items()),
        )

        frame, dedup_stats = dedup.deduplicate(frame)
        funnel.record(
            "Khử trùng lặp (chặn → cosine ký tự → giá)",
            frame,
            f"{dedup_stats['nhóm trùng']} nhóm, loại {dedup_stats['dòng bị loại']} dòng",
        )

        # IQR và điền trung vị KHÔNG còn chạy ở đây. Cả hai fit trên toàn bảng, tức
        # trên cả những dòng sau này nằm trong tập kiểm: ngưỡng IQR tính trên log(giá/m²)
        # — một đại lượng dẫn xuất từ nhãn — và trung vị điền thiếu tính cả trên test.
        # Quy tắc chống rò rỉ số 3 của báo cáo hứa mọi phép biến đổi chỉ fit trên phần
        # train của từng fold, nên hai bước này đã chuyển vào luồng huấn luyện:
        # `runner.scope_iqr` (ngưỡng học từ phần train) và `GroupMedianImputer` (nằm
        # trong Pipeline). Bảng ngưỡng dưới đây chỉ để BÁO CÁO, không loại dòng nào.
        iqr_stats = {"ngưỡng theo quận": clean.fit_iqr_bounds(frame)["info"]}
        funnel.record(
            "IQR log(giá/m²) theo từng quận",
            frame,
            "đã chuyển vào fit theo fold (xem runner.scope_iqr) — không loại ở bước này",
        )

        frame, missing_stats = clean.mark_missing(frame)
        funnel.record(
            "Cột chỉ báo thiếu + điền hạng mục mặc định",
            frame,
            ", ".join(f"{k}: {v}" for k, v in missing_stats.items())
            + " · điền số theo (loại nhà × quận) nằm trong pipeline, fit theo fold",
        )

        # Văn bản dùng cho mô hình là bản ĐÃ XOÁ GIÁ; bản gốc giữ lại để tra cứu.
        frame["description_clean"] = (
            frame["title"].fillna("") + " " + frame["description"].fillna("")
        ).map(strip_price_mentions)
        # Tách từ ngay ở bước tiền xử lý: làm một lần cho cả dự án thay vì lặp lại
        # trong từng lần fit của từng fold.
        from src.features.text import pretokenize

        # Lọc giá LẦN HAI sau khi tách từ. Bộ tách từ bỏ dấu câu bên trong token, nên
        # "5,85 tỷ" (đã bị lọc từ vòng đầu) có thể tái sinh dưới dạng "585 tỷ" từ những
        # mảnh khác. Lọc trước khi vector hoá là chốt chặn cuối cùng, và test rò rỉ đo
        # đúng cột này.
        frame["description_tokens"] = (
            frame["description_clean"].map(pretokenize).map(strip_price_mentions)
        )
        frame["price_per_m2"] = frame["total_price_vnd"] / frame["area_m2"]

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(OUTPUT, index=False)

        FUNNEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        FUNNEL_PATH.write_text(funnel.to_markdown(), encoding="utf-8")

        # Mẫu cặp trùng để rà tay, theo yêu cầu "kiểm 50 cặp" của runbook 02.
        sample_path = config.DATA_INTERIM / "duplicate_pairs_sample.json"
        pd.DataFrame(dedup_stats["mẫu cặp để rà tay"]).to_json(
            sample_path, orient="records", force_ascii=False, indent=2
        )

        manifest.count("rows_out", len(frame))
        manifest.count("duplicates_removed", dedup_stats["dòng bị loại"])
        # Không còn "outliers_removed" ở bước này: ngưỡng IQR nay học theo từng fold
        # trong luồng huấn luyện, bảng dưới đây chỉ để báo cáo.
        manifest.note(f"ngưỡng IQR theo quận (chỉ để báo cáo): {iqr_stats['ngưỡng theo quận']}")

        # Chỉ số minh bạch của bước quy đổi phường: trước đây được tính rồi bỏ đó.
        ward_quality = resolver.quality_report()
        manifest.note(f"chất lượng ánh xạ phường: {ward_quality}")
        logger.info(
            "ánh xạ phường: %.2f%% không quy được về hệ cũ, %d ánh xạ đa số mỏng",
            ward_quality["tỷ lệ không ánh xạ được"] * 100,
            len(ward_quality["ánh xạ đa số mỏng"]),
        )
        for ward, share in ward_quality["ánh xạ đa số mỏng"].items():
            logger.warning("ánh xạ yếu: %s (đa số chỉ %.2f)", ward, share)

    logger.info("còn %d dòng → %s", len(frame), OUTPUT)
    logger.info("funnel → %s", FUNNEL_PATH)
    print(funnel.to_markdown())


if __name__ == "__main__":
    main()
