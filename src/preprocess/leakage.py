"""T2.15 — xoá dấu vết giá khỏi văn bản trước khi vector hoá.

Gần như tin rao nào cũng nhắc lại giá trong mô tả ("giá chỉ 5,2 tỷ"). Để nguyên rồi
chạy TF-IDF thì mô hình không học định giá bất động sản, nó học đọc lại con số trong
mô tả. Kết quả sẽ rất đẹp và hoàn toàn vô dụng.

Hàm `verify_no_money_tokens` là chốt chặn thứ hai: sau khi fit TF-IDF, nó soi lại các
đặc trưng có trọng số cao nhất xem còn token tiền tệ nào sống sót không. Một luật lọc
tự nhận là sạch mà không có phép kiểm độc lập thì không đáng tin.
"""

from __future__ import annotations

import re

PRICE_PLACEHOLDER = " GIÁTIỀN "

# Cụm tiền tệ tiếng Việt, kể cả biến thể có đơn vị theo m² hoặc theo tháng.
# Đơn giá theo m² phải đứng ĐẦU danh sách và không được đòi ranh giới từ sau đơn vị:
# sau khi tách từ, "110 triệu/m2" mất dấu gạch chéo và dính thành "110 triệum2". Mẫu
# nào yêu cầu \b sau "triệu" sẽ trượt đúng những dòng nguy hiểm nhất, vì đơn giá nhân
# diện tích ra thẳng nhãn.
MONEY_PATTERNS = [
    re.compile(r"\d+[.,]?\d*\s*(?:tỷ|tỉ|triệu|trieu|tr)\s*/?\s*m\s*[²2]", re.IGNORECASE),
    re.compile(r"\d+[.,]?\d*\s*(?:tỷ|tỉ|ty|ti)\s*\d*\s*(?:triệu|trieu|tr)?", re.IGNORECASE),
    re.compile(r"\d+[.,]?\d*\s*(?:triệu|trieu|tr|củ|cu)\b", re.IGNORECASE),
    re.compile(r"\d{9,}\s*(?:đ|vnd|vnđ|đồng|dong)?", re.IGNORECASE),
    re.compile(r"\d{4,}\s*(?:đ|vnd|vnđ|đồng|dong)\b", re.IGNORECASE),
    re.compile(r"\bgiá\s*[:\-]?\s*\d+[.,]?\d*", re.IGNORECASE),
]

# Token còn sót lại sau khi lọc thì coi là thất bại: dùng cho phép kiểm ngược.
# Tên đơn vị tiền tệ trần ("đồng", "vnd") chỉ tính là tiền khi đi sau một số từ 4 chữ
# số trở lên. Không có ràng buộc đó thì phép kiểm kêu nhầm ở hai chỗ rất phổ biến:
# "74 Đồng Đen" là số nhà trên một con đường ở Tân Bình, và "đường 10 đồng bộ" là mô tả
# hạ tầng. Một phép kiểm hay kêu nhầm sẽ sớm bị bỏ qua, tức là mất hẳn tác dụng.
MONEY_TOKEN = re.compile(
    r"(?:^|\W)(?:\d+[.,]?\d*\s*(?:tỷ|tỉ|ty\b|ti\b|triệu|trieu|tr\b|củ\b)"
    r"|\d{4,}\s*(?:đồng|vnd|vnđ|đ)\b)",
    re.IGNORECASE,
)


MAX_PASSES = 4


def strip_price_mentions(text: str | None) -> str:
    """Thay mọi cụm tiền bằng một placeholder duy nhất.

    Dùng placeholder thay vì xoá trắng để giữ lại thông tin "tin này có nhắc giá" —
    bản thân việc rao giá công khai đã là một tín hiệu, chỉ con số là không được dùng.

    Chạy lặp tới khi văn bản không đổi nữa (tối đa `MAX_PASSES` vòng): xoá một cụm có
    thể làm hai mảnh còn lại dính vào nhau thành một cụm tiền mới ("giá 5,2 tỷ - 6 tỷ"
    sau vòng một còn "GIÁTIỀN - 6 tỷ"). Một vòng duy nhất bỏ sót đúng loại trường hợp
    đó.
    """
    if not text:
        return ""
    cleaned = str(text)
    for _ in range(MAX_PASSES):
        before = cleaned
        for pattern in MONEY_PATTERNS:
            cleaned = pattern.sub(PRICE_PLACEHOLDER, cleaned)
        if cleaned == before:
            break
    return re.sub(r"\s+", " ", cleaned).strip()


def count_money_tokens(text: str | None) -> int:
    return len(MONEY_TOKEN.findall(str(text or "")))


def verify_no_money_tokens(feature_names) -> list[str]:
    """Các đặc trưng TF-IDF còn mang hình dạng tiền tệ. Rỗng nghĩa là đã sạch."""
    return [name for name in feature_names if count_money_tokens(name)]
