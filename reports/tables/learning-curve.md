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

**Bước cuối xấu đi 0,8 điểm phần trăm** chứ không giảm. Mỗi tỷ lệ chỉ chạy một lần trên một tập con ngẫu nhiên, nên một bước đi lên cỡ này chưa tách được khỏi dao động giữa các lần lấy mẫu. Vì vậy không thể dựa vào riêng bước cuối để kết luận đường cong đã phẳng: muốn chốt thì phải lặp lại mỗi tỷ lệ nhiều lần rồi so trung bình.
