# E3: giữ lại từng phường làm tập kiểm (leave-one-ward-out)

Mô hình: LightGBM. Mỗi dòng: bỏ toàn bộ tin của một phường ra khỏi
tập huấn luyện, rồi dự báo đúng phường đó. Đây là phép đo khả năng tổng quát
sang khu vực CHƯA TỪNG THẤY.

| Phường giữ lại | Số tin kiểm | MdAPE (%) | RMSE (tỷ) | R² |
|---|---:|---:|---:|---:|
| Phường 15 | 159 | 21,4 | 2,827 | 0,462 |
| Phường 10 | 140 | 17,2 | 1,840 | 0,818 |
| Phường Thạnh Xuân | 128 | 13,3 | 1,732 | 0,802 |
| Phường Tân Sơn Nhì | 122 | 11,8 | 2,562 | 0,644 |
| Phường Phú Thọ Hòa | 113 | 12,1 | 2,338 | 0,593 |

Trung bình MdAPE: 15,2% ± 4,1.

Kết quả kém hơn E1 là một phát hiện, không phải một thất bại: nó cho biết mô
hình dựa vào địa bàn đến mức nào, và cảnh báo rằng đem mô hình này sang một
phường chưa có dữ liệu thì sai số sẽ ở mức nào.
