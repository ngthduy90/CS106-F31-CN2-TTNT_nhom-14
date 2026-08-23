"""T6.12 — sinh `danh-sach-nhom.xlsx` từ `config/thanh-vien.yaml`.

Đề yêu cầu file Excel ba cột: Họ tên, MSSV, Lớp. Script đọc từ một file YAML duy nhất
để danh sách thành viên chỉ tồn tại ở một chỗ; trang bìa báo cáo và slide phân công cũng
lấy từ đó, nên không thể xảy ra chuyện ba tài liệu ghi ba danh sách khác nhau.

Script **từ chối chạy** nếu danh sách còn ở trạng thái mẫu chưa điền, thay vì tạo ra một
file Excel trông có vẻ hợp lệ.

    python scripts/build-member-list.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "thanh-vien.yaml"
OUTPUT = ROOT / "submission" / "danh-sach-nhom.xlsx"


def main() -> int:
    if not SOURCE.exists():
        print(f"Chưa có {SOURCE.relative_to(ROOT)}")
        return 1

    data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    members = data.get("thanh_vien") or []

    problems = [
        f"thành viên #{i + 1} thiếu {field}"
        for i, member in enumerate(members)
        for field in ("ho_ten", "mssv", "lop")
        if not str(member.get(field) or "").strip()
    ]
    if not members:
        problems.append("danh sách rỗng")
    if problems:
        print("CHƯA SINH ĐƯỢC FILE — danh sách chưa đầy đủ:")
        for problem in problems:
            print(f"  - {problem}")
        print(f"\nSửa {SOURCE.relative_to(ROOT)} rồi chạy lại.")
        return 1

    frame = pd.DataFrame(
        [
            {"Họ tên": m["ho_ten"], "MSSV": str(m["mssv"]), "Lớp": m["lop"]}
            for m in members
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=f"Nhom {data.get('nhom', '')}".strip())
        sheet = writer.sheets[list(writer.sheets)[0]]
        for column, width in zip("ABC", (28, 14, 18)):
            sheet.column_dimensions[column].width = width

    print(f"{len(frame)} thành viên → {OUTPUT.relative_to(ROOT)}")
    if len(frame) == 1:
        print("CHÚ Ý: danh sách hiện chỉ có 1 người. Bổ sung các thành viên còn lại.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
