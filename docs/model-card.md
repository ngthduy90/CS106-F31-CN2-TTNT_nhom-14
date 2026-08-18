# Model card — XGBoost

## Dùng để làm gì

Ước lượng tổng giá rao của nhà ở riêng lẻ và căn hộ tại TP.HCM từ các thuộc
tính cơ bản và mô tả tự do của tin rao. Đây là mô hình học từ GIÁ RAO, không
phải giá giao dịch: dùng nó để tham khảo mặt bằng rao bán, không dùng để định
giá tài sản thế chấp hay ra quyết định tài chính.

## Dữ liệu huấn luyện

- Số dòng: 2.326
- Nguồn: chotot
- Khoảng thời gian: 08/2026 – 08/2026
- Địa bàn: TP.HCM, dày nhất ở Tân Bình, Tân Phú, Quận 12

## Kết quả (5-fold trên nguồn Chợ Tốt)

| Chỉ số | Giá trị |
|---|---:|
| RMSE (tỷ) | 3,736 |
| MAE (tỷ) | 1,560 |
| MdAPE (%) | 12,975 |
| R² | 0,726 |

## Hạn chế đã biết

- Học từ giá rao; giá giao dịch thực tế thường thấp hơn nhưng nhóm không có dữ
  liệu để đo khoảng cách đó.
- Chỉ phủ TP.HCM, và dày nhất ở ba quận mục tiêu. Đưa sang tỉnh khác thì không
  còn giá trị.
- Tin rao có nhiễu: cùng một căn có thể được mô tả bằng hai bộ số khác nhau
  (xem bảng chất lượng trích xuất).
- Không dùng được cho bất động sản đặc thù: đất nền diện tích lớn, nhà xưởng,
  khách sạn — chúng đã bị loại ở bước làm sạch.

Seed: 42. Tham số tốt nhất: `{'model__regressor__subsample': '0.7', 'model__regressor__n_estimators': '800', 'model__regressor__max_depth': '4', 'model__regressor__learning_rate': '0.05'}`.
