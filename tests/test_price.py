"""Kiểm tra bộ chuẩn hoá giá.

Các chuỗi trong CASES lấy từ chính dữ liệu crawl ngày 2026-08-19 (trường
`price_string` của Chợ Tốt và `price_text` của mogi), không phải ví dụ tự nghĩ ra.
"""

import pytest

from src.preprocess.price import (
    TY,
    cross_check,
    looks_like_rental,
    normalise_numeric_price,
    parse_price,
)

# (chuỗi, diện tích m², tổng giá VND kỳ vọng)
CASES = [
    ("5 tỷ 2", None, 5_200_000_000),
    ("5,2 tỷ", None, 5_200_000_000),
    ("5 tỷ 200 triệu", None, 5_200_000_000),
    ("5200 triệu", None, 5_200_000_000),
    ("52 triệu/m²", 100, 5_200_000_000),
    ("52 triệu/m2", 100, 5_200_000_000),
    ("115 triệu/m2", 120, 13_800_000_000),
    ("8,8 tỷ", None, 8_800_000_000),
    ("2,4 tỷ", None, 2_400_000_000),
    ("4,85 tỷ", None, 4_850_000_000),
    ("2,79 tỷ", None, 2_790_000_000),
    ("6.79 tỷ", None, 6_790_000_000),
    ("8.2 tỷ", None, 8_200_000_000),
    ("9,5 tỷ", None, 9_500_000_000),
    ("120 tỷ", None, 120_000_000_000),
    ("2 tỷ 200 triệu", None, 2_200_000_000),
    ("3 tỷ 550 triệu", None, 3_550_000_000),
    ("4 tỷ 350 triệu", None, 4_350_000_000),
    ("7 tỷ 200 triệu", None, 7_200_000_000),
    ("890 triệu", None, 890_000_000),
    ("690 triệu", None, 690_000_000),
    ("1,2 tỉ", None, 1_200_000_000),
    ("5 tỷ 25", None, 5_250_000_000),
    ("10,6 tỷ", None, 10_600_000_000),
    ("13900000000", None, 13_900_000_000),
    ("4ty9", None, 4_900_000_000),
    ("2 tỷ 500 triệu", None, 2_500_000_000),
    ("5,7 tỷ", None, 5_700_000_000),
    ("nhinh 6 tỷ", None, 6_000_000_000),
    ("giá 9.29 tỷ", None, 9_290_000_000),
]

MISSING_CASES = ["thoả thuận", "thỏa thuận", "Giá liên hệ", "thương lượng", "", None]


@pytest.mark.parametrize("text,area,expected", CASES, ids=[c[0] or "rỗng" for c in CASES])
def test_parse_dung_30_chuoi_gia_that(text, area, expected):
    assert parse_price(text, area_m2=area).total_vnd == expected


@pytest.mark.parametrize("text", MISSING_CASES)
def test_gia_thoa_thuan_la_nhan_thieu(text):
    assert parse_price(text).total_vnd is None


def test_don_gia_khong_co_dien_tich_thi_khong_bia_tong_gia():
    parsed = parse_price("52 triệu/m²", area_m2=None)
    assert parsed.total_vnd is None
    assert parsed.unit_vnd_per_m2 == 52_000_000


def test_gia_0_va_1_coi_nhu_khong_cong_bo():
    assert normalise_numeric_price(0) is None
    assert normalise_numeric_price(1) is None
    assert normalise_numeric_price(5_200_000_000) == 5_200_000_000


def test_kiem_cheo_tong_gia_voi_don_gia():
    ok, deviation = cross_check(5.2 * TY, 52_000_000, 100)
    assert ok and deviation == pytest.approx(0.0)

    ok, deviation = cross_check(3.0 * TY, 52_000_000, 100)
    assert not ok and deviation > 0.4

    # Thiếu dữ liệu để đối chiếu thì không được gắn cờ đỏ.
    assert cross_check(5.2 * TY, None, 100) == (True, None)


def test_nhan_ra_tin_cho_thue():
    assert looks_like_rental("Cho thuê nhà nguyên căn", None)
    assert looks_like_rental("Giá 15 triệu/tháng", None)
    assert looks_like_rental("Bán nhà", 20_000_000)  # dưới cận dưới giá bán
    assert not looks_like_rental("Bán nhà Tân Bình 60m2", 5_200_000_000)
