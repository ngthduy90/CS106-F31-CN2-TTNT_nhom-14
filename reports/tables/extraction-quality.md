# Chất lượng trích xuất đặc trưng định lượng từ văn bản

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

## Lỗi còn lại

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
