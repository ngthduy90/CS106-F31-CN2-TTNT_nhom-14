# E1: Nguồn B · Chợ Tốt 2026

2.326 dòng, chia hold-out 80/20, 5-fold trên phần train, seed 42.
Ngân sách tinh chỉnh: RandomizedSearch 20 cấu hình, giống nhau cho mọi mô hình.

Mỗi ô là trung bình ± độ lệch chuẩn qua 5 fold. **In đậm** là tốt nhất mỗi cột.

| Tầng | Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 0 · mốc | Dummy (trung vị) | 7,250 ± 1,350 | 3,698 ± 0,396 | 34,6 ± 2,1 | -0,053 ± 0,005 |
| 0 · mốc | Trung vị giá/m² theo nhóm | 3,802 ± 0,647 | 2,074 ± 0,237 | 20,5 ± 1,4 | 0,706 ± 0,053 |
| 1 · tuyến tính | Hồi quy tuyến tính | 10,970 ± 10,006 | 2,479 ± 0,881 | 18,8 ± 0,7 | -2,783 ± 5,169 |
| 1 · tuyến tính | Lasso | 11,265 ± 10,458 | 2,492 ± 0,918 | 18,6 ± 0,7 | -3,029 ± 5,603 |
| 1 · tuyến tính | Ridge | 7,002 ± 2,962 | 2,461 ± 0,339 | 19,7 ± 0,7 | -0,160 ± 0,983 |
| 2 · chủ lực | CatBoost | 3,857 ± 1,195 | **1,609 ± 0,259** | 14,2 ± 1,2 | 0,708 ± 0,076 |
| 2 · chủ lực | LightGBM | 3,925 ± 1,125 | 1,633 ± 0,269 | **13,9 ± 1,2** | 0,698 ± 0,061 |
| 2 · chủ lực | Random Forest | 4,626 ± 1,276 | 1,835 ± 0,284 | 15,1 ± 0,9 | 0,579 ± 0,076 |
| 2 · chủ lực | XGBoost | **3,793 ± 1,131** | 1,623 ± 0,256 | 14,0 ± 1,1 | **0,716 ± 0,069** |
| 3 · mở rộng | Cây quyết định | 4,665 ± 1,298 | 2,229 ± 0,308 | 19,8 ± 0,9 | 0,571 ± 0,082 |
| 3 · mở rộng | K láng giềng | 5,048 ± 1,141 | 2,296 ± 0,201 | 20,6 ± 1,1 | 0,493 ± 0,064 |
| 3 · mở rộng | MLP | 7,952 ± 6,551 | 2,292 ± 0,708 | 19,0 ± 2,1 | -1,038 ± 2,558 |

## Đo trên tập hold-out (chưa từng dùng để chọn tham số)

| Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---:|---:|---:|---:|
| Dummy (trung vị) | 6,624 | 3,550 | 36,3 | -0,052 |
| Trung vị giá/m² theo nhóm | 3,338 | 1,908 | 19,6 | 0,733 |
| Hồi quy tuyến tính | 14,137 | 2,483 | 17,8 | -3,790 |
| Lasso | 15,878 | 2,552 | 17,1 | -5,042 |
| Ridge | 10,198 | 2,405 | 18,7 | -1,492 |
| CatBoost | 3,248 | 1,437 | 13,8 | 0,747 |
| LightGBM | 3,197 | 1,467 | 14,2 | 0,755 |
| Random Forest | 3,673 | 1,595 | 14,3 | 0,677 |
| XGBoost | 2,825 | 1,430 | 13,4 | 0,809 |
| Cây quyết định | 4,178 | 2,055 | 19,8 | 0,582 |
| K láng giềng | 3,931 | 2,123 | 21,7 | 0,630 |
| MLP | 3,837 | 1,865 | 17,3 | 0,647 |

Mô hình tốt nhất (LightGBM) hơn baseline kiểu môi giới **6,66 điểm phần trăm MdAPE**. Đây mới là phần giá trị mà học máy
tạo ra so với cách định giá thủ công; khoảng cách so với Dummy chỉ nói rằng dữ
liệu có tín hiệu.

**Chú ý khi đọc**: Hồi quy tuyến tính, Lasso, MLP có độ lệch chuẩn của RMSE lớn
so với chính trung bình của nó. Nguyên nhân là mô hình huấn luyện trên log(giá)
và phép `exp` khuếch đại một vài dự báo ngoại suy xa thành sai số khổng lồ trên
thang VND. Trung vị không bị ảnh hưởng nên MdAPE của các mô hình này vẫn ở mức
khá, và đó chính là lý do bảng báo cả bốn chỉ số thay vì chỉ một.

Ghi chú: mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính sau khi đã quy
ngược về thang VND. RMSE và MAE tính bằng tỷ đồng. MdAPE là sai số phần trăm
trung vị. Mọi mô hình dùng CHUNG một bộ fold, nên chênh lệch giữa các dòng không
lẫn chênh lệch giữa các phép chia tập.
