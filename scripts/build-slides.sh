#!/bin/bash
# Dựng slide PowerPoint từ Markdown.
#
#   bash scripts/build-slides.sh
#
# Mỗi "---" là một slide. Số liệu trên slide phải lấy từ cùng file bảng mà báo cáo dùng
# (thầy dễ soi lệch số giữa slide và báo cáo), nên các chỗ cần bảng được đánh dấu
# "<!-- SLIDE: ... -->" và người trình bày chèn bảng rút gọn từ đúng file đó.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/reports/slides/slides.md"
SRC="$ROOT/reports/slides/_built/slides.md"
OUT="$ROOT/reports/slides/slides.pptx"

"${PYTHON:-python}" "$ROOT/scripts/assemble-report.py" || true

pandoc "$SRC" \
  --from=markdown \
  --resource-path="$ROOT/reports/slides/_built:$ROOT/reports/slides:$ROOT/reports/figures:$ROOT" \
  --slide-level=1 \
  -o "$OUT"

echo "Xong: $OUT"
