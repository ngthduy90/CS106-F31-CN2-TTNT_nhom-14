# Cổng kiểm chất lượng dữ liệu thô

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

## Quyết định

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
