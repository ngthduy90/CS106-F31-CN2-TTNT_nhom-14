# E1 — Nguồn B — Chợ Tốt 2026

2.326 dòng, chia hold-out 80/20, 5-fold trên phần train, seed 42.
Ngân sách tinh chỉnh: RandomizedSearch 20 cấu hình, giống nhau cho mọi mô hình.

Mỗi ô là trung bình ± độ lệch chuẩn qua 5 fold. **In đậm** là tốt nhất mỗi cột.

| Tầng | Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 0 — mốc | Dummy (trung vị) | 7,250 ± 1,350 | 3,698 ± 0,396 | 34,6 ± 2,1 | -0,053 ± 0,005 |
| 0 — mốc | Trung vị giá/m² theo nhóm | **3,640 ± 0,354** | 1,948 ± 0,146 | 19,5 ± 1,1 | 0,719 ± 0,083 |
| 1 — tuyến tính | Hồi quy tuyến tính | 10,303 ± 9,224 | 2,434 ± 0,818 | 18,4 ± 0,4 | -2,306 ± 4,426 |
| 1 — tuyến tính | Lasso | 10,795 ± 9,976 | 2,444 ± 0,877 | 17,8 ± 0,6 | -2,709 ± 5,083 |
| 1 — tuyến tính | Ridge | 7,920 ± 4,818 | 2,417 ± 0,504 | 18,8 ± 0,5 | -0,672 ± 1,774 |
| 2 — chủ lực | CatBoost | 3,802 ± 1,147 | **1,547 ± 0,238** | 13,5 ± 1,2 | 0,717 ± 0,066 |
| 2 — chủ lực | LightGBM | 3,749 ± 1,133 | 1,550 ± 0,235 | 13,4 ± 0,9 | 0,724 ± 0,068 |
| 2 — chủ lực | Random Forest | 4,513 ± 1,221 | 1,777 ± 0,251 | 14,7 ± 0,6 | 0,599 ± 0,069 |
| 2 — chủ lực | XGBoost | 3,736 ± 1,159 | 1,560 ± 0,245 | **13,0 ± 1,0** | **0,726 ± 0,072** |
| 3 — mở rộng | Cây quyết định | 4,628 ± 1,301 | 2,175 ± 0,332 | 19,4 ± 1,9 | 0,578 ± 0,083 |
| 3 — mở rộng | K láng giềng | 4,693 ± 1,115 | 2,164 ± 0,206 | 19,8 ± 1,1 | 0,558 ± 0,088 |
| 3 — mở rộng | MLP | 12,585 ± 13,378 | 2,594 ± 0,898 | 19,0 ± 0,8 | -4,513 ± 8,896 |

## Đo trên tập hold-out (chưa từng dùng để chọn tham số)

| Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---:|---:|---:|---:|
| Dummy (trung vị) | 6,624 | 3,550 | 36,3 | -0,052 |
| Trung vị giá/m² theo nhóm | 2,988 | 1,801 | 19,4 | 0,786 |
| Hồi quy tuyến tính | 12,599 | 2,336 | 17,0 | -2,804 |
| Lasso | 15,807 | 2,497 | 17,6 | -4,988 |
| Ridge | 13,209 | 2,514 | 19,2 | -3,182 |
| CatBoost | 3,092 | 1,383 | 13,0 | 0,771 |
| LightGBM | 3,109 | 1,403 | 12,7 | 0,768 |
| Random Forest | 3,587 | 1,583 | 14,5 | 0,692 |
| XGBoost | 2,938 | 1,399 | 13,5 | 0,793 |
| Cây quyết định | 4,100 | 1,986 | 18,4 | 0,597 |
| K láng giềng | 3,409 | 1,989 | 21,5 | 0,722 |
| MLP | 4,542 | 2,000 | 18,1 | 0,506 |

**Chú ý khi đọc**: Hồi quy tuyến tính, Lasso, Ridge, MLP có độ lệch chuẩn của RMSE lớn
so với chính trung bình của nó. Nguyên nhân là mô hình huấn luyện trên log(giá)
và phép `exp` khuếch đại một vài dự báo ngoại suy xa thành sai số khổng lồ trên
thang VND. Trung vị không bị ảnh hưởng nên MdAPE của các mô hình này vẫn ở mức
khá — đó chính là lý do bảng báo cả bốn chỉ số thay vì chỉ một.

Ghi chú: mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính sau khi đã quy
ngược về thang VND. RMSE và MAE tính bằng tỷ đồng. MdAPE là sai số phần trăm
trung vị. Mọi mô hình dùng CHUNG một bộ fold, nên chênh lệch giữa các dòng không
lẫn chênh lệch giữa các phép chia tập.
