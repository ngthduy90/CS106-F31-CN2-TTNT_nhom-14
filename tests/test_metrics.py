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
