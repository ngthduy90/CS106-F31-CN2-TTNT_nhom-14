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
- **Loại bất động sản**: nhà ở riêng lẻ, nhà phố, căn hộ chung cư, biệt thự, đất và mặt
  bằng kinh doanh. Loại bất động sản là một đặc trưng đầu vào của mô hình, nên năm nhóm
  này được giữ chung trong một bảng thay vì tách thành năm bài toán. Loại trừ: tin cho
  thuê, tin không ghi giá bằng số, và tin có diện tích hoặc giá nằm ngoài miền hợp lệ
  khai báo ở chương 2.
- **Thời gian**: tin rao thu thập tháng 08/2026. Dữ liệu lịch sử trải từ 06/2025 tới
  03/2026; lát cắt tới 06/2025 dùng làm tập huấn luyện cho thí nghiệm chuyển giao theo
  thời gian, phần còn lại dùng để quan sát mặt bằng giá thay đổi ra sao.
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
5. So sánh các thuật toán bằng RMSE, MAE và R² theo yêu cầu của đề, bổ sung MdAPE vì
   phân phối giá lệch phải mạnh khiến ba chỉ số kia dễ bị đọc sai. Đề yêu cầu tối thiểu
   ba thuật toán; đồ án chạy một danh mục rộng hơn để bảng kết quả nói được vì sao mỗi
   họ mô hình ứng xử như vậy, chứ không chỉ để nhiều dòng.

## Đóng góp của đồ án

- Một quy trình thu thập và làm sạch dữ liệu tin rao tiếng Việt, có ghi lại số dòng bị
  loại ở từng bước để người đọc kiểm chứng được.
- Bộ luật trích xuất đặc trưng từ văn bản rao vặt tiếng Việt, kèm số đo chất lượng trên
  bộ nhãn kiểm chứng thay vì chỉ mô tả định tính.
- Một bảng so sánh mô hình có kiểm soát: cùng tập chia, cùng ngân sách tinh chỉnh tham
  số, báo cáo trung bình và độ lệch chuẩn qua 5 fold.
- Thí nghiệm chuyển giao theo thời gian: huấn luyện trên tin rao tới 06/2025, kiểm tra
  trên tin rao tháng 08/2026, để đo mức độ mô hình mất chính xác khi giá thị trường trôi.
- Một bộ kiểm chống rò rỉ nhãn chạy tự động trước mỗi lần huấn luyện. Nó không phải phần
  trang trí: trong quá trình làm, bộ kiểm này bắt được hai lỗi rò rỉ thật mà đọc mã
  nguồn bằng mắt không phát hiện ra (chi tiết ở chương 3).

## Cấu trúc báo cáo

Chương 2 mô tả dữ liệu và cách thu thập. Chương 3 trình bày phương pháp, gồm tiền xử lý,
trích đặc trưng và danh mục mô hình. Chương 4 trình bày thiết kế thí nghiệm và kết quả.
Chương 5 kết luận, nêu giới hạn và hướng phát triển.
