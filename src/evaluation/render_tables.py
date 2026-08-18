"""T4.14 — sinh lại MỌI bảng markdown từ các file kết quả JSON.

Bảng trong báo cáo không bao giờ được gõ tay. Chạy lại script này phải cho ra file
giống hệt byte-to-byte, nhờ vậy con số trong báo cáo luôn truy được về đúng một lần
chạy và không thể lệch giữa báo cáo với slide.

    python -m src.evaluation.render_tables
"""

from __future__ import annotations

import json

from src import config
from src.evaluation.metrics import LOWER_IS_BETTER, METRIC_ORDER
from src.models.registry import TIER_ORDER
from src.utils.logging_setup import get_logger

RESULTS_DIR = config.REPORTS / "results"
TABLES_DIR = config.TABLES


def _vi(value: float, digits: int = 3) -> str:
    """Số theo cách viết Việt Nam: dấu phẩy thập phân."""
    return f"{value:.{digits}f}".replace(".", ",")


def _cell(mean: float, std: float, digits: int = 3, bold: bool = False) -> str:
    text = f"{_vi(mean, digits)} ± {_vi(std, digits)}"
    return f"**{text}**" if bold else text


def _best_index(values: list[float], metric: str) -> int:
    if LOWER_IS_BETTER[metric]:
        return min(range(len(values)), key=lambda i: values[i])
    return max(range(len(values)), key=lambda i: values[i])


def render_e1(payload: dict) -> str:
    models = sorted(
        payload["models"],
        key=lambda m: (TIER_ORDER.index(m["tier"]) if m["tier"] in TIER_ORDER else 99, m["name"]),
    )
    lines = [
        f"# E1 — {payload['label']}",
        "",
        f"{payload['n_rows']:,} dòng".replace(",", ".")
        + f", chia hold-out {int((1 - config.HOLDOUT_TEST_SIZE) * 100)}/"
        + f"{int(config.HOLDOUT_TEST_SIZE * 100)}"
        + f", {config.CV_FOLDS}-fold trên phần train, seed {payload['seed']}.",
        f"Ngân sách tinh chỉnh: RandomizedSearch {payload['search_iterations']} cấu hình, "
        "giống nhau cho mọi mô hình.",
        "",
        "Mỗi ô là trung bình ± độ lệch chuẩn qua 5 fold. **In đậm** là tốt nhất mỗi cột.",
        "",
        "| Tầng | Mô hình | " + " | ".join(METRIC_ORDER) + " |",
        "|---|---|" + "---:|" * len(METRIC_ORDER),
    ]

    best = {
        metric: _best_index([m["cv_mean"][metric] for m in models], metric)
        for metric in METRIC_ORDER
    }

    for position, model in enumerate(models):
        cells = []
        for metric in METRIC_ORDER:
            digits = 1 if metric == "MdAPE (%)" else 3
            cells.append(
                _cell(model["cv_mean"][metric], model["cv_std"][metric], digits,
                      bold=(position == best[metric]))
            )
        lines.append(f"| {model['tier']} | {model['name']} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Đo trên tập hold-out (chưa từng dùng để chọn tham số)",
        "",
        "| Mô hình | " + " | ".join(METRIC_ORDER) + " |",
        "|---|" + "---:|" * len(METRIC_ORDER),
    ]
    for model in models:
        cells = [
            _vi(model["holdout"][metric], 1 if metric == "MdAPE (%)" else 3)
            for metric in METRIC_ORDER
        ]
        lines.append(f"| {model['name']} | " + " | ".join(cells) + " |")

    # Nhóm tuyến tính hay có std của RMSE lớn hơn cả trung bình; đó là dấu hiệu chứ
    # không phải lỗi, và người đọc bảng cần được cảnh báo ngay dưới bảng.
    unstable = [
        m["name"] for m in models
        if m["cv_std"]["RMSE (tỷ)"] > m["cv_mean"]["RMSE (tỷ)"] * 0.6
    ]
    if unstable:
        lines += [
            "",
            "**Chú ý khi đọc**: " + ", ".join(unstable) + " có độ lệch chuẩn của RMSE lớn",
            "so với chính trung bình của nó. Nguyên nhân là mô hình huấn luyện trên log(giá)",
            "và phép `exp` khuếch đại một vài dự báo ngoại suy xa thành sai số khổng lồ trên",
            "thang VND. Trung vị không bị ảnh hưởng nên MdAPE của các mô hình này vẫn ở mức",
            "khá — đó chính là lý do bảng báo cả bốn chỉ số thay vì chỉ một.",
        ]

    lines += [
        "",
        "Ghi chú: mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính sau khi đã quy",
        "ngược về thang VND. RMSE và MAE tính bằng tỷ đồng. MdAPE là sai số phần trăm",
        "trung vị. Mọi mô hình dùng CHUNG một bộ fold, nên chênh lệch giữa các dòng không",
        "lẫn chênh lệch giữa các phép chia tập.",
    ]
    return "\n".join(lines) + "\n"


def render_e2(payload: dict) -> str:
    lines = [
        "# E2 — chuyển giao theo thời gian",
        "",
        f"Huấn luyện trên {payload['train_rows']:,} tin đăng tới {payload['cutoff']}, ".replace(",", ".")
        + f"kiểm trên {payload['test_rows']:,} tin crawl tháng 08/2026.".replace(",", "."),
        "",
        "Cả hai phía đều là GIÁ RAO nên chênh lệch đo được là trôi giá theo thời gian,",
        "không lẫn khoảng cách giữa giá rao và giá giao dịch.",
        "",
        "| Mô hình | " + " | ".join(METRIC_ORDER) + " |",
        "|---|" + "---:|" * len(METRIC_ORDER),
    ]
    for model in payload["models"]:
        cells = [
            _vi(model["transfer"][metric], 1 if metric == "MdAPE (%)" else 3)
            for metric in METRIC_ORDER
        ]
        lines.append(f"| {model['name']} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "So sánh trực tiếp với cột cùng tên trong bảng E1 nguồn B (train 2026 → test",
        "2026): khoảng cách giữa hai bảng chính là cái giá phải trả khi dùng mô hình cũ",
        "cho thị trường mới.",
    ]
    return "\n".join(lines) + "\n"


def render_ablation(payload: dict) -> str:
    rows = payload["rows"]
    baseline = rows[0]["cv_mean"]["MdAPE (%)"]
    lines = [
        "# Ablation — đặc trưng văn bản đáng bao nhiêu?",
        "",
        f"Mô hình: {payload['model']}. Cả bốn cấu hình chạy trên CÙNG một bộ fold và cùng",
        "một ngân sách tinh chỉnh, nên khác biệt duy nhất giữa các dòng là nhánh văn bản.",
        "",
        "| Cấu hình đặc trưng | MdAPE (%) | Δ so với chỉ bảng | RMSE (tỷ) | R² |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        mdape = row["cv_mean"]["MdAPE (%)"]
        delta = mdape - baseline
        sign = "+" if delta > 0 else ""
        lines.append(
            f"| {row['configuration']} | {_vi(mdape, 2)} | {sign}{_vi(delta, 2)} | "
            f"{_vi(row['cv_mean']['RMSE (tỷ)'], 3)} | {_vi(row['cv_mean']['R²'], 3)} |"
        )
    lines += [
        "",
        "Δ âm nghĩa là thêm nhánh đó làm sai số giảm. Đây là con số trả lời trực tiếp câu",
        "hỏi của đề: mô tả rao vặt mang bao nhiêu tín hiệu giá.",
    ]
    return "\n".join(lines) + "\n"


def render_e3(payload: dict) -> str:
    rows = payload["rows"]
    lines = [
        "# E3 — giữ lại từng phường làm tập kiểm (leave-one-ward-out)",
        "",
        f"Mô hình: {payload['model']}. Mỗi dòng: bỏ toàn bộ tin của một phường ra khỏi",
        "tập huấn luyện, rồi dự báo đúng phường đó. Đây là phép đo khả năng tổng quát",
        "sang khu vực CHƯA TỪNG THẤY.",
        "",
        "| Phường giữ lại | Số tin kiểm | MdAPE (%) | RMSE (tỷ) | R² |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        m = row["metrics"]
        lines.append(
            f"| {row['ward']} | {row['n_test']} | {_vi(m['MdAPE (%)'], 1)} | "
            f"{_vi(m['RMSE (tỷ)'], 3)} | {_vi(m['R²'], 3)} |"
        )
    if rows:
        values = [row["metrics"]["MdAPE (%)"] for row in rows]
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / max(len(values) - 1, 1)) ** 0.5
        lines += ["", f"Trung bình MdAPE: {_vi(mean, 1)}% ± {_vi(std, 1)}."]
    lines += [
        "",
        "Kết quả kém hơn E1 là một phát hiện, không phải một thất bại: nó cho biết mô",
        "hình dựa vào địa bàn đến mức nào, và cảnh báo rằng đem mô hình này sang một",
        "phường chưa có dữ liệu thì sai số sẽ ở mức nào.",
    ]
    return "\n".join(lines) + "\n"


RENDERERS = {
    "e1_chotot": ("e1-results-chotot.md", render_e1),
    "e1_hf": ("e1-results-hf.md", render_e1),
    "e2": ("e2-results.md", render_e2),
    "e3": ("e3-results.md", render_e3),
    "ablation": ("ablation.md", render_ablation),
}


def main() -> None:
    logger = get_logger("render_tables")
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    for key, (filename, renderer) in RENDERERS.items():
        source = RESULTS_DIR / f"{key}.json"
        if not source.exists():
            logger.info("chưa có %s, bỏ qua", source.name)
            continue
        payload = json.loads(source.read_text(encoding="utf-8"))
        (TABLES_DIR / filename).write_text(renderer(payload), encoding="utf-8")
        logger.info("%s → %s", source.name, filename)
        written += 1

    logger.info("đã sinh %d bảng", written)


if __name__ == "__main__":
    main()
