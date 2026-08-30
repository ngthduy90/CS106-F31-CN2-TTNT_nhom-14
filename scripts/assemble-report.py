"""Ghép các chương báo cáo, chèn bảng sinh tự động vào đúng chỗ.

Chương báo cáo viết bằng tay, nhưng mọi con số phải đến từ file bảng do pipeline sinh
ra. Cơ chế: trong chương đặt một dòng đánh dấu

    <!-- include: reports/tables/data-funnel.md -->

Script thay dòng đó bằng nội dung file, đã bỏ dòng tiêu đề cấp 1 (chương đã có tiêu đề
riêng). Nhờ vậy sửa số liệu là chạy lại pipeline chứ không phải sửa tay báo cáo, và
không bao giờ có chuyện bảng trong báo cáo lệch với bảng trong `reports/tables/`.

    python scripts/assemble-report.py            # ghi ra reports/scientific-report/_built/
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reports" / "scientific-report"
BUILD = SRC / "_built"

INCLUDE = re.compile(r"^<!--\s*include:\s*(.+?)\s*-->\s*$", re.MULTILINE)
PLACEHOLDER = re.compile(r"\{\{T[0-9.]*[^}]*\}\}")


def _strip_title(text: str) -> str:
    """Bỏ tiêu đề cấp 1 của file bảng: chương đã có tiêu đề của nó."""
    lines = text.strip().split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def _demote(text: str, levels: int = 2) -> str:
    """Hạ cấp tiêu đề của bảng để nằm gọn dưới mục của chương."""
    return re.sub(r"^(#{1,5}) ", lambda m: "#" * (len(m.group(1)) + levels) + " ", text,
                  flags=re.MULTILINE)


def assemble(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    missing: list[str] = []

    def replace(match: re.Match) -> str:
        target = ROOT / match.group(1)
        demote = 2 if "scientific-report" in str(path) else 0
        if not target.exists():
            missing.append(match.group(1))
            return (
                f"> **Chưa có `{match.group(1)}`.** Chạy lại pipeline để sinh bảng này."
            )
        body = target.read_text(encoding="utf-8")
        # Slide giữ nguyên tiêu đề cấp 1 vì mỗi tiêu đề là một slide.
        if demote:
            return _demote(_strip_title(body), demote)
        return body.strip()

    return INCLUDE.sub(replace, text), missing


def assemble_slides() -> list[str]:
    """Ghép slide theo cùng cơ chế, ghi ra reports/slides/_built/slides.md."""
    source = ROOT / "reports" / "slides" / "slides.md"
    if not source.exists():
        return []
    text, missing = assemble(source)
    target = ROOT / "reports" / "slides" / "_built"
    target.mkdir(parents=True, exist_ok=True)
    (target / "slides.md").write_text(text, encoding="utf-8")
    return missing


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    all_missing: list[str] = []
    placeholders: list[str] = []

    for path in sorted(SRC.glob("*.md")):
        text, missing = assemble(path)
        all_missing += missing
        placeholders += [f"{path.name}: {m}" for m in PLACEHOLDER.findall(text)]
        (BUILD / path.name).write_text(text, encoding="utf-8")

    for path in SRC.glob("*.yaml"):
        (BUILD / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    all_missing += assemble_slides()

    if all_missing:
        print("THIẾU bảng: " + ", ".join(sorted(set(all_missing))))
    if placeholders:
        print("CÒN placeholder chưa điền:")
        for item in placeholders:
            print("   " + item)

    print(f"đã ghép → {BUILD.relative_to(ROOT)}")
    return 1 if placeholders else 0


if __name__ == "__main__":
    sys.exit(main())
