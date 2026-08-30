"""Kiểm tra bộ xoá thông tin cá nhân.

Mỗi ca trong OBFUSCATIONS là một kiểu nguỵ trang số điện thoại thật sự gặp trong tin
rao bất động sản. NEGATIVES là các dãy số PHẢI được giữ nguyên (giá, diện tích, ngày
tháng, mã tin) — xoá nhầm chúng là làm hỏng dữ liệu huấn luyện.
"""

import pytest

from src.crawl.pii import (
    REDACTION,
    contains_phone,
    find_phones,
    scrub_record,
    scrub_text,
)

# 14 kiểu nguỵ trang, đủ phủ yêu cầu "≥ 12 pattern" của T1.7.
OBFUSCATIONS = [
    ("thường", "Liên hệ 0901234567 xem nhà"),
    ("cách khoảng trắng", "LH 0901 234 567 chính chủ"),
    ("dấu chấm", "sđt 0901.234.567"),
    ("gạch nối", "Call 0901-234-567 gặp Ms Lan"),
    ("mã quốc gia", "Zalo +84 901 234 567"),
    ("mã quốc gia không dấu cộng", "hotline 84901234567"),
    ("dấu sao chèn giữa", "SDT: 0901*234*567"),
    ("ngoặc đơn", "Điện thoại (028) 3822 1234"),
    ("chữ O thay số 0", "LH O9O1234567 xem nhà ngay"),
    ("chữ l thay số 1", "lh 09Ol234567"),
    ("ký tự vô hình", "sdt 0901​234​567"),
    ("chữ số Unicode", "lien he ٠٩٠١٢٣٤٥٦٧"),
    ("emoji keycap", "gọi 0️⃣9️⃣0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣ nhé"),
    ("viết bằng chữ", "liên hệ không chín không một hai ba bốn năm sáu bảy"),
]

NEGATIVES = [
    "Nhà 2 tầng, diện tích 4x15 = 60m2, giá 5,2 tỷ",
    "Giá 3.500.000.000 đồng, thương lượng",
    "Đăng ngày 01.02.2026, sổ hồng riêng",
    "Hẻm 6m thông, cách chợ 300m, xây năm 2018",
    "Mặt tiền đường Trường Chinh, ngang 4m dài 15m",
    "Căn hộ 2PN 2WC, 68m2, ban công hướng Đông Nam",
]


@pytest.mark.parametrize("label,text", OBFUSCATIONS, ids=[c[0] for c in OBFUSCATIONS])
def test_bat_duoc_moi_kieu_nguy_trang(label, text):
    clean, count = scrub_text(text)
    assert count >= 1, f"{label}: không phát hiện số điện thoại trong {text!r}"
    assert REDACTION in clean
    assert not contains_phone(clean), f"{label}: còn số sót lại trong {clean!r}"


@pytest.mark.parametrize("text", NEGATIVES)
def test_khong_xoa_nham_so_khac(text):
    clean, count = scrub_text(text)
    assert count == 0, f"xoá nhầm {find_phones(text)} trong {text!r}"
    assert clean == text


def test_giu_nguyen_phan_van_ban_con_lai():
    clean, _ = scrub_text("Nhà 60m2, giá 5,2 tỷ, LH 0901234567 gặp chủ")
    assert clean == f"Nhà 60m2, giá 5,2 tỷ, LH {REDACTION} gặp chủ"


def test_nhieu_so_trong_mot_tin():
    clean, count = scrub_text("Gọi 0901234567 hoặc 0987654321")
    assert count == 2
    assert clean.count(REDACTION) == 2


def test_bo_truong_ca_nhan():
    record = {
        "list_id": 123,
        "subject": "Bán nhà Tân Bình, LH 0901234567",
        "body": "Nhà 60m2 giá 5,2 tỷ",
        "account_name": "Nguyễn Văn A",
        "account_id": 9876,
        "phone": "0901234567",
        "avatar": "https://example.com/a.jpg",
    }
    clean, count = scrub_record(record)

    assert set(clean) == {"list_id", "subject", "body"}
    assert count == 1
    assert REDACTION in clean["subject"]
    assert clean["body"] == record["body"]
    assert "account_name" in record, "bản ghi gốc không được sửa tại chỗ"


def test_bo_truong_ca_nhan_long_nhau():
    record = {"ad": {"seller_info": {"phone": "0901234567"}, "body": "sdt 0909888777"}}
    clean, count = scrub_record(record)

    assert clean == {"ad": {"body": f"sdt {REDACTION}"}}
    assert count == 1


def test_contains_phone_quet_ca_bang_ghi():
    assert contains_phone({"a": ["x", {"b": "lh 0901234567"}]})
    assert not contains_phone({"a": ["x", {"b": "giá 5,2 tỷ"}]})
