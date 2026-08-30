"""Chuẩn hoá địa chỉ và xử lý sáp nhập hành chính 2025 (runbook 02 §2).

Từ 01/07/2025 cả nước bỏ cấp quận/huyện, riêng TP.HCM còn 168 phường/xã. Dữ liệu của
dự án nằm ở cả hai hệ: tin crawl 2026 ghi phường MỚI, bộ lịch sử và mogi ghi phường
CŨ. Không quy về một hệ thì cùng một khu phố bị tách thành nhiều nhóm và mọi thống kê
theo địa bàn đều sai.

**Hệ quy chiếu chọn: CŨ (quận + phường cũ)** — theo phương án 2a của runbook. Phần lớn
dữ liệu đã ở hệ này, quận cũ là mức phân giải mà thị trường BĐS quen dùng, và 168
phường mới quá mịn cho vài nghìn tin.

**Bảng ánh xạ mới→cũ dựng từ chính dữ liệu crawl**, không tải từ repo ngoài. Lý do:
API Chợ Tốt trả CẢ HAI tên phường cho cùng một tin (`ward_name` hệ cũ và `ward_name_v3`
hệ mới), nên mỗi tin là một cặp ánh xạ do chính sàn khẳng định. Bảng dựng theo cách này
đúng với đúng bộ dữ liệu đang dùng, có ngày chốt rõ ràng, và không kéo theo ràng buộc
license của bên thứ ba. Hạn chế phải nêu: bảng chỉ phủ các phường xuất hiện trong dữ
liệu đã crawl.

Cạm bẫy đã xử lý:
- Một phường mới gộp từ phường của HAI quận cũ → chọn quận chiếm đa số, và lưu lại tỷ
  lệ đa số đó để biết ánh xạ nào đáng ngờ.
- "Phường 1" có ở cả chục quận → luôn ánh xạ theo cặp (phường, quận), không bao giờ
  theo tên phường đứng một mình.
- Biến thể chữ: `Q.12`, `Quận 12`, `quan 12`, `12` quy về một dạng chuẩn duy nhất.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from src import config
from src.crawl.store import iter_raw

MAPPING_PATH = config.DATA_EXTERNAL / "ward_mapping_new_to_old.json"

# Quận/huyện TP.HCM theo hệ CŨ. Tên có chữ giữ nguyên, quận số chuẩn hoá thành "Quận N".
NAMED_DISTRICTS = [
    "Bình Tân",
    "Bình Thạnh",
    "Gò Vấp",
    "Phú Nhuận",
    "Tân Bình",
    "Tân Phú",
    "Thủ Đức",
    "Bình Chánh",
    "Cần Giờ",
    "Củ Chi",
    "Hóc Môn",
    "Nhà Bè",
]

UNKNOWN = "không rõ"


def deaccent(text: str) -> str:
    compatible = unicodedata.normalize("NFKC", str(text))
    decomposed = unicodedata.normalize("NFD", compatible)
    without = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", without.replace("đ", "d").replace("Đ", "D").lower()).strip()


_NAMED_LOOKUP = {deaccent(name): name for name in NAMED_DISTRICTS}
# "quận 12", "q.12", "q 12", "12"
_NUMBERED_DISTRICT = re.compile(r"\b(?:quan|q)\s*\.?\s*(\d{1,2})\b|^(\d{1,2})$")
_NUMBERED_WARD = re.compile(r"\b(?:phuong|p)\s*\.?\s*(\d{1,2})\b|^(\d{1,2})$")


def normalise_district(text: str | None) -> str:
    """Mọi cách viết một quận → một chuỗi chuẩn duy nhất.

    Bộ lịch sử ghi quận số trần ("12"), Chợ Tốt ghi "Quận 12", mogi ghi "Quận 12" trong
    một chuỗi địa chỉ dài. Cả ba phải ra cùng một giá trị, nếu không one-hot encoding
    sẽ tạo ba cột cho cùng một quận.
    """
    if not text:
        return UNKNOWN
    flat = deaccent(text)

    for key, name in _NAMED_LOOKUP.items():
        if re.search(rf"\b{re.escape(key)}\b", flat):
            return name

    match = _NUMBERED_DISTRICT.search(flat)
    if match:
        number = int(match.group(1) or match.group(2))
        if 1 <= number <= 12:
            return f"Quận {number}"
    return UNKNOWN


def normalise_ward(text: str | None) -> str:
    """"13" / "P.13" / "Phường 13" → "Phường 13"; phường có tên giữ nguyên chữ hoa đầu."""
    if not text:
        return UNKNOWN
    raw = re.sub(r"\s+", " ", str(text)).strip()
    flat = deaccent(raw)

    match = _NUMBERED_WARD.search(flat)
    if match:
        return f"Phường {int(match.group(1) or match.group(2))}"

    cleaned = re.sub(r"^(?:phường|phuong|p\.?|xã|xa|x\.?)\s+", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" ,.")
    return f"Phường {cleaned}" if cleaned else UNKNOWN


@dataclass(frozen=True)
class Address:
    street: str
    ward: str
    district: str

    @property
    def resolved(self) -> bool:
        return self.district != UNKNOWN


def parse_address(text: str | None) -> Address:
    """Chuỗi địa chỉ tự do → (đường, phường, quận).

    mogi ghi "Trường Chinh, Phường Tân Thới Nhất, Quận 12, TPHCM" — tách theo dấu phẩy
    là đủ. Với chuỗi không theo khuôn, hàm vẫn cố tìm quận và phường ở bất kỳ đoạn nào.
    """
    if not text:
        return Address(UNKNOWN, UNKNOWN, UNKNOWN)

    parts = [part.strip() for part in str(text).split(",") if part.strip()]
    street = ward = district = UNKNOWN

    for part in parts:
        flat = deaccent(part)
        if district == UNKNOWN:
            found = normalise_district(part)
            if found != UNKNOWN:
                district = found
                continue
        if ward == UNKNOWN and re.match(r"^(?:phuong|p\.?\s|xa|x\.?\s)", flat):
            ward = normalise_ward(part)
            continue
        if street == UNKNOWN and not re.search(r"\b(?:tphcm|tp\.?\s*hcm|ho chi minh|viet nam)\b", flat):
            street = part

    return Address(street, ward, district)


# --- bảng ánh xạ phường mới → phường cũ --------------------------------------


def build_ward_mapping(source: str = "chotot") -> dict:
    """Dựng bảng ánh xạ từ các cặp (phường mới, phường cũ, quận cũ) trong kho thô."""
    pairs: dict[str, Counter] = defaultdict(Counter)

    for record in iter_raw(source):
        new_ward = record.get("ward_name_v3")
        old_ward = record.get("ward_name")
        old_district = record.get("area_name")
        if not (new_ward and old_ward and old_district):
            continue
        key = normalise_ward(new_ward)
        value = (normalise_ward(old_ward), normalise_district(old_district))
        pairs[key][value] += 1

    mapping = {}
    for new_ward, counter in pairs.items():
        (old_ward, old_district), top = counter.most_common(1)[0]
        total = sum(counter.values())
        mapping[new_ward] = {
            "old_ward": old_ward,
            "old_district": old_district,
            "support": total,
            "majority_share": round(top / total, 3),
            "alternatives": [
                {"old_ward": w, "old_district": d, "count": n}
                for (w, d), n in counter.most_common()[1:]
            ],
        }

    return {
        "snapshot_date": date.today().isoformat(),
        "derived_from": f"cặp ward_name / ward_name_v3 trong kho thô {source}",
        "n_new_wards": len(mapping),
        "mapping": mapping,
    }


def save_ward_mapping(source: str = "chotot") -> dict:
    table = build_ward_mapping(source)
    MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAPPING_PATH.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
    return table


def load_ward_mapping() -> dict:
    if not MAPPING_PATH.exists():
        return save_ward_mapping()
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


class WardResolver:
    """Quy một địa chỉ về hệ cũ, ưu tiên thông tin sẵn có rồi mới tra bảng."""

    def __init__(self, table: dict | None = None) -> None:
        table = table or load_ward_mapping()
        self.mapping = table["mapping"]
        self.snapshot_date = table["snapshot_date"]
        self.stats = Counter()

    def resolve(
        self,
        ward_old: str | None = None,
        ward_new: str | None = None,
        district: str | None = None,
    ) -> tuple[str, str, str]:
        """Trả về (phường cũ, quận cũ, nguồn đơn vị) — nguồn để báo cáo minh bạch."""
        known_district = normalise_district(district) if district else UNKNOWN

        if ward_old:
            ward = normalise_ward(ward_old)
            if ward != UNKNOWN:
                self.stats["hệ cũ sẵn có"] += 1
                return ward, known_district, "cũ"

        if ward_new:
            ward = normalise_ward(ward_new)
            entry = self.mapping.get(ward)
            if entry:
                self.stats["tra bảng mới→cũ"] += 1
                return (
                    entry["old_ward"],
                    known_district if known_district != UNKNOWN else entry["old_district"],
                    "mới (đã ánh xạ)",
                )

        self.stats["không ánh xạ được"] += 1
        return UNKNOWN, known_district, "không rõ"

    def unmapped_rate(self) -> float:
        total = sum(self.stats.values())
        return self.stats["không ánh xạ được"] / total if total else 0.0
