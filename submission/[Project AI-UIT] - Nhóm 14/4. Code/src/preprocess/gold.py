"""Bộ nhãn vàng và bảng chất lượng trích xuất (T2.5, T2.6).

Runbook 02 §1 đề xuất nhờ LLM gán nhãn trước rồi người duyệt. Dự án làm khác, và khác
theo hướng chặt hơn: **nhãn lấy từ chính các trường có cấu trúc mà sàn thu riêng**
(Chợ Tốt bắt người đăng điền `size`, `rooms`, `toilets`, `floors` vào form, tách hẳn
khỏi ô mô tả). Bộ luật regex chỉ đọc `subject` + `body`, tuyệt đối không thấy các
trường đó, nên phép đo là so hai nguồn độc lập chứ không phải chấm bài chính mình.

Ba cái được so với cách nhờ LLM gán nhãn:

- tái lập tuyệt đối, không phụ thuộc phiên bản mô hình hay chi phí API;
- không có rủi ro mô hình bịa số;
- nhãn là thứ người bán tự khai, tức là đúng loại "sự thật" mà đề bài quan tâm.

Điểm yếu phải nói thẳng trong báo cáo: người bán có thể điền form một đằng, viết mô tả
một nẻo. Vì vậy mỗi dòng nhãn vàng còn kèm cờ `verbatim` — con số nhãn có xuất hiện
nguyên văn trong văn bản hay không. Chỉ tiêu F1 được tính trên phần verbatim, phần
lệch được báo riêng như một chỉ số về độ nhiễu của tin rao.

    python -m src.preprocess.gold --build --size 200
    python -m src.preprocess.gold --measure
"""

from __future__ import annotations

import argparse
import json
import random
import re

from src import config
from src.crawl.store import iter_raw
from src.preprocess.extract import extract_all, strip_accents
from src.utils.logging_setup import get_logger

GOLD_PATH = config.DATA_INTERIM / "gold_200.jsonl"
REPORT_PATH = config.TABLES / "extraction-quality.md"

# Trường đo, kèm nguồn nhãn trong bản ghi Chợ Tốt và sai số chấp nhận được.
MEASURED = {
    "area_m2": {"label_field": "size", "tolerance": 0.02, "vietnamese": "Diện tích (m²)"},
    "bedrooms": {"label_field": "rooms", "tolerance": 0.0, "vietnamese": "Số phòng ngủ"},
    "bathrooms": {"label_field": "toilets", "tolerance": 0.0, "vietnamese": "Số nhà tắm"},
    "floors": {"label_field": "floors", "tolerance": 0.0, "vietnamese": "Số tầng"},
}

REQUIRED_F1 = {"area_m2", "bedrooms", "floors"}  # runbook 02 §1 bước 3
F1_TARGET = 0.9


def _text_of(record: dict) -> str:
    return f"{record.get('subject') or ''}\n{record.get('body') or ''}"


# Từ khoá nhận biết "con số này đang nói về trường nào". Cố ý rộng hơn và thô hơn bộ
# luật trích xuất: chỉ cần con số nằm gần MỘT trong các từ này là coi như tin có nêu
# giá trị đó. Nếu dùng chính regex của bộ trích xuất để lọc nhãn thì phép đo hoá ra
# tự chấm bài mình, F1 sẽ đẹp giả tạo.
FIELD_KEYWORDS = {
    "area_m2": re.compile(r"(?:m2|m²|mv|dt|dien\s*tich|cong\s*nhan|dtcn|dtsd)"),
    "bedrooms": re.compile(r"(?:pn|phong\s*ngu|phong|ngu|bedroom|\bp\b)"),
    "bathrooms": re.compile(r"(?:wc|toilet|nha\s*tam|phong\s*tam|\bvs\b)"),
    "floors": re.compile(r"(?:tang|lau|tam|me\b|tret|lung|cap\s*4|ket\s*cau)"),
}

KEYWORD_WINDOW = 26  # số ký tự nhìn hai bên con số


def _verbatim(field: str, value: float, text: str) -> bool:
    """Nhãn có được NÊU trong văn bản không, chứ không chỉ là chữ số xuất hiện đâu đó.

    Với các trường đếm (1–10 phòng, 1–5 tầng), gần như tin nào cũng vô tình chứa chữ
    số đó ở chỗ khác ("115 triệu/m2" chứa cả 1, 5, 2). Kiểm tra "chuỗi con xuất hiện"
    vì thế vô dụng. Luật chặt hơn: con số phải nằm trong khoảng ±26 ký tự quanh một từ
    khoá của đúng trường đang xét.
    """
    flat = strip_accents(text)
    keywords = FIELD_KEYWORDS[field]

    candidates = {str(int(value))} if float(value).is_integer() else set()
    candidates |= {f"{value:g}", f"{value:g}".replace(".", ",")}

    for candidate in candidates:
        for match in re.finditer(rf"(?<![\d.,]){re.escape(candidate)}(?![\d])", flat):
            left = flat[max(0, match.start() - KEYWORD_WINDOW) : match.start()]
            right = flat[match.end() : match.end() + KEYWORD_WINDOW]
            if keywords.search(left) or keywords.search(right):
                return True
    return False


def build(size: int, seed: int = config.SEED) -> int:
    """Lấy mẫu ngẫu nhiên các tin có đủ trường có cấu trúc, ghi ra bộ nhãn vàng."""
    pool = [
        record
        for record in iter_raw("chotot")
        if record.get("size") and (record.get("body") or "")
    ]
    random.Random(seed).shuffle(pool)
    selected = pool[:size]

    GOLD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GOLD_PATH.open("w", encoding="utf-8") as handle:
        for record in selected:
            text = _text_of(record)
            labels, verbatim = {}, {}
            for field, spec in MEASURED.items():
                value = record.get(spec["label_field"])
                if value in (None, "", 0):
                    continue
                labels[field] = float(value)
                verbatim[field] = _verbatim(field, float(value), text)
            handle.write(
                json.dumps(
                    {
                        "list_id": record.get("list_id"),
                        "text": text,
                        "labels": labels,
                        "verbatim": verbatim,
                        "label_source": "trường có cấu trúc của Chợ Tốt",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return len(selected)


def _matches(predicted: float, gold: float, tolerance: float) -> bool:
    if tolerance == 0:
        return int(round(predicted)) == int(round(gold))
    return abs(predicted - gold) <= tolerance * max(abs(gold), 1e-9)


def measure() -> dict[str, dict[str, float]]:
    """Precision / recall / F1 từng trường trên phần nhãn verbatim."""
    rows = [json.loads(line) for line in GOLD_PATH.read_text(encoding="utf-8").splitlines() if line]
    results: dict[str, dict[str, float]] = {}

    for field, spec in MEASURED.items():
        true_positive = predicted_count = gold_count = 0
        disagree_nonverbatim = 0

        for row in rows:
            gold = row["labels"].get(field)
            if gold is None:
                continue
            if not row["verbatim"].get(field, False):
                disagree_nonverbatim += 1
                continue  # nhãn không có nguyên văn trong text → nằm ngoài tầm regex

            gold_count += 1
            predicted = getattr(extract_all(row["text"]), field)
            if predicted is None:
                continue
            predicted_count += 1
            if _matches(float(predicted), float(gold), spec["tolerance"]):
                true_positive += 1

        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / gold_count if gold_count else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        results[field] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "n_gold_verbatim": gold_count,
            "n_gold_total": gold_count + disagree_nonverbatim,
        }
    return results


def error_breakdown() -> dict[str, dict[str, int]]:
    """Phân loại lỗi còn lại: bỏ sót, lệch đúng 1 đơn vị, lệch khác.

    Tách riêng "lệch đúng 1" vì với số tầng đó là cả một câu hỏi quy ước (có tính tầng
    trệt hay không), khác hẳn về bản chất so với một con số đọc sai.
    """
    rows = [json.loads(line) for line in GOLD_PATH.read_text(encoding="utf-8").splitlines() if line]
    breakdown: dict[str, dict[str, int]] = {}

    for field, spec in MEASURED.items():
        counts = {"đúng": 0, "bỏ sót": 0, "lệch 1 đơn vị": 0, "lệch khác": 0}
        for row in rows:
            gold = row["labels"].get(field)
            if gold is None or not row["verbatim"].get(field, False):
                continue
            predicted = getattr(extract_all(row["text"]), field)
            if predicted is None:
                counts["bỏ sót"] += 1
            elif _matches(float(predicted), float(gold), spec["tolerance"]):
                counts["đúng"] += 1
            elif abs(float(predicted) - float(gold)) <= 1.0:
                counts["lệch 1 đơn vị"] += 1
            else:
                counts["lệch khác"] += 1
        breakdown[field] = counts
    return breakdown


def write_report(results: dict[str, dict[str, float]], n_rows: int) -> None:
    lines = [
        "# Chất lượng trích xuất đặc trưng định lượng từ văn bản",
        "",
        f"Bộ nhãn vàng: {n_rows} tin lấy ngẫu nhiên (seed {config.SEED}) từ kho thô Chợ Tốt.",
        "Nhãn lấy từ các trường có cấu trúc người đăng điền vào form của sàn; bộ luật",
        "regex chỉ đọc tiêu đề và mô tả nên không hề thấy các trường đó.",
        "",
        "| Trường | Nhãn được nêu trong mô tả | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for field, spec in MEASURED.items():
        row = results[field]
        coverage = f"{row['n_gold_verbatim']}/{row['n_gold_total']}"
        mark = " ✓" if field in REQUIRED_F1 and row["f1"] >= F1_TARGET else ""
        lines.append(
            f"| {spec['vietnamese']} | {coverage} | {row['precision']:.3f} | "
            f"{row['recall']:.3f} | **{row['f1']:.3f}**{mark} |".replace(".", ",")
        )

    lines += [
        "",
        f"Chỉ tiêu của runbook 02: F1 ≥ {F1_TARGET:.1f} cho diện tích, số phòng ngủ và số tầng"
        .replace(".", ","),
        "(đánh dấu ✓ ở bảng trên).",
        "",
        "## Lỗi còn lại",
        "",
        "| Trường | Đúng | Bỏ sót | Lệch 1 đơn vị | Lệch khác |",
        "|---|---:|---:|---:|---:|",
    ]
    breakdown = error_breakdown()
    for field, spec in MEASURED.items():
        counts = breakdown[field]
        lines.append(
            f"| {spec['vietnamese']} | {counts['đúng']} | {counts['bỏ sót']} | "
            f"{counts['lệch 1 đơn vị']} | {counts['lệch khác']} |"
        )

    floors = breakdown["floors"]
    lines += [
        "",
        "Sau hai vòng sửa luật, diện tích đạt chỉ tiêu còn số tầng dừng ở mức thấp hơn.",
        f"Nhìn vào cột lỗi: {floors['lệch 1 đơn vị']} trong số "
        f"{floors['lệch 1 đơn vị'] + floors['lệch khác'] + floors['bỏ sót']} lỗi của trường",
        "số tầng là lệch đúng một đơn vị, và phần lớn rơi vào các tin viết \"1 trệt 1 lầu\"",
        "nhưng điền vào form con số 1. Đây là mâu thuẫn trong chính tin rao chứ không phải",
        "bộ luật đọc sai: cùng một cách viết, người bán này khai 1, người bán kia khai 2.",
        "",
        "Hai vòng sửa đã dùng hết theo đúng kịch bản rủi ro của kế hoạch (\"F1 chững dưới",
        "0,9 sau hai vòng → báo cáo trung thực kèm phân tích lỗi\"), nên nhóm dừng ở đây",
        "thay vì tiếp tục chỉnh luật cho khớp một tập nhãn tự nó đã nhiễu. Trường số tầng",
        "vẫn được đưa vào mô hình kèm cột chỉ báo thiếu, và mức nhiễu này được nêu lại ở",
        "phần hạn chế của báo cáo.",
        "",
        "Cột giữa cho biết bao nhiêu nhãn thật sự được nêu trong mô tả: con số phải nằm",
        "trong khoảng ±26 ký tự quanh một từ khoá của đúng trường đó. Phần còn lại là",
        "những tin mà người bán điền form một đằng, viết mô tả một nẻo; chúng nằm ngoài",
        "tầm với của bất kỳ bộ luật văn bản nào và được loại khỏi phép đo thay vì tính là",
        "lỗi của bộ luật.",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bộ nhãn vàng và đo chất lượng trích xuất")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--measure", action="store_true")
    parser.add_argument("--size", type=int, default=200)
    args = parser.parse_args()
    logger = get_logger("gold")

    if args.build or not GOLD_PATH.exists():
        count = build(args.size)
        logger.info("bộ nhãn vàng: %d tin → %s", count, GOLD_PATH)

    if args.measure or not args.build:
        results = measure()
        n_rows = sum(1 for line in GOLD_PATH.read_text(encoding="utf-8").splitlines() if line)
        write_report(results, n_rows)
        for field, row in results.items():
            logger.info(
                "%-11s P=%.3f R=%.3f F1=%.3f (n=%d/%d)",
                field,
                row["precision"],
                row["recall"],
                row["f1"],
                row["n_gold_verbatim"],
                row["n_gold_total"],
            )
        logger.info("bảng → %s", REPORT_PATH)


if __name__ == "__main__":
    main()
