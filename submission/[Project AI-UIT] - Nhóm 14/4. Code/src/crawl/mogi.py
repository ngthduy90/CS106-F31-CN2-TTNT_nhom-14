"""Crawler mogi.vn (nguồn chính #2) — HTML render sẵn phía máy chủ.

Hai bước theo runbook 01 §4: trang danh sách cho ra URL tin (15 tin/trang, phân trang
bằng tham số `cp`), trang chi tiết cho ra đủ trường. BeautifulSoup là đủ, không cần
trình duyệt headless.

Ranh giới đã kiểm ngày 2026-08-19 từ chính robots.txt của trang (bản chụp trong
`docs/robots-snapshots/`): cấm `/api/`, `/Property/`, `/template/`, `/MarketPrice/`,
`/trang-ca-nhan/`. Đường dẫn danh sách và trang chi tiết đều nằm ngoài các nhánh này.

Trang chi tiết có khối JSON-LD kiểu Person chứa TÊN và SỐ ĐIỆN THOẠI người bán. Parser
chỉ lấy đúng hai thứ trong khối đó — giá dạng số và mô tả — rồi bỏ phần còn lại; kho
thô không bao giờ thấy khối đó nguyên vẹn.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any, Iterator

from bs4 import BeautifulSoup

from src import config
from src.crawl.http import PoliteSession
from src.crawl.store import Checkpoint, RawStore

BASE = "https://mogi.vn"
SOURCE = "mogi"
ID_FIELD = "listing_id"
PER_PAGE = 15  # số tin trang danh sách trả về, đo ngày 2026-08-19

_ID_IN_URL = re.compile(r"-id(\d+)(?:$|[/?#])")
_COORDS_IN_MAP = re.compile(r"maps/embed/v1/place[^\"']*?[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)")
_NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")


def listing_id(url: str) -> str | None:
    """Mã tin nằm ở đuôi URL dạng `-id22747715`; đây là khoá khử trùng lặp."""
    match = _ID_IN_URL.search(url)
    return match.group(1) if match else None


def _text(node: Any) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _first_number(text: str) -> float | None:
    match = _NUMBER.search(text.replace(".", "").replace(",", "."))
    return float(match.group(0)) if match else None


# --- bước 1: trang danh sách -------------------------------------------------


def parse_list_page(markup: str) -> list[dict[str, Any]]:
    """Rút URL tin + vài trường tóm tắt từ một trang danh sách."""
    soup = BeautifulSoup(markup, "lxml")
    results: list[dict[str, Any]] = []

    for block in soup.select("div.prop-info"):
        link = block.select_one("a.link-overlay[href]")
        if not link:
            continue
        url = link["href"]
        if not listing_id(url):
            continue
        results.append(
            {
                "url": url if url.startswith("http") else f"{BASE}{url}",
                "title": _text(block.select_one(".prop-title")),
                "address_summary": _text(block.select_one(".prop-addr")),
                "price_text_list": _text(block.select_one(".price")),
            }
        )
    return results


def iter_listing_urls(
    session: PoliteSession,
    district: str,
    max_urls: int,
    start_page: int = 1,
    logger=None,
) -> Iterator[tuple[dict[str, Any], int]]:
    """Sinh (tóm tắt tin, số trang vừa đọc) cho tới khi đủ max_urls hoặc hết trang."""
    path = config.MOGI_DISTRICT_PATHS[district]
    page = start_page
    taken = 0

    while taken < max_urls:
        url = f"{BASE}/{path}" + (f"?cp={page}" if page > 1 else "")
        summaries = parse_list_page(session.get(url).text)
        if logger:
            logger.info("%s trang %d → %d tin", district, page, len(summaries))
        if not summaries:
            break

        for summary in summaries:
            if taken >= max_urls:
                break
            taken += 1
            yield summary, page

        page += 1


# --- bước 2: trang chi tiết --------------------------------------------------

# Nhãn hàng thuộc tính trên trang chi tiết → tên trường trong kho thô.
ATTR_LABELS = {
    "diện tích sử dụng": "usable_area_text",
    "diện tích đất": "land_area_text",
    "diện tích": "area_text",
    "mặt tiền": "frontage_text",
    "đường vào": "road_width_text",
    "phòng ngủ": "bedrooms_text",
    "nhà tắm": "bathrooms_text",
    "số tầng": "floors_text",
    "hướng": "direction",
    "pháp lý": "legal_status",
    "ngày đăng": "posted_at_text",
    "mã bđs": "listing_code",
}


def _person_offer(soup: BeautifulSoup) -> dict[str, Any]:
    """Giá dạng số và mô tả từ khối JSON-LD, bỏ toàn bộ thông tin người bán."""
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or ""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(data, dict) or data.get("@type") != "Person":
            continue

        offer = data.get("makesOffer") or {}
        spec = offer.get("priceSpecification") or {}
        item = offer.get("itemOffered") or {}
        description = html.unescape(re.sub(r"<br\s*/?>", "\n", str(item.get("description") or "")))
        return {
            "price_vnd_ld": spec.get("price"),
            "property_type_ld": item.get("@type"),
            "description_ld": description.strip(),
        }
    return {}


def parse_detail_page(markup: str, url: str) -> dict[str, Any]:
    """Một tin đầy đủ. Trường nào trang không có thì để trống, không ném lỗi.

    Tin rao trên mogi thiếu trường rất tuỳ hứng (nhà phố có mặt tiền, chung cư không;
    tin cũ không có toạ độ). Parser vì thế bỏ qua từng trường một chứ không đòi cả
    khối phải tồn tại, nếu không một tin lệch chuẩn sẽ làm hỏng cả phiên crawl.
    """
    soup = BeautifulSoup(markup, "lxml")

    record: dict[str, Any] = {
        "listing_id": listing_id(url),
        "url": url,
        "title": _text(soup.select_one("h1")),
        "address": _text(soup.select_one(".address")),
        "price_text": _text(soup.select_one(".main-info .price") or soup.select_one(".price")),
        "description": _text(soup.select_one(".info-content-body")).strip(),
    }

    for row in soup.select(".info-attrs .info-attr"):
        cells = [_text(cell) for cell in row.find_all(["span", "div"], recursive=False)]
        if len(cells) < 2:
            parts = row.get_text("|", strip=True).split("|")
            cells = [parts[0], " ".join(parts[1:])] if len(parts) >= 2 else parts
        if len(cells) < 2:
            continue
        label = cells[0].strip().lower().rstrip(":")
        field = ATTR_LABELS.get(label)
        if field:
            record[field] = " ".join(cells[1:]).strip()

    coords = _COORDS_IN_MAP.search(markup)
    if coords:
        record["latitude"] = float(coords.group(1))
        record["longitude"] = float(coords.group(2))

    record.update(_person_offer(soup))

    # Mô tả trong JSON-LD giữ được xuống dòng, bản trong HTML thì không; lấy bản dài hơn.
    if len(record.get("description_ld") or "") > len(record.get("description") or ""):
        record["description"] = record.pop("description_ld")
    else:
        record.pop("description_ld", None)

    return record


def crawl_district(
    session: PoliteSession,
    district: str,
    max_listings: int,
    resume: bool = True,
    logger=None,
) -> dict[str, int]:
    """Crawl một quận: quét danh sách rồi tải từng trang chi tiết chưa có trong kho."""
    store = RawStore(SOURCE, district, ID_FIELD)
    checkpoint = Checkpoint(SOURCE, district)
    start_page = int(checkpoint.get("page", 1)) if resume else 1

    seen_before = set(store.seen_ids)
    detail_errors = 0
    scanned = 0

    for summary, page in iter_listing_urls(
        session, district, max_urls=max_listings * 3, start_page=start_page, logger=logger
    ):
        if store.written >= max_listings:
            break
        scanned += 1
        code = listing_id(summary["url"])
        if code in seen_before:
            continue

        try:
            markup = session.get(summary["url"]).text
        except Exception as exc:  # noqa: BLE001 — một tin hỏng không được giết cả phiên
            detail_errors += 1
            if logger:
                logger.warning("bỏ qua %s: %s", summary["url"], exc)
            continue

        record = parse_detail_page(markup, summary["url"])
        record["price_text_list"] = summary["price_text_list"]
        record["address_summary"] = summary["address_summary"]
        store.append(record, source_url=summary["url"])
        checkpoint.save(page=page, written_total=store.written)

    stats = {
        "scanned": scanned,
        "written": store.written,
        "skipped_duplicate": store.skipped_duplicate,
        "detail_errors": detail_errors,
        "pii_redactions": store.pii_redactions,
    }
    if logger:
        logger.info("%s: %s", district, stats)
    return stats
