# Giới thiệu

## Bài toán

Người mua nhà ở TP.HCM khó biết một căn nhà đang rao có đúng giá thị trường hay không.
Thông tin định giá nằm rải rác trong hàng trăm nghìn tin rao vặt, phần lớn ở dạng văn
bản tự do, mỗi người viết một kiểu. Đồ án này xây dựng một hệ thống học từ chính các
tin rao đó để dự báo giá bán của một căn nhà, dựa trên vị trí, thông số vật lý và nội
dung mô tả.

Bài toán được phát biểu dưới dạng hồi quy: cho một tin rao gồm địa chỉ, diện tích, số
phòng ngủ, số tầng, chiều rộng mặt tiền và đoạn mô tả tự do, dự báo tổng giá bán tính
bằng đồng Việt Nam.

## Phạm vi

- **Không gian**: TP.HCM, phủ dày ba quận theo hệ hành chính trước 2025 là Tân Bình,
  Tân Phú và Quận 12, mở rộng ra toàn thành phố để đủ số lượng mẫu.
- **Loại bất động sản**: nhà ở riêng lẻ và nhà phố; loại trừ tin cho thuê, đất nền
  không có công trình và các tin không ghi giá bằng số.
- **Thời gian**: dữ liệu tin rao thu thập trong năm 2026, đối chiếu với dữ liệu lịch sử
  tới giữa năm 2025.
- **Loại giá**: giá rao (asking price), không phải giá giao dịch. Đây là giới hạn quan
  trọng của mọi kết luận trong báo cáo, được nhắc lại ở chương 5.

## Mục tiêu

1. Thu thập tối thiểu 5.000 tin rao có mô tả văn bản, tuân thủ robots.txt và không lưu
   thông tin cá nhân người đăng tin.
2. Trích các đặc trưng định lượng (diện tích, số phòng ngủ, số tầng, chiều rộng mặt
   tiền) từ văn bản tự do và đo được chất lượng trích xuất trên một bộ nhãn kiểm chứng.
3. Chuẩn hoá địa chỉ về một hệ quy chiếu hành chính duy nhất, xử lý được đợt sáp nhập
   đơn vị hành chính năm 2025.
4. Biểu diễn phần mô tả bằng TF-IDF kết hợp giảm chiều, và đo xem phần văn bản đóng góp
   bao nhiêu vào độ chính xác.
5. So sánh tối thiểu ba thuật toán bằng RMSE, MAE và R², bổ sung MdAPE vì phân phối giá
   lệch mạnh.

## Đóng góp của đồ án

- Một quy trình thu thập và làm sạch dữ liệu tin rao tiếng Việt, có ghi lại số dòng bị
  loại ở từng bước để người đọc kiểm chứng được.
- Bộ luật trích xuất đặc trưng từ văn bản rao vặt tiếng Việt, kèm số đo chất lượng trên
  bộ nhãn kiểm chứng thay vì chỉ mô tả định tính.
- Một bảng so sánh mô hình có kiểm soát: cùng tập chia, cùng ngân sách tinh chỉnh tham
  số, báo cáo trung bình và độ lệch chuẩn qua 5 fold.
- Thí nghiệm chuyển giao theo thời gian: huấn luyện trên tin rao tới giữa 2025, kiểm tra
  trên tin rao 2026, để đo mức độ mô hình mất chính xác khi giá thị trường trôi.

## Cấu trúc báo cáo

Chương 2 mô tả dữ liệu và cách thu thập. Chương 3 trình bày phương pháp, gồm tiền xử lý,
trích đặc trưng và danh mục mô hình. Chương 4 trình bày thiết kế thí nghiệm và kết quả.
Chương 5 kết luận, nêu giới hạn và hướng phát triển.
