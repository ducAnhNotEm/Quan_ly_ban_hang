# Sales Store Project

## Kiểm tra số dư ví khi mua hàng

Trước khi tạo đơn hàng, hệ thống kiểm tra số dư ví của khách hàng. Nếu số dư không đủ, đơn hàng sẽ không được tạo và người dùng được yêu cầu nạp thêm tiền. Nếu số dư đủ, hệ thống tạo đơn hàng và trừ tiền trong ví.

## Các luồng chính hiện có

- Trang chủ (Trưng bày sản phẩm ngẫu nhiên).
- Đăng nhập / Đăng ký.
- Yêu cầu nạp tiền, Admin duyệt số dư.
- Xem chi tiết sản phẩm.
- Giỏ hàng (thêm, sửa, xóa, chọn mua).
- Thanh toán và Đơn hàng (mua ngay, giỏ hàng).

### Quản lý Sản Phẩm (Dành cho Admin/Staff)
Admin/Staff có thể:
- Xem danh sách toàn bộ sản phẩm.
- Thêm sản phẩm mới kèm hình ảnh, mô tả chi tiết.
- Sửa thông tin sản phẩm (giá bán, tồn kho, phần trăm giảm giá).
- Xóa sản phẩm (hỗ trợ bảo lưu lịch sử đơn hàng an toàn).

### Quản lý Khách Hàng (Dành cho Admin/Staff)
Chức năng quản lý khách hàng cho phép Admin/Staff xem danh sách khách hàng, chỉnh sửa thông tin cơ bản và khóa hoặc mở khóa tài khoản. Hệ thống không xóa khách hàng để tránh mất dữ liệu liên quan đến đơn hàng, ví tiền và lịch sử nạp tiền. Việc khóa tài khoản được thực hiện bằng cách thay đổi trường is_active của User trong Django.
Admin/Staff có thể:
- Xem danh sách khách hàng
- Sửa thông tin khách hàng (họ tên, email, sđt, địa chỉ, ngày sinh, giới tính)
- Khóa/Mở khóa tài khoản khách hàng

## Cài đặt và chạy thử
