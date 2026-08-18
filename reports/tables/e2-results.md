# E2: chuyển giao theo thời gian

Huấn luyện trên 31.947 tin đăng tới 2025-06-30, kiểm trên 2.326 tin Chợ Tốt crawl tháng 08/2026.

Cả hai phía đều là GIÁ RAO nên chênh lệch đo được là trôi giá theo thời gian,
không lẫn khoảng cách giữa giá rao và giá giao dịch.

Cột Δ so với cột cùng tên ở bảng E1 nguồn Chợ Tốt (huấn luyện và kiểm cùng trên
dữ liệu 2026). Δ dương nghĩa là chuyển giao làm sai số xấu đi.

| Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² | Δ MdAPE |
|---|---:|---:|---:|---:|---:|
| Dummy (trung vị) | 7,061 | 4,230 | 50,0 | -0,009 | +15,4 |
| Trung vị giá/m² theo nhóm | 3,945 | 2,120 | 21,3 | 0,685 | +0,8 |
| Hồi quy tuyến tính | tràn số | tràn số | tràn số | tràn số | không tính được |
| Ridge | 5,675 | 2,289 | 22,2 | 0,348 | +2,5 |
| Lasso | 7,248 | 4,819 | 60,0 | -0,063 | +41,4 |
| Random Forest | 4,170 | 1,907 | 17,0 | 0,648 | +1,9 |
| K láng giềng | 5,050 | 2,573 | 25,3 | 0,484 | +4,7 |
| Cây quyết định | 6,547 | 3,180 | 27,9 | 0,133 | +8,0 |
| LightGBM | 3,752 | 1,723 | 16,3 | 0,715 | +2,4 |
| CatBoost | 3,569 | 1,588 | 15,0 | 0,742 | +0,8 |
| XGBoost | 3,713 | 1,768 | 17,1 | 0,721 | +3,1 |
| MLP | 21,765 | 10,345 | 24,8 | -8,584 | +5,8 |

**Dự báo tràn số khi chuyển giao**: Hồi quy tuyến tính (2326 dòng).

Đây là kết quả đáng chú ý chứ không phải sự cố kỹ thuật. Hồi quy tuyến tính
không có điều chuẩn, học trên hàng chục nghìn dòng với vài trăm cột, sinh ra hệ
số rất lớn; đem sang một tập có phân phối khác thì dự báo trên thang log vọt lên
tới mức `exp` tràn số thực 64 bit. Ridge, cũng là mô hình tuyến tính nhưng có
điều chuẩn, chuyển giao bình thường. Khoảng cách giữa hai dòng đó chính là giá
trị của điều chuẩn khi phân phối dữ liệu dịch chuyển.

Trung vị mức xấu đi khi chuyển giao: **2,8 điểm phần trăm
MdAPE** (10/10 mô hình xấu đi; khoảng 0,8 tới 41,4).

Dùng trung vị vì vài mô hình hỏng nặng khi chuyển giao kéo trung bình lên gấp
đôi; nhóm mô hình chủ lực mới là phần đáng đọc.

Đây là cái giá của việc dùng một mô hình huấn luyện trên dữ liệu cũ cho thị
trường hiện tại. Cần đọc kèm một cảnh báo: tập huấn luyện và tập kiểm không chỉ
khác nhau về thời gian mà còn khác nhau về SÀN, nên một phần chênh lệch là chênh
giữa hai nguồn chứ không phải trôi giá thuần tuý.
