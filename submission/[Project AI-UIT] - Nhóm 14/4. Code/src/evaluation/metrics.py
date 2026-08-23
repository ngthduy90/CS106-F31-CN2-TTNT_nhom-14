"""T4.1 — chỉ số đánh giá, luôn tính trên THANG GIÁ GỐC.

Mô hình huấn luyện trên log(giá) nhưng người đọc báo cáo cần con số bằng tỷ đồng. Mọi
chỉ số ở đây vì thế nhận vào giá đã quy ngược về VND, không phải log.

Bốn chỉ số, mỗi cái trả lời một câu khác nhau:

- **RMSE** phạt nặng sai số lớn → nhạy với vài căn dị biệt. Đề bài yêu cầu.
- **MAE** là sai số điển hình tính bằng tiền. Đề bài yêu cầu.
- **MdAPE** là sai số phần trăm TRUNG VỊ. Bất biến thang đo, nên so được giữa quận đắt
  và quận rẻ; đây là con số đáng tin nhất khi phân phối lệch phải nặng như giá nhà.
- **R²** đề bài yêu cầu, nhưng đọc một mình trên phân phối lệch thì dễ hiểu nhầm, nên
  luôn báo cùng ba chỉ số kia (runbook 03 §7.6).
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BILLION = 1e9


def median_absolute_percentage_error(y_true, y_pred) -> float:
    """Trung vị của |sai số| / giá thật, tính bằng phần trăm."""
    y_true = np.asarray(y_true, dtype="float64")
    y_pred = np.asarray(y_pred, dtype="float64")
    valid = y_true > 0
    if not valid.any():
        return float("nan")
    return float(np.median(np.abs(y_pred[valid] - y_true[valid]) / y_true[valid]) * 100)


def compute_metrics(y_true, y_pred) -> dict[str, float]:
    """Bộ bốn chỉ số. RMSE/MAE quy ra tỷ đồng để bảng báo cáo đọc được bằng mắt.

    Chịu được dự báo vô cực. Mô hình huấn luyện trên log(giá) rồi lấy `exp` để quay về
    thang VND; một dự báo log đủ lớn sẽ tràn số thành `inf`, và scikit-learn từ chối
    tính chỉ số trên đó. Chuyện này xảy ra thật với MLP trên bộ lịch sử, và nó làm gãy
    cả phiên chạy thí nghiệm.

    Cách xử lý là báo cáo chứ không che: chỉ số tính trên phần dự báo hữu hạn, còn số
    dự báo không hữu hạn được trả về ở khoá `n_non_finite` để bảng kết quả nêu ra. Cắt
    ngưỡng dự báo cho đẹp sẽ giấu mất một tính chất có thật của phương pháp log-target,
    mà đó lại đúng là điều đáng nói trong báo cáo.
    """
    y_true = np.asarray(y_true, dtype="float64")
    y_pred = np.asarray(y_pred, dtype="float64")

    finite = np.isfinite(y_pred) & np.isfinite(y_true)
    n_bad = int((~finite).sum())

    if not finite.any():
        return {
            "RMSE (tỷ)": float("nan"),
            "MAE (tỷ)": float("nan"),
            "MdAPE (%)": float("nan"),
            "R²": float("nan"),
            "n_non_finite": n_bad,
        }

    true_ok, pred_ok = y_true[finite], y_pred[finite]
    return {
        "RMSE (tỷ)": float(np.sqrt(mean_squared_error(true_ok, pred_ok))) / BILLION,
        "MAE (tỷ)": float(mean_absolute_error(true_ok, pred_ok)) / BILLION,
        "MdAPE (%)": median_absolute_percentage_error(true_ok, pred_ok),
        "R²": float(r2_score(true_ok, pred_ok)) if len(true_ok) > 1 else float("nan"),
        "n_non_finite": n_bad,
    }


METRIC_ORDER = ["RMSE (tỷ)", "MAE (tỷ)", "MdAPE (%)", "R²"]
# Chỉ số nào càng nhỏ càng tốt — dùng để in đậm ô tốt nhất mỗi cột.
LOWER_IS_BETTER = {"RMSE (tỷ)": True, "MAE (tỷ)": True, "MdAPE (%)": True, "R²": False}
