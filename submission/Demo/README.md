# Ảnh chụp demo

Web app dự báo giá nhà, chạy bằng `make demo` (Streamlit, cổng mặc định 8501).

| Ảnh | Nội dung |
|---|---|
| `demo-01-man-hinh-nhap-lieu.png` | Màn hình nhập thông tin bất động sản |
| `demo-02-ket-qua-va-giai-thich.png` | Kết quả dự báo kèm biểu đồ giải thích SHAP |
| `demo-03-toan-bo-panel-ket-qua.png` | Toàn bộ panel kết quả, gồm chú thích biểu đồ và cảnh báo về giá rao |

Bộ số dùng để chụp: Tân Bình, Phường 1, nhà phố, 60 m², 3 tầng, 3 phòng ngủ, 2 nhà tắm,
mặt tiền 4 m, hẻm 5 m, vị trí hẻm, mô tả "Nhà đẹp hẻm xe hơi, sổ hồng riêng, full nội
thất, gần chợ và trường học, vào ở ngay."

Kết quả: **8,04 tỷ đồng**, khoảng tham khảo 6,90 tới 9,19 tỷ. Bề rộng khoảng lấy từ sai
số phần trăm trung vị đo trên tập hold-out (14,2%), không phải một con số tự đặt.

Một quan sát khi chụp: đổi vị trí từ "hẻm" sang "mặt tiền" mà giữ nguyên mọi thứ khác
chỉ làm giá đổi từ 8,04 lên 8,05 tỷ. Lý do là phần mô tả vẫn ghi "hẻm xe hơi", và mô
hình đọc được điều đó; cột vị trí chỉ là một trong nhiều đặc trưng chứ không phải công
tắc. Đây là ví dụ trực quan cho kết quả của bảng ablation: mô tả tự do có mang tín hiệu.
