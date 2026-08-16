# Phương pháp

## Pipeline tổng thể

![Pipeline dự báo giá nhà từ tin rao vặt](../figures/01-pipeline-tong-the.png)

Bảy khối nối tiếp nhau: nguồn tin rao, script thu thập, kho dữ liệu thô bất biến, tiền
xử lý, trích đặc trưng, mô hình hoá, đánh giá và bàn giao. Kho thô chỉ ghi một lần theo
ngày thu thập và không bao giờ bị sửa; mọi thay đổi diễn ra ở bước tiền xử lý. Nhờ vậy
làm sai bước nào cũng chạy lại được từ dữ liệu gốc mà không phải thu thập lại.

Vòng lặp duy nhất trong sơ đồ đi từ khối đánh giá ngược về khối đặc trưng: kết quả phân
tích lỗi quyết định việc bổ sung hay sửa đặc trưng, rồi huấn luyện lại.

## Tiền xử lý

### Chuẩn hoá giá

Bước này chạy trước mọi bước khác vì giá vừa là nhãn vừa là căn cứ lọc. Bộ luật parse
phủ các cách viết phổ biến trong tin rao: "5 tỷ 2", "5,2 tỷ", "5200 triệu", và dạng đơn
giá "52 triệu/m²" nhân với diện tích ra tổng giá. Tin có cả tổng giá lẫn đơn giá được
kiểm khớp chéo với dung sai 10%; lệch nhiều hơn thì gắn cờ để rà tay.

Tin ghi giá 0, giá 1 hoặc "thoả thuận" bị loại khỏi tập huấn luyện thay vì điền giá trị
thay thế, vì đây là thiếu nhãn chứ không phải thiếu đặc trưng. Tỷ lệ loại được báo cáo
ở bảng data funnel.

### Trích đặc trưng định lượng từ văn bản

Đề bài yêu cầu trích diện tích, số phòng ngủ, số tầng và chiều rộng mặt tiền từ phần mô
tả. Phương án dùng ở đây là luật regex kết hợp từ điển biến thể, đo chất lượng trên một
bộ nhãn kiểm chứng 200 tin.

Các mẫu ngôn ngữ phải phủ:

- Diện tích: "DT", "diện tích" kèm số và đơn vị; dạng kích thước "4x15" hoặc "ngang 4
  dài 15" thì nhân ra diện tích và lấy luôn chiều ngang làm mặt tiền.
- Số phòng ngủ: "3PN", "3 phòng ngủ", "2PN2WC".
- Số tầng: "tầng", "lầu", "tấm", "mê"; luật cộng cho "1 trệt 2 lầu" ra 3 tầng; "cấp 4"
  quy về 1 tầng.
- Mặt tiền: phân biệt số đo chiều ngang với cụm "nhà mặt tiền" chỉ vị trí.
- Vị trí hẻm: "hẻm", "HXH", "hẻm xe hơi" kèm bề rộng nếu có.
- Pháp lý: "sổ hồng", "sổ đỏ", "SHR", "giấy tay", "vi bằng".

Chất lượng trích xuất được báo cáo bằng precision, recall và F1 cho từng trường trên bộ
nhãn kiểm chứng, xem bảng ở chương 4. Trường không bắt được để trống và xử lý ở bước
giá trị thiếu.

### Chuẩn hoá địa chỉ

Từ 01/07/2025, cả nước chuyển từ 63 xuống 34 tỉnh thành và bỏ cấp quận huyện; TP.HCM
hợp nhất thêm Bình Dương và Bà Rịa - Vũng Tàu, còn 168 đơn vị cấp xã. Hệ quả trực tiếp
cho đồ án: dữ liệu lịch sử ghi theo đơn vị cũ, tin rao 2026 ghi theo phường mới. Không
chuẩn hoá thì cùng một khu vực bị tách thành nhiều nhóm và mô hình học sai.

Hệ quy chiếu chọn là hệ CŨ, gồm quận huyện và phường trước sáp nhập. Lý do: phần lớn dữ
liệu đã ở hệ này, cấp quận cũ là mức phân giải quen thuộc của thị trường bất động sản,
và 168 phường mới quá mịn so với quy mô khoảng 10.000 tin. Địa chỉ dạng văn bản được
parse thành bộ ba (đường, phường, quận) bằng từ điển kết hợp regex, sau đó tin 2026 tra
bảng ánh xạ phường mới sang phường cũ rồi quy về quận cũ.

Hai cạm bẫy được xử lý riêng: một phường mới có thể gộp từ phường của hai quận cũ, khi
đó áp luật ưu tiên theo quận chiếm phần lớn và ghi lại cột nguồn đơn vị; và tên "Phường
1" tồn tại ở hàng chục quận nên bắt buộc parse kèm quận.

### Khử trùng lặp

Một căn nhà thường được đăng lại nhiều lần và trên nhiều sàn. Nếu bản sao rơi vào cả
tập huấn luyện lẫn tập kiểm tra thì kết quả đẹp giả tạo. Quy trình gồm ba bước: chặn
theo phường và diện tích làm tròn, so độ tương đồng mô tả trong từng khối bằng TF-IDF
mức ký tự với ngưỡng cosine 0,85, và chỉ coi là trùng khi cả thông số gần nhau (giá lệch
dưới 3%) lẫn văn bản giống nhau. Bản giữ lại là tin mới nhất hoặc tin có mô tả dài nhất.

Bước này chạy TRƯỚC khi chia tập, không phải sau.

### Giá trị thiếu và ngoại lai

Dòng thiếu diện tích hoặc giá bị loại. Số phòng ngủ, số tầng và mặt tiền được điền bằng
trung vị theo nhóm (loại nhà × quận), kèm một cột chỉ báo đánh dấu giá trị đã điền, vì
bản thân việc người đăng không ghi cũng là thông tin.

Ngoại lai xử lý hai tầng. Tầng một là luật cứng về miền hợp lệ, ví dụ diện tích trong
khoảng 10 đến 1.000 m². Tầng hai là IQR trên log của giá mỗi m² tính theo TỪNG QUẬN, vì
mức giá bình thường ở quận trung tâm là phi lý ở vùng ven. Quận có quá ít tin thì lùi về
ngưỡng toàn thành phố. Ngưỡng lấy từ chính dữ liệu, không lấy từ kinh nghiệm.

## Biểu diễn phần mô tả

Văn bản tiếng Việt được tách từ bằng underthesea, loại stopwords chung cộng với một
stoplist riêng cho tin rao ("liên hệ", "chính chủ", "lh"), nhưng giữ lại các từ mang tín
hiệu giá như "gấp" và "ngộp".

Phương án chính là TF-IDF 1-2 gram, chặn từ hiếm bằng min_df, rồi giảm chiều bằng
TruncatedSVD xuống 50 đến 150 chiều. Lý do chọn: đúng phạm vi kỹ thuật đề bài nêu, chạy
nhanh, và các trục sau giảm chiều còn diễn giải được. Song song, khoảng 10 đến 30 cờ nhị
phân được chưng cất thủ công từ mô tả ("mặt tiền", "hẻm xe hơi", "sổ hồng riêng", "mới
xây") để dùng cho họ mô hình cây, vốn học kém trên vector thưa nghìn chiều.

## Danh mục mô hình

![Thiết kế thí nghiệm mô hình hoá](../figures/03-thiet-ke-thi-nghiem.png)

Danh mục chia ba tầng, chạy cùng một tập chia và cùng ngân sách tinh chỉnh tham số:

| Tầng | Mô hình | Vai trò |
|---|---|---|
| 0 | Dummy (trung vị) và baseline trung vị giá/m² theo nhóm | Mốc so sánh, mọi mô hình phải thắng |
| 1 | Linear Regression, Ridge, Lasso | Chuẩn tham chiếu, hệ số diễn giải được |
| 2 | Random Forest, LightGBM, CatBoost | Nhóm chủ lực cho dữ liệu bảng |
| 3 | KNN, Decision Tree, MLP | Mở rộng, minh hoạ ưu nhược từng họ |

Biến mục tiêu khi huấn luyện là log của tổng giá, vì phân phối giá lệch phải nặng và
log biến sai số tuyệt đối thành sai số tương đối. Mọi chỉ số báo cáo được tính sau khi
đổi ngược về thang đồng.

Tham số được tinh chỉnh bằng RandomizedSearch với ngân sách 40 cấu hình cho mỗi mô hình,
cùng seed, để so sánh công bằng.

## Ba luật chống rò rỉ dữ liệu

Ba luật này áp dụng trước mọi lần huấn luyện và có kiểm thử tự động:

1. Xoá mọi cụm giá khỏi phần mô tả trước khi vector hoá. Không làm thì mô hình chỉ đọc
   lại giá đã có sẵn trong văn bản.
2. Không đưa giá mỗi m² hay bất kỳ đại lượng dẫn xuất từ nhãn vào tập đặc trưng, vì tổng
   giá bằng giá mỗi m² nhân diện tích.
3. Mọi phép biến đổi (TF-IDF, chuẩn hoá, điền thiếu, mã hoá, ngưỡng ngoại lai) đều nằm
   trong pipeline và chỉ fit trên phần huấn luyện của từng fold.
