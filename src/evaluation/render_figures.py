"""Sinh toàn bộ hình cho báo cáo (T2.16, T4.9–T4.12).

Mọi hình dùng chung một bảng màu và một cỡ chữ để bộ hình trong báo cáo trông như một
bộ chứ không như tám lần thử khác nhau. Chú thích viết tiếng Việt vì báo cáo là tiếng
Việt; tên file không dấu để không vỡ trên máy khác.

    python -m src.evaluation.render_figures
"""

from __future__ import annotations

import json

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src import config  # noqa: E402
from src.utils.logging_setup import get_logger  # noqa: E402

PALETTE = {
    "chotot": "#0891B2",
    "hf": "#D97706",
    "mogi": "#7C3AED",
    "neutral": "#334155",
    "grid": "#E2E8F0",
}
BILLION = 1e9

plt.rcParams.update(
    {
        "figure.dpi": 140,
        "savefig.dpi": 140,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.grid": True,
        "grid.color": PALETTE["grid"],
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def _save(fig, name: str, logger) -> None:
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES / name
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info("hình → %s", path.name)


def figure_price_distribution(frame: pd.DataFrame, logger) -> None:
    """Phân phối giá ở thang gốc và thang log — lý do chọn log làm biến mục tiêu.

    Hai bảng cạnh nhau nói được điều mà một câu văn phải mất cả đoạn: thang gốc lệch
    phải nặng với đuôi dài tới hàng chục tỷ, thang log gần đối xứng. Đó chính là lập
    luận cho việc huấn luyện trên log(giá).
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    price = frame["total_price_vnd"] / BILLION

    axes[0].hist(price, bins=60, color=PALETTE["chotot"], edgecolor="white", linewidth=0.4)
    axes[0].set_title("Phân phối tổng giá (thang gốc)")
    axes[0].set_xlabel("Tỷ đồng")
    axes[0].set_ylabel("Số tin")

    axes[1].hist(np.log(price), bins=60, color=PALETTE["hf"], edgecolor="white", linewidth=0.4)
    axes[1].set_title("Phân phối log(tổng giá)")
    axes[1].set_xlabel("log(tỷ đồng)")
    axes[1].set_ylabel("Số tin")

    _save(fig, "eda-01-phan-phoi-gia.png", logger)


def figure_area_distribution(frame: pd.DataFrame, logger) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.hist(frame["area_m2"], bins=60, color=PALETTE["neutral"], edgecolor="white", linewidth=0.4)
    ax.set_title("Phân phối diện tích")
    ax.set_xlabel("m²")
    ax.set_ylabel("Số tin")
    _save(fig, "eda-02-phan-phoi-dien-tich.png", logger)


def figure_count_by_district(frame: pd.DataFrame, logger) -> None:
    counts = (
        frame.groupby(["district", "source"]).size().unstack(fill_value=0).sort_values(
            by=list(frame["source"].unique())[0], ascending=True
        )
    )
    counts = counts.tail(15)
    fig, ax = plt.subplots(figsize=(7, max(3.5, 0.28 * len(counts))))
    bottom = np.zeros(len(counts))
    for source in counts.columns:
        ax.barh(counts.index, counts[source], left=bottom,
                color=PALETTE.get(source, PALETTE["neutral"]), label=source)
        bottom += counts[source].to_numpy()
    ax.set_title("Số tin theo quận và theo nguồn")
    ax.set_xlabel("Số tin")
    ax.legend(frameon=False)
    _save(fig, "eda-03-so-tin-theo-quan.png", logger)


def figure_unit_price_by_quarter(frame: pd.DataFrame, logger) -> None:
    """Giá/m² trung vị theo quý, tách theo quận — nền cho phần diễn giải trôi giá."""
    data = frame.dropna(subset=["published_at"]).copy()
    data["published_at"] = pd.to_datetime(data["published_at"], errors="coerce", utc=True)
    data = data.dropna(subset=["published_at"])
    data["quarter"] = data["published_at"].dt.to_period("Q").astype(str)
    data["unit_price"] = data["total_price_vnd"] / data["area_m2"] / 1e6

    top = data["district"].value_counts().head(5).index
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for district in top:
        series = (
            data[data["district"] == district]
            .groupby("quarter")["unit_price"]
            .median()
            .sort_index()
        )
        if len(series) >= 2:
            ax.plot(series.index, series.to_numpy(), marker="o", label=district, linewidth=1.8)

    ax.set_title("Giá/m² trung vị theo quý")
    ax.set_xlabel("Quý")
    ax.set_ylabel("Triệu đồng/m²")
    ax.legend(frameon=False, ncol=2)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    _save(fig, "eda-04-gia-m2-theo-quy.png", logger)


def figure_error_by_slice(logger) -> None:
    """MdAPE theo quận và theo bin giá — chỗ giám khảo hỏi sâu nhất (T4.10)."""
    path = config.REPORTS / "results" / "error_analysis.json"
    if not path.exists():
        logger.info("chưa có error_analysis.json, bỏ qua hình phân tích lỗi")
        return

    payload = json.loads(path.read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))

    districts = payload["by_district"][:10]
    axes[0].barh([d["district"] for d in districts], [d["MdAPE (%)"] for d in districts],
                 color=PALETTE["chotot"])
    axes[0].set_title("MdAPE theo quận")
    axes[0].set_xlabel("%")

    bins = payload["by_price_bin"]
    axes[1].bar([b["bin"] for b in bins], [b["MdAPE (%)"] for b in bins], color=PALETTE["hf"])
    axes[1].set_title("MdAPE theo khoảng giá")
    axes[1].set_ylabel("%")
    plt.setp(axes[1].get_xticklabels(), rotation=20, ha="right")

    _save(fig, "ket-qua-01-sai-so-theo-lat-cat.png", logger)


def figure_learning_curve(logger) -> None:
    """RMSE theo cỡ tập huấn luyện — trả lời "crawl thêm có đáng không" (T4.11)."""
    path = config.REPORTS / "results" / "learning_curve.json"
    if not path.exists():
        logger.info("chưa có learning_curve.json, bỏ qua")
        return

    payload = json.loads(path.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    sizes = [row["n_train"] for row in payload["points"]]
    rmse = [row["RMSE (tỷ)"] for row in payload["points"]]
    mdape = [row["MdAPE (%)"] for row in payload["points"]]

    ax.plot(sizes, rmse, marker="o", color=PALETTE["chotot"], label="RMSE (tỷ)")
    ax.set_xlabel("Số tin dùng để huấn luyện")
    ax.set_ylabel("RMSE (tỷ đồng)")
    twin = ax.twinx()
    twin.plot(sizes, mdape, marker="s", color=PALETTE["hf"], label="MdAPE (%)")
    twin.set_ylabel("MdAPE (%)")
    twin.grid(False)
    ax.set_title("Đường cong học theo cỡ tập huấn luyện")

    handles = ax.get_lines() + twin.get_lines()
    ax.legend(handles, [h.get_label() for h in handles], frameon=False, loc="upper right")
    _save(fig, "ket-qua-02-duong-cong-hoc.png", logger)


def main() -> None:
    logger = get_logger("figures")
    frame = pd.read_parquet(config.DATA_PROCESSED / "listings.parquet")

    figure_price_distribution(frame, logger)
    figure_area_distribution(frame, logger)
    figure_count_by_district(frame, logger)
    figure_unit_price_by_quarter(frame, logger)
    figure_error_by_slice(logger)
    figure_learning_curve(logger)


if __name__ == "__main__":
    main()
