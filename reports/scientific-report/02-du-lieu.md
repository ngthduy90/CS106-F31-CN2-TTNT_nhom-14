# Dữ liệu

## Nguồn thu thập

![Nguồn dữ liệu và schema kho thô](../figures/02-nguon-du-lieu-va-schema.png)

| Nguồn | Cách lấy | Thời điểm | Vai trò |
|---|---|---|---|
| Chợ Tốt | API JSON công khai của gateway, quét theo từng quận | {{T1.2: ngày crawl}} | Nguồn chính, tin đang rao 2026 |
| mogi.vn | Parse HTML trang danh sách và trang chi tiết | {{T1.5: ngày crawl}} | Nguồn thứ hai, giảm lệch theo một sàn |
| `tinixai/vietnam-real-estates` | Tải bộ dữ liệu công bố trên Hugging Face | {{T1.6: ngày tải}} | Nguồn lịch sử, tin rao tới ~06/2025 |

Lý do dùng hai nguồn crawl thay vì một: mỗi sàn có tệp người đăng và cách viết tin khác
nhau, học trên một sàn duy nhất thì mô hình bám theo thói quen của sàn đó. Bộ dữ liệu
Hugging Face đóng vai trò dữ liệu lịch sử để đo mức trôi giá theo thời gian, và là
phương án dự phòng nếu crawler hỏng.

Các trang bị loại khỏi phạm vi: batdongsan.com.vn, muaban.net, cafeland và guland đều
chặn bằng Cloudflare. Đồ án không vượt cơ chế chống bot chủ động, đây là ranh giới tự
đặt và được ghi lại ở mục đạo đức bên dưới.

## Quy mô và quy trình làm sạch

{{T2.12: chèn bảng data funnel từ reports/tables/data-funnel.md — số dòng vào và ra ở
từng bước, tách theo nguồn}}

Số tin sau làm sạch: {{T2.12}}. Ngưỡng tối thiểu của đề bài là 5.000 mẫu.

## Mô tả trường dữ liệu

{{T2.17: bảng mô tả trường lấy từ docs/dataset-card.md — tên trường, kiểu, đơn vị, tỷ lệ
thiếu, nguồn (thu trực tiếp hay trích từ mô tả)}}

## Thống kê mô tả

{{T2.16: bốn hình — phân phối giá thang gốc và thang log, phân phối diện tích, số tin
theo quận, trung vị giá mỗi m² theo quý}}

Nhận xét cần viết sau khi có hình: độ lệch phải của phân phối giá là lý do huấn luyện
trên log; chênh lệch giá mỗi m² giữa các quận là lý do tính ngưỡng ngoại lai theo quận.

## Chất lượng trích xuất từ văn bản

{{T2.6: bảng precision/recall/F1 theo từng trường trên bộ nhãn kiểm chứng 200 tin}}

Bộ nhãn kiểm chứng được gán nhãn với sự hỗ trợ của mô hình ngôn ngữ, sau đó lọc tự động
bằng luật "giá trị trích ra phải xuất hiện nguyên văn trong đoạn mô tả" và rà tay một
mẫu con. Cách làm này được ghi rõ để người đọc biết đây không phải nhãn thủ công hoàn
toàn.

## Đạo đức và pháp lý khi thu thập

1. Tôn trọng robots.txt của từng trang. Bản chụp robots.txt tại thời điểm thu thập lưu
   trong `docs/robots-snapshots/`.
2. Tốc độ tối đa một request mỗi 1 đến 2 giây, có backoff khi gặp lỗi giới hạn tần suất.
3. Không thu thập và không lưu thông tin cá nhân người đăng tin. Tên tài khoản, ảnh đại
   diện và số điện thoại bị loại ngay tại bước ghi dữ liệu, kể cả số điện thoại nằm lẫn
   trong đoạn mô tả. Căn cứ: Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.
4. Không tái phân phối dữ liệu thô. Kho GitHub chỉ chứa mã nguồn, dữ liệu đã tổng hợp và
   kết quả.
5. Bộ dữ liệu Hugging Face dùng theo license CC BY-NC 4.0, phù hợp mục đích học thuật
   phi thương mại, có ghi nguồn ở phần tài liệu tham khảo.

## Giới hạn của dữ liệu

Giá trong tin rao là giá người bán đề nghị, không phải giá chốt giao dịch. Tin có thể
trùng, có thể ảo, và mô tả do người đăng tự viết nên chất lượng không đồng đều. Mọi kết
luận trong báo cáo phải đọc trong khuôn khổ đó.
