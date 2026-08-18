"""Xoá dấu vết cá nhân khỏi tin rao, áp dụng NGAY LÚC GHI FILE THÔ.

Hai việc: bỏ hẳn các trường tài khoản người đăng, và xoá số điện thoại lẫn trong
tiêu đề / mô tả. Người rao thường né bộ lọc của sàn nên số điện thoại xuất hiện dưới
đủ kiểu nguỵ trang: chữ số Unicode khác ASCII, emoji keycap, chữ cái thay số
("O9O1..."), viết chữ ("không chín một"), ký tự vô hình chèn giữa. Một chuỗi regex
đơn giản trên văn bản gốc bắt không xuể.

Cách làm: chuẩn hoá văn bản thành một chuỗi "chỉ để dò" (mọi biến thể quy về chữ số
ASCII) nhưng GIỮ bản đồ vị trí ngược về văn bản gốc, dò trên bản chuẩn hoá rồi cắt
đúng đoạn tương ứng trong bản gốc. Nhờ vậy phần văn bản không phải số điện thoại giữ
nguyên từng ký tự.

Nguyên tắc an toàn: thà xoá nhầm một dãy số vô hại còn hơn để lọt một số điện thoại
(Nghị định 13/2023/NĐ-CP; runbook 01 §3.4 và §7.3).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterator

REDACTION = "[SDT_DA_XOA]"

# Trường bị loại thẳng, không bao giờ chạm tới kho thô. Khớp không phân biệt hoa
# thường, áp dụng đệ quy cho dict lồng nhau.
PII_FIELDS = frozenset(
    {
        "account_id",
        "account_name",
        "account_oid",
        "avatar",
        "avatar_url",
        "contact_name",
        "email",
        "owner",
        "owner_name",
        "phone",
        "phone_hidden",
        "seller_info",
        "user_id",
        "user_name",
        "zalo",
    }
)

# --- bảng quy đổi -------------------------------------------------------------

# Ký tự vô hình: người rao chèn vào giữa dãy số để cắt regex.
_ZERO_WIDTH = frozenset("​‌‍‎‏⁠﻿­")

# Chữ cái được dùng thay chữ số. Chỉ quy đổi khi ký tự NẰM SÁT một chữ số thật,
# nếu không thì "O" trong "NHÀ O TÂN BÌNH" sẽ bị hiểu nhầm.
_HOMOGLYPHS = {
    "O": "0", "o": "0", "Q": "0", "Ο": "0", "О": "0", "ο": "0", "о": "0",
    "D": "0", "Ð": "0",
    "l": "1", "I": "1", "|": "1", "!": "1", "ǀ": "1", "Ⅰ": "1",
}

# Số viết bằng chữ. "ba", "sáu", "năm" cũng là từ thường gặp trong tin rao, nhưng một
# chữ số lẻ không tạo ra dãy dài nên không kích hoạt việc xoá — chỉ khi ghép đủ dài
# thành dạng số điện thoại hợp lệ mới bị cắt.
_WORD_DIGITS = {
    "không": "0", "khong": "0", "ko": "0", "kg": "0",
    "một": "1", "mot": "1", "mốt": "1", "mot.": "1",
    "hai": "2",
    "ba": "3",
    "bốn": "4", "bon": "4", "tư": "4", "tu": "4",
    "năm": "5", "nam": "5", "lăm": "5", "lam": "5",
    "sáu": "6", "sau": "6",
    "bảy": "7", "bay": "7", "bẩy": "7",
    "tám": "8", "tam": "8",
    "chín": "9", "chin": "9",
}

_WORD_DIGIT_RE = re.compile(
    r"(?<![^\W\d_])(?:"
    + "|".join(sorted((re.escape(w) for w in _WORD_DIGITS), key=len, reverse=True))
    + r")(?![^\W\d_])",
    re.IGNORECASE,
)

# --- dò dãy số ----------------------------------------------------------------

# Dấu ngăn cách được chấp nhận giữa hai chữ số của cùng một số điện thoại.
_SEP = r"[\s.,\-–—_*+()\[\]{}/\\|·•~#:;'\"]"

# Dãy 8–15 chữ số nối nhau qua tối đa 3 ký tự ngăn cách.
_DIGIT_RUN = re.compile(rf"\d(?:{_SEP}{{0,3}}\d){{7,14}}")

# Từ khoá báo hiệu "đoạn sau là số liên hệ". Có nó thì hạ ngưỡng nghi ngờ.
_CONTACT_HINT = re.compile(
    r"(?:liên\s*hệ|lien\s*he|số\s*điện\s*thoại|so\s*dien\s*thoai|chính\s*chủ|"
    r"\bl\.?h\b|\bsđt\b|\bsdt\b|\bđt\b|\bdt\b|\bzalo\b|\bviber\b|\bwhatsapp\b|"
    r"\bcall\b|\bhotline\b|\bphone\b|\btel\b|\balo\b|\bib\b|\bms\b|\bmr\b|\bmrs\b|"
    r"\bgọi\b|\bgoi\b|\bmobile\b|\bmob\b)"
    rf"(?:{_SEP}|\w){{0,12}}$",
    re.IGNORECASE,
)

_CONTEXT_WINDOW = 40  # số ký tự nhìn ngược để tìm từ khoá liên hệ


def _looks_like_vn_phone(digits: str, has_hint: bool) -> bool:
    """Dãy chữ số đã bỏ hết dấu ngăn cách có phải số điện thoại Việt Nam không."""
    if digits.startswith("84") and 11 <= len(digits) <= 12:
        return True
    if digits.startswith("0") and 10 <= len(digits) <= 11:
        return True
    if has_hint and 8 <= len(digits) <= 15:
        return True
    # Số di động viết thiếu số 0 đầu: 9 chữ số, đầu số hợp lệ.
    if len(digits) == 9 and digits[0] in "35789":
        return True
    return False


# --- chuẩn hoá có bản đồ vị trí ----------------------------------------------


def _neighbour_is_digit(text: str, index: int, step: int) -> bool:
    """Ký tự sát bên (bỏ qua ký tự vô hình) có phải chữ số không."""
    i = index + step
    while 0 <= i < len(text) and text[i] in _ZERO_WIDTH:
        i += step
    return 0 <= i < len(text) and text[i].isdigit()


def _normalise(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Trả về (chuỗi chỉ-để-dò, bản đồ vị trí ngược về chuỗi gốc).

    Phần tử thứ i của bản đồ là khoảng [start, end) trong chuỗi gốc đã sinh ra ký tự
    thứ i của chuỗi chuẩn hoá. Nhờ khoảng này, một đoạn khớp trên chuỗi chuẩn hoá luôn
    quy được về đúng đoạn văn bản gốc cần xoá, kể cả khi một từ ("không") thu lại
    thành một ký tự ("0").
    """
    lowered = text.lower()
    out: list[str] = []
    spans: list[tuple[int, int]] = []
    i, n = 0, len(text)

    while i < n:
        ch = text[i]

        if ch in _ZERO_WIDTH:
            i += 1
            continue

        if ch.isdigit():
            end = i + 1
            # emoji keycap: chữ số + (VS16) + U+20E3
            if end < n and text[end] == "️":
                end += 1
            if end < n and text[end] == "⃣":
                end += 1
            try:
                value = str(unicodedata.digit(ch))
            except (TypeError, ValueError):
                value = ch
            out.append(value)
            spans.append((i, end))
            i = end
            continue

        match = _WORD_DIGIT_RE.match(lowered, i)
        if match:
            word = match.group(0).rstrip(".")
            digit = _WORD_DIGITS.get(word)
            if digit is not None:
                out.append(digit)
                spans.append((i, match.end()))
                i = match.end()
                continue

        if ch in _HOMOGLYPHS and (
            _neighbour_is_digit(text, i, -1) or _neighbour_is_digit(text, i, 1)
        ):
            out.append(_HOMOGLYPHS[ch])
            spans.append((i, i + 1))
            i += 1
            continue

        out.append(ch)
        spans.append((i, i + 1))
        i += 1

    return "".join(out), spans


def find_phone_spans(text: str) -> list[tuple[int, int]]:
    """Khoảng [start, end) trong chuỗi GỐC được coi là số điện thoại."""
    if not text:
        return []

    normalised, spans = _normalise(text)
    hits: list[tuple[int, int]] = []

    for match in _DIGIT_RUN.finditer(normalised):
        digits = re.sub(r"\D", "", match.group(0))
        left = normalised[max(0, match.start() - _CONTEXT_WINDOW) : match.start()]
        has_hint = bool(_CONTACT_HINT.search(left))
        if not _looks_like_vn_phone(digits, has_hint):
            continue
        start = spans[match.start()][0]
        end = spans[match.end() - 1][1]
        hits.append((start, end))

    return _merge(hits)


def _merge(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Gộp các khoảng chồng lấn hoặc dính nhau."""
    if not spans:
        return []
    spans = sorted(spans)
    merged = [spans[0]]
    for start, end in spans[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def find_phones(text: str) -> list[str]:
    """Các đoạn văn bản gốc bị coi là số điện thoại (dùng cho test và QA gate)."""
    return [text[start:end] for start, end in find_phone_spans(text)]


def scrub_text(text: str) -> tuple[str, int]:
    """Thay mọi số điện thoại bằng REDACTION. Trả về (văn bản sạch, số lần xoá)."""
    if not text:
        return text, 0

    spans = find_phone_spans(text)
    if not spans:
        return text, 0

    pieces: list[str] = []
    cursor = 0
    for start, end in spans:
        pieces.append(text[cursor:start])
        pieces.append(REDACTION)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces), len(spans)


# --- áp dụng lên bản ghi ------------------------------------------------------


def _walk(value: Any) -> Iterator[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk(child)


def scrub_record(record: Any, extra_fields: frozenset[str] | set[str] = frozenset()) -> tuple[Any, int]:
    """Bỏ trường cá nhân và xoá số điện thoại trong mọi chuỗi của bản ghi.

    Trả về (bản ghi sạch, tổng số lần xoá số điện thoại). Bản ghi gốc không bị sửa.
    """
    drop = {name.lower() for name in PII_FIELDS | set(extra_fields)}
    return _scrub_value(record, drop)


def _scrub_value(value: Any, drop: set[str]) -> tuple[Any, int]:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        total = 0
        for key, item in value.items():
            if isinstance(key, str) and key.lower() in drop:
                continue
            cleaned, count = _scrub_value(item, drop)
            clean[key] = cleaned
            total += count
        return clean, total

    if isinstance(value, list):
        cleaned_items = []
        total = 0
        for item in value:
            cleaned, count = _scrub_value(item, drop)
            cleaned_items.append(cleaned)
            total += count
        return cleaned_items, total

    if isinstance(value, str):
        return scrub_text(value)

    return value, 0


def contains_phone(record: Any) -> bool:
    """True nếu còn bất kỳ chuỗi nào trong bản ghi chứa số điện thoại."""
    return any(
        isinstance(node, str) and find_phone_spans(node) for node in _walk(record)
    )
