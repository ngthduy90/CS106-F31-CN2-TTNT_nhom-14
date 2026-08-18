"""Chuẩn hoá giá — bước phải chạy TRƯỚC mọi bước làm sạch khác (runbook 02 §3.2).

Giá là nhãn của bài toán, nên một lỗi parse ở đây không chỉ làm bẩn một đặc trưng mà
làm sai thẳng mục tiêu huấn luyện. Ba dạng phải phân biệt cho bằng được:

- **Tổng giá**: "5,2 tỷ", "5 tỷ 2", "5 tỷ 200 triệu", "5200 triệu".
- **Đơn giá theo m²**: "52 triệu/m²" — phải nhân diện tích mới ra tổng giá.
- **Không có giá**: "thoả thuận", "giá liên hệ", 0, 1 — là NHÃN THIẾU, phải loại khỏi
  tập huấn luyện chứ không được impute (impute nhãn là bịa dữ liệu).

Dấu thập phân tiếng Việt là dấu phẩy còn dấu chấm là dấu nghìn, nhưng tin rao dùng lẫn
lộn cả hai ("6.79 tỷ" và "8,2 tỷ" cùng xuất hiện trong dữ liệu crawl). Luật phân định:
xem cả hai là dấu thập phân khi phần sau chúng ngắn hơn 3 chữ số hoặc khi con số nằm
ngay trước đơn vị "tỷ"; ngược lại coi là dấu nghìn.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

from src import config

TY = 1_000_000_000
TRIEU = 1_000_000

# Cách viết "không có giá". Khớp trên chuỗi đã bỏ dấu để "thỏa"/"thoả" cùng trúng.
NEGOTIABLE = re.compile(
    r"(thoa\s*thuan|gia\s*lien\s*he|lien\s*he|thuong\s*luong|khong\s*ro|dang\s*cap\s*nhat|"
    r"gia\s*thoa|call|contact)",
    re.IGNORECASE,
)

_UNIT_BILLION = r"(?:tỷ|tỉ|ty|ti\b|billion|b\b)"
_UNIT_MILLION = r"(?:triệu|trieu|tr\b|củ|cu\b|million|m\b)"
_PER_M2 = r"(?:/|trên|tren|mỗi|moi|per)?\s*m\s*[²2]"


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def _to_float(token: str) -> float | None:
    """"6.79" → 6.79 · "5,2" → 5.2 · "5.200" → 5200 · "1.234,5" → 1234.5."""
    token = token.strip().replace(" ", "")
    if not token:
        return None

    if "," in token and "." in token:
        # Dấu xuất hiện sau cùng là dấu thập phân, dấu kia là dấu nghìn.
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        head, _, tail = token.rpartition(",")
        token = f"{head}.{tail}" if len(tail) != 3 else f"{head}{tail}"
    elif "." in token:
        head, _, tail = token.rpartition(".")
        # "5.200" là năm nghìn hai trăm; "6.79" là sáu phẩy bảy chín.
        token = f"{head}{tail}" if len(tail) == 3 and head.isdigit() else f"{head}.{tail}"

    try:
        return float(token)
    except ValueError:
        return None


_NUM = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"

# "52 triệu/m2" — phải thử TRƯỚC các mẫu tổng giá, nếu không "52 triệu" bị đọc thành
# tổng giá 52 triệu và căn nhà 5 tỷ biến thành căn nhà 52 triệu.
_RE_PER_M2_MILLION = re.compile(rf"{_NUM}\s*{_UNIT_MILLION}\s*{_PER_M2}", re.IGNORECASE)
_RE_PER_M2_BILLION = re.compile(rf"{_NUM}\s*{_UNIT_BILLION}\s*{_PER_M2}", re.IGNORECASE)

# "5 tỷ 200 triệu" và "5 tỷ 2" (đuôi rời nghĩa là phần trăm triệu: 5 tỷ 2 = 5,2 tỷ)
_RE_BILLION_MILLION = re.compile(rf"{_NUM}\s*{_UNIT_BILLION}\s*{_NUM}\s*{_UNIT_MILLION}", re.IGNORECASE)
_RE_BILLION_TAIL = re.compile(rf"{_NUM}\s*{_UNIT_BILLION}\s*(\d{{1,3}})(?!\s*\d)(?!\s*m)", re.IGNORECASE)
_RE_BILLION = re.compile(rf"{_NUM}\s*{_UNIT_BILLION}", re.IGNORECASE)
_RE_MILLION = re.compile(rf"{_NUM}\s*{_UNIT_MILLION}", re.IGNORECASE)


def _round_vnd(value: float | None) -> float | None:
    """Làm tròn tới nghìn đồng: 8,2 tỷ tính bằng dấu phẩy động ra 8.199.999.999,999."""
    return None if value is None else round(value / 1_000) * 1_000


@dataclass(frozen=True)
class ParsedPrice:
    """Kết quả parse một chuỗi giá.

    `total_vnd` là tổng giá đã quy về VND; `unit_vnd_per_m2` chỉ có khi tin ghi đơn giá.
    `kind` ghi lại đường đi nào đã được dùng, để bảng data-funnel truy được vì sao một
    dòng bị loại.
    """

    total_vnd: float | None
    unit_vnd_per_m2: float | None
    kind: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "total_vnd", _round_vnd(self.total_vnd))
        object.__setattr__(self, "unit_vnd_per_m2", _round_vnd(self.unit_vnd_per_m2))

    @property
    def ok(self) -> bool:
        return self.total_vnd is not None


MISSING = ParsedPrice(None, None, "missing")
NEGOTIABLE_RESULT = ParsedPrice(None, None, "negotiable")


def parse_price(text: str | None, area_m2: float | None = None) -> ParsedPrice:
    """Chuỗi giá → tổng giá VND. Cần `area_m2` khi tin chỉ ghi đơn giá theo m²."""
    if text is None:
        return MISSING
    text = str(text).strip()
    if not text:
        return MISSING

    flat = _strip_accents(text)
    if NEGOTIABLE.search(flat) and not re.search(r"\d", text):
        return NEGOTIABLE_RESULT

    match = _RE_PER_M2_MILLION.search(text)
    if match:
        unit = _to_float(match.group(1))
        if unit is not None:
            unit_vnd = unit * TRIEU
            total = unit_vnd * area_m2 if area_m2 else None
            return ParsedPrice(total, unit_vnd, "unit_million_per_m2")

    match = _RE_PER_M2_BILLION.search(text)
    if match:
        unit = _to_float(match.group(1))
        if unit is not None:
            unit_vnd = unit * TY
            total = unit_vnd * area_m2 if area_m2 else None
            return ParsedPrice(total, unit_vnd, "unit_billion_per_m2")

    match = _RE_BILLION_MILLION.search(text)
    if match:
        billions, millions = _to_float(match.group(1)), _to_float(match.group(2))
        if billions is not None and millions is not None:
            return ParsedPrice(billions * TY + millions * TRIEU, None, "billion_million")

    match = _RE_BILLION_TAIL.search(text)
    if match:
        billions, tail = _to_float(match.group(1)), match.group(2)
        if billions is not None and billions == int(billions):
            # "5 tỷ 2" = 5,2 tỷ · "5 tỷ 25" = 5,25 tỷ
            fraction = int(tail) / (10 ** len(tail))
            return ParsedPrice((billions + fraction) * TY, None, "billion_tail")

    match = _RE_BILLION.search(text)
    if match:
        billions = _to_float(match.group(1))
        if billions is not None:
            return ParsedPrice(billions * TY, None, "billion")

    match = _RE_MILLION.search(text)
    if match:
        millions = _to_float(match.group(1))
        if millions is not None:
            return ParsedPrice(millions * TRIEU, None, "million")

    # Số trần không đơn vị: chỉ nhận khi lớn tới mức chỉ có thể là VND.
    bare = re.fullmatch(r"[\d.,\s]+", text)
    if bare:
        value = _to_float(text)
        if value is not None and value >= 1e8:
            return ParsedPrice(value, None, "bare_vnd")

    if NEGOTIABLE.search(flat):
        return NEGOTIABLE_RESULT
    return MISSING


def normalise_numeric_price(value: float | int | str | None) -> float | None:
    """Giá do API/dataset trả về dạng số. Giá 0/1 là quy ước "không công bố"."""
    if value is None:
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 1:
        return None
    return number


def cross_check(
    total_vnd: float | None,
    unit_vnd_per_m2: float | None,
    area_m2: float | None,
    tolerance: float = config.PRICE_CROSS_CHECK_TOLERANCE,
) -> tuple[bool, float | None]:
    """Tin ghi cả tổng giá lẫn đơn giá thì hai con số phải khớp.

    Trả về (khớp hay không, sai số tương đối). Không đủ dữ liệu để đối chiếu thì coi
    như khớp — không có bằng chứng sai thì không gắn cờ đỏ.
    """
    if not (total_vnd and unit_vnd_per_m2 and area_m2):
        return True, None
    implied = unit_vnd_per_m2 * area_m2
    if implied <= 0:
        return True, None
    deviation = abs(total_vnd - implied) / implied
    return deviation <= tolerance, deviation


# --- lọc tin cho thuê (T2.3) --------------------------------------------------

RENTAL_MARKERS = re.compile(
    r"(cho\s*thue|can\s*thue|gia\s*thue|thue\s*nha|thue\s*phong|/\s*thang|"
    r"mot\s*thang|1\s*thang|per\s*month|month)",
    re.IGNORECASE,
)


def looks_like_rental(title: str | None, total_vnd: float | None = None) -> bool:
    """Tin cho thuê lọt vào danh mục bán: nhận ra bằng TIÊU ĐỀ hoặc bằng giá quá thấp.

    Chỉ đọc TIÊU ĐỀ, không đọc mô tả. Quét cả mô tả thì tỷ lệ gắn cờ vọt lên 27%, vì
    tin bán rất hay lấy dòng tiền cho thuê ra làm điểm bán hàng ("nhà đang cho thuê 15
    triệu/tháng, mua là có thu nhập ngay"). Những tin đó là tin BÁN; loại chúng đi là
    tự cắt mất một phần dữ liệu hợp lệ.

    Ngưỡng giá lấy từ `config.VALID_TOTAL_PRICE_VND`, không phải con số nhớ trong đầu:
    dưới cận dưới đó thì với nhà TP.HCM gần như chắc chắn là giá thuê tháng.
    """
    if total_vnd is not None and 0 < total_vnd < config.VALID_TOTAL_PRICE_VND[0]:
        return True
    if not title:
        return False
    return bool(RENTAL_MARKERS.search(_strip_accents(str(title))))
