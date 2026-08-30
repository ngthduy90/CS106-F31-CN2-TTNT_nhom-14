"""T2.1 — ba nguồn về một bảng duy nhất.

Mỗi nguồn có lược đồ riêng, nhưng mô hình chỉ ăn được một bảng. Quy tắc gộp:

1. **Trường có cấu trúc thắng trường trích từ văn bản.** Người bán điền form thì con
   số đó là ý định của họ; regex chỉ dùng để lấp chỗ trống. Cột `*_from_text` ghi lại
   giá trị nào đến từ đường nào, để báo cáo nói được văn bản đóng góp bao nhiêu.
2. **Giá luôn chạy qua bộ parse**, kể cả khi nguồn đã trả số, vì "0"/"1" là quy ước
   "không công bố" chứ không phải giá thật.
3. **Cột `source` và `collected_at` bắt buộc có ở mọi dòng.** Runbook 03 §4 cấm trộn
   mù hai nguồn; muốn tách được thì cờ nguồn phải đi cùng dữ liệu từ đầu.
"""

from __future__ import annotations

import pandas as pd

from src import config
from src.crawl.store import iter_raw
from src.preprocess.address import UNKNOWN, WardResolver, normalise_district, normalise_ward, parse_address
from src.preprocess.extract import extract_all
from src.preprocess.price import cross_check, looks_like_rental, normalise_numeric_price, parse_price

# Lược đồ thống nhất. Thứ tự cột cố định để mọi bảng xuất ra đọc giống nhau.
SCHEMA = [
    "listing_id",
    "source",
    "collected_at",
    "published_at",
    "title",
    "description",
    "total_price_vnd",
    "price_kind",
    "price_mismatch",
    "area_m2",
    "bedrooms",
    "bathrooms",
    "floors",
    "frontage_m",
    "alley_width_m",
    "position",
    "legal_status",
    "direction",
    "property_type",
    "street",
    "ward",
    "district",
    "ward_frame",
    "latitude",
    "longitude",
    "area_from_text",
    "bedrooms_from_text",
    "floors_from_text",
    "is_rental",
]

CHOTOT_LEGAL = {1: "sổ hồng", 2: "hợp đồng mua bán", 3: "giấy tay"}

# API trả hướng nhà dưới dạng mã 1–8 mà không kèm bảng giải mã. Bảng dưới đây suy ra
# từ chính dữ liệu: với mỗi mã, đối chiếu hướng mà bộ trích xuất đọc được trong phần
# mô tả. Cả 8 mã đều cho một hướng chiếm đa số rõ rệt (ví dụ mã 6 → "Đông Nam" 37 lần,
# hướng đứng nhì chỉ 2 lần), nên bảng này là quan sát chứ không phải phỏng đoán.
CHOTOT_DIRECTION = {
    1: "Đông",
    2: "Tây",
    3: "Nam",
    4: "Bắc",
    5: "Đông Bắc",
    6: "Đông Nam",
    7: "Tây Bắc",
    8: "Tây Nam",
}
CHOTOT_HOUSE_TYPE = {1: "Nhà mặt phố", 2: "Nhà ngõ/hẻm", 3: "Nhà phố liền kề", 4: "Biệt thự"}

# Mã loại nhà của Chợ Tốt mang luôn thông tin VỊ TRÍ: "Nhà mặt phố" và "Nhà ngõ/hẻm" là
# hai mức của cùng một trường. Khi quy tên loại về bộ từ vựng chung, thông tin đó không
# được vứt đi mà chuyển sang cột `position` — nơi nó thuộc về. Đây là trường người bán
# chọn trong form nên đáng tin hơn kết quả regex đọc từ mô tả, và theo đúng quy tắc
# "trường có cấu trúc thắng trường trích từ văn bản" của module này.
CHOTOT_POSITION = {1: "mặt tiền", 2: "hẻm"}

# Ba nguồn gọi cùng một loại bất động sản bằng ba bộ từ vựng khác nhau, và mogi thì trả
# thẳng tên kiểu schema.org bằng tiếng Anh. Để nguyên thì one-hot sinh ra 16 cột cho
# khoảng 5 khái niệm, mô hình không chia sẻ được thông tin giữa các nguồn, và giao diện
# demo hiện "Apartment" giữa một màn hình tiếng Việt.
#
# Bảng dưới quy tất cả về 5 loại. Việc gộp "Nhà mặt phố" với "Nhà ngõ/hẻm" không mất
# thông tin: vị trí mặt tiền hay trong hẻm đã có cột `position` riêng.
PROPERTY_TYPE_CANON = {
    # nhà riêng lẻ
    "nha": "Nhà phố",
    "nha mat pho": "Nhà phố",
    "nha ngo/hem": "Nhà phố",
    "nha pho lien ke": "Nhà phố",
    "nha rieng": "Nhà phố",
    "house": "Nhà phố",
    "singlefamilyresidence": "Nhà phố",
    # chung cư
    "can ho/chung cu": "Căn hộ chung cư",
    "can ho chung cu": "Căn hộ chung cư",
    "can ho": "Căn hộ chung cư",
    "apartment": "Căn hộ chung cư",
    # biệt thự
    "biet thu": "Biệt thự",
    "biet thu/nha lien ke": "Biệt thự",
    # đất
    "dat": "Đất",
    "land": "Đất",
    # mặt bằng kinh doanh
    "shophouse": "Mặt bằng kinh doanh",
    "shop": "Mặt bằng kinh doanh",
    "van phong, mat bang kinh doanh": "Mặt bằng kinh doanh",
    "office": "Mặt bằng kinh doanh",
    "store": "Mặt bằng kinh doanh",
}


def canonical_property_type(value: str | None) -> str:
    """Quy tên loại bất động sản của ba nguồn về một bộ từ vựng tiếng Việt duy nhất."""
    if not value:
        return UNKNOWN
    from src.preprocess.address import deaccent

    return PROPERTY_TYPE_CANON.get(deaccent(str(value)), UNKNOWN)


def _pick(structured, from_text, low=None, high=None):
    """Trường có cấu trúc trước, văn bản sau. Trả về (giá trị, có phải từ văn bản không)."""
    for value, from_text_flag in ((structured, False), (from_text, True)):
        if value in (None, "", 0):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if low is not None and not (low <= number <= high):
            continue
        return number, from_text_flag
    return None, False


def _load_chotot(resolver: WardResolver) -> pd.DataFrame:
    rows = []
    for record in iter_raw("chotot"):
        text = f"{record.get('subject') or ''}\n{record.get('body') or ''}"
        found = extract_all(text)

        price = normalise_numeric_price(record.get("price"))
        kind = "trường có cấu trúc"
        if price is None:
            parsed = parse_price(record.get("price_string"), area_m2=record.get("size"))
            price, kind = parsed.total_vnd, parsed.kind

        area, area_text = _pick(record.get("size"), found.area_m2, *config.VALID_AREA_M2)
        unit_price = normalise_numeric_price(record.get("price_million_per_m2"))
        matched, _ = cross_check(price, (unit_price or 0) * 1e6 or None, area)

        ward, district, frame = resolver.resolve(
            ward_old=record.get("ward_name"),
            ward_new=record.get("ward_name_v3"),
            district=record.get("area_name"),
        )
        bedrooms, bedrooms_text = _pick(record.get("rooms"), found.bedrooms, 1, 20)
        floors, floors_text = _pick(record.get("floors"), found.floors, 1, 15)

        rows.append(
            {
                "listing_id": f"chotot-{record.get('list_id')}",
                "source": "chotot",
                "collected_at": record.get("_collected_at"),
                "published_at": pd.to_datetime(record.get("list_time"), unit="ms", errors="coerce"),
                "title": record.get("subject"),
                "description": record.get("body"),
                "total_price_vnd": price,
                "price_kind": kind,
                "price_mismatch": not matched,
                "area_m2": area,
                "bedrooms": bedrooms,
                "bathrooms": _pick(record.get("toilets"), found.bathrooms, 1, 20)[0],
                "floors": floors,
                "frontage_m": _pick(record.get("width"), found.frontage_m, 1.5, 30)[0],
                "alley_width_m": found.alley_width_m,
                "position": CHOTOT_POSITION.get(record.get("house_type"), found.position),
                "legal_status": CHOTOT_LEGAL.get(
                    record.get("property_legal_document"), found.legal_status
                ),
                "direction": CHOTOT_DIRECTION.get(record.get("direction"), found.direction),
                "property_type": canonical_property_type(
                    CHOTOT_HOUSE_TYPE.get(record.get("house_type"))
                    or record.get("category_name")
                ),
                "street": record.get("street_name") or UNKNOWN,
                "ward": ward,
                "district": district,
                "ward_frame": frame,
                "latitude": record.get("latitude"),
                "longitude": record.get("longitude"),
                "area_from_text": area_text,
                "bedrooms_from_text": bedrooms_text,
                "floors_from_text": floors_text,
                "is_rental": looks_like_rental(record.get("subject"), price),
            }
        )
    return pd.DataFrame(rows)


def _load_mogi(resolver: WardResolver) -> pd.DataFrame:
    rows = []
    for record in iter_raw("mogi"):
        text = f"{record.get('title') or ''}\n{record.get('description') or ''}"
        found = extract_all(text)
        address = parse_address(record.get("address"))

        price = normalise_numeric_price(record.get("price_vnd_ld"))
        kind = "JSON-LD"
        if price is None:
            parsed = parse_price(record.get("price_text"), area_m2=found.area_m2)
            price, kind = parsed.total_vnd, parsed.kind

        area_text_field = record.get("usable_area_text") or record.get("land_area_text") or record.get("area_text")
        structured_area = extract_all(area_text_field).area_m2 if area_text_field else None
        area, area_from_text = _pick(structured_area, found.area_m2, *config.VALID_AREA_M2)

        ward, district, frame = resolver.resolve(ward_old=address.ward, district=address.district)
        bedrooms, bedrooms_text = _pick(record.get("bedrooms_text"), found.bedrooms, 1, 20)
        floors, floors_text = _pick(record.get("floors_text"), found.floors, 1, 15)

        rows.append(
            {
                "listing_id": f"mogi-{record.get('listing_id')}",
                "source": "mogi",
                "collected_at": record.get("_collected_at"),
                "published_at": pd.to_datetime(
                    record.get("posted_at_text"), format="%d/%m/%Y", errors="coerce"
                ),
                "title": record.get("title"),
                "description": record.get("description"),
                "total_price_vnd": price,
                "price_kind": kind,
                "price_mismatch": False,
                "area_m2": area,
                "bedrooms": bedrooms,
                "bathrooms": _pick(record.get("bathrooms_text"), found.bathrooms, 1, 20)[0],
                "floors": floors,
                "frontage_m": _pick(record.get("frontage_text"), found.frontage_m, 1.5, 30)[0],
                "alley_width_m": found.alley_width_m,
                "position": found.position,
                "legal_status": record.get("legal_status") or found.legal_status,
                "direction": record.get("direction") or found.direction,
                "property_type": canonical_property_type(record.get("property_type_ld")),
                "street": address.street,
                "ward": ward,
                "district": district,
                "ward_frame": frame,
                "latitude": record.get("latitude"),
                "longitude": record.get("longitude"),
                "area_from_text": area_from_text,
                "bedrooms_from_text": bedrooms_text,
                "floors_from_text": floors_text,
                "is_rental": looks_like_rental(record.get("title"), price),
            }
        )
    return pd.DataFrame(rows)


def _load_hf(path=None, limit: int | None = None) -> pd.DataFrame:
    """Bộ lịch sử. Đã có sẵn cột số nên chỉ cần đổi tên và chuẩn hoá địa danh."""
    source_path = path or config.DATA_EXTERNAL / "hf_hcmc_listings.parquet"
    if not source_path.exists():
        return pd.DataFrame(columns=SCHEMA)

    frame = pd.read_parquet(source_path)
    if limit and len(frame) > limit:
        frame = frame.sample(limit, random_state=config.SEED)

    text = frame["name"].fillna("") + "\n" + frame["description"].fillna("")
    found = [extract_all(value) for value in text]

    out = pd.DataFrame(
        {
            "listing_id": [f"hf-{i}" for i in frame.index],
            "source": "hf",
            "collected_at": None,
            "published_at": frame["published_at"],
            "title": frame["name"],
            "description": frame["description"],
            "total_price_vnd": frame["price"].map(normalise_numeric_price),
            "price_kind": "trường có cấu trúc",
            "price_mismatch": False,
            "area_m2": frame["area"],
            "bedrooms": frame["bedroom_count"],
            "bathrooms": frame["bathroom_count"],
            "floors": frame["floor_count"],
            "frontage_m": frame["frontage_width"],
            "alley_width_m": frame["road_width"],
            "position": [item.position for item in found],
            "legal_status": [item.legal_status for item in found],
            "direction": frame["house_direction"].fillna(UNKNOWN),
            "property_type": [canonical_property_type(v) for v in frame["property_type_name"]],
            "street": frame["street_name"].fillna(UNKNOWN),
            "ward": [normalise_ward(w) for w in frame["ward_name"]],
            "district": [normalise_district(d) for d in frame["district_name"]],
            "ward_frame": "cũ",
            "latitude": None,
            "longitude": None,
            "area_from_text": False,
            "bedrooms_from_text": False,
            "floors_from_text": False,
            "is_rental": [
                looks_like_rental(name, p)
                for name, p in zip(frame["name"], frame["price"].map(normalise_numeric_price))
            ],
        }
    )

    # Bộ lịch sử thiếu số tầng ở 83% dòng; regex lấp được phần nào từ mô tả.
    from_text = pd.Series([item.floors for item in found], index=out.index, dtype="float64")
    missing = out["floors"].isna() & from_text.notna()
    out["floors"] = out["floors"].astype("float64").where(~missing, from_text)
    out["floors_from_text"] = missing
    return out


def load_all(hf_limit: int | None = 40_000, resolver: WardResolver | None = None) -> pd.DataFrame:
    """Bảng gộp của cả ba nguồn, theo đúng thứ tự cột của SCHEMA.

    Nơi gọi truyền *resolver* vào khi cần đọc lại chỉ số chất lượng của bước quy đổi
    phường (`resolver.quality_report()`) — chỉ số đó vô nghĩa nếu không ai đọc.
    """
    resolver = resolver or WardResolver()
    frames = [_load_chotot(resolver), _load_mogi(resolver), _load_hf(limit=hf_limit)]
    frames = [f.dropna(axis=1, how="all") for f in frames if len(f)]
    frame = pd.concat(frames, ignore_index=True)
    for column in SCHEMA:
        if column not in frame.columns:
            frame[column] = None

    # Cột phân loại phải thuần chuỗi: mỗi nguồn trả một kiểu khác nhau (mã số, chuỗi,
    # None) và parquet từ chối ghi cột lẫn kiểu.
    for column in ("position", "legal_status", "direction", "property_type", "street",
                   "ward", "district", "ward_frame", "price_kind"):
        frame[column] = frame[column].fillna(UNKNOWN).astype(str)

    return frame[SCHEMA]
