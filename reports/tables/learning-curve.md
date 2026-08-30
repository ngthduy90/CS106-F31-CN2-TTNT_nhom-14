# Đường cong học

Mô hình: LightGBM. Mỗi dòng: lấy ngẫu nhiên một phần tập huấn luyện,
huấn luyện lại, đo trên cùng một tập hold-out.

| Tỷ lệ tập huấn luyện | Số tin | RMSE (tỷ) | MdAPE (%) |
|---:|---:|---:|---:|
| 10% | 186 | 5,071 | 22,9 |
| 25% | 465 | 3,735 | 15,7 |
| 40% | 744 | 3,538 | 15,3 |
| 55% | 1023 | 3,380 | 15,5 |
| 70% | 1302 | 3,372 | 14,2 |
| 85% | 1581 | 3,276 | 13,4 |
| 100% | 1860 | 3,197 | 14,2 |

Từ 186 lên 1860 tin, MdAPE giảm từ 22,9% xuống 14,2%.

**Bước cuối gần như không giảm nữa**, nghĩa là đường cong đã phẳng: nút thắt nằm ở chất lượng đặc trưng và nhãn chứ không ở số lượng tin, nên công sức nên chuyển sang chỗ khác thay vì crawl thêm.
