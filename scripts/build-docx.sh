#!/bin/bash
# Ghép các chương Markdown thành báo cáo Word (bài nộp) và một bản PDF để xem nhanh.
#
#   bash scripts/build-docx.sh
#
# Word là định dạng bắt buộc của bài nộp. Bản PDF chỉ để đọc lại trong lúc làm,
# không nộp. Trang bìa và mục lục tự động lấy từ reference.docx (T6.8); khi chưa có
# file đó, pandoc dùng style mặc định và mục lục vẫn tự sinh.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/reports/scientific-report"
OUT="$ROOT/reports"
REF="$SRC/reference.docx"
FILTER="$ROOT/scripts/pandoc/pdf-fixes.lua"

CHAPTERS=(
  "$SRC/00-metadata.yaml"
  "$SRC/01-gioi-thieu.md"
  "$SRC/02-du-lieu.md"
  "$SRC/03-phuong-phap.md"
  "$SRC/04-thi-nghiem-va-ket-qua.md"
  "$SRC/05-ket-luan.md"
  "$SRC/06-tai-lieu-tham-khao.md"
)

# Cảnh báo nếu còn placeholder chưa điền
if grep -rn "{{T" "$SRC"/*.md >/dev/null 2>&1; then
  echo "CHÚ Ý: báo cáo còn placeholder chưa điền:"
  grep -rno "{{T[0-9.]*[^}]*}}" "$SRC"/*.md | cut -c1-120
  echo
fi

COMMON=(
  --from=markdown+lists_without_preceding_blankline
  --resource-path="$SRC:$ROOT/reports/figures"
  --toc --toc-depth=3
  -M lang=vi
)

echo ">>> Word"
DOCX_OPTS=()
[ -f "$REF" ] && DOCX_OPTS+=(--reference-doc="$REF")
# ${arr[@]+...} vì bash 3.2 trên macOS coi mảng rỗng là biến chưa đặt khi set -u
pandoc "${CHAPTERS[@]}" "${COMMON[@]}" ${DOCX_OPTS[@]+"${DOCX_OPTS[@]}"} \
  -o "$OUT/bao-cao-khoa-hoc.docx"

echo ">>> PDF (bản xem nhanh)"
pandoc "${CHAPTERS[@]}" "${COMMON[@]}" \
  --pdf-engine=xelatex \
  --lua-filter="$FILTER" \
  -V header-includes="\\usepackage{xurl}" \
  -V geometry:a4paper -V geometry:margin=2.2cm \
  -V fontsize=11pt \
  -V mainfont=texgyrepagella \
  -V mainfontoptions="Extension=.otf, UprightFont=*-regular, BoldFont=*-bold, ItalicFont=*-italic, BoldItalicFont=*-bolditalic" \
  -V monofont=NotoSansMono \
  -V monofontoptions="Extension=.ttf, UprightFont=*-Regular, BoldFont=*-Bold, AutoFakeSlant=0.2, Scale=0.85" \
  -V colorlinks=true -V linkcolor=NavyBlue -V urlcolor=NavyBlue -V toccolor=NavyBlue \
  -o "$OUT/bao-cao-khoa-hoc.pdf"

echo "Xong: $OUT/bao-cao-khoa-hoc.docx và .pdf"
