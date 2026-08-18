# Thí nghiệm và kết quả

## Thiết kế thí nghiệm

![Thiết kế ba thí nghiệm](../figures/03-thiet-ke-thi-nghiem.png)

Ba thí nghiệm chạy trên cùng một danh mục mô hình và cùng quy tắc chia tập.

- **E1, bảng so sánh chính**: hold-out 80/20 cộng 5-fold cross-validation trên phần
  huấn luyện, chạy riêng cho từng nguồn dữ liệu. Chia tập có phân tầng theo quận và theo
  khoảng giá. Khử trùng lặp thực hiện trước khi chia.
- **E2, chuyển giao theo thời gian**: huấn luyện trên tin rao tới 06/2025, kiểm tra trên
  tin rao crawl tháng 08/2026. Chênh lệch so với E1 nguồn 2026 là thước đo mức trôi giá
  theo thời gian.
- **E3, stress test không gian**: giữ lần lượt các phường nhiều tin nhất làm tập kiểm
  tra, báo cáo trung bình và độ lệch chuẩn. Thí nghiệm này đo khả năng tổng quát hoá sang
  khu vực mô hình chưa thấy.

Hai nguồn dữ liệu không được trộn chung làm thí nghiệm chính vì chúng phủ thời kỳ và địa
bàn khác nhau, nên cờ nguồn sẽ lẫn với biến thời gian và với địa bàn.

Sau khi nguồn lịch sử chuyển sang bộ Hugging Face, cả hai phía của E2 đều là **giá rao**.
Thiết kế ban đầu định đo chênh lệch giữa giá giao dịch và giá rao lẫn với trôi giá theo
thời gian; thiết kế hiện tại chỉ đo một thứ, và vì thế dễ bảo vệ hơn.

## Điều kiện so sánh công bằng

Ba ràng buộc được cài vào code chứ không dựa vào kỷ luật của người chạy:

**Cùng một bộ fold cho mọi mô hình.** Phép chia được tính một lần rồi ghi ra đĩa kèm mã
băm của bộ mã tin. Nếu mỗi mô hình tự chia tập theo seed riêng thì chênh lệch giữa hai
dòng trong bảng một phần là chênh lệch giữa hai phép chia, không đọc được gì.

**Cùng ngân sách tinh chỉnh.** RandomizedSearch với số cấu hình như nhau cho mọi mô
hình, cùng seed. Cho mô hình này hai trăm cấu hình còn mô hình kia mười thì bảng so sánh
đo ngân sách chứ không đo mô hình.

**Danh sách kiểm rò rỉ chạy trước mỗi lần huấn luyện**, không phải một lần lúc đầu. Kết
quả được lưu cạnh mỗi file kết quả. Chi tiết ở chương Phương pháp.

## Chỉ số đánh giá

Mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính **sau khi đã quy ngược về thang
VND**. RMSE và MAE báo bằng tỷ đồng. MdAPE là sai số phần trăm trung vị, bất biến theo
thang đo nên so được giữa quận đắt và quận rẻ. R² báo kèm ba chỉ số kia chứ không đứng
một mình.

## Bảng kết quả chính (E1)

2.326 dòng, chia hold-out 80/20, 5-fold trên phần train, seed 42.
Ngân sách tinh chỉnh: RandomizedSearch 20 cấu hình, giống nhau cho mọi mô hình.

Mỗi ô là trung bình ± độ lệch chuẩn qua 5 fold. **In đậm** là tốt nhất mỗi cột.

| Tầng | Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 0 — mốc | Dummy (trung vị) | 7,250 ± 1,350 | 3,698 ± 0,396 | 34,6 ± 2,1 | -0,053 ± 0,005 |
| 0 — mốc | Trung vị giá/m² theo nhóm | **3,640 ± 0,354** | 1,948 ± 0,146 | 19,5 ± 1,1 | 0,719 ± 0,083 |
| 1 — tuyến tính | Hồi quy tuyến tính | 10,303 ± 9,224 | 2,434 ± 0,818 | 18,4 ± 0,4 | -2,306 ± 4,426 |
| 1 — tuyến tính | Lasso | 10,795 ± 9,976 | 2,444 ± 0,877 | 17,8 ± 0,6 | -2,709 ± 5,083 |
| 1 — tuyến tính | Ridge | 7,920 ± 4,818 | 2,417 ± 0,504 | 18,8 ± 0,5 | -0,672 ± 1,774 |
| 2 — chủ lực | CatBoost | 3,802 ± 1,147 | **1,547 ± 0,238** | 13,5 ± 1,2 | 0,717 ± 0,066 |
| 2 — chủ lực | LightGBM | 3,749 ± 1,133 | 1,550 ± 0,235 | 13,4 ± 0,9 | 0,724 ± 0,068 |
| 2 — chủ lực | Random Forest | 4,513 ± 1,221 | 1,777 ± 0,251 | 14,7 ± 0,6 | 0,599 ± 0,069 |
| 2 — chủ lực | XGBoost | 3,736 ± 1,159 | 1,560 ± 0,245 | **13,0 ± 1,0** | **0,726 ± 0,072** |
| 3 — mở rộng | Cây quyết định | 4,628 ± 1,301 | 2,175 ± 0,332 | 19,4 ± 1,9 | 0,578 ± 0,083 |
| 3 — mở rộng | K láng giềng | 4,693 ± 1,115 | 2,164 ± 0,206 | 19,8 ± 1,1 | 0,558 ± 0,088 |
| 3 — mở rộng | MLP | 12,585 ± 13,378 | 2,594 ± 0,898 | 19,0 ± 0,8 | -4,513 ± 8,896 |

#### Đo trên tập hold-out (chưa từng dùng để chọn tham số)

| Mô hình | RMSE (tỷ) | MAE (tỷ) | MdAPE (%) | R² |
|---|---:|---:|---:|---:|
| Dummy (trung vị) | 6,624 | 3,550 | 36,3 | -0,052 |
| Trung vị giá/m² theo nhóm | 2,988 | 1,801 | 19,4 | 0,786 |
| Hồi quy tuyến tính | 12,599 | 2,336 | 17,0 | -2,804 |
| Lasso | 15,807 | 2,497 | 17,6 | -4,988 |
| Ridge | 13,209 | 2,514 | 19,2 | -3,182 |
| CatBoost | 3,092 | 1,383 | 13,0 | 0,771 |
| LightGBM | 3,109 | 1,403 | 12,7 | 0,768 |
| Random Forest | 3,587 | 1,583 | 14,5 | 0,692 |
| XGBoost | 2,938 | 1,399 | 13,5 | 0,793 |
| Cây quyết định | 4,100 | 1,986 | 18,4 | 0,597 |
| K láng giềng | 3,409 | 1,989 | 21,5 | 0,722 |
| MLP | 4,542 | 2,000 | 18,1 | 0,506 |

**Chú ý khi đọc**: Hồi quy tuyến tính, Lasso, Ridge, MLP có độ lệch chuẩn của RMSE lớn
so với chính trung bình của nó. Nguyên nhân là mô hình huấn luyện trên log(giá)
và phép `exp` khuếch đại một vài dự báo ngoại suy xa thành sai số khổng lồ trên
thang VND. Trung vị không bị ảnh hưởng nên MdAPE của các mô hình này vẫn ở mức
khá — đó chính là lý do bảng báo cả bốn chỉ số thay vì chỉ một.

Ghi chú: mô hình huấn luyện trên log(tổng giá), mọi chỉ số tính sau khi đã quy
ngược về thang VND. RMSE và MAE tính bằng tỷ đồng. MdAPE là sai số phần trăm
trung vị. Mọi mô hình dùng CHUNG một bộ fold, nên chênh lệch giữa các dòng không
lẫn chênh lệch giữa các phép chia tập.
> **Chưa có `reports/tables/e1-results-hf.md`.** Chạy lại pipeline để sinh bảng này.
### Đọc bảng E1

**Mọi mô hình học máy đều thắng Dummy, nhưng mốc đáng quan tâm là baseline môi giới.**
Trung vị giá mỗi m² theo (quận, phường, loại nhà) nhân diện tích chính là cách một người
môi giới định giá trong đầu. Khoảng cách giữa mô hình tốt nhất và mốc đó mới là phần giá
trị mà học máy thực sự tạo ra; khoảng cách so với Dummy chỉ nói rằng dữ liệu có tín hiệu.

**Nhóm boosting dẫn đầu, và cách biệt giữa chúng nhỏ hơn độ lệch chuẩn giữa các fold.**
Khi hai khoảng trung bình ± độ lệch chuẩn chồng lấn gần hết thì không được tuyên bố mô
hình này tốt hơn mô hình kia; bảng chỉ cho phép nói cả nhóm boosting cùng ở mức tốt nhất.

**Nhóm tuyến tính có MdAPE khá nhưng RMSE và R² rất xấu, có khi âm.** Đây không phải lỗi
cài đặt mà là hệ quả trực tiếp của việc huấn luyện trên log giá: mô hình tuyến tính trên
không gian đặc trưng nhiều chiều thỉnh thoảng ngoại suy rất xa ở một vài điểm, và phép
`exp` biến sai lệch đó thành con số khổng lồ trên thang VND. Trung vị không bị ảnh hưởng
nên MdAPE vẫn đẹp, còn RMSE và R² thì sụp.

Đây chính là lý do đề tài yêu cầu báo cả ba chỉ số. Đọc R² một mình sẽ kết luận hồi quy
tuyến tính vô dụng; đọc MdAPE một mình sẽ kết luận nó ngang ngửa boosting. Cả hai kết
luận đều sai. Sự thật là hồi quy tuyến tính đúng ở phần lớn ca nhưng sai thảm ở một số ít
ca, còn boosting thì ổn định ở cả hai mặt.

### Không so R² giữa hai bảng E1

Hai bảng E1 nằm cạnh nhau nên rất dễ bị đọc chéo cột. Với MdAPE thì đọc chéo được, vì đó
là sai số phần trăm và không phụ thuộc phương sai của tập. Với **R² thì không**.

R² đo phần phương sai được giải thích, mà mẫu số của nó chính là phương sai của tập đang
xét. Bộ lịch sử phủ toàn thành phố với hơn hai mươi quận và biên độ giá rộng hơn hẳn bộ
crawl, vốn tập trung vào ba quận. Tập nào có phương sai lớn hơn thì cùng một mô hình sẽ
cho R² cao hơn, kể cả khi nó dự báo tệ hơn theo phần trăm. Trên dữ liệu của nhóm, hiện
tượng đó xảy ra đúng như vậy: cùng một mô hình cho R² cao hơn nhưng MdAPE lại tệ hơn trên
bộ lịch sử.

Vì thế mỗi bảng E1 chỉ được dùng để xếp hạng các mô hình **bên trong** nó. So sánh giữa
hai nguồn phải dựa vào MdAPE, và câu hỏi "chuyển giao giữa hai nguồn mất bao nhiêu" là
việc của thí nghiệm E2 chứ không phải của việc đặt hai bảng cạnh nhau.

## Ablation: đặc trưng văn bản đáng bao nhiêu?

> **Chưa có `reports/tables/ablation.md`.** Chạy lại pipeline để sinh bảng này.
Bốn cấu hình chạy trên cùng bộ fold, cùng mô hình, cùng ngân sách tinh chỉnh, khác biệt
duy nhất là nhánh văn bản. Đây là con số trả lời trực tiếp câu hỏi trung tâm của đề tài:
mô tả rao vặt mang bao nhiêu tín hiệu giá mà các trường có cấu trúc không có.

## Chuyển giao theo thời gian (E2)

> **Chưa có `reports/tables/e2-results.md`.** Chạy lại pipeline để sinh bảng này.
![Giá mỗi m² trung vị theo tháng](../figures/eda-04-gia-m2-theo-thang.png)

### Một cảnh báo phải đọc kèm hình trên

Đường trung vị của cả ba quận mục tiêu đi ngang trong suốt mười tháng dữ liệu lịch sử
(06/2025 – 03/2026), rồi **rơi xuống** ở điểm tin crawl tháng 08/2026. Cám dỗ là kết
luận ngay rằng mặt bằng giá rao đã giảm. Kết luận đó chưa đủ căn cứ, vì đoạn nét đứt
trên hình cùng lúc bắc qua hai thứ:

- **năm tháng không có dữ liệu** (04/2026 – 07/2026), và
- **một lần đổi nguồn**: phần bên trái là bộ lịch sử, điểm bên phải là dữ liệu nhóm tự
  crawl từ hai sàn khác.

Hai sàn khác nhau có tệp người đăng và cơ cấu sản phẩm khác nhau, nên một phần mức chênh
là chênh giữa nguồn chứ không phải chênh theo thời gian. Nhóm không tách được hai thành
phần này bằng dữ liệu hiện có, nên không quy toàn bộ mức rơi cho trôi giá. Đây cũng là
lý do hình được vẽ nét đứt và ký hiệu điểm khác nhau ở hai phía thay vì một đường liền:
người đọc phải thấy chỗ nối là chỗ đáng ngờ.

Cách kiểm chứng cho lần sau đã rõ: crawl bù các tháng còn thiếu trên chính hai sàn đang
dùng, khi đó cả đường sẽ nằm trên một nguồn duy nhất và mức trôi đọc được trực tiếp.

## Stress test không gian (E3)

> **Chưa có `reports/tables/e3-results.md`.** Chạy lại pipeline để sinh bảng này.
## Phân tích lỗi

![Sai số theo quận và theo khoảng giá](../figures/ket-qua-01-sai-so-theo-lat-cat.png)

Đo trên tập hold-out của nguồn Chợ Tốt, bằng mô hình vô địch của bảng E1.

#### Theo quận

| Quận | Số tin kiểm | MdAPE (%) |
|---|---:|---:|
| Tân Bình | 154 | 15,3 |
| Tân Phú | 156 | 13,5 |
| Quận 12 | 156 | 12,0 |

#### Theo khoảng giá

| Khoảng giá | Số tin kiểm | MdAPE (%) |
|---|---:|---:|
| dưới 2 tỷ | 26 | 23,0 |
| 2–5 tỷ | 154 | 13,9 |
| 5–10 tỷ | 205 | 10,7 |
| trên 10 tỷ | 81 | 20,4 |

Sai số thấp nhất ở khoảng 5–10 tỷ (10,7%) và cao nhất
ở khoảng dưới 2 tỷ (23,0%). Đây là hình chữ U quen
thuộc của bài toán định giá: phân khúc giữa vừa nhiều mẫu vừa đồng nhất, còn hai
đầu vừa ít mẫu vừa đa dạng — nhà rẻ thường là nhà có vấn đề pháp lý hoặc vị trí
đặc thù, nhà đắt thường là bất động sản dị biệt mà vài chục mẫu không đủ để học.
Lát cắt theo quận cho biết mô hình yếu ở địa bàn nào. Lát cắt theo khoảng giá cho thấy
một hình chữ U rất rõ: sai số thấp nhất ở phân khúc giữa, cao hơn hẳn ở cả hai đầu. Đọc
được ngay từ hình này là một cảnh báo thực dụng cho người dùng mô hình — với căn nhà nằm
ở hai đầu phân khúc, con số dự báo phải được coi là ước lượng thô, không phải một mức
giá đáng tin.

## Giải thích mô hình

![SHAP beeswarm](../figures/ket-qua-03-shap-beeswarm.png)

Biểu đồ beeswarm cho biết đặc trưng nào ảnh hưởng mạnh nhất tới dự báo trên toàn tập, và
ảnh hưởng theo chiều nào.

![Permutation importance](../figures/ket-qua-05-permutation-importance.png)

Permutation importance được báo kèm chứ không dùng riêng impurity importance của mô hình
cây. Impurity importance thiên vị các biến có nhiều mức — như tên đường và phường — nên
đọc một mình sẽ dẫn tới kết luận sai về biến nào thật sự quan trọng.

![Ca sai nặng nhất](../figures/ket-qua-04-shap-waterfall-1.png)

Ba biểu đồ waterfall cho ba ca sai nặng nhất được xem riêng. Chúng thường là bất động
sản dị biệt: diện tích rất lớn, vị trí đặc thù, hoặc tin ghi thiếu thông tin then chốt.

## Đường cong học

![Đường cong học theo cỡ tập huấn luyện](../figures/ket-qua-02-duong-cong-hoc.png)

Mô hình: XGBoost. Mỗi dòng: lấy ngẫu nhiên một phần tập huấn luyện,
huấn luyện lại, đo trên cùng một tập hold-out.

| Tỷ lệ tập huấn luyện | Số tin | RMSE (tỷ) | MdAPE (%) |
|---:|---:|---:|---:|
| 10% | 186 | 4,679 | 18,9 |
| 25% | 465 | 3,555 | 15,9 |
| 40% | 744 | 3,475 | 14,7 |
| 55% | 1023 | 3,078 | 14,6 |
| 70% | 1302 | 3,216 | 13,8 |
| 85% | 1581 | 2,822 | 12,8 |
| 100% | 1860 | 2,699 | 12,0 |

Từ 186 lên 1860 tin, MdAPE giảm từ 18,9% xuống 12,0%.

**Bước cuối vẫn còn giảm 0,8 điểm phần trăm**, nghĩa là đường cong chưa phẳng: thu thập thêm dữ liệu vẫn còn cải thiện được sai số, và đó là chỗ đáng đầu tư tiếp theo.
Đường cong này trả lời một câu hỏi thực tế mà nhóm phải quyết: crawl thêm dữ liệu có
đáng không, hay nên dồn công sức vào chất lượng đặc trưng. Câu trả lời nằm ở bước cuối
cùng của bảng — nếu thêm 15% dữ liệu cuối vẫn còn kéo sai số xuống thì đường chưa bão
hoà và việc thu thập vẫn còn giá trị.
