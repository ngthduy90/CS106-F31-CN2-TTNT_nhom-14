# Data funnel — số dòng còn lại sau từng bước

| Bước | Tổng | Chợ Tốt | mogi | HF (lịch sử) | Ghi chú |
|---|---:|---:|---:|---:|---|
| Gộp ba nguồn | 42.760 | 2.400 | 360 | 40.000 | sau khử trùng theo id ngay lúc crawl |
| Loại dòng thiếu giá hoặc diện tích | 41.997 (-763) | 2.397 | 356 | 39.244 | thiếu giá 756, thiếu diện tích 7 |
| Luật cứng miền hợp lệ + lọc tin cho thuê | 38.370 (-3.627) | 2.358 | 347 | 35.665 | diện tích ngoài khoảng: 567, giá ngoài khoảng: 1364, tin cho thuê: 2110 |
| Khử trùng lặp (chặn → cosine ký tự → giá) | 35.617 (-2.753) | 2.342 | 339 | 32.936 | 2372 nhóm, loại 2753 dòng |
| IQR log(giá/m²) theo từng quận | 34.607 (-1.010) | 2.326 | 334 | 31.947 | loại 1010 dòng |
| Điền trung vị theo (loại nhà × quận) + cột chỉ báo | 34.607 (+0) | 2.326 | 334 | 31.947 | bedrooms: 13167, bathrooms: 14827, floors: 5485, frontage_m: 16008, alley_width_m: 31752 |
