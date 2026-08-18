# Ablation: đặc trưng văn bản đáng bao nhiêu?

Mô hình: Random Forest. Cả bốn cấu hình chạy trên CÙNG một bộ fold và cùng
một ngân sách tinh chỉnh, nên khác biệt duy nhất giữa các dòng là nhánh văn bản.

| Cấu hình đặc trưng | MdAPE (%) | Δ so với chỉ bảng | RMSE (tỷ) | R² |
|---|---:|---:|---:|---:|
| Chỉ đặc trưng bảng | 14,18 | 0,00 | 4,243 | 0,646 |
| Bảng + cờ văn bản thủ công | 13,69 | -0,49 | 4,193 | 0,655 |
| Bảng + TF-IDF/SVD | 15,70 | +1,52 | 4,592 | 0,585 |
| Bảng + TF-IDF/SVD + cờ | 15,07 | +0,88 | 4,626 | 0,579 |

Δ âm nghĩa là thêm nhánh đó làm sai số giảm. Đây là con số trả lời trực tiếp câu
hỏi của đề: mô tả rao vặt mang bao nhiêu tín hiệu giá.

## Đọc bảng

Hai nhánh văn bản đi ngược chiều nhau, và đó mới là kết quả đáng nói.

**Cờ thủ công giúp được** (0,49 điểm phần trăm). Đây là
vài chục cột nhị phân, mỗi cột là một khái niệm mà người mua nhà thật sự
quan tâm: hẻm xe hơi, sổ hồng riêng, ngộp bank, nở hậu. Cây quyết định tách
trên chúng rất dễ, và mỗi lần tách đều giải thích được.

**TF-IDF cộng SVD làm tệ đi** (1,52 điểm phần trăm).
Nguyên nhân hợp lý nhất là tỷ lệ: hơn một trăm trục SVD dày đặc, mỗi trục
mang rất ít tín hiệu, đổ vào một tập chỉ vài nghìn dòng. Rừng cây phải chọn
điểm tách trong một rừng cột nhiễu, và xác suất chọn trúng cột hữu ích giảm
xuống. Đây là hiện tượng quen thuộc của mô hình cây trên đặc trưng dày và
yếu, không phải bằng chứng rằng mô tả rao vặt vô giá trị.

Kết luận đúng của thí nghiệm này: **mô tả CÓ mang tín hiệu giá, nhưng phải
được chưng cất trước khi dùng.** Nén cả mô tả thành trăm trục vô danh thì
phần tín hiệu ít ỏi bị chôn trong nhiễu; rút thành vài chục khái niệm cụ thể
thì nó nổi lên. Với cỡ dữ liệu hiện tại, cách rẻ hơn lại là cách tốt hơn.
