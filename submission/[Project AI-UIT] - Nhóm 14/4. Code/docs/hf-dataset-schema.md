# Lược đồ bộ dữ liệu lịch sử (nguồn A)

Nguồn: Hugging Face `tinixai/vietnam-real-estates`, license CC BY-NC 4.0.
Phạm vi đã lọc: `province_name == "Hồ Chí Minh"`, `published_at <= 2025-06-30`.
Số dòng sau lọc: 87.811

| Trường | Kiểu | Tỷ lệ có giá trị | Ví dụ |
|---|---|---|---|
| `name` | object | 100.0% | Bán gấp nhà mặt tiền 4 tầng khu phân lô  |
| `description` | object | 100.0% | Nhà 4 tầng mặt tiền KDC Tạ Quang Bửu P5  |
| `property_type_name` | object | 100.0% | Nhà |
| `province_name` | object | 100.0% | Hồ Chí Minh |
| `district_name` | object | 97.7% | 8 |
| `ward_name` | object | 86.0% | 5 |
| `street_name` | object | 62.6% | Tạ Quang Bửu |
| `project_name` | object | 17.9% | Thái An Apartment |
| `price` | object | 98.1% | 9100000000 |
| `area` | float64 | 100.0% | 48.0 |
| `floor_count` | float64 | 16.6% | 4.0 |
| `frontage_width` | float64 | 50.8% | 4.0 |
| `house_depth` | float64 | 1.6% | 12.33 |
| `road_width` | float64 | 7.9% | 5.0 |
| `bedroom_count` | float64 | 57.0% | 3.0 |
| `bathroom_count` | float64 | 53.3% | 3.0 |
| `house_direction` | object | 22.6% | Tây Nam |
| `balcony_direction` | object | 11.7% | Tây Nam |
| `published_at` | datetime64[ns] | 100.0% | 2025-06-06 04:37:25.903000 |

Ghi chú: số điện thoại trong `name` và `description` đã được chính bộ dữ liệu
thay bằng chuỗi `[phone_number]`; pipeline vẫn chạy lại bộ lọc của dự án lên
cột văn bản để không phụ thuộc vào cam kết của bên thứ ba.
