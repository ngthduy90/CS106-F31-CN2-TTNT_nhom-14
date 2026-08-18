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
SRC="$ROOT/reports/slides/slides.md"
OUT="$ROOT/reports/slides/slides.pptx"

if grep -q "<!-- SLIDE:" "$SRC"; then
  echo "CHÚ Ý: còn chỗ cần chèn bảng thủ công:"
  grep -n "<!-- SLIDE:" "$SRC" | cut -c1-110
  echo
fi

pandoc "$SRC" \
  --from=markdown \
  --resource-path="$ROOT/reports/slides:$ROOT/reports/figures:$ROOT" \
  --slide-level=1 \
  -o "$OUT"

echo "Xong: $OUT"
