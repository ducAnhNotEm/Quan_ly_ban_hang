# HỆ THỐNG QUẢN LÝ BÁN HÀNG - DJANGO

## 1. Giới thiệu dự án

Đây là dự án website quản lý bán hàng được xây dựng bằng Django. Hệ thống hỗ trợ các chức năng cơ bản của một website thương mại điện tử như:

- Đăng ký tài khoản.
- Đăng nhập, đăng xuất.
- Xem danh sách sản phẩm.
- Tìm kiếm và lọc sản phẩm.
- Xem chi tiết sản phẩm.
- Thêm sản phẩm vào giỏ hàng.
- Cập nhật giỏ hàng.
- Xóa sản phẩm khỏi giỏ hàng.
- Mua ngay sản phẩm.
- Thanh toán đơn hàng.
- Quản lý ví tiền.
- Gửi yêu cầu nạp tiền.
- Admin/Staff duyệt yêu cầu nạp tiền.
- Admin/Staff xem thống kê bán hàng.
- Admin/Staff quản lý sản phẩm.
- Admin/Staff quản lý khách hàng nếu chức năng này đã được bổ sung.

Dự án sử dụng Django làm backend, MySQL làm cơ sở dữ liệu và Django Template để xây dựng giao diện.

---

## 2. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python |
| Framework | Django |
| Cơ sở dữ liệu | MySQL |
| Giao diện | HTML, CSS, Django Template |
| Xử lý ảnh | Pillow |
| Quản lý ảnh upload | Django Media |
| ORM | Django ORM |
| Tài khoản | Django Authentication |
| UML | PlantUML |

---

## 3. Cấu trúc tổng quan dự án

Cấu trúc chính của dự án:

```text
Quan_ly_ban_hang/
│
├── accounts/
│   ├── models.py
│   ├── forms.py
│   └── ...
│
├── products/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── orders/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── banhang/
│   ├── settings.py
│   ├── urls.py
│   ├── sql_utils.py
│   ├── wsgi.py
│   └── ...
│
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   └── ...
│
├── static/
│   └── ...
│
├── media/
│   └── products/
│
├── sql/
│   └── ...
│
├── UML/
│   └── ...
│
├── manage.py
├── requirements.txt
├── .env.mysql.example
└── README.md
```

Ý nghĩa các thư mục chính:

| Thư mục/File | Vai trò |
|---|---|
| `accounts` | Quản lý khách hàng, ví tiền và yêu cầu nạp tiền |
| `products` | Quản lý sản phẩm, ảnh sản phẩm, giỏ hàng |
| `orders` | Quản lý thanh toán, đơn hàng và chi tiết đơn hàng |
| `banhang` | Cấu hình chính của project Django |
| `templates` | Chứa giao diện HTML |
| `static` | Chứa file tĩnh như CSS, JS, ảnh giao diện |
| `media` | Chứa ảnh sản phẩm upload |
| `sql` | Chứa các câu SQL dùng riêng cho một số chức năng |
| `UML` | Chứa sơ đồ UML của hệ thống |
| `manage.py` | File quản lý project Django |

---

## 4. Các app chính trong hệ thống

Trong `banhang/settings.py`, project khai báo các app chính:

```python
INSTALLED_APPS = [
    ...
    'accounts',
    'products',
    'orders',
]
```

### 4.1. App `accounts`

App `accounts` dùng để quản lý thông tin người dùng phía khách hàng.

Các model chính:

| Model | Chức năng |
|---|---|
| `Customer` | Lưu hồ sơ khách hàng |
| `Wallet` | Lưu ví tiền của khách hàng |
| `TopUpRequest` | Lưu yêu cầu nạp tiền |

Mỗi tài khoản Django `User` có thể gắn với một hồ sơ `Customer`. Mỗi `Customer` có một `Wallet`. Khách hàng có thể gửi nhiều yêu cầu nạp tiền thông qua `TopUpRequest`.

---

### 4.2. App `products`

App `products` dùng để quản lý sản phẩm và giỏ hàng.

Các model chính:

| Model | Chức năng |
|---|---|
| `Product` | Lưu thông tin sản phẩm |
| `Cart` | Lưu giỏ hàng của khách hàng |
| `CartItem` | Lưu từng sản phẩm trong giỏ hàng |

Model `Product` có các thông tin như tên sản phẩm, danh mục, mô tả, giá, phần trăm giảm giá, số lượng tồn kho và ảnh sản phẩm.

Model `CartItem` có số lượng sản phẩm, trạng thái chọn sản phẩm và các trường tính tiền như `sub_total`, `discount_amount`.

---

### 4.3. App `orders`

App `orders` dùng để quản lý đơn hàng và thanh toán.

Các model chính:

| Model | Chức năng |
|---|---|
| `Order` | Lưu thông tin đơn hàng |
| `OrderDetail` | Lưu chi tiết từng sản phẩm trong đơn hàng |

Một đơn hàng thuộc về một khách hàng. Một đơn hàng có nhiều dòng chi tiết đơn hàng. Mỗi dòng chi tiết đơn hàng lưu sản phẩm, số lượng, đơn giá, giảm giá và thành tiền.

---

## 5. Yêu cầu môi trường

Trước khi chạy dự án, cần cài đặt:

- Python 3.12 trở lên.
- MySQL Server.
- Git.
- Visual Studio Code hoặc PyCharm.
- Trình duyệt web như Chrome, Edge hoặc Firefox.

Kiểm tra Python:

```bash
python --version
```

Kiểm tra pip:

```bash
pip --version
```

Kiểm tra Git:

```bash
git --version
```

Kiểm tra MySQL:

```bash
mysql --version
```

---

## 6. Tải source code từ GitHub

Mở terminal hoặc command prompt và chạy:

```bash
git clone https://github.com/ducAnhNotEm/Quan_ly_ban_hang.git
```

Di chuyển vào thư mục dự án:

```bash
cd Quan_ly_ban_hang
```

Mở bằng VS Code:

```bash
code .
```

---

## 7. Tạo môi trường ảo `.venv`

Môi trường ảo giúp tách thư viện của dự án này với các dự án Python khác trên máy.

### 7.1. Tạo `.venv`

Trên Windows:

```bash
python -m venv .venv
```

Hoặc:

```bash
py -m venv .venv
```

Sau khi chạy xong, trong project sẽ có thư mục:

```text
.venv/
```

---

### 7.2. Kích hoạt `.venv`

Nếu dùng CMD:

```bash
.venv\Scripts\activate
```

Nếu dùng PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Nếu PowerShell báo lỗi không cho chạy script, chạy lệnh:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Sau đó kích hoạt lại:

```bash
.venv\Scripts\Activate.ps1
```

Khi kích hoạt thành công, terminal sẽ có dạng:

```bash
(.venv) PS D:\Quan_ly_ban_hang>
```

---

## 8. Cài đặt thư viện

Chạy:

```bash
pip install -r requirements.txt
```

Lưu ý: nếu file `requirements.txt` đang viết các thư viện trên cùng một dòng như:

```text
django==6.0.3 mysqlclient==2.2.8 Pillow==12.2.0
```

thì nên sửa lại thành mỗi thư viện một dòng:

```text
django==6.0.3
mysqlclient==2.2.8
Pillow==12.2.0
```

Sau đó chạy lại:

```bash
pip install -r requirements.txt
```

Ý nghĩa các thư viện:

| Thư viện | Vai trò |
|---|---|
| `django` | Framework chính để xây dựng website |
| `mysqlclient` | Kết nối Django với MySQL |
| `Pillow` | Hỗ trợ xử lý ảnh upload |

---

## 9. Cài đặt và cấu hình MySQL

### 9.1. Tạo database

Đăng nhập vào MySQL:

```bash
mysql -u root -p
```

Tạo database:

```sql
CREATE DATABASE quan_ly_ban_hang_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Kiểm tra database:

```sql
SHOW DATABASES;
```

Thoát MySQL:

```sql
EXIT;
```

---

### 9.2. Tạo file `.env`

Trong project có file mẫu:

```text
.env.mysql.example
```

Tạo file mới tên `.env` ở thư mục gốc dự án:

```bash
copy .env.mysql.example .env
```

Hoặc tạo thủ công file `.env` với nội dung:

```env
MYSQL_DATABASE=quan_ly_ban_hang_db
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

Nếu mật khẩu MySQL trên máy khác `123456`, hãy đổi lại cho đúng.

Ví dụ:

```env
MYSQL_DATABASE=quan_ly_ban_hang_db
MYSQL_USER=root
MYSQL_PASSWORD=mat_khau_mysql_cua_ban
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

---

## 10. Cấu hình `settings.py` trong app `banhang`

File cấu hình chính nằm tại:

```text
banhang/settings.py
```

### 10.1. Cấu hình `BASE_DIR`

```python
BASE_DIR = Path(__file__).resolve().parent.parent
```

`BASE_DIR` là đường dẫn gốc của project. Django dùng nó để xác định vị trí các thư mục như `templates`, `static`, `media`.

---

### 10.2. Cấu hình nạp file `.env`

Trong `settings.py`, project có hàm `_load_env_file()` để đọc file `.env`:

```python
_load_env_file(BASE_DIR / '.env')
```

Mục đích là lấy các thông tin cấu hình database như tên database, user, password, host và port.

---

### 10.3. Cấu hình `INSTALLED_APPS`

Project khai báo các app:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts',
    'products',
    'orders',
]
```

Ý nghĩa:

| App | Vai trò |
|---|---|
| `django.contrib.admin` | Trang quản trị mặc định Django |
| `django.contrib.auth` | Xác thực người dùng |
| `django.contrib.sessions` | Quản lý phiên đăng nhập |
| `accounts` | Quản lý khách hàng, ví, nạp tiền |
| `products` | Quản lý sản phẩm, giỏ hàng |
| `orders` | Quản lý đơn hàng, thanh toán |

---

### 10.4. Cấu hình `TEMPLATES`

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        ...
    },
]
```

Cấu hình này cho phép Django tìm file HTML trong thư mục:

```text
templates/
```

Ví dụ:

```text
templates/home.html
templates/login.html
templates/register.html
```

---

### 10.5. Cấu hình MySQL trong `DATABASES`

Project dùng MySQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'quan_ly_ban_hang_db'),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'),
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}
```

Ý nghĩa:

| Cấu hình | Giải thích |
|---|---|
| `ENGINE` | Dùng MySQL |
| `NAME` | Tên database |
| `USER` | Tài khoản MySQL |
| `PASSWORD` | Mật khẩu MySQL |
| `HOST` | Địa chỉ server MySQL |
| `PORT` | Cổng MySQL |
| `charset` | Hỗ trợ tiếng Việt tốt hơn |

---

### 10.6. Cấu hình static file

```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

Static file là các file như:

- CSS.
- JavaScript.
- Ảnh giao diện.
- Icon.

Thư mục chứa static file:

```text
static/
```

---

### 10.7. Cấu hình media file

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Media file là các file người dùng upload, ví dụ ảnh sản phẩm.

Khi Admin thêm sản phẩm có ảnh, file ảnh được lưu trong thư mục `media`, còn database MySQL lưu đường dẫn đến ảnh đó.

---

## 11. Chạy migration

Sau khi cấu hình database xong, chạy:

```bash
python manage.py makemigrations
```

Sau đó:

```bash
python manage.py migrate
```

Ý nghĩa:

| Lệnh | Vai trò |
|---|---|
| `makemigrations` | Tạo file migration từ model |
| `migrate` | Tạo bảng trong database MySQL |

Sau khi migrate, MySQL sẽ có các bảng cho:

- User.
- Customer.
- Wallet.
- TopUpRequest.
- Product.
- Cart.
- CartItem.
- Order.
- OrderDetail.

---

## 12. Tạo tài khoản Admin

Chạy:

```bash
python manage.py createsuperuser
```

Nhập thông tin:

```text
Username: admin
Email address: admin@example.com
Password: ********
Password again: ********
```

Tài khoản này có quyền truy cập Django Admin và các chức năng dành cho Staff/Admin trong hệ thống.

---

## 13. Chạy server

Chạy lệnh:

```bash
python manage.py runserver
```

Mở trình duyệt:

```text
http://127.0.0.1:8000/
```

Trang Django Admin:

```text
http://127.0.0.1:8000/admin/
```

---

## 14. Các đường dẫn chính

| Đường dẫn | Chức năng |
|---|---|
| `/` | Trang chủ, hiển thị sản phẩm |
| `/login/` | Đăng nhập |
| `/logout/` | Đăng xuất |
| `/register/` | Đăng ký |
| `/nap-tien/` | Gửi yêu cầu nạp tiền |
| `/admin/duyet-nap-tien/` | Admin/Staff duyệt nạp tiền |
| `/admin/thong-ke-ban-hang/` | Admin/Staff xem thống kê bán hàng |
| `/san-pham/admin/them-san-pham/` | Admin/Staff thêm sản phẩm |
| `/gio-hang/` | Xem giỏ hàng |
| `/gio-hang/them/` | Thêm sản phẩm vào giỏ |
| `/gio-hang/cap-nhat/` | Cập nhật giỏ hàng |
| `/gio-hang/xoa/` | Xóa sản phẩm khỏi giỏ |
| `/thanh-toan/gio-hang/` | Thanh toán từ giỏ hàng |
| `/thanh-toan/mua-ngay/` | Mua ngay |
| `/thanh-toan/xac-nhan/` | Xác nhận thanh toán |
| `/don-hang/` | Danh sách đơn hàng |
| `/vi/` | Xem ví tiền |

Nếu đã bổ sung chức năng quản lý khách hàng, có thể có thêm:

| Đường dẫn | Chức năng |
|---|---|
| `/admin/khach-hang/` | Danh sách khách hàng |
| `/admin/khach-hang/<id>/sua/` | Sửa thông tin khách hàng |
| `/admin/khach-hang/<id>/khoa-mo-khoa/` | Khóa/Mở khóa tài khoản |
| `/admin/khach-hang/<id>/xoa/` | Xóa khách hàng nếu có triển khai |

---

## 15. Mô tả chức năng hệ thống

## 15.1. Chức năng khách vãng lai

Khách vãng lai là người chưa đăng nhập vào hệ thống.

Khách vãng lai có thể:

- Xem trang chủ.
- Xem danh sách sản phẩm.
- Tìm kiếm sản phẩm.
- Lọc sản phẩm.
- Xem chi tiết sản phẩm.
- Đăng ký tài khoản.
- Đăng nhập.

---

## 15.2. Chức năng khách hàng

Khách hàng là người đã có tài khoản và đã đăng nhập.

Khách hàng có thể:

- Xem danh sách sản phẩm.
- Tìm kiếm sản phẩm.
- Lọc sản phẩm theo danh mục, giá, tồn kho.
- Xem chi tiết sản phẩm.
- Thêm sản phẩm vào giỏ hàng.
- Cập nhật số lượng sản phẩm trong giỏ.
- Xóa sản phẩm khỏi giỏ.
- Thanh toán sản phẩm trong giỏ.
- Mua ngay sản phẩm.
- Xem ví tiền.
- Gửi yêu cầu nạp tiền.
- Xem lịch sử đơn hàng.

---

## 15.3. Chức năng Admin/Staff

Admin/Staff là tài khoản có quyền quản trị hệ thống.

Admin/Staff có thể:

- Đăng nhập hệ thống.
- Thêm sản phẩm.
- Sửa sản phẩm nếu chức năng đã được bổ sung.
- Xóa sản phẩm nếu chức năng đã được bổ sung.
- Duyệt yêu cầu nạp tiền.
- Từ chối yêu cầu nạp tiền.
- Xem thống kê bán hàng.
- Quản lý khách hàng nếu chức năng đã được bổ sung.

Với chức năng quản lý khách hàng, Admin/Staff có thể:

- Xem danh sách khách hàng.
- Sửa thông tin cơ bản của khách hàng.
- Khóa hoặc mở khóa tài khoản.
- Xóa khách hàng nếu dự án có triển khai chức năng xóa.

---

## 16. Mô tả database và các model chính

## 16.1. User

`User` là model mặc định của Django dùng để quản lý tài khoản đăng nhập.

Các thông tin quan trọng:

| Trường | Ý nghĩa |
|---|---|
| `username` | Tên đăng nhập |
| `email` | Email |
| `password` | Mật khẩu đã được mã hóa |
| `is_staff` | Xác định tài khoản có quyền Staff/Admin |
| `is_active` | Xác định tài khoản còn hoạt động hay bị khóa |

Nếu `is_staff = true`, tài khoản được xem là Staff/Admin.

Nếu `is_active = false`, tài khoản bị khóa và không đăng nhập được.

---

## 16.2. Customer

`Customer` lưu hồ sơ khách hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `user` | Liên kết với tài khoản Django User |
| `full_name` | Họ tên khách hàng |
| `phone_number` | Số điện thoại |
| `address` | Địa chỉ |
| `date_of_birth` | Ngày sinh |
| `gender` | Giới tính |

Quan hệ:

```text
User 1 - 1 Customer
```

---

## 16.3. Wallet

`Wallet` lưu ví tiền của khách hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `customer` | Khách hàng sở hữu ví |
| `balance` | Số dư ví |

Quan hệ:

```text
Customer 1 - 1 Wallet
```

Ví được dùng để thanh toán đơn hàng.

---

## 16.4. TopUpRequest

`TopUpRequest` lưu yêu cầu nạp tiền của khách hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `customer` | Khách hàng gửi yêu cầu |
| `amount` | Số tiền muốn nạp |
| `note` | Ghi chú/lý do nạp |
| `status` | Trạng thái yêu cầu |

Các trạng thái:

| Trạng thái | Ý nghĩa |
|---|---|
| `PENDING` | Đang chờ duyệt |
| `APPROVED` | Đã duyệt |
| `REJECTED` | Đã từ chối |

Quan hệ:

```text
Customer 1 - n TopUpRequest
```

---

## 16.5. Product

`Product` lưu thông tin sản phẩm.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `product_name` | Tên sản phẩm |
| `category` | Danh mục |
| `description` | Mô tả |
| `price` | Giá gốc |
| `discount_percent` | Phần trăm giảm giá |
| `stock_quantity` | Số lượng tồn kho |
| `image` | Ảnh sản phẩm upload |
| `image_url` | Link ảnh ngoài nếu có |
| `created_at` | Thời gian tạo |

Khi Admin thêm sản phẩm, hệ thống lưu thông tin sản phẩm vào MySQL. Nếu có ảnh, file ảnh được lưu trong thư mục `media`, còn đường dẫn ảnh được lưu trong database.

---



## 16.6. Cart

`Cart` là giỏ hàng của khách hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `customer` | Chủ giỏ hàng |
| `updated_at` | Thời gian cập nhật |

Quan hệ:

```text
Customer 1 - 1 Cart
```

---

## 16.7. CartItem

`CartItem` là từng dòng sản phẩm trong giỏ hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `cart` | Giỏ hàng |
| `product` | Sản phẩm |
| `quantity` | Số lượng |
| `is_selected` | Trạng thái được chọn |
| `sub_total` | Thành tiền |
| `discount_amount` | Số tiền giảm |

Quan hệ:

```text
Cart 1 - n CartItem
Product 1 - n CartItem
```

---

## 16.8. Order

`Order` lưu thông tin đơn hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `customer` | Khách hàng đặt hàng |
| `sub_total_amount` | Tổng tiền gốc |
| `discount_amount` | Tổng tiền giảm |
| `total_amount` | Tổng tiền cần thanh toán |
| `status` | Trạng thái đơn hàng |
| `created_at` | Ngày tạo đơn |

Trạng thái đơn hàng:

| Trạng thái | Ý nghĩa |
|---|---|
| `PAID` | Đã thanh toán |
| `CANCELLED` | Đã hủy |

Quan hệ:

```text
Customer 1 - n Order
```

---

## 16.9. OrderDetail

`OrderDetail` lưu từng sản phẩm trong đơn hàng.

Các trường chính:

| Trường | Ý nghĩa |
|---|---|
| `order` | Đơn hàng |
| `product` | Sản phẩm |
| `quantity` | Số lượng |
| `unit_price` | Đơn giá tại thời điểm mua |
| `discount_percent` | Phần trăm giảm giá tại thời điểm mua |
| `discount_amount` | Số tiền giảm |
| `sub_total` | Thành tiền |

Quan hệ:

```text
Order 1 - n OrderDetail
Product 1 - n OrderDetail
```

Việc lưu `unit_price` trong `OrderDetail` giúp đơn hàng giữ nguyên giá tại thời điểm mua, kể cả khi giá sản phẩm thay đổi sau này.

---

## 17. Luồng hoạt động chính

## 17.1. Luồng đăng ký tài khoản

1. Người dùng mở trang đăng ký.
2. Nhập username, email, mật khẩu và thông tin cá nhân.
3. Hệ thống kiểm tra dữ liệu form.
4. Nếu hợp lệ, hệ thống tạo tài khoản `User`.
5. Hệ thống tạo hồ sơ `Customer`.
6. Hệ thống tạo ví `Wallet`.
7. Hệ thống chuyển người dùng sang trang đăng nhập.

---

## 17.2. Luồng đăng nhập

1. Người dùng nhập username và password.
2. Hệ thống kiểm tra tài khoản có tồn tại không.
3. Hệ thống kiểm tra tài khoản còn hoạt động không.
4. Hệ thống xác thực mật khẩu.
5. Nếu đúng, hệ thống tạo phiên đăng nhập.
6. Người dùng được chuyển về trang chủ.

Nếu tài khoản bị khóa bằng `is_active = false`, hệ thống không cho đăng nhập.

---

## 17.3. Luồng xem sản phẩm

1. Người dùng truy cập trang chủ.
2. Hệ thống lấy danh sách sản phẩm từ database.
3. Người dùng có thể tìm kiếm theo tên sản phẩm.
4. Người dùng có thể lọc theo danh mục.
5. Người dùng có thể lọc theo khoảng giá.
6. Người dùng có thể lọc theo trạng thái tồn kho.
7. Hệ thống phân trang sản phẩm.
8. Giao diện hiển thị danh sách sản phẩm.

---

## 17.4. Luồng thêm sản phẩm vào giỏ hàng

1. Khách hàng đăng nhập.
2. Khách hàng chọn sản phẩm.
3. Khách hàng bấm thêm vào giỏ.
4. Hệ thống kiểm tra sản phẩm có tồn tại không.
5. Hệ thống kiểm tra số lượng có hợp lệ không.
6. Hệ thống kiểm tra tồn kho.
7. Nếu sản phẩm chưa có trong giỏ, hệ thống tạo `CartItem`.
8. Nếu sản phẩm đã có trong giỏ, hệ thống cập nhật số lượng.
9. Hệ thống tính lại thành tiền.

---

## 17.5. Luồng thanh toán từ giỏ hàng

1. Khách hàng mở giỏ hàng.
2. Khách hàng chọn sản phẩm cần mua.
3. Khách hàng bấm thanh toán.
4. Hệ thống tính tổng tiền.
5. Hệ thống kiểm tra số dư ví.
6. Nếu ví không đủ tiền, hệ thống yêu cầu khách hàng nạp thêm.
7. Nếu ví đủ tiền, hệ thống kiểm tra tồn kho.
8. Hệ thống tạo `Order`.
9. Hệ thống tạo các dòng `OrderDetail`.
10. Hệ thống trừ tồn kho sản phẩm.
11. Hệ thống trừ tiền trong ví.
12. Hệ thống xóa sản phẩm đã mua khỏi giỏ.
13. Hệ thống chuyển sang trang đơn hàng.

---

## 17.6. Luồng mua ngay

1. Khách hàng chọn sản phẩm.
2. Khách hàng bấm mua ngay.
3. Hệ thống kiểm tra sản phẩm.
4. Hệ thống kiểm tra số lượng.
5. Hệ thống hiển thị trang xác nhận.
6. Khách hàng xác nhận thanh toán.
7. Hệ thống kiểm tra ví.
8. Hệ thống tạo đơn hàng.
9. Hệ thống tạo chi tiết đơn hàng.
10. Hệ thống trừ tồn kho.
11. Hệ thống trừ tiền ví.
12. Hệ thống chuyển sang trang đơn hàng.

---

## 17.7. Luồng nạp tiền

1. Khách hàng đăng nhập.
2. Khách hàng mở trang nạp tiền.
3. Khách hàng nhập số tiền và ghi chú.
4. Hệ thống kiểm tra số tiền hợp lệ.
5. Hệ thống tạo `TopUpRequest` với trạng thái `PENDING`.
6. Admin/Staff mở trang duyệt nạp tiền.
7. Admin/Staff chọn duyệt hoặc từ chối.
8. Nếu duyệt, hệ thống đổi trạng thái thành `APPROVED` và cộng tiền vào ví.
9. Nếu từ chối, hệ thống đổi trạng thái thành `REJECTED`.

---

## 17.8. Luồng Admin thêm sản phẩm

1. Admin/Staff đăng nhập.
2. Hệ thống kiểm tra quyền `is_staff`.
3. Admin/Staff mở trang thêm sản phẩm.
4. Admin/Staff nhập tên sản phẩm, danh mục, mô tả, giá, giảm giá, tồn kho và ảnh.
5. Hệ thống kiểm tra dữ liệu.
6. Hệ thống lưu sản phẩm vào MySQL.
7. Nếu có ảnh, hệ thống lưu file ảnh vào thư mục `media`.
8. Hệ thống hiển thị thông báo thêm sản phẩm thành công.

---

## 17.9. Luồng Admin quản lý khách hàng

Nếu đã bổ sung chức năng quản lý khách hàng, luồng hoạt động như sau:

1. Admin/Staff đăng nhập.
2. Hệ thống kiểm tra quyền `is_staff`.
3. Admin/Staff mở trang quản lý khách hàng.
4. Hệ thống hiển thị danh sách khách hàng.
5. Admin/Staff có thể sửa thông tin cơ bản.
6. Admin/Staff có thể khóa hoặc mở khóa tài khoản.
7. Nếu có chức năng xóa, hệ thống yêu cầu xác nhận trước khi xóa.
8. Hệ thống cập nhật dữ liệu vào database.

Không nên cho sửa trực tiếp số dư ví trong trang quản lý khách hàng. Việc thay đổi số dư nên thông qua chức năng duyệt yêu cầu nạp tiền.

---

## 18. Hướng dẫn xem sơ đồ UML

Dự án có thể mô tả bằng các sơ đồ UML như:

- Use Case Diagram.
- Class Diagram.
- Activity Diagram.
- Sequence Diagram.

Để xem sơ đồ UML:

1. Truy cập link:

```text
https://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa700001
```

2. Copy nội dung PlantUML.

3. Mở PlantUML Online Server:

```text
https://www.plantuml.com/plantuml/
```

4. Dán code PlantUML vào ô nhập.

5. Bấm Submit để render sơ đồ.

Ngoài ra có thể dùng VS Code:

1. Cài extension `PlantUML`.
2. Mở file `.puml`.
3. Bấm preview để xem sơ đồ.

---

## 19. Mô tả sơ đồ Use Case

Biểu đồ Use Case mô tả các tác nhân và chức năng chính của hệ thống.

Các tác nhân chính:

| Tác nhân | Vai trò |
|---|---|
| Khách vãng lai | Người chưa đăng nhập |
| Khách hàng | Người đã đăng ký và đăng nhập |
| Admin/Staff | Người quản trị hệ thống |

Các nhóm chức năng chính:

- Quản lý tài khoản.
- Xem sản phẩm.
- Quản lý giỏ hàng.
- Thanh toán.
- Quản lý ví tiền.
- Gửi yêu cầu nạp tiền.
- Duyệt yêu cầu nạp tiền.
- Quản trị sản phẩm.
- Quản trị khách hàng nếu đã bổ sung.
- Thống kê bán hàng.

---

## 20. Mô tả sơ đồ lớp

Biểu đồ lớp mô tả các thực thể chính trong hệ thống và quan hệ giữa chúng.

Các lớp chính:

| Lớp | Ý nghĩa |
|---|---|
| `User` | Tài khoản đăng nhập |
| `Customer` | Hồ sơ khách hàng |
| `Wallet` | Ví tiền |
| `TopUpRequest` | Yêu cầu nạp tiền |
| `Product` | Sản phẩm |
| `Cart` | Giỏ hàng |
| `CartItem` | Sản phẩm trong giỏ |
| `Order` | Đơn hàng |
| `OrderDetail` | Chi tiết đơn hàng |

Các quan hệ chính:

```text
User 1 - 1 Customer
Customer 1 - 1 Wallet
Customer 1 - n TopUpRequest
Customer 1 - 1 Cart
Cart 1 - n CartItem
Product 1 - n CartItem
Customer 1 - n Order
Order 1 - n OrderDetail
Product 1 - n OrderDetail
```

---

## 21. Mô tả sơ đồ hoạt động

Sơ đồ hoạt động mô tả trình tự xử lý nghiệp vụ.

Các sơ đồ hoạt động có thể có:

| Sơ đồ | Nội dung |
|---|---|
| Activity mua hàng | Mô tả quá trình khách hàng mua sản phẩm |
| Activity nạp tiền | Mô tả quá trình khách hàng gửi yêu cầu nạp tiền |
| Activity duyệt nạp tiền | Mô tả quá trình Admin duyệt yêu cầu |
| Activity quản lý sản phẩm | Mô tả Admin thêm, sửa, xóa sản phẩm |
| Activity quản lý khách hàng | Mô tả Admin xem, sửa, khóa/mở khóa hoặc xóa khách hàng |

---

## 22. Mô tả sơ đồ tuần tự

Sơ đồ tuần tự mô tả sự tương tác giữa người dùng, giao diện, Django View và database.

Ví dụ luồng mua hàng:

```text
Khách hàng
→ Giao diện
→ Django View
→ Wallet
→ Product
→ Order
→ OrderDetail
→ Database
```

Ý nghĩa:

1. Khách hàng gửi yêu cầu mua hàng.
2. Giao diện gửi request đến Django.
3. Django kiểm tra dữ liệu.
4. Django kiểm tra ví.
5. Django kiểm tra tồn kho.
6. Django tạo đơn hàng.
7. Django tạo chi tiết đơn hàng.
8. Django cập nhật ví và tồn kho.
9. Django trả kết quả cho giao diện.

---

## 23. Một số lỗi thường gặp

### 23.1. Lỗi không kết nối được MySQL

Cách kiểm tra:

- MySQL Server đã bật chưa.
- Database đã được tạo chưa.
- User và password trong `.env` đúng chưa.
- Port MySQL có đúng là `3306` không.

Kiểm tra bằng lệnh:

```bash
mysql -u root -p
```

---

### 23.2. Lỗi thiếu thư viện `mysqlclient`

Thử cài lại:

```bash
pip install mysqlclient
```

Nếu vẫn lỗi, kiểm tra:

- Python có tương thích không.
- MySQL đã cài đầy đủ chưa.
- Máy đã có công cụ build cần thiết chưa.

---

### 23.3. Lỗi không hiển thị ảnh sản phẩm

Kiểm tra:

- File ảnh đã được upload chưa.
- Thư mục `media` có tồn tại không.
- `MEDIA_URL` đã cấu hình chưa.
- `MEDIA_ROOT` đã cấu hình chưa.
- `urls.py` đã cấu hình phục vụ media khi `DEBUG=True` chưa.
- Template có gọi đúng `product.image.url` không.

---

### 23.4. Lỗi không hiển thị sản phẩm

Kiểm tra:

- Database đã có sản phẩm chưa.
- Đã chạy `migrate` chưa.
- View có lấy `Product.objects.all()` không.
- Template có lặp qua danh sách sản phẩm không.
- Bộ lọc tìm kiếm có đang lọc sai không.
- Sản phẩm có tồn kho không nếu đang bật lọc tồn kho.

---

### 23.5. Lỗi đăng nhập không được

Kiểm tra:

- Username đúng chưa.
- Password đúng chưa.
- Tài khoản có bị khóa không.
- Trường `is_active` của tài khoản có đang là `true` không.
- Đã tạo user trong database chưa.

---

## 24. Hướng phát triển thêm

Một số chức năng có thể bổ sung:

- Sửa sản phẩm cho Admin/Staff.
- Xóa sản phẩm cho Admin/Staff.
- Quản lý khách hàng cho Admin/Staff.
- Khóa/Mở khóa tài khoản khách hàng.
- Xóa khách hàng có xác nhận.
- Thêm trạng thái đơn hàng như `PENDING`, `SHIPPING`, `COMPLETED`.
- Hủy đơn hàng.
- Tìm kiếm nâng cao.
- Đánh giá sản phẩm.
- Dashboard thống kê doanh thu theo ngày/tháng.
- Giao diện responsive cho điện thoại.
- Viết test đơn giản cho đăng nhập, giỏ hàng, thanh toán và nạp tiền.

---

## 25. Kết luận

Dự án `Quan_ly_ban_hang` là một website quản lý bán hàng được xây dựng bằng Django và MySQL. Hệ thống có đầy đủ các chức năng cơ bản của một website bán hàng như quản lý tài khoản, xem sản phẩm, giỏ hàng, thanh toán, ví tiền, nạp tiền và quản trị hệ thống.

Về mặt thiết kế, dự án được chia thành các app riêng như `accounts`, `products` và `orders`, giúp code dễ quản lý và dễ mở rộng. Cơ sở dữ liệu được tổ chức xoay quanh các thực thể chính như khách hàng, ví tiền, sản phẩm, giỏ hàng, đơn hàng và yêu cầu nạp tiền.

Dự án phù hợp để trình bày trong báo cáo môn học vì có đầy đủ các phần: cài đặt môi trường, cấu hình database, xử lý nghiệp vụ, phân quyền người dùng, giao diện, cơ sở dữ liệu và sơ đồ UML.