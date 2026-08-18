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


SERIES_COLORS = ["#0891B2", "#D97706", "#7C3AED", "#059669", "#DC2626"]


def figure_unit_price_by_month(frame: pd.DataFrame, logger) -> None:
    """Giá/m² trung vị theo tháng, 2025-06 → 2026-08 (T4.12).

    Bảng đã tiền xử lý chỉ chứa lát cắt ≤ mốc cắt của nguồn lịch sử cộng với tin crawl
    2026, nên vẽ trên nó chỉ ra được hai điểm mốc và một đường thẳng nối chúng — nhìn
    thì gọn mà không nói được gì về diễn biến ở giữa. Hình này vì thế đọc thêm file
    `hf_hcmc_timeline.parquet` (toàn chuỗi 2025-06 → 2026-03) và ghép với dữ liệu crawl
    tháng 08/2026, cho ra một đường thật sự có hình dạng.

    Trung vị theo THÁNG chứ không theo quý: mười tháng dữ liệu chia thành bốn quý thì
    mỗi quý chỉ còn một điểm, quá thô để thấy xu hướng.
    """
    parts = []

    timeline_path = config.DATA_EXTERNAL / "hf_hcmc_timeline.parquet"
    if timeline_path.exists():
        timeline = pd.read_parquet(
            timeline_path, columns=["district_name", "price", "area", "published_at"]
        )
        timeline = timeline.rename(
            columns={"district_name": "district", "price": "total_price_vnd", "area": "area_m2"}
        )
        timeline["total_price_vnd"] = pd.to_numeric(timeline["total_price_vnd"], errors="coerce")
        # Cùng miền hợp lệ với pipeline chính, nếu không đường trung vị bị vài tin rác kéo lệch.
        low, high = config.VALID_TOTAL_PRICE_VND
        timeline = timeline[
            timeline["total_price_vnd"].between(low, high)
            & timeline["area_m2"].between(*config.VALID_AREA_M2)
        ]
        from src.preprocess.address import normalise_district

        timeline["district"] = [normalise_district(d) for d in timeline["district"]]
        parts.append(timeline[["district", "total_price_vnd", "area_m2", "published_at"]])

    crawl = frame[frame["source"].isin(["chotot", "mogi"])]
    parts.append(crawl[["district", "total_price_vnd", "area_m2", "published_at"]])

    data = pd.concat(parts, ignore_index=True)
    data["published_at"] = pd.to_datetime(data["published_at"], errors="coerce", utc=True)
    data = data.dropna(subset=["published_at", "total_price_vnd", "area_m2"])
    data["month"] = data["published_at"].dt.tz_localize(None).dt.to_period("M").astype(str)
    data["unit_price"] = data["total_price_vnd"] / data["area_m2"] / 1e6

    # Ba quận mục tiêu đứng trước, rồi bù thêm quận đông tin nhất cho đủ năm đường.
    ranked = list(data["district"].value_counts().index)
    districts = [d for d in config.TARGET_DISTRICTS if d in ranked]
    districts += [d for d in ranked if d not in districts][: 5 - len(districts)]

    # Dữ liệu lịch sử dừng ở 2026-03, tin crawl là 2026-08: giữa hai mốc có năm tháng
    # trống. Nối thẳng qua khoảng trống đó là vẽ ra một xu hướng chưa hề quan sát được,
    # nên đoạn bắc cầu được vẽ nét đứt và điểm crawl được đánh dấu riêng.
    months = sorted(data["month"].unique())
    crawl_months = sorted(
        data.loc[data["published_at"].dt.year >= 2026, "month"].unique()
    )
    bridge_from = None
    if len(months) >= 2:
        gaps = [
            (months[i], months[i + 1])
            for i in range(len(months) - 1)
            if (pd.Period(months[i + 1]) - pd.Period(months[i])).n > 1
        ]
        bridge_from = gaps[-1] if gaps else None

    fig, ax = plt.subplots(figsize=(9, 4.2))

    for colour, district in zip(SERIES_COLORS, districts):
        series = (
            data[data["district"] == district]
            .groupby("month")["unit_price"]
            .agg(["median", "size"])
            .sort_index()
        )
        # Tháng dưới 15 tin thì trung vị quá nhiễu để vẽ thành xu hướng.
        series = series[series["size"] >= 15]
        if len(series) < 2:
            continue

        if bridge_from and bridge_from[0] in series.index and bridge_from[1] in series.index:
            left = series.loc[:bridge_from[0]]
            right = series.loc[bridge_from[1]:]
            ax.plot(left.index, left["median"].to_numpy(), marker="o", markersize=4,
                    label=district, linewidth=1.8, color=colour)
            ax.plot(list(bridge_from), [left["median"].iloc[-1], right["median"].iloc[0]],
                    linestyle="--", linewidth=1.2, color=colour, alpha=0.6)
            ax.plot(right.index, right["median"].to_numpy(), marker="D", markersize=6,
                    linewidth=1.8, color=colour)
        else:
            ax.plot(series.index, series["median"].to_numpy(), marker="o", markersize=4,
                    label=district, linewidth=1.8, color=colour)

    ax.set_title("Giá/m² trung vị theo tháng")
    ax.set_xlabel("Tháng đăng tin")
    ax.set_ylabel("Triệu đồng/m²")
    ax.legend(frameon=False, ncol=1, fontsize=9, loc="center left", bbox_to_anchor=(1.01, 0.5))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

    if bridge_from:
        ax.text(
            0.5, -0.42,
            f"Nét đứt: khoảng trống dữ liệu {bridge_from[0]} → {bridge_from[1]}. "
            "Hình thoi là tin crawl 08/2026 (nguồn B), tròn là bộ lịch sử (nguồn A).",
            transform=ax.transAxes, ha="center", fontsize=8, color="#475569",
        )
    _save(fig, "eda-04-gia-m2-theo-thang.png", logger)


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
    figure_unit_price_by_month(frame, logger)
    figure_error_by_slice(logger)
    figure_learning_curve(logger)


if __name__ == "__main__":
    main()
