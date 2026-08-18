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

Nghị quyết 202/2025/QH15 (12/06/2025) sắp xếp lại đơn vị hành chính cấp tỉnh, cả nước
còn 34 đơn vị. Nghị quyết 1685/NQ-UBTVQH15 (16/06/2025) sắp xếp cấp xã của TP.HCM: sau
sắp xếp thành phố có 168 đơn vị cấp xã gồm 113 phường, 54 xã và 1 đặc khu. Mô hình chính
quyền hai cấp vận hành từ 01/07/2025. Hệ quả trực tiếp
cho đồ án: dữ liệu lịch sử ghi theo đơn vị cũ, tin rao 2026 ghi theo phường mới. Không
chuẩn hoá thì cùng một khu vực bị tách thành nhiều nhóm và mô hình học sai.

Hệ quy chiếu chọn là hệ CŨ, gồm quận huyện và phường trước sáp nhập. Lý do: phần lớn dữ
liệu đã ở hệ này, cấp quận cũ là mức phân giải quen thuộc của thị trường bất động sản,
và 168 đơn vị cấp xã mới quá mịn so với quy mô dữ liệu của đồ án. Địa chỉ dạng văn bản được
parse thành bộ ba (đường, phường, quận) bằng từ điển kết hợp regex, sau đó tin 2026 tra
bảng ánh xạ phường mới sang phường cũ rồi quy về quận cũ.

Bảng ánh xạ không lấy từ kho dữ liệu bên ngoài mà dựng từ chính dữ liệu đã crawl: API
Chợ Tốt trả cả tên phường theo hệ cũ lẫn hệ mới cho cùng một tin, nên mỗi tin là một cặp
ánh xạ do sàn khẳng định. Cách dựng và hạn chế của bảng nêu ở chương Dữ liệu.

Hai cạm bẫy được xử lý riêng: một phường mới có thể gộp từ phường của hai quận cũ, khi
đó áp luật ưu tiên theo quận chiếm phần lớn và ghi lại cột nguồn đơn vị; và tên "Phường
1" tồn tại ở hàng chục quận nên bắt buộc parse kèm quận. Cạm bẫy thứ nhất không phải
trường hợp hiếm: trên dữ liệu thực tế, phần lớn phường mới gộp từ nhiều phường cũ, nên
tỷ lệ đa số của mỗi ánh xạ được lưu lại để biết ánh xạ nào đáng ngờ.

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

Phương án chính là TF-IDF trên chuỗi ĐÃ TÁCH TỪ, chặn từ hiếm bằng `min_df = 5`, rồi
giảm chiều bằng TruncatedSVD xuống 120 chiều.

Một lưu ý về n-gram: TF-IDF chạy ở mức 1-gram chứ không phải 1-2 gram, vì bộ tách từ
tiếng Việt đã ghép sẵn các từ ghép thành một token ("sổ_hồng", "hẻm_xe_hơi",
"nội_thất"). Nói cách khác, phần lớn 2-gram đáng quan tâm của văn bản gốc đã trở thành
1-gram sau khi tách từ; bật thêm 2-gram chỉ làm từ vựng phình lên mà không thêm được
khái niệm mới.

Bước tách từ được đưa lên giai đoạn tiền xử lý thay vì đặt trong analyzer của
TfidfVectorizer. Đây là quyết định về hiệu năng nhưng hệ quả rất lớn: để trong analyzer
thì bộ tách từ chạy lại toàn bộ tập dữ liệu ở mỗi lần fit, tức là mỗi fold nhân với mỗi
cấu hình tìm kiếm tham số, hàng trăm lần cho cùng một kết quả. Lý do chọn: đúng phạm vi kỹ thuật đề bài nêu, chạy
nhanh, và các trục sau giảm chiều còn diễn giải được. Song song, 24 cờ nhị phân được chưng cất thủ công từ mô tả ("mặt tiền", "hẻm xe hơi",
"sổ hồng riêng", "mới xây", "ngộp bank", "ô tô đỗ cửa") để dùng cho họ mô hình cây, vốn
học kém trên vector thưa nghìn chiều. Cờ thủ công còn có một giá trị mà SVD không có:
một cây quyết định tách trên cờ "hẻm xe hơi" đọc được ngay, còn tách trên trục SVD thứ
37 thì không giải thích được cho ai.

## Danh mục mô hình

![Thiết kế thí nghiệm mô hình hoá](../figures/03-thiet-ke-thi-nghiem.png)

Danh mục chia ba tầng, chạy cùng một tập chia và cùng ngân sách tinh chỉnh tham số:

| Tầng | Mô hình | Vai trò |
|---|---|---|
| 0 | Dummy (trung vị) và baseline trung vị giá/m² theo nhóm | Mốc so sánh, mọi mô hình phải thắng |
| 1 | Linear Regression, Ridge, Lasso | Chuẩn tham chiếu, hệ số diễn giải được |
| 2 | Random Forest, LightGBM, CatBoost, XGBoost | Nhóm chủ lực cho dữ liệu bảng |
| 3 | KNN, Decision Tree, MLP | Mở rộng, minh hoạ ưu nhược từng họ |

Biến mục tiêu khi huấn luyện là log của tổng giá, vì phân phối giá lệch phải nặng và
log biến sai số tuyệt đối thành sai số tương đối. Mọi chỉ số báo cáo được tính sau khi
đổi ngược về thang đồng.

Tham số được tinh chỉnh bằng RandomizedSearch với ngân sách cấu hình GIỐNG NHAU cho mọi
mô hình và cùng seed; con số ngân sách thực dùng ghi ngay dưới mỗi bảng kết quả ở chương
4. Việc tinh chỉnh chạy một lần trên phần huấn luyện với 3-fold nội bộ, rồi cấu hình tốt
nhất được dùng lại cho cả 5 fold ngoài. Chạy tìm kiếm lại trong từng fold tốn gấp năm
lần mà không đo thêm được gì: cái cần đo là mô hình đã tinh chỉnh ổn định đến đâu giữa
các fold, không phải bộ tìm kiếm dao động đến đâu.

## Ba luật chống rò rỉ dữ liệu

Ba luật này áp dụng trước mọi lần huấn luyện và có kiểm thử tự động:

1. Xoá mọi cụm giá khỏi phần mô tả trước khi vector hoá. Không làm thì mô hình chỉ đọc
   lại giá đã có sẵn trong văn bản.
2. Không đưa giá mỗi m² hay bất kỳ đại lượng dẫn xuất từ nhãn vào tập đặc trưng, vì tổng
   giá bằng giá mỗi m² nhân diện tích.
3. Mọi phép biến đổi (TF-IDF, chuẩn hoá, điền thiếu, mã hoá, ngưỡng ngoại lai) đều nằm
   trong pipeline và chỉ fit trên phần huấn luyện của từng fold.

### Danh sách kiểm này đã bắt được gì

Ba luật trên không phải là cam kết suông. Một script kiểm chạy trước MỖI lần huấn luyện
và lưu kết quả cạnh file kết quả của lần chạy đó. Trong quá trình làm, nó bắt được hai
lỗi thật mà đọc code bằng mắt không thấy:

**Bước tách từ tái tạo cụm tiền sau khi đã lọc.** Bộ lọc giá chạy đúng trên văn bản gốc,
nhưng bộ tách từ bỏ dấu câu bên trong token, nên "5,85" biến thành "585" và nằm cạnh một
chữ "tỷ" còn sót lại từ mảnh khác. Kết quả là hàng trăm dòng mang cụm tiền vào TF-IDF dù
văn bản gốc đã sạch. Cách sửa: lọc thêm một lượt SAU khi tách từ, và cho bộ lọc chạy lặp
tới khi văn bản không đổi nữa, vì xoá một cụm có thể làm hai mảnh còn lại dính vào nhau
thành cụm mới.

**Một dạng đơn giá lọt qua bộ lọc.** Cụm "110 triệu/m²" sau khi tách từ mất dấu gạch
chéo và thành "110 triệum2". Mẫu regex cũ đòi ranh giới từ ngay sau "triệu" nên trượt
đúng dạng nguy hiểm nhất: đơn giá nhân với diện tích ra thẳng nhãn.

Cả hai lỗi đều đủ để làm kết quả đẹp lên một cách vô nghĩa. Sau khi sửa, phép kiểm xác
nhận không còn dòng nào mang cụm tiền vào bước vector hoá.

Bản thân phép kiểm cũng phải sửa một lần: ban đầu nó coi mọi con số đứng trước chữ
"đồng" là tiền, nên gắn cờ "74 Đồng Đen" (một địa chỉ ở Tân Bình) và "đường 10 đồng
bộ". Một phép kiểm hay kêu nhầm sẽ sớm bị người ta bỏ qua, tức là mất hẳn tác dụng, nên
điều kiện được siết lại: tên đơn vị tiền tệ trần chỉ tính là tiền khi đi sau một số từ
bốn chữ số trở lên.
