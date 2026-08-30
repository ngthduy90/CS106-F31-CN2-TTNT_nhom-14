"""Chèn chỉ số đầu bảng vào README, lấy từ chính file kết quả.

README là chỗ người xem repo đọc đầu tiên, nên nó phải có con số chứ không chỉ có link.
Nhưng gõ tay thì mỗi lần chạy lại thí nghiệm là README lệch với báo cáo. Script thay
phần giữa hai dấu mốc bằng nội dung sinh từ `reports/results/`.

    python scripts/update-readme-metrics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RESULTS = ROOT / "reports" / "results"
START = "<!-- metrics:start -->"
END = "<!-- metrics:end -->"


def _vi(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def build_block() -> str:
    e1 = json.loads((RESULTS / "e1_chotot.json").read_text(encoding="utf-8"))
    models = e1["models"]
    learned = [m for m in models if not m["tier"].startswith("0")]
    best = min(learned, key=lambda m: m["cv_mean"]["MdAPE (%)"])
    margin = best["cv_std"]["MdAPE (%)"]
    leaders = [
        m for m in learned
        if m["cv_mean"]["MdAPE (%)"] <= best["cv_mean"]["MdAPE (%)"] + margin
    ]
    baseline = next(m for m in models if m["name"] == "Trung vị giá/m² theo nhóm")
    dummy = next(m for m in models if m["name"].startswith("Dummy"))

    lines = [
        f"Trên {e1['n_rows']:,} tin Chợ Tốt".replace(",", ".")
        + ", 5-fold, cùng bộ fold và cùng ngân sách tinh chỉnh cho mọi mô hình:",
        "",
        "| | MdAPE (%) | RMSE (tỷ) | R² |",
        "|---|---:|---:|---:|",
    ]
    for model in sorted(leaders, key=lambda m: m["cv_mean"]["MdAPE (%)"]):
        lines.append(
            f"| **{model['name']}** | {_vi(model['cv_mean']['MdAPE (%)'])} ± "
            f"{_vi(model['cv_std']['MdAPE (%)'])} | {_vi(model['cv_mean']['RMSE (tỷ)'])} | "
            f"{_vi(model['cv_mean']['R²'], 3)} |"
        )
    for model in (baseline, dummy):
        lines.append(
            f"| {model['name']} | {_vi(model['cv_mean']['MdAPE (%)'])} ± "
            f"{_vi(model['cv_std']['MdAPE (%)'])} | {_vi(model['cv_mean']['RMSE (tỷ)'])} | "
            f"{_vi(model['cv_mean']['R²'], 3)} |"
        )

    # Con số cũ là khoảng cách của RIÊNG mô hình tốt nhất, nhưng câu văn nói "nhóm dẫn
    # đầu": đọc lên thành cả nhóm đều hơn baseline đúng ngần ấy. Ghi khoảng của cả nhóm.
    gaps = [baseline["cv_mean"]["MdAPE (%)"] - m["cv_mean"]["MdAPE (%)"] for m in leaders]
    if len(gaps) == 1:
        gap_text = f"{_vi(gaps[0])} điểm phần trăm MdAPE"
    else:
        gap_text = f"{_vi(min(gaps))}–{_vi(max(gaps))} điểm phần trăm MdAPE"
    lines += [
        "",
        f"Nhóm dẫn đầu hơn baseline kiểu môi giới {gap_text}. Các mô",
        "hình in đậm cách nhau chưa tới một độ lệch chuẩn giữa các fold, nên bảng không",
        "chọn ra một mô hình thắng.",
    ]
    return "\n".join(lines)


def main() -> int:
    if not (RESULTS / "e1_chotot.json").exists():
        print("chưa có kết quả E1, bỏ qua")
        return 1

    text = README.read_text(encoding="utf-8")
    block = build_block()
    if START in text and END in text:
        head, _, rest = text.partition(START)
        _, _, tail = rest.partition(END)
        text = f"{head}{START}\n\n{block}\n\n{END}{tail}"
    else:
        print(f"README chưa có dấu mốc {START} / {END}")
        return 1

    README.write_text(text, encoding="utf-8")
    print("đã cập nhật chỉ số trong README")
    return 0


if __name__ == "__main__":
    sys.exit(main())
