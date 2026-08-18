# E3: giữ lại từng phường làm tập kiểm (leave-one-ward-out)

Mô hình: Random Forest. Mỗi dòng: bỏ toàn bộ tin của một phường ra khỏi
tập huấn luyện, rồi dự báo đúng phường đó. Đây là phép đo khả năng tổng quát
sang khu vực CHƯA TỪNG THẤY.

| Phường giữ lại | Số tin kiểm | MdAPE (%) | RMSE (tỷ) | R² |
|---|---:|---:|---:|---:|
| Phường 15 | 159 | 18,1 | 2,248 | 0,660 |
| Phường 10 | 140 | 16,6 | 1,846 | 0,816 |
| Phường Thạnh Xuân | 128 | 13,8 | 1,772 | 0,792 |
| Phường Tân Sơn Nhì | 122 | 14,3 | 2,604 | 0,632 |
| Phường Phú Thọ Hòa | 113 | 13,6 | 2,131 | 0,662 |

Trung bình MdAPE: 15,3% ± 2,0.

Kết quả kém hơn E1 là một phát hiện, không phải một thất bại: nó cho biết mô
hình dựa vào địa bàn đến mức nào, và cảnh báo rằng đem mô hình này sang một
phường chưa có dữ liệu thì sai số sẽ ở mức nào.
