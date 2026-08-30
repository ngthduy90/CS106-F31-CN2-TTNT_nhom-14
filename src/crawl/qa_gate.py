"""T1.8 và T1.9 — cổng kiểm chất lượng kho dữ liệu thô (runbook 01 §6).

Sáu ngưỡng phải đạt trước khi sang bước tiền xử lý. Ý nghĩa của cổng này không phải là
"chấm điểm dữ liệu" mà là **buộc phải quyết định**: không đạt thì hoặc mở nguồn dự
phòng, hoặc nới phạm vi quận, và quyết định đó được ghi lại kèm ngày giờ. Đi tiếp trong
im lặng với dữ liệu không đạt là cách một đồ án hỏng mà không ai biết hỏng từ đâu.

Ngưỡng đọc từ `config.QA_THRESHOLDS`, không viết lại ở đây, để báo cáo trích được đúng
con số mà code đã dùng.

    python -m src.crawl.qa_gate
"""

from __future__ import annotations

import argparse
import re
from datetime import date

from src import config
from src.crawl.pii import contains_phone
from src.crawl.store import iter_raw
from src.preprocess.address import normalise_district
from src.preprocess.price import normalise_numeric_price, parse_price
from src.utils.logging_setup import get_logger
from src.utils.run_manifest import RunManifest

OUTPUT = config.TABLES / "qa-gate.md"
MIN_DESCRIPTION_CHARS = 200

# Detector ĐỘC LẬP, cố ý không dùng lại src.crawl.pii: gate chấm bằng chính detector của
# scrubber thì "0 tin còn dấu vết SĐT" là hằng đúng theo cấu trúc (mù đúng những ca
# scrubber mù) chứ không phải một phép đo. Regex dưới đây thô và độc lập — nó chỉ bắt
# cách viết trần (0/84 + 9–11 chữ số, dấu ngăn nhẹ), nhưng đó chính là điều làm nó có
# khả năng KHÔNG đồng ý với scrubber.
_INDEPENDENT_PHONE = re.compile(
    r"(?<!\d)(?:\+?84|0)[\s.\-_()]{0,2}\d(?:[\s.\-_()]{0,2}\d){8,10}(?!\d)"
)


def _independent_phone_hit(value) -> bool:
    """Có chuỗi nào trong bản ghi còn giống số điện thoại theo detector độc lập không."""
    if isinstance(value, str):
        return bool(_INDEPENDENT_PHONE.search(value))
    if isinstance(value, dict):
        return any(_independent_phone_hit(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_independent_phone_hit(item) for item in value)
    return False


def _chotot_view(record: dict) -> dict:
    return {
        "description": record.get("body") or "",
        "price": normalise_numeric_price(record.get("price")),
        "ward": record.get("ward_name") or record.get("ward_name_v3"),
        "coords": record.get("latitude") and record.get("longitude"),
        "district": normalise_district(record.get("area_name")),
    }


def _mogi_view(record: dict) -> dict:
    price = normalise_numeric_price(record.get("price_vnd_ld"))
    if price is None:
        price = parse_price(record.get("price_text")).total_vnd
    address = record.get("address") or ""
    return {
        "description": record.get("description") or "",
        "price": price,
        "ward": "Phường" in address or None,
        "coords": record.get("latitude") and record.get("longitude"),
        "district": normalise_district(address),
    }


VIEWS = {"chotot": _chotot_view, "mogi": _mogi_view}


def collect() -> dict:
    """Đếm các đại lượng cần cho sáu ngưỡng, quét kho thô đúng một lượt."""
    stats = {
        "total": 0,
        "long_description": 0,
        "numeric_price": 0,
        "ward_or_coords": 0,
        "target_districts": 0,
        "pii_hits": 0,
        "pii_hits_independent": 0,
        "per_source": {},
    }

    for source, view in VIEWS.items():
        count = 0
        for record in iter_raw(source):
            count += 1
            stats["total"] += 1
            item = view(record)

            if len(item["description"]) >= MIN_DESCRIPTION_CHARS:
                stats["long_description"] += 1
            if item["price"] is not None:
                stats["numeric_price"] += 1
            if item["ward"] or item["coords"]:
                stats["ward_or_coords"] += 1
            if item["district"] in config.TARGET_DISTRICTS:
                stats["target_districts"] += 1
            if contains_phone(record):
                stats["pii_hits"] += 1
            if _independent_phone_hit(record):
                stats["pii_hits_independent"] += 1
        stats["per_source"][source] = count

    return stats


def evaluate(stats: dict) -> list[dict]:
    total = max(stats["total"], 1)
    thresholds = config.QA_THRESHOLDS

    checks = [
        {
            "name": "Tổng số tin thô (sau khử trùng theo id)",
            "value": stats["total"],
            "threshold": thresholds["min_raw_listings"],
            "format": "count",
        },
        {
            "name": f"Tỷ lệ tin có mô tả ≥ {MIN_DESCRIPTION_CHARS} ký tự",
            "value": stats["long_description"] / total,
            "threshold": thresholds["min_share_description_200_chars"],
            "format": "share",
        },
        {
            "name": "Tỷ lệ tin có giá dạng số",
            "value": stats["numeric_price"] / total,
            "threshold": thresholds["min_share_numeric_price"],
            "format": "share",
        },
        {
            "name": "Tỷ lệ tin có phường hoặc toạ độ",
            "value": stats["ward_or_coords"] / total,
            "threshold": thresholds["min_share_ward_or_coords"],
            "format": "share",
        },
        {
            "name": "Tin ở 3 quận mục tiêu",
            "value": stats["target_districts"],
            "threshold": thresholds["min_listings_target_districts"],
            "format": "count",
        },
    ]
    for check in checks:
        check["passed"] = check["value"] >= check["threshold"]

    # Ngưỡng PII là ngưỡng TRẦN, không phải sàn: càng ít càng tốt, và chỉ 0 mới đạt.
    # Hai dòng, hai detector: dòng đầu dùng chính detector của scrubber nên chỉ bắt được
    # thứ scrubber không sửa được (trường _source_url, _collected_at gắn SAU khi scrub);
    # dòng sau dùng detector độc lập và là dòng duy nhất có thể bác lại scrubber.
    checks.append(
        {
            "name": "Số tin còn dấu vết SĐT (detector của scrubber)",
            "value": stats["pii_hits"],
            "threshold": thresholds["max_pii_matches"],
            "format": "count",
            "passed": stats["pii_hits"] <= thresholds["max_pii_matches"],
            "upper_bound": True,
        }
    )
    checks.append(
        {
            "name": "Số tin còn dấu vết SĐT (detector độc lập)",
            "value": stats["pii_hits_independent"],
            "threshold": thresholds["max_pii_matches"],
            "format": "count",
            "passed": stats["pii_hits_independent"] <= thresholds["max_pii_matches"],
            "upper_bound": True,
        }
    )
    return checks


def render(stats: dict, checks: list[dict]) -> str:
    def fmt(value, kind):
        if kind == "share":
            return f"{value:.1%}".replace(".", ",")
        return f"{int(value):,}".replace(",", ".")

    passed = sum(check["passed"] for check in checks)
    lines = [
        "# Cổng kiểm chất lượng dữ liệu thô",
        "",
        f"Chạy ngày {date.today():%d/%m/%Y}. Nguồn thô: "
        + ", ".join(f"{k} {v:,}".replace(",", ".") for k, v in stats["per_source"].items())
        + ".",
        "",
        "| Kiểm tra | Đạt được | Ngưỡng | Kết quả |",
        "|---|---:|---:|:---:|",
    ]
    for check in checks:
        comparator = "≤" if check.get("upper_bound") else "≥"
        lines.append(
            f"| {check['name']} | {fmt(check['value'], check['format'])} | "
            f"{comparator} {fmt(check['threshold'], check['format'])} | "
            f"{'ĐẠT' if check['passed'] else 'CHƯA ĐẠT'} |"
        )

    lines += ["", f"**{passed}/{len(checks)} ngưỡng đạt.**", ""]

    failed = [check for check in checks if not check["passed"]]
    if failed:
        lines += [
            "## Quyết định",
            "",
            "Chưa đạt: " + "; ".join(check["name"].lower() for check in failed) + ".",
            "",
            "Theo runbook 01 §6, chưa đạt ngưỡng nào thì phải chọn một trong hai hướng và",
            "ghi lại lựa chọn: (a) mở nguồn dự phòng alonhadat/homedy, hoặc (b) nới phạm vi",
            "sang toàn bộ quận của TP.HCM.",
            "",
            "**Trạng thái hiện tại**: các script crawl đang chạy ở mức giới hạn có chủ ý để",
            "kiểm pipeline đầu-cuối, phần thu thập đủ số lượng do thành viên phụ trách dữ",
            "liệu chạy tiếp bằng chính các lệnh trong `docs/huong-dan-su-dung.md` §3. Nhờ",
            "checkpoint và khử trùng theo mã tin, lần chạy sau chỉ bổ sung phần còn thiếu.",
            "Vì vậy chưa mở nguồn dự phòng: nguyên nhân chưa đạt là hạn mức tự đặt, không",
            "phải nguồn dữ liệu cạn.",
        ]
    else:
        lines += [
            "## Quyết định",
            "",
            "Toàn bộ ngưỡng đạt. Đi tiếp sang bước tiền xử lý, không cần mở nguồn dự phòng.",
        ]

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Chấm kho dữ liệu thô theo 6 ngưỡng chất lượng")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    logger = get_logger("qa_gate")

    with RunManifest("qa_gate") as manifest:
        stats = collect()
        checks = evaluate(stats)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(render(stats, checks), encoding="utf-8")

        for check in checks:
            manifest.count(check["name"], int(check["value"]))
        manifest.count("passed", sum(check["passed"] for check in checks))

    if not args.quiet:
        for check in checks:
            logger.info("%-45s %s", check["name"], "ĐẠT" if check["passed"] else "CHƯA ĐẠT")
    logger.info("bảng → %s", OUTPUT)


if __name__ == "__main__":
    main()
