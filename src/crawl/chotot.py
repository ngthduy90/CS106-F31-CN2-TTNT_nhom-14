"""Client Chợ Tốt (nguồn chính #1) — gateway API công khai, trả JSON sạch.

Quyết định kỹ thuật đáng ghi lại: API danh sách đã trả về `body` ĐẦY ĐỦ (đã đối chiếu
với endpoint chi tiết trên cùng một tin ngày 2026-08-19, độ dài khớp nhau), nên crawler
KHÔNG gọi trang chi tiết. Một request lấy được 20 tin thay vì 1, giảm tải cho máy chủ
bên kia khoảng 20 lần và rút thời gian crawl xuống tương ứng. Endpoint chi tiết còn
kèm cả trường `phone`, thêm một lý do để không đụng vào.

API có trần hiển thị total = 10.000 nên phải quét theo từng quận (`area_v2`) thay vì
cả thành phố, đúng như runbook 01 §3.1.
"""

from __future__ import annotations

from typing import Any, Iterator

from src import config
from src.crawl.http import PoliteSession
from src.crawl.store import Checkpoint, RawStore

LISTING_URL = "https://gateway.chotot.com/v1/public/ad-listing"
AD_URL_TEMPLATE = "https://www.nhatot.com/mua-ban-nha-dat/{list_id}.htm"

PAGE_SIZE = 20  # API trả tối đa 20 tin/lần
SOURCE = "chotot"
ID_FIELD = "list_id"

# Trường được giữ lại (runbook 01 §3.3). Danh sách là whitelist chứ không phải
# blacklist: API thêm trường mới lúc nào không báo, và trường mới có thể là dữ liệu cá
# nhân. Không có trong danh sách này thì không vào kho thô.
KEEP_FIELDS = (
    "list_id",
    "ad_id",
    "subject",
    "body",
    "price",
    "price_string",
    "price_million_per_m2",   # chỉ để đối chiếu, KHÔNG dùng làm đặc trưng (leakage)
    "size",
    "living_size",
    "width",
    "length",
    "rooms",
    "toilets",
    "floors",
    "direction",
    "house_type",
    "property_legal_document",
    "furnishing_sell",
    "category",
    "category_name",
    "region_v2",
    "region_name",
    "area_v2",
    "area_name",
    "ward",
    "ward_name",
    "ward_name_v3",           # tên phường theo hệ MỚI sau sáp nhập 2025
    "street_name",
    "latitude",
    "longitude",
    "list_time",
    "orig_list_time",
    "date",
    "company_ad",
    "type",
    "state",
)


def parse_ad(raw: dict[str, Any]) -> dict[str, Any]:
    """Rút gọn tin thô về đúng các trường cần giữ, giá trị để nguyên như API trả."""
    return {field: raw.get(field) for field in KEEP_FIELDS if field in raw}


def fetch_page(
    session: PoliteSession, area_code: int, offset: int, limit: int = PAGE_SIZE
) -> tuple[list[dict[str, Any]], int]:
    """Một trang tin bán của một quận. Trả về (danh sách tin, tổng số tin của quận)."""
    params = {
        "cg": config.CHOTOT_CATEGORY_SALE,
        "st": config.CHOTOT_STATUS_SELLING,
        "region_v2": config.CHOTOT_REGION_HCMC,
        "area_v2": area_code,
        "limit": limit,
        "o": offset,
    }
    payload = session.get(LISTING_URL, params=params).json()
    return payload.get("ads", []), int(payload.get("total", 0))


def iter_district(
    session: PoliteSession,
    area_code: int,
    max_ads: int,
    start_offset: int = 0,
    logger=None,
) -> Iterator[tuple[dict[str, Any], int]]:
    """Sinh (tin, offset sau khi lấy tin đó) cho tới khi hết trang hoặc đủ max_ads.

    Trả kèm offset để nơi gọi ghi checkpoint sau mỗi tin: lần chạy sau tiếp tục đúng
    chỗ đã dừng, kể cả khi tiến trình bị giết giữa chừng.
    """
    offset = start_offset
    taken = 0

    while taken < max_ads:
        limit = min(PAGE_SIZE, max_ads - taken)
        ads, total = fetch_page(session, area_code, offset, limit)
        if logger:
            logger.info(
                "area %s offset %d → %d tin (tổng sàn báo %d)",
                area_code,
                offset,
                len(ads),
                total,
            )
        if not ads:
            break

        for raw in ads:
            offset += 1
            taken += 1
            yield parse_ad(raw), offset

        if offset >= total:
            break


# Số tin liên tiếp ĐÃ CÓ trong kho đủ để kết luận đã chạm phần cũ của danh sách.
STOP_AFTER_SEEN = 120


def crawl_district(
    session: PoliteSession,
    district: str,
    area_code: int,
    max_ads: int,
    resume: bool = True,
    logger=None,
) -> dict[str, int]:
    """Crawl một quận vào kho thô. Trả về thống kê của quận đó."""
    store = RawStore(SOURCE, district, ID_FIELD)
    checkpoint = Checkpoint(SOURCE, district)
    if not resume:
        checkpoint.reset()

    # Con trỏ resume cũ là VỊ TRÍ trong một tập kết quả sống, và không bao giờ được
    # reset. Hai hệ quả: quận đã cạn lưu offset == total nên mọi lần chạy sau bắt đầu
    # đúng chỗ hết tin và ghi 0 tin mới vĩnh viễn; và giữa hai lần chạy, tin mới đăng
    # đẩy tập kết quả trượt đi nên resume tại offset N rơi vào tin cũ thứ N-k và không
    # bao giờ thấy k tin mới nhất. Dedup theo list_id đã bảo đảm quét lại từ đầu là an
    # toàn tuyệt đối, nên quét từ 0 và dừng sau một chuỗi tin đã có trong kho.
    seen_before = set(store.seen_ids)
    consecutive_seen = 0

    for ad, _offset in iter_district(session, area_code, max_ads * 3, 0, logger):
        # max_ads đếm tin GHI ĐƯỢC, đúng như help text, chứ không phải tin fetch về.
        if store.written >= max_ads:
            break
        if str(ad.get("list_id")) in seen_before:
            consecutive_seen += 1
            if resume and consecutive_seen >= STOP_AFTER_SEEN:
                if logger:
                    logger.info(
                        "%s: %d tin liên tiếp đã có trong kho → dừng sớm",
                        district, consecutive_seen,
                    )
                break
            continue
        consecutive_seen = 0
        url = AD_URL_TEMPLATE.format(list_id=ad.get("list_id"))
        store.append(ad, source_url=url)
        checkpoint.save(written_total=store.written)

    stats = {
        "written": store.written,
        "skipped_duplicate": store.skipped_duplicate,
        "pii_redactions": store.pii_redactions,
    }
    if logger:
        logger.info("%s: %s", district, stats)
    return stats
