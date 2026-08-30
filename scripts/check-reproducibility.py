"""T7.2 — kiểm tra tính tái lập.

Hai phép kiểm, mỗi phép trả lời một câu khác nhau:

1. **Bảng sinh lại giống hệt.** Chạy `render_tables` hai lần và so từng byte. Nếu khác
   nhau thì có chỗ nào đó trong đường sinh bảng đang phụ thuộc thời điểm chạy hoặc thứ
   tự duyệt dict, và con số trong báo cáo sẽ trôi mỗi lần build lại.
2. **Huấn luyện lại cho ra cùng chỉ số.** Fit lại một mô hình trên cùng fold với cùng
   seed, so tới ba chữ số thập phân. Đây là phép kiểm bắt được các nguồn ngẫu nhiên bị
   bỏ sót seed.

    python scripts/check-reproducibility.py
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def check_tables() -> list[str]:
    """Sinh lại toàn bộ bảng và so với bản hiện có."""
    # Bảng của slide cũng do render_tables sinh ra và cũng là chỗ thầy soi lệch số giữa
    # hai tài liệu, nên gate phải phủ luôn, không chỉ reports/tables.
    slide_dir = config.REPORTS / "slides" / "tables"
    tables = sorted(config.TABLES.glob("*.md")) + sorted(slide_dir.glob("slide-*.md"))
    if not tables:
        return ["chưa có bảng nào để so — chạy pipeline trước"]

    snapshot = Path(tempfile.mkdtemp())
    before = {}
    for path in tables:
        shutil.copy2(path, snapshot / path.name)
        before[path.name] = (path, _digest(path))

    result = subprocess.run(
        [sys.executable, "-m", "src.evaluation.render_tables"],
        cwd=ROOT, capture_output=True, check=False,
    )
    # Không nhìn returncode thì render_tables crash cũng không ghi lại file nào, digest
    # trước với sau trùng nhau theo định nghĩa, và gate in "Tái lập được" đúng trong ca
    # nó sinh ra để bắt.
    if result.returncode != 0:
        shutil.rmtree(snapshot, ignore_errors=True)
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        return [f"render_tables thoát mã {result.returncode}:\n{stderr}"]

    problems = []
    for name, (path, digest) in before.items():
        if not path.exists():
            problems.append(f"{name}: biến mất sau khi sinh lại")
        elif _digest(path) != digest:
            problems.append(f"{name}: nội dung đổi giữa hai lần sinh")
    shutil.rmtree(snapshot, ignore_errors=True)
    return problems


def check_training() -> list[str]:
    """Fit hai lần cùng một mô hình trên cùng fold, so chỉ số tới 3 chữ số."""
    import pandas as pd

    from src.evaluation.metrics import METRIC_ORDER, compute_metrics
    from src.evaluation.runner import build_estimator
    from src.evaluation.splits import make_splits
    from src.features.build import build_feature_frame
    from src.models.registry import build_registry

    processed = config.DATA_PROCESSED / "listings.parquet"
    if not processed.exists():
        return ["chưa có data/processed/listings.parquet — chạy `make prep` trước"]

    frame = pd.read_parquet(processed)
    subset = frame[frame["source"] == "chotot"].reset_index(drop=True)
    if len(subset) < 300:
        return ["quá ít dòng để kiểm huấn luyện"]

    split = make_splits(subset, "e1_chotot")
    features = build_feature_frame(subset)
    target = subset["total_price_vnd"].to_numpy(dtype="float64")
    spec = next(s for s in build_registry() if s.name == "Random Forest")

    runs = []
    for _ in range(2):
        estimator = build_estimator(spec)
        estimator.fit(features.iloc[split["train"]], target[split["train"]])
        runs.append(compute_metrics(target[split["test"]], estimator.predict(features.iloc[split["test"]])))

    return [
        f"{metric}: {runs[0][metric]:.6f} ≠ {runs[1][metric]:.6f}"
        for metric in METRIC_ORDER
        if round(runs[0][metric], 3) != round(runs[1][metric], 3)
    ]


def main() -> int:
    print("== Sinh lại bảng hai lần ==")
    table_problems = check_tables()
    print("  giống hệt" if not table_problems else "\n".join(f"  {p}" for p in table_problems))

    print("\n== Huấn luyện lại cùng seed ==")
    training_problems = check_training()
    print("  khớp tới 3 chữ số" if not training_problems
          else "\n".join(f"  {p}" for p in training_problems))

    print(f"\nseed = {config.SEED}, phiên bản thư viện chốt ở requirements-lock.txt")

    if table_problems or training_problems:
        print("\nKHÔNG TÁI LẬP ĐƯỢC — xem các dòng trên.")
        return 1
    print("\nTái lập được.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
