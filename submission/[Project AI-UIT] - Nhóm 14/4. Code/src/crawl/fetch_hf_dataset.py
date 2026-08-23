"""T1.6 — bộ Hugging Face `tinixai/vietnam-real-estates` làm NGUỒN A (lịch sử).

Bộ dữ liệu thành viên 2022–2025 không lấy được, nên nguồn lịch sử chuyển sang bộ này
(execution-plan §2). Cả hai nguồn giờ đều là GIÁ RAO, nên thí nghiệm E2 đo đúng một
thứ: trôi giá theo thời gian giữa tin ≤06/2025 và tin crawl 2026, không còn lẫn chênh
lệch giá rao / giá giao dịch.

Bộ gốc 3,5 triệu dòng chia 10 shard parquet, tổng ~1,67 GB. Script tải TỪNG shard, lọc
ngay về TP.HCM rồi XOÁ shard đó trước khi tải shard kế: đỉnh dung lượng đĩa giữ ở mức
một shard (~170 MB) thay vì 1,67 GB.

ĐÍNH CHÍNH so với runbook 01 §2 (kiểm lại ngày 2026-08-19): bộ dữ liệu KHÔNG dừng ở
06/2025 mà trải từ 2025-06 tới 2026-03, và các shard xếp theo thời gian tăng dần. Hệ
quả có lợi: ngoài lát cắt ≤06/2025 dùng làm tập huấn luyện của E2, dự án có thêm một
chuỗi thời gian 10 tháng liên tục để vẽ đường trôi giá và để tách "trôi theo thời
gian" khỏi "khác nguồn". Vì thế script ghi HAI file:

- `hf_hcmc_listings.parquet` — lát cắt ≤ HF_CUTOFF, tập huấn luyện của E2 (3 shard đầu
  là đủ, chúng phủ trọn tháng 06/2025).
- `hf_hcmc_timeline.parquet` — toàn bộ 2025-06 → 2026-03 (cần cả 10 shard), dùng cho
  hình trôi giá và cho dòng đối chứng "trôi nội bộ cùng nguồn" của E2.

License CC BY-NC 4.0: dùng được cho đồ án (phi thương mại), phải ghi nguồn trong phần
tài liệu tham khảo, và KHÔNG tái phân phối dữ liệu thô trong repo (đã chặn bằng
.gitignore).

    python -m src.crawl.fetch_hf_dataset
    python -m src.crawl.fetch_hf_dataset --max-shards 10
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

from src import config
from src.utils.logging_setup import get_logger
from src.utils.run_manifest import RunManifest

REPO_ID = config.HF_DATASET
N_SHARDS = 10
SHARD_TEMPLATE = "shard_{index:04d}.parquet"
OUTPUT = config.DATA_EXTERNAL / "hf_hcmc_listings.parquet"
OUTPUT_TIMELINE = config.DATA_EXTERNAL / "hf_hcmc_timeline.parquet"
SCHEMA_DOC = config.DOCS / "hf-dataset-schema.md"

COLUMNS = [
    "name",
    "description",
    "property_type_name",
    "province_name",
    "district_name",
    "ward_name",
    "street_name",
    "project_name",
    "price",
    "area",
    "floor_count",
    "frontage_width",
    "house_depth",
    "road_width",
    "bedroom_count",
    "bathroom_count",
    "house_direction",
    "balcony_direction",
    "published_at",
]


def _load_shard(index: int, logger) -> pd.DataFrame:
    """Tải một shard, lọc về TP.HCM, rồi xoá file gốc khỏi đĩa."""
    filename = SHARD_TEMPLATE.format(index=index)
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        repo_type="dataset",
        cache_dir=str(config.CACHE / "huggingface"),
    )
    table = pq.read_table(path, columns=COLUMNS)
    frame = table.to_pandas()
    total = len(frame)
    frame = frame[frame["province_name"] == config.HF_PROVINCE].copy()
    logger.info("%s: %d dòng → %d dòng TP.HCM", filename, total, len(frame))

    # Shard gốc chiếm ~170 MB và không dùng lại; xoá ngay để đĩa không phình.
    Path(path).unlink(missing_ok=True)
    return frame


def write_schema_doc(frame: pd.DataFrame) -> None:
    """Bảng mô tả trường, dùng thẳng cho chương Dữ liệu của báo cáo."""
    lines = [
        "# Lược đồ bộ dữ liệu lịch sử (nguồn A)",
        "",
        f"Nguồn: Hugging Face `{REPO_ID}`, license CC BY-NC 4.0.",
        f"Phạm vi đã lọc: `province_name == \"{config.HF_PROVINCE}\"`, "
        f"`published_at <= {config.HF_CUTOFF}`.",
        f"Số dòng sau lọc: {len(frame):,}".replace(",", "."),
        "",
        "| Trường | Kiểu | Tỷ lệ có giá trị | Ví dụ |",
        "|---|---|---|---|",
    ]
    for column in frame.columns:
        series = frame[column]
        filled = series.notna().mean()
        sample = series.dropna()
        example = str(sample.iloc[0])[:40].replace("|", "/").replace("\n", " ") if len(sample) else "(trống)"
        lines.append(f"| `{column}` | {series.dtype} | {filled:.1%} | {example} |")

    lines += [
        "",
        "Ghi chú: số điện thoại trong `name` và `description` đã được chính bộ dữ liệu",
        "thay bằng chuỗi `[phone_number]`; pipeline vẫn chạy lại bộ lọc của dự án lên",
        "cột văn bản để không phụ thuộc vào cam kết của bên thứ ba.",
    ]
    SCHEMA_DOC.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tải và lọc bộ dữ liệu lịch sử từ Hugging Face")
    parser.add_argument("--max-shards", type=int, default=3, help=f"số shard cần tải (tối đa {N_SHARDS})")
    parser.add_argument(
        "--keep-after-cutoff",
        action="store_true",
        help="giữ trọn chuỗi thời gian 2025-06 → 2026-03, ghi ra hf_hcmc_timeline.parquet",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="đường dẫn parquet đầu ra; mặc định suy ra từ --keep-after-cutoff",
    )
    args = parser.parse_args()
    logger = get_logger("fetch_hf")

    params = {"repo": REPO_ID, "max_shards": args.max_shards, "cutoff": config.HF_CUTOFF}

    with RunManifest("fetch_hf_dataset", params=params) as manifest:
        frames = [_load_shard(i, logger) for i in range(min(args.max_shards, N_SHARDS))]
        frame = pd.concat(frames, ignore_index=True)
        manifest.count("rows_hcmc_raw", len(frame))

        frame["published_at"] = pd.to_datetime(frame["published_at"], errors="coerce")
        if not args.keep_after_cutoff:
            cutoff = pd.Timestamp(config.HF_CUTOFF)
            before = len(frame)
            frame = frame[frame["published_at"] <= cutoff]
            logger.info("cắt mốc %s: %d → %d dòng", config.HF_CUTOFF, before, len(frame))
        manifest.count("rows_after_cutoff", len(frame))

        in_target = frame["district_name"].isin(config.TARGET_DISTRICTS)
        manifest.count("rows_target_districts", int(in_target.sum()))
        logger.info(
            "3 quận mục tiêu: %d dòng | %d quận khác nhau",
            int(in_target.sum()),
            frame["district_name"].nunique(),
        )

        default_output = OUTPUT_TIMELINE if args.keep_after_cutoff else OUTPUT
        output = Path(args.output) if args.output else default_output
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(output, index=False)
        if output == OUTPUT:
            write_schema_doc(frame)
        manifest.count("rows_written", len(frame))
        manifest.note(f"ghi {output}")

    logger.info(
        "xong: %d dòng (%s → %s) → %s",
        len(frame),
        frame["published_at"].min().date(),
        frame["published_at"].max().date(),
        output,
    )


if __name__ == "__main__":
    main()
