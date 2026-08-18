# Tài liệu tham khảo

Mọi URL trong danh sách đã được mở lại ngày 19/08/2026. Hai nghị quyết về sắp xếp đơn vị
hành chính được đối chiếu với bản đăng trên cổng thông tin của Chính phủ và Quốc hội,
không trích theo trí nhớ.

## Đề bài và yêu cầu môn học

1. Nguyễn Đình Hiển. *Đề tài môn Trí tuệ nhân tạo*, CS106.F31.CN2, Trường Đại học Công
   nghệ Thông tin, ĐHQG-HCM, 2026. Đề tài 5 và yêu cầu bài nộp.

## Nguồn dữ liệu

2. Chợ Tốt. Gateway API công khai `gateway.chotot.com/v1/public/ad-listing`. Truy cập
   19/08/2026.
3. mogi.vn. Chuyên trang mua bán nhà đất TP.HCM. `mogi.vn/ho-chi-minh`. Truy cập
   19/08/2026. Bản chụp `robots.txt` lưu tại `docs/robots-snapshots/mogi.vn.robots.txt`.
4. tinixai. *vietnam-real-estates* dataset. Hugging Face, license CC BY-NC 4.0.
   `huggingface.co/datasets/tinixai/vietnam-real-estates`. Truy cập 19/08/2026. Phạm vi
   thực dùng: lát cắt TP.HCM, tin đăng 06/2025 – 03/2026.

## Công cụ xử lý ngôn ngữ tiếng Việt

5. Underthesea contributors. *underthesea: Vietnamese NLP toolkit*, phiên bản 6.8.4.
   Apache-2.0. `github.com/undertheseanlp/underthesea`.
6. Trần Việt Trung. *pyvi: Python Vietnamese toolkit*, phiên bản 0.1.1. Dùng làm phương
   án dự phòng cho bước tách từ. `github.com/trungtv/pyvi`.

Danh sách từ dừng và stoplist riêng cho tin rao do nhóm tự xây dựng trong
`src/features/text.py`, không lấy từ kho bên ngoài, nên không có trích dẫn ở mục này.

## Phương pháp và mô hình

7. Chen, T. và Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System". *KDD '16*.
8. Ke, G. và cộng sự (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision
   Tree". *NIPS '17*.
9. Prokhorenkova, L. và cộng sự (2018). "CatBoost: unbiased boosting with categorical
   features". *NeurIPS '18*, arXiv:1706.09516.
10. Lundberg, S. và Lee, S.-I. (2017). "A Unified Approach to Interpreting Model
    Predictions". *NIPS '17*.
11. De Cock, D. (2011). "Ames, Iowa: Alternative to the Boston Housing Data as an End of
    Semester Regression Project". *Journal of Statistics Education*, 19(3). Tiền lệ mô
    hình hoá log giá nhà trong giảng dạy.
12. Pedregosa, F. và cộng sự (2011). "Scikit-learn: Machine Learning in Python".
    *Journal of Machine Learning Research*, 12, 2825-2830.

## Dữ liệu hành chính và địa lý

13. Quốc hội khoá XV. *Nghị quyết số 202/2025/QH15 ngày 12/06/2025 về việc sắp xếp đơn
    vị hành chính cấp tỉnh*. Cả nước còn 34 đơn vị cấp tỉnh gồm 28 tỉnh và 6 thành phố.
    Toàn văn: `vanban.chinhphu.vn` và `xaydungchinhsach.chinhphu.vn`.
14. Uỷ ban Thường vụ Quốc hội khoá XV. *Nghị quyết số 1685/NQ-UBTVQH15 ngày 16/06/2025
    về việc sắp xếp các đơn vị hành chính cấp xã của Thành phố Hồ Chí Minh năm 2025*.
    Sau sắp xếp TP.HCM có 168 đơn vị: 113 phường, 54 xã và 1 đặc khu. Toàn văn:
    `xaydungchinhsach.chinhphu.vn`.
15. Bảng ánh xạ phường mới sang phường cũ do nhóm tự dựng từ các cặp `ward_name` và
    `ward_name_v3` trong dữ liệu Chợ Tốt đã crawl. Ngày chốt và toàn bộ bảng lưu tại
    `data/external/ward_mapping_new_to_old.json`. Không dùng bảng ánh xạ của bên thứ ba
    nên không phát sinh ràng buộc license.

## Pháp lý về dữ liệu cá nhân

16. Quốc hội. *Luật Bảo vệ dữ liệu cá nhân 2025*, hiệu lực từ 01/01/2026, cùng Nghị định
    356/2025/NĐ-CP hướng dẫn thi hành. Đây là căn cứ pháp lý hiện hành cho quy tắc không
    thu thập và không lưu thông tin người đăng tin của đồ án.
17. Chính phủ. *Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân*. **Đã hết hiệu lực từ
    01/01/2026**, được thay thế bởi Luật Bảo vệ dữ liệu cá nhân 2025. Ghi ở đây vì tài
    liệu khảo sát ban đầu của nhóm còn dẫn văn bản này; dữ liệu của đồ án thu thập tháng
    08/2026 nên thuộc phạm vi điều chỉnh của luật mới.

Nhóm không trích dẫn điều khoản cụ thể nào của hai văn bản trên. Quy tắc áp dụng trong
đồ án — không thu thập, không lưu, không tái phân phối thông tin cá nhân người đăng tin
— chặt hơn mức tối thiểu mà quy định yêu cầu, nên không cần diễn giải điều khoản để biện
minh cho một lựa chọn kỹ thuật nào.
