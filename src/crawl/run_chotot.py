"""Chạy crawl Chợ Tốt (T1.2).

Mặc định lấy ÍT: đủ để dựng và kiểm pipeline đầu-cuối. Thành viên phụ trách thu thập
chạy lại cùng script với `--max-per-district` lớn hơn để đạt đích 8.000 tin; nhờ
checkpoint và khử trùng theo list_id, lần chạy sau chỉ bổ sung phần còn thiếu.

    python -m src.crawl.run_chotot                       # 300 tin/quận, 3 quận mục tiêu
    python -m src.crawl.run_chotot --max-per-district 2000
    python -m src.crawl.run_chotot --all-hcmc --max-per-district 500
    python -m src.crawl.run_chotot --dry-run             # 2 trang, không ghi file
"""

from __future__ import annotations

import argparse

from src import config
from src.crawl.chotot import PAGE_SIZE, crawl_district, fetch_page, parse_ad
from src.crawl.http import PoliteSession
from src.crawl.store import slugify
from src.utils.logging_setup import get_logger
from src.utils.run_manifest import RunManifest

DEFAULT_MAX_PER_DISTRICT = 300


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl tin bán nhà đất trên Chợ Tốt")
    parser.add_argument(
        "--max-per-district",
        type=int,
        default=DEFAULT_MAX_PER_DISTRICT,
        help="số tin tối đa lấy thêm cho mỗi quận trong lần chạy này",
    )
    parser.add_argument(
        "--districts",
        nargs="*",
        default=None,
        help="tên quận cần crawl; mặc định là 3 quận mục tiêu trong config",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="bỏ qua checkpoint, quét lại từ trang đầu",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="lấy 2 trang mỗi quận, in ra màn hình, KHÔNG ghi vào kho thô",
    )
    return parser


def dry_run(logger) -> None:
    """Hai trang cho quận đầu tiên, chỉ để xác nhận API và bộ parse còn đúng."""
    district, area_code = next(iter(config.CHOTOT_AREA_CODES.items()))
    with PoliteSession(logger=logger) as session:
        for page in range(2):
            ads, total = fetch_page(session, area_code, page * PAGE_SIZE, PAGE_SIZE)
            logger.info("%s trang %d: %d tin / tổng %d", district, page + 1, len(ads), total)
            for raw in ads[:3]:
                ad = parse_ad(raw)
                logger.info(
                    "  %s | %s | giá %s | %s m² | %s",
                    ad.get("list_id"),
                    (ad.get("subject") or "")[:48],
                    ad.get("price"),
                    ad.get("size"),
                    ad.get("ward_name"),
                )


def main() -> None:
    args = build_parser().parse_args()
    logger = get_logger("crawl_chotot")

    if args.dry_run:
        dry_run(logger)
        return

    districts = args.districts or list(config.CHOTOT_AREA_CODES)
    unknown = [d for d in districts if d not in config.CHOTOT_AREA_CODES]
    if unknown:
        raise SystemExit(f"chưa có mã area_v2 cho: {unknown}. Bổ sung vào src/config.py")

    params = {
        "max_per_district": args.max_per_district,
        "districts": districts,
        "resume": not args.no_resume,
    }

    with RunManifest("crawl_chotot", params=params) as manifest:
        with PoliteSession(logger=logger) as session:
            total_written = 0
            for district in districts:
                stats = crawl_district(
                    session,
                    district,
                    config.CHOTOT_AREA_CODES[district],
                    max_ads=args.max_per_district,
                    resume=not args.no_resume,
                    logger=logger,
                )
                total_written += stats["written"]
                for key, value in stats.items():
                    manifest.count(f"{slugify(district)}__{key}", value)

            manifest.count("written_total", total_written)
            manifest.count("http_requests", session.stats["requests"])
            manifest.count("http_retries", session.stats["retries"])

    logger.info("xong: ghi thêm %d tin", total_written)


if __name__ == "__main__":
    main()
