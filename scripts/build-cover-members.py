"""Sinh khối metadata trang bìa cho báo cáo, từ cùng nguồn với file Excel bài nộp.

Trang bìa, file Excel danh sách nhóm và bảng phân công ở slide đều đọc
`config/thanh-vien.yaml`, nên ba tài liệu không thể ghi ba danh sách khác nhau.

Trang bìa được dựng bằng KHỐI METADATA của pandoc chứ không phải bằng một chương riêng.
Lý do: `--toc` chèn mục lục ngay sau khối metadata và trước phần thân, nên một "chương
trang bìa" sẽ nằm SAU mục lục. Đưa vào metadata thì trang bìa ra đúng trang đầu ở cả
bản Word lẫn bản PDF.

    python scripts/build-cover-members.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "thanh-vien.yaml"
OUTPUT = ROOT / "reports" / "scientific-report" / "00-metadata.yaml"

TITLE = "DỰ BÁO GIÁ NHÀ TẠI THÀNH PHỐ HỒ CHÍ MINH TỪ DỮ LIỆU TIN RAO VẶT"
SUBTITLE = "Báo cáo đồ án cuối kỳ · Môn Trí tuệ nhân tạo · Đề tài số 5"
SCHOOL = "Trường Đại học Công nghệ Thông tin, ĐHQG-HCM · Khoa Khoa học Máy tính"
LECTURER = "Nguyễn Đình Hiển"
PLACE_DATE = "Thành phố Hồ Chí Minh, tháng 08 năm 2026"


def main() -> int:
    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    members = data.get("thanh_vien") or []
    group = data.get("nhom", "")
    course = data.get("lop", "")

    authors = [SCHOOL, f"Mã lớp: {course}", f"Giảng viên hướng dẫn: {LECTURER}", ""]
    authors.append(f"Nhóm {group}")
    if members:
        authors += [f"{m['ho_ten']} · {m['mssv']} · {m['lop']}" for m in members]
    else:
        authors.append("(chưa có danh sách thành viên)")

    payload = {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "author": authors,
        "date": PLACE_DATE,
        "lang": "vi",
        "toc": True,
        "toc-depth": 3,
        "numbersections": True,
        "figureTitle": "Hình",
        "tableTitle": "Bảng",
    }

    text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=200)
    OUTPUT.write_text(
        "---\n"
        "# SINH TỰ ĐỘNG bằng scripts/build-cover-members.py, đừng sửa tay.\n"
        "# Danh sách thành viên lấy từ config/thanh-vien.yaml.\n"
        + text + "---\n",
        encoding="utf-8",
    )

    print(f"{len(members)} thành viên → {OUTPUT.relative_to(ROOT)}")
    if not members:
        print("CHÚ Ý: config/thanh-vien.yaml chưa có thành viên nào")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
