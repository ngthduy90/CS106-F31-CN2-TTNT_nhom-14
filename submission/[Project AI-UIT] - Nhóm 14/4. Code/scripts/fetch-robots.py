"""T1.10 — lưu ảnh chụp robots.txt của mọi host đã crawl hoặc đã cân nhắc.

Báo cáo phần đạo đức phải trích được nguyên văn quy tắc của từng trang TẠI THỜI ĐIỂM
crawl. Trang có thể sửa robots.txt bất kỳ lúc nào, nên câu "chúng tôi tôn trọng
robots.txt" chỉ có sức nặng khi kèm bản chụp có ngày giờ.

    python scripts/fetch-robots.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config
from src.crawl.http import PoliteSession
from src.utils.logging_setup import get_logger

HOSTS = {
    "nhatot.com": "https://www.nhatot.com/robots.txt",
    "gateway.chotot.com": "https://gateway.chotot.com/robots.txt",
    "mogi.vn": "https://mogi.vn/robots.txt",
    "alonhadat.com.vn": "https://alonhadat.com.vn/robots.txt",
    "homedy.com": "https://homedy.com/robots.txt",
}


def main() -> None:
    logger = get_logger("fetch_robots")
    target = config.DOCS / "robots-snapshots"
    target.mkdir(parents=True, exist_ok=True)

    with PoliteSession(logger=logger) as session:
        for host, url in HOSTS.items():
            stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            try:
                body = session.get(url).text
                header = f"# nguồn: {url}\n# thời điểm tải: {stamp}\n# HTTP 200\n\n"
            except Exception as exc:  # noqa: BLE001 — ghi lại chính lỗi đó cũng là dữ liệu
                body = ""
                header = f"# nguồn: {url}\n# thời điểm tải: {stamp}\n# KHÔNG TẢI ĐƯỢC: {exc}\n\n"
                logger.warning("%s: %s", host, exc)

            path = target / f"{host}.robots.txt"
            path.write_text(header + body, encoding="utf-8")
            logger.info("%s → %s (%d ký tự)", host, path.name, len(body))


if __name__ == "__main__":
    main()
