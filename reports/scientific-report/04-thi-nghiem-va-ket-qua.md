# Thí nghiệm và kết quả

## Thiết kế thí nghiệm

Ba thí nghiệm chạy trên cùng một danh mục mô hình và cùng quy tắc chia tập.

- **E1, bảng so sánh chính**: hold-out 80/20 cộng 5-fold cross-validation trên phần
  huấn luyện, chạy riêng cho từng nguồn dữ liệu. Chia tập có phân tầng theo quận và theo
  khoảng giá. Khử trùng lặp thực hiện trước khi chia.
- **E2, chuyển giao theo thời gian**: huấn luyện trên tin rao tới 06/2025, kiểm tra trên
  tin rao 2026, đối chiếu với trường hợp huấn luyện và kiểm tra cùng trên dữ liệu 2026.
  Chênh lệch giữa hai trường hợp là thước đo mức trôi giá theo thời gian.
- **E3, stress test không gian**: giữ lần lượt 3 đến 5 phường nhiều tin nhất làm tập
  kiểm tra, báo cáo trung bình và độ lệch chuẩn. Thí nghiệm này đo khả năng tổng quát
  hoá sang khu vực mô hình chưa thấy.

Hai nguồn dữ liệu không được trộn chung làm thí nghiệm chính vì chúng phủ thời kỳ khác
nhau, nên cờ nguồn sẽ lẫn với biến thời gian.

## Chỉ số đánh giá

RMSE và MAE tính trên thang đồng sau khi đổi ngược từ log, kèm MdAPE là sai số phần trăm
trung vị vì chỉ số này bất biến theo thang đo và đọc được ngay. R² báo cáo kèm ghi chú
về thang tính. Mỗi ô trong bảng kết quả ghi trung bình và độ lệch chuẩn của 5 fold.

## Bảng kết quả chính (E1)

{{T4.5: chèn bảng từ reports/tables/e1-results.md — hàng là mô hình theo thứ tự tầng,
Dummy trên cùng; cột là RMSE, MAE, MdAPE, R²; in đậm giá trị tốt nhất mỗi cột}}

Ghi chú bắt buộc dưới bảng: biến mục tiêu huấn luyện là log(giá), chỉ số tính trên thang
giá gốc, cách chia tập, seed, ngân sách tinh chỉnh tham số.

Nguyên tắc đọc bảng: không kết luận mô hình A tốt hơn mô hình B khi hai khoảng trung
bình cộng trừ độ lệch chuẩn chồng lấn gần hết.

## Kết quả chuyển giao theo thời gian (E2)

{{T4.6: bảng so sánh hai trường hợp huấn luyện, kèm mức chênh lệch}}

{{T4.12: hình trung vị giá mỗi m² theo quý từ 2023 đến 2026 theo quận}}

## Stress test không gian (E3)

{{T4.7: bảng mean ± std khi giữ từng phường làm tập kiểm tra}}

Kết quả kém ở thí nghiệm này là một phát hiện về giới hạn tổng quát hoá, không phải một
thất bại của mô hình.

## Ablation đặc trưng văn bản

{{T4.8: bảng ba cấu hình — chỉ đặc trưng bảng, cộng TF-IDF và SVD, cộng cờ văn bản thủ
công — với cùng mô hình tốt nhất và cùng tập chia}}

Câu hỏi thí nghiệm này trả lời: phần mô tả tự do trong tin rao đáng bao nhiêu điểm MdAPE.

## Phân tích lỗi

{{T4.10: bảng MdAPE theo quận và theo khoảng giá dưới 2 tỷ, 2 đến 5 tỷ, 5 đến 10 tỷ,
trên 10 tỷ}}

{{T4.9: hình SHAP beeswarm toàn cục và 2 đến 3 hình waterfall cho các ca sai nặng nhất}}

## Đường cong học

{{T4.11: hình RMSE theo cỡ tập huấn luyện từ 10% đến 100%}}

Ý nghĩa thực tế: đường cong còn dốc nghĩa là thu thập thêm dữ liệu vẫn còn cải thiện
được, đường cong đã phẳng nghĩa là nút thắt nằm ở đặc trưng chứ không ở số lượng mẫu.
