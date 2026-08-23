"""Kho dữ liệu thô: JSONL bất biến, khử trùng theo id, chạy lại không tải trùng.

Bố cục: `data/raw/<nguồn>/<ngày crawl>/<phân vùng>.jsonl`, một dòng JSON mỗi tin, đúng
yêu cầu "một file mỗi quận mỗi ngày" của runbook 01 §3.6. File thô không bao giờ được
sửa; mọi chỉnh sửa xảy ra ở bước tiền xử lý.

Việc chống trùng dựa trên id do sàn cấp: trước khi ghi, kho đọc lại toàn bộ id đã có
của cùng nguồn (mọi ngày crawl) nên chạy lại script chỉ bổ sung tin mới. Checkpoint chỉ
lưu vị trí quét để không phải phân trang lại từ đầu.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from src import config
from src.crawl.pii import scrub_record


def slugify(value: str) -> str:
    """"Quận 12" → "quan-12". Dùng cho tên file, nên phải không dấu và ổn định."""
    stripped = unicodedata.normalize("NFD", value)
    ascii_only = "".join(c for c in stripped if unicodedata.category(c) != "Mn")
    ascii_only = ascii_only.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


class RawStore:
    """Ghi tin thô vào JSONL, tự bỏ tin đã có và tự xoá thông tin cá nhân."""

    def __init__(
        self,
        source: str,
        partition: str,
        id_field: str,
        crawl_day: date | None = None,
        root: Path | None = None,
    ) -> None:
        self.source = source
        self.partition = slugify(partition)
        self.id_field = id_field
        self.crawl_day = crawl_day or date.today()
        self.root = (root or config.DATA_RAW) / source
        self.path = self.root / self.crawl_day.isoformat() / f"{self.partition}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.seen_ids = self._load_seen_ids()
        self.written = 0
        self.skipped_duplicate = 0
        self.pii_redactions = 0

    def _load_seen_ids(self) -> set[str]:
        """Mọi id đã có của nguồn này, gộp qua tất cả các ngày crawl trước."""
        seen: set[str] = set()
        for file in sorted(self.root.rglob("*.jsonl")):
            for record in read_jsonl(file):
                value = record.get(self.id_field)
                if value is not None:
                    seen.add(str(value))
        return seen

    def append(self, record: dict[str, Any], source_url: str = "") -> bool:
        """Ghi một tin. Trả về False nếu id đã có trong kho."""
        key = record.get(self.id_field)
        if key is None:
            raise ValueError(f"tin thiếu trường id {self.id_field!r}")
        key = str(key)
        if key in self.seen_ids:
            self.skipped_duplicate += 1
            return False

        clean, redactions = scrub_record(record)
        clean["_source"] = self.source
        clean["_source_url"] = source_url
        clean["_collected_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(clean, ensure_ascii=False) + "\n")

        self.seen_ids.add(key)
        self.written += 1
        self.pii_redactions += redactions
        return True


class Checkpoint:
    """Vị trí quét cuối cùng, để chạy lại không phân trang lại từ đầu."""

    def __init__(self, source: str, partition: str, root: Path | None = None) -> None:
        folder = (root or config.DATA_RAW) / "_checkpoints"
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{source}__{slugify(partition)}.json"
        self.state: dict[str, Any] = {}
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def save(self, **values: Any) -> None:
        self.state.update(values)
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def reset(self) -> None:
        self.state = {}
        self.path.unlink(missing_ok=True)


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Đọc từng dòng JSON, bỏ qua dòng hỏng thay vì làm gãy cả lần chạy."""
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def iter_raw(source: str, root: Path | None = None) -> Iterator[dict[str, Any]]:
    """Mọi tin thô của một nguồn, qua mọi ngày crawl."""
    folder = (root or config.DATA_RAW) / source
    if not folder.exists():
        return
    for file in sorted(folder.rglob("*.jsonl")):
        yield from read_jsonl(file)
