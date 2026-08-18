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
MONEY_PATTERNS = [
    re.compile(r"\d+[.,]?\d*\s*(?:tỷ|tỉ|ty|ti)\s*\d*\s*(?:triệu|trieu|tr)?", re.IGNORECASE),
    re.compile(r"\d+[.,]?\d*\s*(?:triệu|trieu|tr|củ|cu)\b", re.IGNORECASE),
    re.compile(r"\d+[.,]?\d*\s*(?:tỷ|tỉ|triệu|trieu|tr)\s*/\s*m\s*[²2]", re.IGNORECASE),
    re.compile(r"\d{9,}\s*(?:đ|vnd|vnđ|đồng|dong)?", re.IGNORECASE),
    re.compile(r"\d+[.,]?\d*\s*(?:đ|vnd|vnđ|đồng|dong)\b", re.IGNORECASE),
    re.compile(r"\bgiá\s*[:\-]?\s*\d+[.,]?\d*", re.IGNORECASE),
]

# Token còn sót lại sau khi lọc thì coi là thất bại: dùng cho phép kiểm ngược.
MONEY_TOKEN = re.compile(
    r"(?:^|\W)(?:\d+[.,]?\d*\s*(?:tỷ|tỉ|ty\b|ti\b|triệu|trieu|tr\b|củ\b|vnd|vnđ|đồng))",
    re.IGNORECASE,
)


def strip_price_mentions(text: str | None) -> str:
    """Thay mọi cụm tiền bằng một placeholder duy nhất.

    Dùng placeholder thay vì xoá trắng để giữ lại thông tin "tin này có nhắc giá" —
    bản thân việc rao giá công khai đã là một tín hiệu, chỉ con số là không được dùng.
    """
    if not text:
        return ""
    cleaned = str(text)
    for pattern in MONEY_PATTERNS:
        cleaned = pattern.sub(PRICE_PLACEHOLDER, cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def count_money_tokens(text: str | None) -> int:
    return len(MONEY_TOKEN.findall(str(text or "")))


def verify_no_money_tokens(feature_names) -> list[str]:
    """Các đặc trưng TF-IDF còn mang hình dạng tiền tệ. Rỗng nghĩa là đã sạch."""
    return [name for name in feature_names if count_money_tokens(name)]
