"""T3.1 và T3.3 — tách từ tiếng Việt, danh sách dừng, và cờ văn bản thủ công.

Tách từ bằng underthesea (Apache-2.0, còn phát triển), lùi về pyvi rồi lùi tiếp về
tách theo khoảng trắng nếu cả hai không dùng được. Bậc thang này để pipeline không
chết trên máy khác chỉ vì thiếu một thư viện; báo cáo ghi rõ bậc nào đã chạy.

**Danh sách dừng được cắt tỉa có chủ đích.** Ngoài hư từ thông thường còn có một
stoplist riêng cho tin rao ("liên hệ", "chính chủ", "lh", "xem nhà 24/7") vì chúng
xuất hiện ở gần như mọi tin nên không phân biệt được gì. Nhưng **giữ lại** các từ mang
tín hiệu giá: "gấp", "ngộp", "kẹt tiền", "giảm" — đây chính là loại tín hiệu mà đề bài
muốn khai thác từ mô tả, bỏ chúng đi là tự cắt tay mình.
"""

from __future__ import annotations

import re
import unicodedata

# Hư từ tiếng Việt hay gặp. Danh sách ngắn có chủ đích: TF-IDF với min_df đã tự dìm
# các từ quá phổ biến, danh sách dừng chỉ cần dọn phần rõ ràng nhất.
BASE_STOPWORDS = {
    "và", "của", "có", "các", "được", "cho", "với", "là", "trong", "này", "đã", "khi",
    "một", "những", "để", "tại", "từ", "hay", "hoặc", "nếu", "thì", "mà", "nên", "vì",
    "cũng", "rất", "sẽ", "đang", "bị", "ra", "vào", "lên", "xuống", "về", "theo", "như",
}

# Từ chỉ có mặt vì đây là tin rao, không nói gì về bất động sản.
AD_STOPWORDS = {
    "liên", "hệ", "lh", "chính", "chủ", "xem", "nhà", "24", "7", "alo", "zalo", "call",
    "hotline", "em", "anh", "chị", "ạ", "nhé", "nha", "ib", "inbox", "quan", "tâm",
    "sđt", "sdt", "gọi", "ngay", "tel", "phone", "ms", "mr", "giatien",
}

# Từ TUYỆT ĐỐI không loại: chúng mang tín hiệu về áp lực bán, tức là về giá.
PRICE_SIGNAL_WORDS = {
    "gấp", "ngộp", "kẹt", "giảm", "lỗ", "rẻ", "cắt", "thiện", "chí", "bank", "nợ",
    "thương", "lượng", "bao", "sang", "tên",
}

STOPWORDS = (BASE_STOPWORDS | AD_STOPWORDS) - PRICE_SIGNAL_WORDS

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def _load_segmenter():
    """Trả về (hàm tách từ, tên bậc đã dùng)."""
    try:
        from underthesea import word_tokenize

        return (lambda text: word_tokenize(text, format="text")), "underthesea"
    except Exception:  # noqa: BLE001
        pass
    try:
        from pyvi import ViTokenizer

        return ViTokenizer.tokenize, "pyvi"
    except Exception:  # noqa: BLE001
        pass
    return (lambda text: text), "khoảng trắng"


_SEGMENT, SEGMENTER_NAME = _load_segmenter()


def normalise(text: str | None) -> str:
    """Chuẩn hoá nhưng GIỮ dấu câu, vì bộ tách từ cần chúng làm ranh giới.

    Bỏ dấu câu trước khi tách từ là một lỗi tinh vi: "nội thất, ngộp bank" mất dấu
    phẩy sẽ bị tách thành "nội_thất_ngộp", và "cửa, sổ hồng" thành "cửa_sổ" (ô cửa)
    thay vì "cửa" + "sổ hồng" (giấy tờ nhà). Dấu câu được dọn SAU khi tách.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    return _SPACES.sub(" ", text).strip()


def tokenize(text: str | None) -> list[str]:
    """Chuỗi → danh sách token đã tách từ, bỏ từ dừng và token quá ngắn."""
    cleaned = normalise(text)
    if not cleaned:
        return []
    tokens = _SEGMENT(cleaned).split()
    tokens = [_PUNCT.sub("", token).strip("_") for token in tokens]
    return [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]


def pretokenize(text: str | None) -> str:
    """Token đã tách, nối lại bằng khoảng trắng để TF-IDF chỉ cần `str.split`.

    Tách từ tiếng Việt là bước ĐẮT NHẤT của cả pipeline. Nếu để TfidfVectorizer gọi bộ
    tách từ trong analyzer thì mỗi lần fit lại (mỗi fold × mỗi cấu hình search) sẽ tách
    lại toàn bộ tập dữ liệu — vài trăm lần cho cùng một kết quả. Tách một lần ở bước
    dựng bảng đặc trưng rút thời gian chạy thí nghiệm xuống hai bậc độ lớn.
    """
    return " ".join(tokenize(text))


def analyzer(text: str | None) -> list[str]:
    """Analyzer cho chuỗi ĐÃ tách từ sẵn bằng `pretokenize`."""
    return str(text or "").split()


# --- cờ văn bản thủ công (T3.3) ----------------------------------------------

# Mỗi cờ là một khái niệm mà người mua nhà TP.HCM thật sự quan tâm, viết ở dạng có thể
# giải thích được cho hội đồng. Cây quyết định học trên 20 cột nhị phân này dễ đọc hơn
# nhiều so với học trên 150 trục SVD vô danh.
TEXT_FLAGS: dict[str, str] = {
    "co_mat_tien": r"mat\s*tien|\bmt\b",
    "hem_xe_hoi": r"hem\s*xe\s*hoi|\bhxh\b|xe\s*hoi\s*vao",
    "hem_nho": r"hem\s*(?:nho|ba\s*gac|xe\s*may)|hem\s*[123]\s*m",
    "so_hong_rieng": r"so\s*hong\s*rieng|\bshr\b",
    "giay_tay": r"giay\s*tay|vi\s*bang",
    "ngop_bank": r"ngop|ngan\s*hang\s*siet|\bno\s*bank\b|ket\s*tien",
    # "gấp" và "gặp" giống hệt nhau sau khi bỏ dấu, mà "gặp" là từ cực thường gặp trong
    # tin rao ("hẹn gặp", "gặp chính chủ") — cờ bán gấp vì thế nhiễu thẳng vào narrative
    # SHAP. Chỉ nhận "gấp" khi nó đứng cạnh từ chỉ việc bán/cần.
    "ban_gap": r"(?:ban|can|thanh\s*ly|xa)\s*gap|gap\s*(?:ban|can|thanh\s*ly)"
               r"|can\s*ban\s*nhanh|ban\s*nhanh",
    "giam_gia": r"giam\s*gia|giam\s*\d|cat\s*lo|\blo\s*von\b",
    "moi_xay": r"moi\s*xay|nha\s*moi|xay\s*moi|vao\s*o\s*ngay",
    "cu_nat": r"nha\s*cu|nha\s*nat|can\s*sua|xuong\s*cap",
    "full_noi_that": r"full\s*noi\s*that|noi\s*that\s*day\s*du|hoan\s*thien",
    "gan_cho": r"gan\s*cho|sat\s*cho",
    "gan_truong": r"gan\s*truong|truong\s*hoc",
    "gan_benh_vien": r"gan\s*benh\s*vien",
    "gan_metro": r"metro|tuyen\s*so\s*\d",
    "kinh_doanh": r"kinh\s*doanh|\bkd\b|buon\s*ban|cho\s*thue\s*duoc",
    "thang_may": r"thang\s*may",
    "san_thuong": r"san\s*thuong",
    "o_to_do_cua": r"o\s*to\s*(?:do|ngu)\s*cua|oto\s*do\s*cua|xe\s*hoi\s*do\s*cua",
    "khu_dan_cu": r"khu\s*dan\s*cu|\bkdc\b|khu\s*compound",
    "no_hau": r"no\s*hau",
    "dinh_lo_gioi": r"lo\s*gioi|quy\s*hoach|dinh\s*quy\s*hoach",
    "chinh_chu": r"chinh\s*chu",
    "so_chung": r"so\s*chung|chung\s*so",
}

_COMPILED_FLAGS = {name: re.compile(pattern) for name, pattern in TEXT_FLAGS.items()}


def deaccent(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", unicodedata.normalize("NFKC", str(text)))
    without = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return without.replace("đ", "d").replace("Đ", "D").lower()


def extract_flags(text: str | None) -> dict[str, int]:
    """24 cờ nhị phân từ một đoạn mô tả."""
    flat = deaccent(text or "")
    return {name: int(bool(pattern.search(flat))) for name, pattern in _COMPILED_FLAGS.items()}
