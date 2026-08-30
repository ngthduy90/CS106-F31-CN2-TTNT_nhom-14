"""Kiểm tra tách địa chỉ và chuẩn hoá phường.

Hai lớp lỗi được ghim ở đây, cả hai đều sinh ra giá trị BỊA trông đủ thật để không
check nào phía sau bắt được: cổng nhận phường bỏ sót cách viết "P.13" trong khi nuốt
nhầm "Xa lộ", và normalise_ward gắn "Phường " vào bất kỳ phần dư nào, kể cả sentinel
"không rõ".
"""

import pytest

from src.preprocess.address import UNKNOWN, normalise_ward, parse_address


@pytest.mark.parametrize(
    "text,ward",
    [
        ("Trường Chinh, P.13, Quận Tân Bình, TPHCM", "Phường 13"),
        ("Trường Chinh, P13, Quận Tân Bình", "Phường 13"),
        ("Trường Chinh, Phường Tân Thới Nhất, Quận 12", "Phường Tân Thới Nhất"),
        ("Đường số 7, Xã Bà Điểm, Hóc Môn", "Phường Bà Điểm"),
        ("Đường số 7, X. Bà Điểm, Hóc Môn", "Phường Bà Điểm"),
    ],
)
def test_nhan_dung_phuong(text, ward):
    assert parse_address(text).ward == ward


def test_xa_lo_khong_bi_nham_thanh_phuong():
    """"Xã" và "Xa" giống nhau sau khi bỏ dấu: "Xa lộ Hà Nội" từng ra phường bịa."""
    address = parse_address("Xa lộ Hà Nội, Phường Thảo Điền, Quận 2")
    assert address.ward == "Phường Thảo Điền"
    assert address.street == "Xa lộ Hà Nội"


@pytest.mark.parametrize("text", [None, "", "   ", UNKNOWN, "TP.HCM", "TPHCM", "Việt Nam"])
def test_normalise_ward_co_duong_that_bai(text):
    """Phần dư không phải tên phường thì trả UNKNOWN, không mint hạng mục giả."""
    assert normalise_ward(text) == UNKNOWN


def test_normalise_ward_giu_nguyen_hanh_vi_dung():
    assert normalise_ward("13") == "Phường 13"
    assert normalise_ward("P.13") == "Phường 13"
    assert normalise_ward("Thảo Điền") == "Phường Thảo Điền"
