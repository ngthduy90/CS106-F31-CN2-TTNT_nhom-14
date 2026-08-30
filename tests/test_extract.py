"""Kiểm tra bộ trích xuất số tầng.

Sau khi bỏ dấu, các từ đơn vị tầng va vào từ cực kỳ thường gặp trong tin rao:
"tắm" → "tam", "lâu" → "lau", "mẹ" → "me". Bộ test này ghim cả hai chiều: ca thật
vẫn ra đúng số, ca boilerplate không được bịa ra tầng nào.
"""

import pytest

from src.preprocess.extract import extract_floors, strip_accents

REAL = [
    ("1 trệt 2 lầu", 3),
    ("trệt lửng 2 lầu", 4),
    ("nhà 3 tầng", 3),
    ("nhà lầu", 2),
    ("nhà đúc 3 tấm", 4),
    ("tám lầu", 9),
    ("nhà cấp 4", 1),
]

FABRICATED = [
    "Nhà 1 trệt, 2 phòng ngủ, 1 phòng tắm",   # "phòng tắm" → tam
    "Bán đất mặt tiền, sử dụng lâu dài",       # "lâu dài" → lau
    "Nhà 2 mẹ con cần bán gấp",                # "mẹ con" → me
    "nhà ba mẹ để lại",                        # "ba mẹ" → ba + me
    "Nhà xây lâu năm cần bán",                 # "lâu năm" → lau
]


@pytest.mark.parametrize("text,expected", REAL, ids=[c[0] for c in REAL])
def test_dem_dung_so_tang_that(text, expected):
    assert extract_floors(strip_accents(text)) == expected


@pytest.mark.parametrize("text", FABRICATED)
def test_khong_biadat_so_tang_tu_boilerplate(text):
    floors = extract_floors(strip_accents(text))
    assert floors is None or floors == 1, f"bịa ra {floors} tầng từ {text!r}"
