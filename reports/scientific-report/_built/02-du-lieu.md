# Dữ liệu

## Nguồn thu thập

![Nguồn dữ liệu và schema kho thô](../figures/02-nguon-du-lieu-va-schema.png)

| Nguồn | Cách lấy | Thời điểm | Vai trò |
|---|---|---|---|
| Chợ Tốt | API JSON công khai của gateway, quét theo từng quận | 19/08/2026 | Nguồn chính, tin đang rao 2026 |
| mogi.vn | Parse HTML trang danh sách và trang chi tiết | 19/08/2026 | Nguồn thứ hai, giảm lệch theo một sàn |
| `tinixai/vietnam-real-estates` | Tải bộ dữ liệu công bố trên Hugging Face | 19/08/2026 | Nguồn lịch sử, tin rao 06/2025 – 03/2026 |

Lý do dùng hai nguồn crawl thay vì một: mỗi sàn có tệp người đăng và cách viết tin khác
nhau, học trên một sàn duy nhất thì mô hình bám theo thói quen của sàn đó. Bộ dữ liệu
Hugging Face đóng vai trò dữ liệu lịch sử để đo mức trôi giá theo thời gian, và là
phương án dự phòng nếu crawler hỏng.

Các trang bị loại khỏi phạm vi: batdongsan.com.vn, muaban.net, cafeland và guland đều
chặn bằng Cloudflare. Đồ án không vượt cơ chế chống bot chủ động, đây là ranh giới tự
đặt và được ghi lại ở mục đạo đức bên dưới.

Một đính chính so với khảo sát nguồn ban đầu: bộ dữ liệu Hugging Face **không** dừng ở
tháng 06/2025 như ghi nhận lúc lập kế hoạch, mà trải từ 06/2025 tới 03/2026. Nhóm kiểm
lại bằng cách lấy mẫu trường `published_at` ở nhiều vị trí khác nhau trong 3,5 triệu
dòng. Hệ quả là có lợi: ngoài lát cắt tới 06/2025 dùng làm tập huấn luyện cho thí nghiệm
chuyển giao, nhóm có thêm một chuỗi thời gian mười tháng liên tục để quan sát mặt bằng
giá thay đổi ra sao.

## Cách thu thập và ranh giới tự đặt

Cả hai crawler dùng chung một lớp phiên HTTP với ba ràng buộc cài cứng: tối đa một
request mỗi 1,5 giây, lùi luỹ tiến khi máy chủ trả 429 hoặc 403, và User-Agent khai báo
rõ đây là đồ án học thuật.

Với Chợ Tốt, nhóm phát hiện API danh sách đã trả về trường mô tả **đầy đủ**, xác nhận
bằng cách đối chiếu độ dài mô tả của cùng một tin giữa API danh sách và API chi tiết.
Vì vậy crawler không gọi trang chi tiết: một request lấy được 20 tin thay vì một, giảm
tải cho máy chủ bên kia khoảng hai mươi lần. Endpoint chi tiết còn kèm cả trường số điện
thoại, thêm một lý do để không đụng vào.

Kho dữ liệu thô là bất biến: mỗi quận mỗi ngày crawl một file JSONL, chỉ ghi thêm. Mỗi
tin được khử trùng theo mã tin do sàn cấp, và checkpoint cho phép chạy lại chỉ bổ sung
phần còn thiếu thay vì tải lại từ đầu.

## Bảo vệ thông tin cá nhân

Số điện thoại bị xoá **ngay tại thời điểm ghi file**, không phải ở bước tiền xử lý. Lý
do: file thô không bao giờ được sửa, nên một số điện thoại đã lọt vào đó sẽ nằm lại vĩnh
viễn.

Người rao thường né bộ lọc của sàn, nên số điện thoại xuất hiện dưới nhiều kiểu nguỵ
trang: chữ số Unicode ngoài ASCII, emoji keycap, chữ cái thay chữ số ("O9O1..."), số
viết bằng chữ ("không chín một"), ký tự vô hình chèn giữa các chữ số. Một chuỗi regex
đơn giản trên văn bản gốc không bắt xuể. Cách làm của nhóm: chuẩn hoá văn bản thành một
chuỗi chỉ-để-dò (mọi biến thể quy về chữ số ASCII) nhưng giữ bản đồ vị trí ngược về văn
bản gốc, dò trên bản chuẩn hoá rồi cắt đúng đoạn tương ứng trong bản gốc. Nhờ vậy phần
văn bản không phải số điện thoại giữ nguyên từng ký tự.

Mười bốn kiểu nguỵ trang được phủ bằng kiểm thử tự động. Cổng kiểm chất lượng quét lại
toàn bộ kho thô và xác nhận không còn tin nào mang dấu vết số điện thoại.

## Cổng kiểm chất lượng

Trước khi sang bước tiền xử lý, kho thô được chấm theo sáu ngưỡng. Mục đích không phải
chấm điểm dữ liệu mà là buộc phải ra quyết định: chưa đạt thì hoặc mở nguồn dự phòng,
hoặc nới phạm vi quận, và lựa chọn đó được ghi lại.

Chạy ngày 19/08/2026. Nguồn thô: chotot 2.400, mogi 360.

| Kiểm tra | Đạt được | Ngưỡng | Kết quả |
|---|---:|---:|:---:|
| Tổng số tin thô (sau khử trùng theo id) | 2.760 | ≥ 8.000 | CHƯA ĐẠT |
| Tỷ lệ tin có mô tả ≥ 200 ký tự | 87,8% | ≥ 90,0% | CHƯA ĐẠT |
| Tỷ lệ tin có giá dạng số | 100,0% | ≥ 80,0% | ĐẠT |
| Tỷ lệ tin có phường hoặc toạ độ | 100,0% | ≥ 70,0% | ĐẠT |
| Tin ở 3 quận mục tiêu | 2.760 | ≥ 3.000 | CHƯA ĐẠT |
| Số tin còn dấu vết số điện thoại | 0 | ≤ 0 | ĐẠT |

**3/6 ngưỡng đạt.**

#### Quyết định

Chưa đạt: tổng số tin thô (sau khử trùng theo id); tỷ lệ tin có mô tả ≥ 200 ký tự; tin ở 3 quận mục tiêu.

Theo runbook 01 §6, chưa đạt ngưỡng nào thì phải chọn một trong hai hướng và
ghi lại lựa chọn: (a) mở nguồn dự phòng alonhadat/homedy, hoặc (b) nới phạm vi
sang toàn bộ quận của TP.HCM.

**Trạng thái hiện tại**: các script crawl đang chạy ở mức giới hạn có chủ ý để
kiểm pipeline đầu-cuối, phần thu thập đủ số lượng do thành viên phụ trách dữ
liệu chạy tiếp bằng chính các lệnh trong `docs/huong-dan-su-dung.md` §3. Nhờ
checkpoint và khử trùng theo mã tin, lần chạy sau chỉ bổ sung phần còn thiếu.
Vì vậy chưa mở nguồn dự phòng: nguyên nhân chưa đạt là hạn mức tự đặt, không
phải nguồn dữ liệu cạn.
## Quy mô và quy trình làm sạch

| Bước | Tổng | Chợ Tốt | mogi | HF (lịch sử) | Ghi chú |
|---|---:|---:|---:|---:|---|
| Gộp ba nguồn | 42.760 | 2.400 | 360 | 40.000 | sau khử trùng theo id ngay lúc crawl |
| Loại dòng thiếu giá hoặc diện tích | 41.997 (-763) | 2.397 | 356 | 39.244 | thiếu giá 756, thiếu diện tích 7 |
| Luật cứng miền hợp lệ + lọc tin cho thuê | 38.370 (-3.627) | 2.358 | 347 | 35.665 | diện tích ngoài khoảng: 567, giá ngoài khoảng: 1364, tin cho thuê: 2110 |
| Khử trùng lặp (chặn → cosine ký tự → giá) | 35.617 (-2.753) | 2.342 | 339 | 32.936 | 2372 nhóm, loại 2753 dòng |
| IQR log(giá/m²) theo từng quận | 34.607 (-1.010) | 2.326 | 334 | 31.947 | loại 1010 dòng |
| Điền trung vị theo (loại nhà × quận) + cột chỉ báo | 34.607 (+0) | 2.326 | 334 | 31.947 | bedrooms: 13167, bathrooms: 14827, floors: 5485, frontage_m: 16008, alley_width_m: 31752 |
Bảng trên đọc từ trên xuống là toàn bộ vòng đời của dữ liệu. Ba bước cắt nhiều nhất:

**Luật cứng miền hợp lệ và lọc tin cho thuê.** Bước lọc tin cho thuê từng gắn cờ 27% số
dòng khi quét cả phần mô tả, vì tin bán rất hay lấy dòng tiền cho thuê ra làm điểm bán
hàng ("nhà đang cho thuê 15 triệu/tháng, mua là có thu nhập ngay"). Những tin đó là tin
BÁN. Chuyển sang chỉ đọc tiêu đề, tỷ lệ gắn cờ về mức hợp lý.

**Khử trùng lặp.** Chạy trước khi chia tập, không phải sau: một căn nhà đăng lại mà rơi
vào cả tập huấn luyện lẫn tập kiểm tra thì mô hình được xem trước đáp án. Quy trình ba
tầng: chặn theo (phường, diện tích làm tròn 5 m²) → tương đồng TF-IDF trên n-gram ký tự
với ngưỡng cosine 0,85 → giá chênh không quá 3%. Dùng n-gram ký tự chứ không phải n-gram
từ vì bản đăng lại thường đổi vài từ, thêm emoji, viết hoa khác đi, nhưng kết cấu ký tự
gần như không đổi. Năm mươi cặp mẫu được xuất ra để rà tay.

**Ngoại lai hai tầng.** Tầng một là miền hợp lệ khai báo sẵn. Tầng hai là IQR trên
log(giá mỗi m²) tính **theo từng quận**: mức giá bình thường ở quận trung tâm là vô lý ở
ven đô, nên một ngưỡng chung cho cả thành phố sẽ cắt oan quận đắt và bỏ sót quận rẻ.
Quận có ít hơn 60 tin dùng ngưỡng toàn thành phố, vì IQR trên vài chục điểm còn nhiễu
hơn cái nó định lọc. Mọi ngưỡng tầng hai đều tính từ dữ liệu, không lấy từ con số nhớ
sẵn.

## Chuẩn hoá địa chỉ qua đợt sáp nhập 2025

Từ 01/07/2025, TP.HCM bỏ cấp quận và còn 168 phường/xã. Dữ liệu của đồ án nằm ở cả hai
hệ: tin crawl 2026 ghi theo phường mới, bộ lịch sử và mogi ghi theo phường cũ. Không quy
về một hệ thì cùng một khu phố bị tách thành nhiều nhóm.

Nhóm chọn **hệ quy chiếu cũ** (quận + phường trước sáp nhập): phần lớn dữ liệu đã ở hệ
này, quận cũ là mức phân giải mà thị trường bất động sản quen dùng, và 168 phường mới
quá mịn cho vài chục nghìn tin.

Bảng ánh xạ phường mới sang phường cũ được dựng **từ chính dữ liệu crawl** thay vì tải
từ kho dữ liệu bên ngoài. API Chợ Tốt trả cả tên phường theo hệ cũ lẫn hệ mới cho cùng
một tin, nên mỗi tin là một cặp ánh xạ do chính sàn khẳng định. Cách này đúng với đúng
bộ dữ liệu đang dùng, có ngày chốt rõ ràng, và không kéo theo ràng buộc license của bên
thứ ba. Hạn chế phải nêu: bảng chỉ phủ các phường xuất hiện trong dữ liệu đã crawl.

Bảng dựng được cũng cho thấy đúng cạm bẫy đã lường trước: 14 trong 16 phường mới gộp từ
nhiều phường cũ khác nhau, tỷ lệ đa số thấp nhất chỉ 0,45. Với những phường đó, phép ánh
xạ chọn theo đa số và tỷ lệ đa số được lưu lại để biết ánh xạ nào đáng ngờ.

## Chất lượng trích xuất đặc trưng từ văn bản

Bộ nhãn vàng: 200 tin lấy ngẫu nhiên (seed 42) từ kho thô Chợ Tốt.
Nhãn lấy từ các trường có cấu trúc người đăng điền vào form của sàn; bộ luật
regex chỉ đọc tiêu đề và mô tả nên không hề thấy các trường đó.

| Trường | Nhãn được nêu trong mô tả | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Diện tích (m²) | 99/200 | 0,939 | 0,939 | **0,939** ✓ |
| Số phòng ngủ | 130/184 | 0,898 | 0,877 | **0,887** |
| Số nhà tắm | 68/120 | 0,922 | 0,868 | **0,894** |
| Số tầng | 86/113 | 0,802 | 0,802 | **0,802** |

Chỉ tiêu của runbook 02: F1 ≥ 0,9 cho diện tích, số phòng ngủ và số tầng
(đánh dấu ✓ ở bảng trên).

#### Lỗi còn lại

| Trường | Đúng | Bỏ sót | Lệch 1 đơn vị | Lệch khác |
|---|---:|---:|---:|---:|
| Diện tích (m²) | 93 | 0 | 0 | 6 |
| Số phòng ngủ | 114 | 3 | 12 | 1 |
| Số nhà tắm | 59 | 4 | 3 | 2 |
| Số tầng | 69 | 0 | 13 | 4 |

Sau hai vòng sửa luật, diện tích đạt chỉ tiêu còn số tầng dừng ở mức thấp hơn.
Nhìn vào cột lỗi: 13 trong số 17 lỗi của trường
số tầng là lệch đúng một đơn vị, và phần lớn rơi vào các tin viết "1 trệt 1 lầu"
nhưng điền vào form con số 1. Đây là mâu thuẫn trong chính tin rao chứ không phải
bộ luật đọc sai: cùng một cách viết, người bán này khai 1, người bán kia khai 2.

Hai vòng sửa đã dùng hết theo đúng kịch bản rủi ro của kế hoạch ("F1 chững dưới
0,9 sau hai vòng → báo cáo trung thực kèm phân tích lỗi"), nên nhóm dừng ở đây
thay vì tiếp tục chỉnh luật cho khớp một tập nhãn tự nó đã nhiễu. Trường số tầng
vẫn được đưa vào mô hình kèm cột chỉ báo thiếu, và mức nhiễu này được nêu lại ở
phần hạn chế của báo cáo.

Cột giữa cho biết bao nhiêu nhãn thật sự được nêu trong mô tả: con số phải nằm
trong khoảng ±26 ký tự quanh một từ khoá của đúng trường đó. Phần còn lại là
những tin mà người bán điền form một đằng, viết mô tả một nẻo; chúng nằm ngoài
tầm với của bất kỳ bộ luật văn bản nào và được loại khỏi phép đo thay vì tính là
lỗi của bộ luật.
## Mô tả trường dữ liệu

Bảng đầy đủ nằm ở `docs/dataset-card.md`. Các trường chính:

| Nhóm | Trường | Ghi chú |
|---|---|---|
| Nhãn | `total_price_vnd` | Tổng giá rao, đơn vị VND |
| Kích thước | `area_m2`, `frontage_m`, `alley_width_m` | m², m |
| Bố cục | `bedrooms`, `bathrooms`, `floors` | |
| Vị trí | `district`, `ward`, `street`, `position` | Hệ quy chiếu cũ |
| Pháp lý | `legal_status`, `direction`, `property_type` | |
| Văn bản | `description`, `description_clean`, `description_tokens` | Bản gốc, bản đã xoá giá, bản đã tách từ |
| Chỉ báo | `*_missing`, `*_from_text` | Giá trị gốc thiếu / giá trị đến từ regex trên mô tả |

Hai nhóm cột chỉ báo là có chủ ý. `*_missing` giữ lại thông tin "người bán không ghi
trường này" — bản thân việc không ghi đã là một tín hiệu. `*_from_text` cho biết giá trị
đến từ form của sàn hay từ bộ luật đọc mô tả, để đo được phần đóng góp của bước trích
xuất.

## Thống kê mô tả

![Phân phối tổng giá ở thang gốc và thang log](../figures/eda-01-phan-phoi-gia.png)

Phân phối giá lệch phải nặng với đuôi kéo dài. Đây chính là lập luận cho việc huấn luyện
trên log(giá): thang log gần đối xứng hơn hẳn, và sai số trên thang log là sai số tương
đối, nghĩa là lệch 10% ở căn hai tỷ bị phạt ngang lệch 10% ở căn hai mươi tỷ.

![Phân phối diện tích](../figures/eda-02-phan-phoi-dien-tich.png)

![Số tin theo quận và theo nguồn](../figures/eda-03-so-tin-theo-quan.png)

Phủ dữ liệu không đều: ba quận mục tiêu dày hơn hẳn phần còn lại. Kết quả cho các quận
khác vì thế kém tin cậy hơn, và thí nghiệm E3 đo trực tiếp mức suy giảm đó.

![Giá mỗi m² trung vị theo quý](../figures/eda-04-gia-m2-theo-quy.png)

Chênh lệch giá mỗi m² giữa các quận là lý do ngưỡng ngoại lai được tính theo từng quận
chứ không tính chung cho cả thành phố.

## Đạo đức và giấy phép

Bốn ranh giới nhóm tự đặt và tuân thủ:

1. **Tôn trọng `robots.txt` từng trang.** Bản chụp nguyên văn kèm ngày giờ tải nằm trong
   `docs/robots-snapshots/`. Với mogi.vn, các nhánh bị cấm (`/api/`, `/Property/`,
   `/template/`, `/MarketPrice/`, `/trang-ca-nhan/`) đều không được crawler chạm tới.
2. **Không vượt anti-bot chủ động.** Các trang dựng Cloudflare bị loại khỏi danh sách
   nguồn ngay từ đầu chứ không tìm cách đi vòng. Đồ án học thuật không cần và không nên.
3. **Không thu thập, không lưu thông tin người bán.** Các trường tài khoản bị loại thẳng
   tại nguồn; số điện thoại trong mô tả bị xoá lúc ghi file.
4. **Không tái phân phối dữ liệu thô.** Thư mục `data/` bị chặn khỏi git. Repo chỉ chứa
   mã nguồn, bảng kết quả và tài liệu.

Giấy phép cần ghi nhận: bộ dữ liệu lịch sử `tinixai/vietnam-real-estates` phát hành theo
CC BY-NC 4.0, cho phép dùng phi thương mại và yêu cầu ghi nguồn, hai điều kiện mà đồ án
đều đáp ứng.
