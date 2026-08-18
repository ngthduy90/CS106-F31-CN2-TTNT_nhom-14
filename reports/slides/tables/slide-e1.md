# Kết quả chính (E1)

2.326 tin Chợ Tốt · 5-fold · cùng bộ fold, cùng ngân sách tinh chỉnh

| Mô hình | MdAPE (%) | RMSE (tỷ) | R² |
|---|---:|---:|---:|
| Dummy (trung vị) | 34,6 | 7,25 | -0,053 |
| Trung vị giá/m² theo nhóm | 20,5 | 3,80 | 0,706 |
| Ridge | 19,7 | 7,00 | -0,160 |
| Random Forest | 15,1 | 4,63 | 0,579 |
| **LightGBM** | 13,9 | 3,92 | 0,698 |
| **XGBoost** | 14,0 | 3,79 | 0,716 |

LightGBM và XGBoost hơn baseline môi giới khoảng 6,7 điểm phần trăm MdAPE.
Cách biệt giữa các mô hình in đậm nhỏ hơn độ lệch chuẩn giữa các fold, nên không chọn ra một mô hình thắng.
