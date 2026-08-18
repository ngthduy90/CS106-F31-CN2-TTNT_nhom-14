# Đường cong học

Mô hình: XGBoost. Mỗi dòng: lấy ngẫu nhiên một phần tập huấn luyện,
huấn luyện lại, đo trên cùng một tập hold-out.

| Tỷ lệ tập huấn luyện | Số tin | RMSE (tỷ) | MdAPE (%) |
|---:|---:|---:|---:|
| 10% | 186 | 4,679 | 18,9 |
| 25% | 465 | 3,555 | 15,9 |
| 40% | 744 | 3,475 | 14,7 |
| 55% | 1023 | 3,078 | 14,6 |
| 70% | 1302 | 3,216 | 13,8 |
| 85% | 1581 | 2,822 | 12,8 |
| 100% | 1860 | 2,699 | 12,0 |

Từ 186 lên 1860 tin, MdAPE giảm từ 18,9% xuống 12,0%.

**Bước cuối vẫn còn giảm 0,8 điểm phần trăm**, nghĩa là đường cong chưa phẳng: thu thập thêm dữ liệu vẫn còn cải thiện được sai số, và đó là chỗ đáng đầu tư tiếp theo.
