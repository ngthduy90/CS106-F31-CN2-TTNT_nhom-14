"""Trích đặc trưng định lượng từ văn bản tin rao (runbook 02 §1).

Đây là yêu cầu trung tâm của đề: mô tả tự do chứa số đo mà cột dữ liệu có cấu trúc bỏ
sót. Bảy trường được rút: diện tích, số phòng ngủ, số nhà tắm, số tầng, mặt tiền, bề
rộng hẻm, pháp lý, hướng nhà.

Chọn regex làm chính (không dùng LLM) vì ba lý do: tái lập được tuyệt đối, giải thích
được từng luật trong báo cáo, và chạy trên 10.000 tin trong vài giây. Giá phải trả là
recall thấp hơn với cách diễn đạt lạ; bộ nhãn vàng ở `gold.py` đo đúng khoảng cách đó.

Ba luật khó nhất, ghi lại vì báo cáo cần giải thích:

1. **"1 trệt 2 lầu" = 3 tầng.** Tiếng Việt đếm tầng bằng phép cộng các thành phần
   (trệt / lửng / lầu / sân thượng) chứ không bằng một con số duy nhất, nên bộ luật
   cộng dồn từng thành phần thay vì bắt một số.
2. **"4x15" là kích thước, không phải diện tích.** Phải nhân ra, và chiều ngang chính
   là mặt tiền, nên một luật cho ra hai trường.
3. **"nhà mặt tiền" khác "mặt tiền 4m".** Cụm đầu là loại vị trí, cụm sau là số đo.
   Luật mặt tiền vì thế bắt buộc phải có con số kèm đơn vị mét đi ngay sau.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field

# --- tiện ích -----------------------------------------------------------------

_NUM = r"(\d{1,4}(?:[.,]\d{1,2})?)"


def strip_accents(text: str) -> str:
    """Bỏ dấu và quy các biến thể ký tự lạ về ASCII trước khi chạy luật.

    NFKC chạy trước vì tin rao dùng rất nhiều chữ Unicode kiểu cách để nổi bật giữa
    dòng thời gian: 𝐃𝐢𝐞̣̂𝐧 𝐭𝐢́𝐜𝐡 (chữ toán học in đậm), ｍ２ (dạng rộng), m² (chỉ số trên).
    Không quy đổi thì mọi luật đều trượt trên đúng những tin được đầu tư viết nhất.
    """
    compatible = unicodedata.normalize("NFKC", str(text))
    decomposed = unicodedata.normalize("NFD", compatible)
    without = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return without.replace("đ", "d").replace("Đ", "D").lower()


def _num(token: str) -> float | None:
    try:
        return float(token.replace(",", "."))
    except (AttributeError, ValueError):
        return None


def _plausible(value: float | None, low: float, high: float) -> float | None:
    return value if value is not None and low <= value <= high else None


# --- diện tích ----------------------------------------------------------------

# "DT 60m2", "diện tích: 60 m²", "60m2", "60 mv"
_AREA_ANY = re.compile(rf"{_NUM}\s*(?:m2|m²|mv|m)\b")
_AREA_LABEL_NEAR = re.compile(r"(?:dt|dtcn|dtsd|dien\s*tich|cong\s*nhan|\bcn\b|so\s*do|shr)")
_RECOGNISED_NEAR = re.compile(r"(?:cong\s*nhan|dtcn|\bcn\b)")

# "4x15", "4 x 15", "4*15", "ngang 4 dài 15", "4m x 15m"
_DIMENSIONS = re.compile(rf"{_NUM}\s*m?\s*[x*×]\s*{_NUM}\s*m?\b")
_WIDTH_LENGTH = re.compile(rf"ngang\s*{_NUM}\s*m?\D{{0,12}}?(?:dai|sau)\s*{_NUM}\s*m?\b")

_AREA_CONTEXT = 24  # số ký tự nhìn quanh một con số để chấm điểm ngữ cảnh


def extract_dimensions(flat: str) -> tuple[float | None, float | None]:
    """(chiều ngang, chiều dài) tính bằng mét, từ cách viết kích thước."""
    for pattern in (_WIDTH_LENGTH, _DIMENSIONS):
        for match in pattern.finditer(flat):
            width = _plausible(_num(match.group(1)), 1.5, 50)
            length = _plausible(_num(match.group(2)), 3, 200)
            if width and length:
                return width, length
    return None, None


def extract_area(flat: str) -> float | None:
    """Diện tích m², chấm điểm theo ngữ cảnh quanh từng con số.

    Tin rao thường chứa vài con số cùng đơn vị mét vuông: kích thước lô ("4x16"), diện
    tích xây dựng, và diện tích CÔNG NHẬN trên sổ. Ba con số này khác nhau khi lô đất
    nở hậu hoặc bị lộ giới, và con số đúng để mô hình học là diện tích công nhận —
    cũng chính là con số người bán điền vào form của sàn.

    Vì vậy luật không lấy con số đầu tiên gặp được mà chấm điểm: nằm cạnh "công nhận"
    được 2 điểm, cạnh "diện tích"/"DT" được 1 điểm, trơ trọi được 0. Tích kích thước
    chỉ dùng khi trong tin không có con số nào kèm đơn vị mét vuông.
    """
    best: tuple[int, float] | None = None

    for match in _AREA_ANY.finditer(flat):
        value = _plausible(_num(match.group(1)), 10, 1_000)
        if value is None:
            continue
        left = flat[max(0, match.start() - _AREA_CONTEXT) : match.start()]
        right = flat[match.end() : match.end() + _AREA_CONTEXT]
        window = left + " " + right

        score = 0
        if _RECOGNISED_NEAR.search(window):
            score = 2
        elif _AREA_LABEL_NEAR.search(left):
            score = 1
        # Con số dính ngay vào "x" là một chiều của kích thước, không phải diện tích.
        if re.search(r"[x*×]\s*$", left) or re.match(r"\s*[x*×]", right):
            continue

        if best is None or score > best[0]:
            best = (score, value)

    if best is not None:
        return best[1]

    width, length = extract_dimensions(flat)
    if width and length:
        return _plausible(round(width * length, 1), 10, 1_000)
    return None


# --- phòng ngủ / nhà tắm ------------------------------------------------------

_BEDROOMS = re.compile(r"(\d{1,2})\s*(?:pn\b|phong\s*ngu|p\.?n\b|bedroom|phong\b|p\b)")
_BEDROOMS_SUFFIX = re.compile(r"(?:phong\s*ngu|pn)\s*[:\-]?\s*(\d{1,2})\b")
_BATHROOMS = re.compile(r"(\d{1,2})\s*(?:wc\b|toilet|nha\s*tam|phong\s*tam|vs\b)")
_BATHROOMS_SUFFIX = re.compile(r"(?:wc|toilet|nha\s*tam)\s*[:\-]?\s*(\d{1,2})\b")


def _count(flat: str, *patterns: re.Pattern[str], high: int) -> int | None:
    for pattern in patterns:
        match = pattern.search(flat)
        if match:
            value = _plausible(_num(match.group(1)), 1, high)
            if value:
                return int(value)
    return None


def extract_bedrooms(flat: str) -> int | None:
    return _count(flat, _BEDROOMS, _BEDROOMS_SUFFIX, high=20)


def extract_bathrooms(flat: str) -> int | None:
    return _count(flat, _BATHROOMS, _BATHROOMS_SUFFIX, high=20)


# --- số tầng ------------------------------------------------------------------

# Thành phần đếm tầng và trọng số của nó. "trệt" và "lửng" đứng một mình là 1 tầng,
# "lầu/tấm/mê" đi kèm số lượng, "sân thượng" tính nửa tầng nên bỏ (chỉ dùng khi đứng
# cùng các thành phần khác thì đã được cộng qua "lầu").
_GROUND = re.compile(r"\b(?:1\s*)?(?:tret|trẹt|ham|ban\s*ham)\b")
_MEZZANINE = re.compile(r"\blung\b")
# "lầu / tấm / mê" đếm tầng TRÊN mặt đất, "tầng" đếm TỔNG. Gộp hai nhóm này là lỗi
# tốn kém nhất của bộ luật: "nhà 2 tầng" bị cộng thêm trệt thành 3.
_UPPER = re.compile(r"(\d{1,2})\s*(?:lau|tam\b|me\b)")
_UPPER_WORD = re.compile(r"\b(mot|hai|ba|bon|nam|sau|bay|tam|chin)\s*(?:lau|tam\b|me\b)")
_UPPER_BARE = re.compile(r"\b(?:lau|tam|me)\b")
_TOTAL_FLOORS = re.compile(r"(\d{1,2})\s*tang\b")
_LEVEL_4 = re.compile(r"\bcap\s*4\b")

_WORD_NUMBERS = {
    "mot": 1, "hai": 2, "ba": 3, "bon": 4, "nam": 5,
    "sau": 6, "bay": 7, "tam": 8, "chin": 9,
}


def extract_floors(flat: str) -> int | None:
    """Số tầng, cộng dồn theo cách người Việt mô tả nhà phố.

    "1 trệt 2 lầu" → 1 + 2 = 3. "trệt lửng 2 lầu" → 1 + 1 + 2 = 4. "nhà cấp 4" → 1.
    Khi tin ghi thẳng "nhà 4 tầng" thì lấy luôn con số đó.
    """
    if _LEVEL_4.search(flat):
        return 1

    # "nhà 4 tầng" đã là tổng số tầng, không cộng thêm gì nữa.
    total = _TOTAL_FLOORS.search(flat)
    if total:
        value = _int_or_none(int(_num(total.group(1)) or 0), 1, 15)
        if value:
            return value

    ground = 1 if _GROUND.search(flat) else 0
    mezzanine = 1 if _MEZZANINE.search(flat) else 0

    upper = 0
    match = _UPPER.search(flat)
    if match:
        upper = int(_num(match.group(1)) or 0)
    else:
        match = _UPPER_WORD.search(flat)
        if match:
            upper = _WORD_NUMBERS.get(match.group(1), 0)
        elif _UPPER_BARE.search(flat):
            # "trệt lầu" không kèm số nghĩa là đúng một lầu.
            upper = 1

    if ground or mezzanine:
        total = ground + mezzanine + upper
        return _int_or_none(total, 1, 15)

    if upper:
        # "2 lầu" hiểu ngầm là có trệt.
        return _int_or_none(upper + 1, 1, 15)
    return None


def _int_or_none(value: int, low: int, high: int) -> int | None:
    return value if low <= value <= high else None


# --- mặt tiền và hẻm ----------------------------------------------------------

# Bắt buộc có số + đơn vị mét ngay sau, để "nhà mặt tiền đường Âu Cơ" không bị hiểu
# thành một số đo.
_FRONTAGE = re.compile(rf"(?:mat\s*tien|mt|ngang|rong)\s*[:\-]?\s*{_NUM}\s*m\b")
_ALLEY_WIDTH = re.compile(rf"(?:hem|hxh|ngo)\s*[:\-]?\s*{_NUM}\s*m\b")
_ALLEY_ANY = re.compile(r"\b(?:hem|hxh|hxt|ngo)\b")
_STREET_FRONT = re.compile(r"\b(?:mat\s*tien|mt)\s*(?:duong|dg|kinh\s*doanh|kd)?\b")


def extract_frontage(flat: str) -> float | None:
    match = _FRONTAGE.search(flat)
    if match:
        return _plausible(_num(match.group(1)), 1.5, 30)
    width, _ = extract_dimensions(flat)
    return width


def extract_alley_width(flat: str) -> float | None:
    match = _ALLEY_WIDTH.search(flat)
    return _plausible(_num(match.group(1)), 1.0, 20) if match else None


def extract_position(flat: str) -> str:
    """"mặt tiền" / "hẻm" / "không rõ" — biến phân loại, không phải số đo."""
    if _STREET_FRONT.search(flat):
        return "mặt tiền"
    if _ALLEY_ANY.search(flat):
        return "hẻm"
    return "không rõ"


# --- pháp lý và hướng ---------------------------------------------------------

LEGAL_PATTERNS = [
    ("sổ hồng riêng", re.compile(r"\bshr\b|so\s*hong\s*rieng")),
    ("sổ hồng", re.compile(r"so\s*hong|\bsh\b|so\s*do|\bsd\b|so\s*rieng")),
    ("hợp đồng mua bán", re.compile(r"hdmb|hop\s*dong\s*mua\s*ban")),
    ("giấy tay", re.compile(r"giay\s*tay|vi\s*bang|giay\s*viet\s*tay")),
    ("đang chờ sổ", re.compile(r"dang\s*cho\s*so|cho\s*ra\s*so|dang\s*lam\s*so")),
]

DIRECTIONS = [
    ("Đông Bắc", re.compile(r"huong\s*dong\s*bac|\bdong\s*bac\b")),
    ("Đông Nam", re.compile(r"huong\s*dong\s*nam|\bdong\s*nam\b")),
    ("Tây Bắc", re.compile(r"huong\s*tay\s*bac|\btay\s*bac\b")),
    ("Tây Nam", re.compile(r"huong\s*tay\s*nam|\btay\s*nam\b")),
    ("Đông", re.compile(r"huong\s*dong\b")),
    ("Tây", re.compile(r"huong\s*tay\b")),
    ("Nam", re.compile(r"huong\s*nam\b")),
    ("Bắc", re.compile(r"huong\s*bac\b")),
]


def extract_legal(flat: str) -> str:
    for label, pattern in LEGAL_PATTERNS:
        if pattern.search(flat):
            return label
    return "không rõ"


def extract_direction(flat: str) -> str:
    """Hướng ghép ("Đông Nam") phải thử trước hướng đơn, nếu không "Đông" nuốt mất."""
    for label, pattern in DIRECTIONS:
        if pattern.search(flat):
            return label
    return "không rõ"


# --- gộp ----------------------------------------------------------------------

FIELDS = (
    "area_m2",
    "bedrooms",
    "bathrooms",
    "floors",
    "frontage_m",
    "alley_width_m",
    "position",
    "legal_status",
    "direction",
)


@dataclass
class Extracted:
    area_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    floors: int | None = None
    frontage_m: float | None = None
    alley_width_m: float | None = None
    position: str = "không rõ"
    legal_status: str = "không rõ"
    direction: str = "không rõ"
    dimensions: tuple[float | None, float | None] = field(default=(None, None))

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data.pop("dimensions")
        return data


def extract_all(text: str | None) -> Extracted:
    """Chạy trọn bộ luật trên một đoạn văn bản (tiêu đề + mô tả nối lại)."""
    if not text:
        return Extracted()
    flat = strip_accents(text)
    width, length = extract_dimensions(flat)
    return Extracted(
        area_m2=extract_area(flat),
        bedrooms=extract_bedrooms(flat),
        bathrooms=extract_bathrooms(flat),
        floors=extract_floors(flat),
        frontage_m=extract_frontage(flat),
        alley_width_m=extract_alley_width(flat),
        position=extract_position(flat),
        legal_status=extract_legal(flat),
        direction=extract_direction(flat),
        dimensions=(width, length),
    )
