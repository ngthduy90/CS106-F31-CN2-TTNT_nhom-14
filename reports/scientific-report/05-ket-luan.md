# Kết luận và hướng phát triển

## Đã làm được gì

Đồ án dựng trọn một đường đi từ tin rao thô tới con số dự báo, và mỗi mắt xích đều có
phép đo riêng chứ không dựa vào cam kết suông.

**Dữ liệu.** Ba nguồn được gộp về một lược đồ: hai sàn rao vặt crawl tháng 08/2026 và
một bộ dữ liệu lịch sử. Quy trình làm sạch được ghi lại thành bảng data funnel, nêu rõ
mất bao nhiêu dòng ở bước nào và vì sao. Số dòng cuối cùng vượt xa ngưỡng 5.000 của đề
bài.

**Trích đặc trưng từ văn bản.** Bộ luật regex rút bảy trường định lượng từ mô tả tự do,
và chất lượng của nó được đo trên bộ nhãn vàng lấy từ chính các trường có cấu trúc mà
sàn thu riêng, nghĩa là bộ luật bị chấm bởi một nguồn nó không hề nhìn thấy. Diện tích
đạt F1 0,939, đạt chỉ tiêu; số tầng dừng ở 0,802 và phần lớn lỗi còn lại là do tin rao
tự mâu thuẫn chứ không phải bộ luật đọc sai.

**Chuẩn hoá địa chỉ.** Đợt sáp nhập hành chính 2025 được xử lý bằng bảng ánh xạ dựng từ
chính dữ liệu, thay vì lấy bảng của bên thứ ba. Cách này cũng phơi ra một sự thật đáng
ghi: phần lớn phường mới gộp từ nhiều phường cũ, nên phép ánh xạ ngược không thể là một
phép tương ứng một-một, và tỷ lệ đa số được lưu lại cho từng ánh xạ.

**Chống rò rỉ nhãn.** Đây là phần nhóm đầu tư nhiều nhất, và cũng là phần trả lại nhiều
nhất. Danh sách kiểm chạy trước mỗi lần huấn luyện đã bắt được hai lỗi thật mà đọc code
bằng mắt không thấy: bước tách từ tái tạo cụm tiền sau khi đã lọc, và một dạng đơn giá
lọt qua bộ lọc. Cả hai đều đủ để làm kết quả đẹp một cách vô nghĩa. Không có phép kiểm
tự động thì cả hai đã đi thẳng vào báo cáo.

## Ba con số đáng nhớ

<!-- include: reports/tables/ablation.md -->

Ba kết luận rút ra từ bảng kết quả, mỗi kết luận kèm con số:

1. **Nhóm boosting dẫn đầu.** Cách biệt giữa ba mô hình boosting nhỏ hơn độ lệch chuẩn
   giữa các fold, nên bảng E1 chỉ cho phép nói cả nhóm cùng ở mức tốt nhất, không cho
   phép chọn ra một mô hình thắng tuyệt đối. Điều đáng nói hơn là khoảng cách so với
   baseline môi giới, tức trung vị giá mỗi m² theo nhóm nhân diện tích. Đó mới là phần
   giá trị mà học máy thực sự tạo ra so với cách định giá thủ công.
2. **Mô tả rao vặt có mang tín hiệu giá.** Cả ba cấu hình có nhánh văn bản đều cho sai
   số thấp hơn cấu hình chỉ dùng đặc trưng bảng, nhất quán về dấu. Nhưng mức cải thiện
   nhỏ hơn độ lệch chuẩn giữa các fold, nên đây là một xu hướng chứ chưa phải một con số
   chốt. Chương 4 nêu rõ điều này thay vì trình bày nó như một chiến thắng.
3. **Chuyển giao theo thời gian có giá của nó.** Mô hình huấn luyện trên tin tới
   06/2025 rồi đem dự báo tin tháng 08/2026 kém hơn hẳn mô hình huấn luyện trên chính dữ
   liệu 2026. Cả hai phía đều là giá rao, nên chênh lệch đó không lẫn khoảng cách giữa
   giá rao và giá giao dịch.

## Hạn chế, nói thẳng

**Giá rao, không phải giá giao dịch.** Đây là hạn chế lớn nhất và không khắc phục được
bằng kỹ thuật. Giá giao dịch thực tế thường thấp hơn giá rao, nhưng nhóm không có dữ
liệu giao dịch để đo khoảng cách đó nên không đưa ra bất kỳ con số phỏng đoán nào. Thiết
kế thí nghiệm ban đầu định đo chính khoảng cách này; khi nguồn dữ liệu giao dịch không
lấy được, nhóm đổi thiết kế thay vì giữ nguyên và diễn giải một con số không đo được.

**Chỉ TP.HCM, và phủ không đều.** Ba quận mục tiêu dày hơn hẳn phần còn lại. Thí nghiệm
E3 đo trực tiếp mức suy giảm khi đem mô hình sang khu vực chưa thấy, và kết quả kém hơn
E1 là một phát hiện chứ không phải một thất bại: nó cho biết mô hình dựa vào địa bàn đến
mức nào.

**Tin rao tự mâu thuẫn.** Cùng một tin có thể ghi một bộ số ở form và một bộ số khác
trong mô tả. Bảng chất lượng trích xuất đo đúng mức chênh này. Không bước tiền xử lý nào
sửa được chuyện người bán khai sai.

**Số tầng chưa đạt chỉ tiêu F1 0,9.** Nhóm dừng sau hai vòng sửa luật theo đúng kịch bản
đã định trước, thay vì tiếp tục chỉnh luật cho khớp một tập nhãn tự nó đã nhiễu. Đây là
lựa chọn có chủ ý và được ghi lại, không phải một thiếu sót bị bỏ quên.

**Địa danh chốt tại một ngày.** Hành chính còn tiếp tục thay đổi sau mốc chốt, và bảng
ánh xạ chỉ phủ các phường xuất hiện trong dữ liệu đã crawl.

## Hướng phát triển

**Bổ sung dữ liệu, nhưng đừng kỳ vọng nhiều vào riêng nó.** Câu hỏi "crawl thêm có đáng
không" được trả lời bằng phép đo chứ không bằng cảm tính, và câu trả lời không như nhóm
dự đoán ban đầu: đường cong học đã gần phẳng ở mốc 100% dữ liệu hiện có. Từ 186 lên
khoảng 1.600 tin, sai số giảm rất mạnh; từ đó tới 1.860 tin thì gần như không giảm nữa.

Ba lý do vẫn nên thu thập thêm, nhưng với kỳ vọng đúng. Thứ nhất, đường cong đo trên
2.326 tin của ba quận, chưa nói gì về việc mở rộng địa bàn. Thứ hai, nhánh TF-IDF cần
nhiều mẫu hơn hẳn mới phát huy hết, và ablation cho thấy nó mới chỉ vừa bắt đầu có ích.
Thứ ba, cả cổng kiểm chất lượng lẫn ngưỡng của đề đều chưa đạt bằng dữ liệu hiện có.

**Toạ độ và đặc trưng khoảng cách.** Bước geocoding đã được thiết kế đầy đủ (Nominatim
1 request mỗi giây, cache trên đĩa, lùi về centroid phường khi không giải được) nhưng
hoãn lại theo thứ tự cắt giảm đã định trước khi bắt tay vào làm. Đây là phần bổ sung có
giá trị rõ ràng nhất còn lại: khoảng cách tới trung tâm và cụm toạ độ là thông tin mà
biến phân loại theo phường không thay thế được.

**Đối chiếu với dữ liệu giao dịch.** Nếu tiếp cận được nguồn giá giao dịch thật, phép so
giữa hai định nghĩa giá sẽ biến hạn chế lớn nhất của đồ án thành một kết quả đo được.

**Biểu diễn văn bản nâng cao.** Nhánh embedding tĩnh và sentence embedding đã được cân
nhắc và xếp sau TF-IDF vì đúng phạm vi môn học. Với hạ tầng pipeline hiện có, thêm một
nhánh biểu diễn mới chỉ là thêm một dòng vào ablation.
