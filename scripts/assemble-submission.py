"""T6.14–T6.16 — ráp thư mục nộp và chạy hai phép quét cuối.

Thư mục nộp theo runbook 04 §1: `submission/[Project AI-UIT] - Nhóm 14/` với bảy hạng
mục. Script chỉ SAO CHÉP từ các sản phẩm đã build, không sinh nội dung mới — nếu một
hạng mục chưa có thì nó báo thiếu chứ không tạo ra một file rỗng cho đủ số.

Kèm hai phép quét bắt buộc trước khi nộp:

- **Đối chiếu số liệu** giữa báo cáo, slide, README và model card. Thầy dễ soi nhất là
  chỗ cùng một con số được làm tròn khác nhau ở hai tài liệu.
- **Quét chéo môn**: tìm mã môn hoặc tên giảng viên của môn khác lọt vào bài nộp.

    python scripts/assemble-submission.py
    python scripts/assemble-submission.py --check-only
"""

from __future__ import annotations

import argparse
import re
import shutil
import zipfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = "Nhóm 14"
TARGET = ROOT / "submission" / f"[Project AI-UIT] - {GROUP}"

# (nguồn, tên trong thư mục nộp, bắt buộc)
ITEMS = [
    ("submission/danh-sach-nhom.xlsx", "1. Danh sách nhóm.xlsx", True),
    ("reports/bao-cao-khoa-hoc.docx", "2. Báo cáo khoa học.docx", True),
    ("reports/slides/slides.pptx", "3. Slide thuyết trình.pptx", True),
    ("reports/technical-report/technical-report.docx", "5. Technical report.docx", True),
    ("docs/huong-dan-su-dung.md", "7. Hướng dẫn sử dụng.md", False),
]

# Thư mục mã nguồn: chép có chọn lọc, tuyệt đối không kéo theo dữ liệu.
CODE_INCLUDE = ["src", "tests", "scripts", "requirements.txt", "Makefile", "README.md", "docs"]
CODE_EXCLUDE = {"__pycache__", ".venv", ".pytest_cache", ".ipynb_checkpoints", ".DS_Store"}

# Mã môn và tên giảng viên của MÔN NÀY. Bất kỳ mã môn nào khác xuất hiện là lỗi.
OWN_COURSE = re.compile(r"CS106", re.IGNORECASE)
OTHER_COURSE = re.compile(r"\b(?:CS|IT|SE|MA|IE|NT|EC|ENG)\d{3}\b", re.IGNORECASE)

TEXT_SUFFIXES = {".md", ".py", ".txt", ".yaml", ".yml", ".sh", ".json", ".cfg", ".toml"}

# docx/pptx/xlsx là file ZIP chứa XML: đọc thẳng bằng read_text ra chuỗi nhị phân vô
# nghĩa, nên hai phép quét "bắt buộc" từng mù với ĐÚNG bốn file giáo viên sẽ mở. Không
# cần thư viện mới, chỉ cần bung phần XML bên trong.
OFFICE_SUFFIXES = {".docx", ".pptx", ".xlsx"}


def _read_searchable_text(path: Path) -> str | None:
    """Nội dung tìm kiếm được của một file, kể cả file Office."""
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None
    if suffix in OFFICE_SUFFIXES:
        try:
            with zipfile.ZipFile(path) as bundle:
                parts = [
                    name for name in bundle.namelist()
                    if name.endswith(".xml") and not name.startswith("docProps/thumbnail")
                ]
                return "\n".join(
                    bundle.read(name).decode("utf-8", errors="ignore") for name in parts
                )
        except (zipfile.BadZipFile, OSError):
            return None
    return None

# Thư mục không bao giờ nằm trong bài nộp. Khi chạy --check-only trên chính repo, phải
# bỏ qua chúng, nếu không phép quét sẽ báo hàng chục "vi phạm" nằm trong .venv và data/
# — tức là kêu ầm ở nơi không có gì, và một phép quét hay kêu nhầm sẽ bị bỏ qua.
SKIP_DIRS = {".venv", ".git", "data", "node_modules", "__pycache__", ".pytest_cache", "_built"}


def _walk(root: Path, skip: set[str] | None = None):
    for path in root.rglob("*"):
        if (skip if skip is not None else SKIP_DIRS) & set(path.parts):
            continue
        if path.is_file():
            yield path


def copy_code(destination: Path) -> None:
    """Chép mã nguồn, bỏ cache và mọi thứ trong data/."""
    destination.mkdir(parents=True, exist_ok=True)
    for name in CODE_INCLUDE:
        source = ROOT / name
        if not source.exists():
            continue
        if source.is_dir():
            shutil.copytree(
                source,
                destination / name,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(*CODE_EXCLUDE),
            )
        else:
            shutil.copy2(source, destination / name)

    # Chép bảng và hình để người chấm đọc được kết quả mà không cần chạy lại.
    for folder in ("reports/tables", "reports/figures", "reports/results"):
        source = ROOT / folder
        if source.exists():
            shutil.copytree(source, destination / folder, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(*CODE_EXCLUDE))


def scan_cross_course(root: Path) -> list[str]:
    """Mã môn của môn khác lọt vào bài nộp (T6.16)."""
    hits: list[str] = []
    for path in _walk(root):
        text = _read_searchable_text(path)
        if text is None:
            continue
        for match in OTHER_COURSE.finditer(text):
            if OWN_COURSE.match(match.group(0)):
                continue
            line = text[: match.start()].count("\n") + 1
            hits.append(f"{path.relative_to(root)}:{line}: {match.group(0)}")
    return hits


def scan_data_leak(root: Path, inside_submission: bool = False) -> list[str]:
    """Dữ liệu thô lọt vào bài nộp — vi phạm cam kết không tái phân phối.

    Khi quét CÂY NỘP thì không được bỏ qua `data/`: một thư mục data lọt vào bài nộp
    chính là thứ phép quét này sinh ra để bắt. Bỏ qua nó chỉ đúng khi quét repo gốc.
    """
    suffixes = {".jsonl", ".parquet"}
    skip = (SKIP_DIRS - {"data"}) if inside_submission else SKIP_DIRS
    hits = []
    for path in _walk(root, skip=skip):
        if path.suffix.lower() not in suffixes and not (
            path.suffix.lower() == ".csv" and "tables" not in path.parts
        ):
            continue
        hits.append(str(path.relative_to(root)))
    return hits


def collect_metrics(root: Path) -> dict[str, set[str]]:
    """Mọi con số dạng phần trăm hoặc "x,yz tỷ" trong từng tài liệu, để đối chiếu (T6.15)."""
    # Đọc bản ĐÃ GHÉP nếu có: chương gốc không chứa con số nào, mọi số liệu do bước
    # ghép chèn vào từ reports/tables/. So trên bản gốc thì luôn ra 0 và phép đối chiếu
    # thành vô nghĩa.
    built = root / "reports" / "scientific-report" / "_built"
    documents = {
        "báo cáo": built if built.exists() else root / "reports" / "scientific-report",
        "slide": (root / "reports" / "slides" / "_built")
        if (root / "reports" / "slides" / "_built").exists()
        else root / "reports" / "slides",
        "README": root / "README.md",
        "model card": root / "docs" / "model-card.md",
    }
    # Bắt cả "13,88" đứng một mình trong ô bảng, không chỉ khi có đơn vị đi kèm: model
    # card ghi chỉ số dạng bảng nên con số không dính đơn vị, và bản so trước đây bỏ sót
    # đúng những chỗ dễ lệch nhất.
    number = re.compile(r"(?<![\d,.])\d{1,3},\d{1,3}(?:\s*(?:%|tỷ))?(?![\d,.])")
    found: dict[str, set[str]] = {}

    for label, path in documents.items():
        values: set[str] = set()
        files = [path] if path.is_file() else list(path.glob("*.md")) if path.exists() else []
        for file in files:
            text = file.read_text(encoding="utf-8", errors="ignore")
            values |= {" ".join(m.split()) for m in number.findall(text)}
        found[label] = values
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Ráp thư mục nộp và quét kiểm tra cuối")
    parser.add_argument("--check-only", action="store_true", help="chỉ quét, không chép file")
    parser.add_argument(
        "--strict-numbers",
        action="store_true",
        help="coi mọi con số chỉ có ở một tài liệu là lỗi (mặc định: chỉ liệt kê để rà tay)",
    )
    args = parser.parse_args()

    problems: list[str] = []

    if not args.check_only:
        if TARGET.exists():
            shutil.rmtree(TARGET)
        TARGET.mkdir(parents=True)

        for source, name, required in ITEMS:
            path = ROOT / source
            if path.exists():
                shutil.copy2(path, TARGET / name)
                print(f"  ✓ {name}")
            elif required:
                problems.append(f"THIẾU (bắt buộc): {source} → {name}")
            else:
                print(f"  – bỏ qua (chưa có): {name}")

        copy_code(TARGET / "4. Code")
        print("  ✓ 4. Code/")

        demo = ROOT / "submission" / "Demo"
        if demo.exists() and any(demo.iterdir()):
            shutil.copytree(demo, TARGET / "6. Demo", dirs_exist_ok=True)
            print("  ✓ 6. Demo/")
        else:
            problems.append("THIẾU: ảnh chụp / clip demo trong submission/Demo/")

    root = TARGET if TARGET.exists() else ROOT

    print("\n== Quét chéo môn ==")
    cross = scan_cross_course(root)
    print("  0 hit" if not cross else "\n".join(f"  {h}" for h in cross[:20]))
    if cross:
        problems.append(f"{len(cross)} chỗ nhắc mã môn khác")

    print("\n== Quét dữ liệu thô lọt vào bài nộp ==")
    leaks = scan_data_leak(root, inside_submission=root is not ROOT and root == TARGET)
    print("  0 file" if not leaks else "\n".join(f"  {h}" for h in leaks[:20]))
    if leaks:
        problems.append(f"{len(leaks)} file dữ liệu lọt vào bài nộp")

    print("\n== Đối chiếu số liệu giữa các tài liệu ==")
    metrics = collect_metrics(ROOT)
    for label, values in metrics.items():
        print(f"  {label}: {len(values)} con số")
    # Trước đây chỉ so slide với báo cáo rồi in ra cho vui: README và model card cũng
    # được thu thập nhưng không ai đối chiếu, và phép kiểm không thể làm hỏng lần chạy.
    reference = metrics.get("báo cáo", set())
    orphans = {
        label: sorted(values - reference)
        for label, values in metrics.items()
        if label != "báo cáo" and (values - reference)
    }
    for label, values in orphans.items():
        print(f"  Con số chỉ có ở {label}, không thấy trong báo cáo:")
        for value in values[:15]:
            print(f"    {value}")
    if orphans:
        print("  (kiểm tay: hoặc là số làm tròn khác, hoặc là số tài liệu đó tự thêm)")
        # Mặc định chỉ liệt kê: script không phân biệt được "làm tròn khác" với "mâu
        # thuẫn", mà một phép quét hay kêu nhầm thì sớm bị bỏ qua — đúng lý do repo này
        # đã ghi cho SKIP_DIRS. --strict-numbers biến nó thành điều kiện chặn khi cần.
        if args.strict_numbers:
            problems.append(
                "số liệu lệch giữa các tài liệu: "
                + ", ".join(f"{label} {len(values)} con số" for label, values in orphans.items())
            )

    print()
    if problems:
        print("CHƯA NỘP ĐƯỢC:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"Thư mục nộp sẵn sàng: {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
