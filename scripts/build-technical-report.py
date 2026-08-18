"""T6.9 — sinh technical report: bảng mô tả hàm + phần văn xuôi về kiến trúc.

Đề yêu cầu một tài liệu RIÊNG mô tả hoạt động của từng hàm trong code. Bảng hàm được
sinh tự động từ chữ ký và docstring bằng `ast` (không import module nào, nên không phụ
thuộc việc cài đủ thư viện), còn phần kiến trúc và luồng chạy được viết tay ở
`reports/technical-report/00-kien-truc.md`.

Ranh giới đó là cố ý: cái máy làm tốt là liệt kê đầy đủ và không bỏ sót; cái người phải
làm là giải thích vì sao các mảnh ghép lại với nhau như vậy.

    python scripts/build-technical-report.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "src"
OUTPUT = ROOT / "reports" / "technical-report" / "02-bang-mo-ta-ham.md"

MODULE_ROLES = {
    "config": "Hằng số dùng chung: đường dẫn, mã vùng, ngưỡng chất lượng, seed",
    "crawl": "Thu thập dữ liệu và bảo vệ thông tin cá nhân",
    "preprocess": "Làm sạch, trích đặc trưng định lượng, chuẩn hoá địa chỉ",
    "features": "Biểu diễn đặc trưng cho mô hình",
    "models": "Danh mục mô hình và baseline",
    "evaluation": "Chia tập, chạy thí nghiệm, chỉ số, bảng biểu, phân tích",
    "demo": "Web app dự báo",
    "utils": "Ghi nhật ký và run manifest",
}


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Chữ ký hàm dạng chuỗi, dựng lại từ cây cú pháp."""
    args = node.args
    parts: list[str] = []

    for index, arg in enumerate(args.args):
        text = arg.arg
        if arg.annotation is not None:
            text += f": {ast.unparse(arg.annotation)}"
        offset = len(args.args) - len(args.defaults)
        if index >= offset:
            text += f" = {ast.unparse(args.defaults[index - offset])}"
        parts.append(text)

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        text = arg.arg
        if default is not None:
            text += f" = {ast.unparse(default)}"
        parts.append(text)
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{node.name}({', '.join(parts)}){returns}"


def summary(node) -> str:
    """Dòng đầu của docstring — phần trả lời "hàm này làm gì"."""
    text = ast.get_docstring(node) or ""
    first = text.strip().split("\n\n")[0].replace("\n", " ").strip()
    return " ".join(first.split()) or "_(chưa có mô tả)_"


def collect(path: Path) -> list[dict]:
    """Mọi hàm và lớp công khai của một file, kèm chữ ký và tóm tắt."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module = str(path.relative_to(ROOT))
    rows: list[dict] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue
            rows.append({"module": module, "kind": "hàm", "signature": signature(node),
                         "summary": summary(node)})
        elif isinstance(node, ast.ClassDef):
            rows.append({"module": module, "kind": "lớp", "signature": node.name,
                         "summary": summary(node)})
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name.startswith("_") and child.name != "__init__":
                        continue
                    rows.append({
                        "module": module,
                        "kind": "phương thức",
                        "signature": f"{node.name}.{signature(child)}",
                        "summary": summary(child),
                    })
    return rows


def main() -> None:
    files = sorted(p for p in SRC.rglob("*.py") if p.name != "__init__.py")
    lines = [
        "# Bảng mô tả hàm",
        "",
        "Bảng này sinh tự động từ chữ ký và docstring trong `src/` bằng",
        "`scripts/build-technical-report.py`. Sửa docstring rồi chạy lại script; không",
        "sửa tay file này.",
        "",
    ]

    total = 0
    for path in files:
        rows = collect(path)
        if not rows:
            continue
        relative = path.relative_to(SRC)
        package = relative.parts[0] if len(relative.parts) > 1 else relative.stem
        role = MODULE_ROLES.get(package, "")

        lines += [
            f"## `src/{relative}`",
            "",
            f"_{role}_" if role else "",
            "",
            "| Loại | Chữ ký | Mô tả |",
            "|---|---|---|",
        ]
        for row in rows:
            escaped = row["signature"].replace("|", "\\|")
            text = row["summary"].replace("|", "\\|")
            lines.append(f"| {row['kind']} | `{escaped}` | {text} |")
        lines.append("")
        total += len(rows)

    lines += [
        "---",
        "",
        f"Tổng cộng {total} hàm, lớp và phương thức công khai trong {len(files)} tệp mã nguồn.",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{total} mục → {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
