"""Chạy crawl mogi.vn (T1.5).

    python -m src.crawl.run_mogi --max-per-district 150
    python -m src.crawl.run_mogi --dry-run
"""

from __future__ import annotations

import argparse

from src import config
from src.crawl.http import PoliteSession
from src.crawl.mogi import crawl_district, iter_listing_urls, parse_detail_page
from src.crawl.store import slugify
from src.utils.logging_setup import get_logger
from src.utils.run_manifest import RunManifest

DEFAULT_MAX_PER_DISTRICT = 120


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl tin bán nhà đất trên mogi.vn")
    parser.add_argument("--max-per-district", type=int, default=DEFAULT_MAX_PER_DISTRICT)
    parser.add_argument("--districts", nargs="*", default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="lấy 1 trang danh sách + 2 trang chi tiết, in ra màn hình, không ghi file",
    )
    return parser


def dry_run(logger) -> None:
    district = next(iter(config.MOGI_DISTRICT_PATHS))
    with PoliteSession(logger=logger) as session:
        for summary, _ in iter_listing_urls(session, district, max_urls=2, logger=logger):
            record = parse_detail_page(session.get(summary["url"]).text, summary["url"])
            logger.info(
                "  %s | %s | %s | %s | mô tả %d ký tự | toạ độ %s,%s",
                record.get("listing_id"),
                (record.get("title") or "")[:40],
                record.get("price_text"),
                record.get("address"),
                len(record.get("description") or ""),
                record.get("latitude"),
                record.get("longitude"),
            )


def main() -> None:
    args = build_parser().parse_args()
    logger = get_logger("crawl_mogi")

    if args.dry_run:
        dry_run(logger)
        return

    districts = args.districts or list(config.MOGI_DISTRICT_PATHS)
    unknown = [d for d in districts if d not in config.MOGI_DISTRICT_PATHS]
    if unknown:
        raise SystemExit(f"chưa có đường dẫn mogi cho: {unknown}. Bổ sung vào src/config.py")

    params = {
        "max_per_district": args.max_per_district,
        "districts": districts,
        "resume": not args.no_resume,
    }

    with RunManifest("crawl_mogi", params=params) as manifest:
        with PoliteSession(logger=logger) as session:
            total = 0
            for district in districts:
                stats = crawl_district(
                    session,
                    district,
                    max_listings=args.max_per_district,
                    resume=not args.no_resume,
                    logger=logger,
                )
                total += stats["written"]
                for key, value in stats.items():
                    manifest.count(f"{slugify(district)}__{key}", value)
            manifest.count("written_total", total)
            manifest.count("http_requests", session.stats["requests"])

    logger.info("xong: ghi thêm %d tin", total)


if __name__ == "__main__":
    main()
