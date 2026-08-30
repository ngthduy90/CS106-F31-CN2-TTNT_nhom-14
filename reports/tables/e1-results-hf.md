# E1: Nguồn A · bộ lịch sử

6.001 dòng, chia hold-out 80/20, 5-fold trên phần train, seed 42.
Ngân sách tinh chỉnh: RandomizedSearch tối đa 20 cấu hình cho mọi mô hình. Số lượt rút THẬT là min(ngân sách, kích thước lưới): lưới rời rạc nhỏ hơn ngân sách thì search không thể rút quá số cấu hình đang có.

Mỗi ô là trung bình ± độ lệch chuẩn qua 5 fold. **In đậm** là tốt nhất mỗi cột.

Lưu ý cách đọc: tinh chỉnh chạy MỘT LẦN trên toàn phần train rồi dùng lại cho cả 5 fold ngoài (không nested), nên cột CV nghiêng lạc quan một chiều. Cột hold-out không dính điều này và là con số nên trích khi cần một chỉ số duy nhất.

| Tầng | Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 0 · mốc | Dummy (trung vị) | 17,489 ± 0,685 | 9,659 ± 0,369 | 56,1 ± 1,0 | -0,148 ± 0,011 |
| 0 · mốc | Trung vị giá/m² theo nhóm | 8,572 ± 0,755 | 4,457 ± 0,176 | 21,7 ± 0,7 | 0,724 ± 0,035 |
| 1 · tuyến tính | Hồi quy tuyến tính | 14,685 ± 3,885 | 5,042 ± 0,354 | 23,3 ± 0,8 | 0,133 ± 0,519 |
| 1 · tuyến tính | Lasso | 15,086 ± 4,428 | 5,056 ± 0,420 | 23,1 ± 0,5 | 0,073 ± 0,599 |
| 1 · tuyến tính | Ridge | 14,805 ± 4,029 | 5,057 ± 0,384 | 23,2 ± 0,7 | 0,116 ± 0,536 |
| 2 · chủ lực | CatBoost | **7,051 ± 0,340** | **3,734 ± 0,144** | **19,3 ± 0,4** | **0,813 ± 0,013** |
| 2 · chủ lực | LightGBM | 7,296 ± 0,315 | 3,843 ± 0,182 | 20,2 ± 0,9 | 0,800 ± 0,009 |
| 2 · chủ lực | Random Forest | 8,771 ± 0,478 | 4,522 ± 0,172 | 23,0 ± 0,8 | 0,711 ± 0,014 |
| 2 · chủ lực | XGBoost | 7,118 ± 0,366 | 3,748 ± 0,132 | 19,4 ± 0,4 | 0,810 ± 0,012 |
| 3 · mở rộng | Cây quyết định | 10,152 ± 0,559 | 5,637 ± 0,201 | 30,0 ± 0,7 | 0,613 ± 0,025 |
| 3 · mở rộng | K láng giềng | 10,152 ± 0,926 | 5,673 ± 0,400 | 31,1 ± 0,6 | 0,612 ± 0,061 |
| 3 · mở rộng | MLP | 937,605 ± 2060,284 | 34,285 ± 67,030 | 20,9 ± 0,6 | -15155,789 ± 33887,869 |

## Đo trên tập hold-out (chưa từng dùng để chọn tham số)

| Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---:|---:|---:|---:|
| Dummy (trung vị) | 19,545 | 10,548 | 56,0 | -0,159 |
| Trung vị giá/m² theo nhóm | 8,779 | 4,533 | 21,1 | 0,766 |
| Hồi quy tuyến tính | 11,310 | 5,001 | 22,7 | 0,612 |
| Lasso | 11,552 | 5,016 | 22,3 | 0,595 |
| Ridge | 11,518 | 5,018 | 22,6 | 0,597 |
| CatBoost | 7,225 | 3,855 | 19,4 | 0,842 |
| LightGBM | 7,648 | 4,060 | 20,2 | 0,822 |
| Random Forest | 9,241 | 4,630 | 22,3 | 0,741 |
| XGBoost | 7,409 | 3,937 | 19,1 | 0,833 |
| Cây quyết định | 10,539 | 5,731 | 29,8 | 0,663 |
| K láng giềng | 10,961 | 6,027 | 30,8 | 0,635 |
| MLP | 7,848 | 4,086 | 20,7 | 0,813 |

Nhóm dẫn đầu (CatBoost, XGBoost) hơn baseline kiểu môi giới **2,28–2,35 điểm phần trăm MdAPE** (khoảng của cả nhóm dẫn đầu). Các mô hình
trong nhóm cách nhau chưa tới một độ lệch chuẩn giữa các fold nên bảng không
chọn ra một mô hình thắng. Đây mới là phần giá trị mà học máy tạo ra so với
cách định giá thủ công; khoảng cách so với Dummy chỉ nói rằng dữ liệu có tín hiệu.

**Chú ý khi đọc**: MLP có độ lệch chuẩn của RMSE lớn
so với chính trung bình của nó. Nguyên nhân là mô hình huấn luyện trên log(giá)
và phép `exp` khuếch đại một vài dự báo ngoại suy xa thành sai số khổng lồ trên
thang VND. Trung vị không bị ảnh hưởng nên MdAPE của các mô hình này vẫn ở mức
khá, và đó chính là lý do bảng báo cả bốn chỉ số thay vì chỉ một.

Ghi chú: mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính sau khi đã quy
ngược về thang VND. RMSE và MAE tính bằng tỷ đồng. MdAPE là sai số phần trăm
trung vị. Mọi mô hình dùng CHUNG một bộ fold, nên chênh lệch giữa các dòng không
lẫn chênh lệch giữa các phép chia tập.
