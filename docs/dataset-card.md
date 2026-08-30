# Dataset card: dữ liệu giá nhà TP.HCM

Bộ dữ liệu do Nhóm 14 dựng cho đồ án CS106.F31.CN2, đề tài 5.

## Tóm tắt

Tin rao bán bất động sản tại TP.HCM, gộp từ ba nguồn, đã làm sạch và chuẩn hoá về một
lược đồ. Mỗi dòng là một tin rao, không phải một giao dịch.

| | |
|---|---|
| Đơn vị một dòng | Một tin rao bán |
| Biến mục tiêu | `total_price_vnd`, tổng giá rao, đơn vị VND |
| Phạm vi địa lý | TP.HCM, dày nhất ở Tân Bình, Tân Phú, Quận 12 |
| Hệ quy chiếu địa danh | **Cũ** (quận + phường trước sáp nhập 01/07/2025) |
| Số dòng sau làm sạch | xem [`data-funnel.md`](../reports/tables/data-funnel.md) |

## Nguồn

| Nguồn | Vai trò | Cách lấy | Thời điểm | License |
|---|---|---|---|---|
| Chợ Tốt | Hiện tại (nguồn B) | API công khai `gateway.chotot.com/v1/public/ad-listing` | 08/2026 | Không tái phân phối dữ liệu thô |
| mogi.vn | Hiện tại (nguồn B) | HTML render sẵn, hai bước danh sách → chi tiết | 08/2026 | Không tái phân phối dữ liệu thô |
| `tinixai/vietnam-real-estates` | Lịch sử (nguồn A) | Tải parquet từ Hugging Face | 2025-06 → 2026-03 | CC BY-NC 4.0 |

Bản chụp `robots.txt` của từng host, kèm ngày giờ tải, nằm trong
[`robots-snapshots/`](robots-snapshots/).

## Các trường

| Trường | Kiểu | Đơn vị | Ghi chú |
|---|---|---|---|
| `listing_id` | chuỗi | | `<nguồn>-<mã tin>` |
| `source` | chuỗi | | `chotot` / `mogi` / `hf` |
| `collected_at` | thời điểm | UTC | Lúc crawl; rỗng với nguồn lịch sử |
| `published_at` | thời điểm | | Lúc tin được đăng |
| `title`, `description` | chuỗi | | Văn bản gốc, đã xoá số điện thoại |
| `description_clean` | chuỗi | | Đã xoá mọi cụm tiền tệ |
| `description_tokens` | chuỗi | | Đã tách từ tiếng Việt, dùng cho TF-IDF |
| `total_price_vnd` | số thực | VND | **Biến mục tiêu** |
| `price_kind` | chuỗi | | Đường parse nào cho ra giá này |
| `price_mismatch` | luận lý | | Tổng giá lệch quá 10% so với đơn giá × diện tích |
| `area_m2` | số thực | m² | |
| `bedrooms`, `bathrooms`, `floors` | số nguyên | | |
| `frontage_m`, `alley_width_m` | số thực | m | |
| `position` | chuỗi | | mặt tiền / hẻm / không rõ |
| `legal_status`, `direction`, `property_type` | chuỗi | | |
| `street`, `ward`, `district` | chuỗi | | Hệ quy chiếu cũ |
| `ward_frame` | chuỗi | | Đơn vị gốc là hệ cũ hay đã ánh xạ từ hệ mới |
| `latitude`, `longitude` | số thực | độ | Chỉ có ở một phần dữ liệu |
| `*_missing` | 0/1 | | Cột chỉ báo: giá trị gốc thiếu và đã được điền |
| `*_from_text` | luận lý | | Giá trị đến từ regex trên mô tả, không từ form |
| `duplicate_group` | chuỗi | | Khoá nhóm tin trùng, để chia tập theo nhóm nếu cần |

## Cách dựng

Chi tiết từng bước và số dòng bị loại ở mỗi bước:
[`data-funnel.md`](../reports/tables/data-funnel.md).

Chất lượng của bước trích đặc trưng từ văn bản:
[`extraction-quality.md`](../reports/tables/extraction-quality.md).

## Hạn chế đã biết

**Giá rao, không phải giá giao dịch.** Đây là hạn chế lớn nhất và không khắc phục được
bằng kỹ thuật. Giá giao dịch thực tế thường thấp hơn giá rao, nhưng nhóm không có dữ
liệu giao dịch để đo khoảng cách đó, nên không đưa ra con số phỏng đoán.

**Tin rao tự mâu thuẫn.** Cùng một tin có thể ghi một bộ số ở form và một bộ số khác
trong mô tả. Bảng chất lượng trích xuất đo đúng mức chênh này: với số tầng, phần lớn
lỗi còn lại là tin viết "1 trệt 1 lầu" nhưng điền số 1 vào form.

**Phủ không đều.** Ba quận mục tiêu dày hơn hẳn phần còn lại, nên kết quả cho các quận
khác kém tin cậy hơn. Thí nghiệm E3 đo trực tiếp mức suy giảm khi sang khu vực chưa
thấy.

**Địa danh chốt tại một ngày.** Bảng ánh xạ phường mới → cũ dựng ngày ghi trong
`data/external/ward_mapping_new_to_old.json`. Hành chính còn tiếp tục thay đổi sau mốc
đó. Bảng chỉ phủ các phường có mặt trong dữ liệu đã crawl, và 14 trong 16 phường mới
gộp từ nhiều phường cũ nên phép ánh xạ chọn theo đa số, tỷ lệ đa số thấp nhất là 0,45.

**Đã loại có chủ ý**: tin cho thuê, tin không công bố giá, bất động sản ngoài miền hợp
lệ (diện tích ngoài 10–1.000 m², giá ngoài 300 triệu–100 tỷ). Tiêu chí lọc được khai
báo ngay từ phần Dữ liệu của báo cáo, không phải áp thêm sau khi thấy chỉ số xấu.

## Ràng buộc sử dụng

- **Không tái phân phối dữ liệu thô.** `data/` bị chặn khỏi git. Tin rao có thể còn dấu
  vết người bán, và bộ lịch sử có license CC BY-NC 4.0 cấm dùng cho mục đích thương mại.
- Trích dẫn bắt buộc khi dùng bộ lịch sử: `tinixai/vietnam-real-estates`, CC BY-NC 4.0.
- Không dùng cho định giá tài sản thế chấp hay quyết định tài chính.
