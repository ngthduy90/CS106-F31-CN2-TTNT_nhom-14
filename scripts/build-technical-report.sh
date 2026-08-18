#!/bin/bash
# Dựng technical report (Word) — tài liệu RIÊNG mà đề yêu cầu, không gộp vào báo cáo khoa học.
#
#   bash scripts/build-technical-report.sh
#
# Bảng mô tả hàm được sinh lại trước khi build, nên nó luôn khớp với mã nguồn hiện tại
# thay vì khớp với mã nguồn của lần build trước.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/reports/technical-report"
OUT="$SRC/technical-report.docx"

"${PYTHON:-python}" "$ROOT/scripts/build-technical-report.py"

pandoc \
  "$SRC/00-kien-truc.md" \
  "$SRC/02-bang-mo-ta-ham.md" \
  --from=markdown \
  --metadata title="Technical report — Dự báo giá nhà TP.HCM từ dữ liệu rao vặt" \
  --metadata author="Nhóm 14 — CS106.F31.CN2" \
  --metadata lang=vi \
  --toc --toc-depth=2 \
  -o "$OUT"

echo "Xong: $OUT"
