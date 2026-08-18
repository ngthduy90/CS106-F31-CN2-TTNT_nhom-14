# Kết luận và hướng phát triển

## Kết luận

{{T6.6: viết sau khi có kết quả. Ba ý phải có, mỗi ý kèm số liệu cụ thể:
1. Mô hình tốt nhất và sai số của nó so với baseline trung vị nhóm.
2. Phần mô tả văn bản đóng góp bao nhiêu, lấy từ bảng ablation.
3. Mức mất chính xác khi chuyển giao theo thời gian, lấy từ E2.}}

## Giới hạn

1. **Giá rao, không phải giá giao dịch.** Toàn bộ dữ liệu là giá người bán đề nghị. Sai
   số của hệ thống so với giá chốt thực tế chưa đo được vì không có dữ liệu giao dịch.
2. **Phạm vi địa lý hẹp.** Dữ liệu tập trung ở ba quận, kết quả không suy rộng ra toàn
   TP.HCM, càng không suy rộng ra tỉnh thành khác. Thí nghiệm E3 cho thấy giới hạn này
   ngay trong phạm vi thành phố.
3. **Nhiễu nội tại của tin rao.** Tin trùng, tin ảo và mô tả phóng đại là đặc tính của
   dữ liệu rao vặt. Khử trùng lặp giảm bớt nhưng không loại hết.
4. **Ảnh hưởng của đợt sáp nhập hành chính 2025.** Việc quy đổi phường mới về hệ cũ dựa
   trên bảng ánh xạ công khai, phần không ánh xạ được {{T2.8: tỷ lệ}} bị bỏ qua.

## Hướng phát triển

1. Bổ sung dữ liệu giao dịch thực nếu tiếp cận được, để hiệu chỉnh khoảng cách giữa giá
   rao và giá chốt.
2. Thêm đặc trưng không gian giàu hơn: khoảng cách tới trường học, bệnh viện, trục
   đường chính, thay vì chỉ khoảng cách tới trung tâm.
3. Thử biểu diễn ngữ nghĩa bằng mô hình ngôn ngữ tiếng Việt tiền huấn luyện làm bộ trích
   đặc trưng, giữ nguyên mô hình hồi quy cổ điển ở tầng trên.
4. Theo dõi trôi giá theo thời gian và huấn luyện lại định kỳ, dựa trên kết quả E2.
