# Ablation: đặc trưng văn bản đáng bao nhiêu?

Mô hình: LightGBM. Cả bốn cấu hình chạy trên CÙNG một bộ fold và cùng
một ngân sách tinh chỉnh, nên khác biệt duy nhất giữa các dòng là nhánh văn bản.

| Cấu hình đặc trưng | MdAPE (%) | Δ so với chỉ bảng | RMSE (tỷ) | R² |
|---|---:|---:|---:|---:|
| Chỉ đặc trưng bảng | 14,77 ± 1,19 | 0,00 | 3,798 | 0,712 |
| Bảng + cờ văn bản thủ công | 14,08 ± 1,15 | -0,69 | 3,795 | 0,713 |
| Bảng + TF-IDF/SVD | 13,91 ± 0,35 | -0,86 | 3,935 | 0,692 |
| Bảng + TF-IDF/SVD + cờ | 13,88 ± 0,77 | -0,89 | 3,844 | 0,709 |

Δ âm nghĩa là thêm nhánh đó làm sai số giảm. Đây là con số trả lời trực tiếp câu
hỏi của đề: mô tả rao vặt mang bao nhiêu tín hiệu giá.

## Đọc bảng

Cả ba cấu hình có văn bản đều thấp hơn cấu hình chỉ có đặc trưng bảng, và
thấp theo cùng một chiều. Mô tả rao vặt vì thế có mang tín hiệu giá mà các
trường điền sẵn không có.

Cần đọc kèm cỡ hiệu ứng: mức cải thiện lớn nhất là 0,86 điểm
phần trăm, trong khi độ lệch chuẩn giữa các fold lên tới 1,19.
Bốn cấu hình dùng CHUNG một bộ fold nên đây là phép so bắt cặp, nhạy hơn hẳn
so với việc đặt hai khoảng mean±std cạnh nhau; dù vậy vẫn nên đọc kết quả này
là **một xu hướng nhất quán về dấu**, không phải một con số chốt.
