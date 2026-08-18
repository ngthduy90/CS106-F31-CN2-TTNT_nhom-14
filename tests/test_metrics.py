"""Kiểm chỉ số bằng bộ số tính tay, không dùng lại thư viện để tự xác nhận chính mình."""

import numpy as np
import pytest

from src.evaluation.metrics import compute_metrics, median_absolute_percentage_error


def test_chi_so_khop_ket_qua_tinh_tay():
    # Sai số: +1, -1, +2 tỷ trên các mức giá 2, 4, 8 tỷ.
    y_true = np.array([2e9, 4e9, 8e9])
    y_pred = np.array([3e9, 3e9, 10e9])

    metrics = compute_metrics(y_true, y_pred)

    # RMSE = sqrt((1 + 1 + 4)/3) = sqrt(2) tỷ
    assert metrics["RMSE (tỷ)"] == pytest.approx(np.sqrt(2), rel=1e-9)
    # MAE = (1 + 1 + 2)/3 tỷ
    assert metrics["MAE (tỷ)"] == pytest.approx(4 / 3, rel=1e-9)
    # Sai số tương đối: 50%, 25%, 25% → trung vị 25%
    assert metrics["MdAPE (%)"] == pytest.approx(25.0, rel=1e-9)


def test_du_doan_hoan_hao():
    y = np.array([2e9, 5e9, 9e9])
    metrics = compute_metrics(y, y)
    assert metrics["RMSE (tỷ)"] == 0
    assert metrics["MAE (tỷ)"] == 0
    assert metrics["MdAPE (%)"] == 0
    assert metrics["R²"] == 1


def test_mdape_bo_qua_gia_khong_duong():
    assert median_absolute_percentage_error([0, 4e9], [1e9, 5e9]) == pytest.approx(25.0)


def test_chiu_duoc_du_bao_vo_cuc():
    """Dự báo `inf` không được làm gãy phép tính, và phải được đếm lại.

    Mô hình huấn luyện trên log(giá) rồi `exp` ngược có thể tràn số. scikit-learn ném
    lỗi khi gặp `inf`, và nếu để nguyên thì một mô hình hỏng sẽ giết cả phiên chạy.
    """
    y_true = np.array([2e9, 4e9, 8e9, 5e9])
    y_pred = np.array([3e9, 3e9, np.inf, 5e9])

    metrics = compute_metrics(y_true, y_pred)

    assert metrics["n_non_finite"] == 1
    assert np.isfinite(metrics["RMSE (tỷ)"])
    # Ba dự báo hữu hạn: sai số 1, 1, 0 tỷ trên giá 2, 4, 5 tỷ → 50%, 25%, 0% → trung vị 25%
    assert metrics["MdAPE (%)"] == pytest.approx(25.0)


def test_toan_bo_du_bao_hong_thi_tra_ve_nan():
    metrics = compute_metrics([2e9, 4e9], [np.inf, np.nan])
    assert metrics["n_non_finite"] == 2
    assert all(np.isnan(metrics[k]) for k in ("RMSE (tỷ)", "MAE (tỷ)", "MdAPE (%)", "R²"))


def test_du_bao_binh_thuong_khong_bi_danh_dau():
    assert compute_metrics([2e9, 4e9], [2.1e9, 3.9e9])["n_non_finite"] == 0
