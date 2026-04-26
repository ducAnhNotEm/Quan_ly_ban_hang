from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.urls import include, path
from django.utils import timezone

from accounts.forms import RegisterForm
from accounts.models import Customer, TopUpRequest, Wallet
from banhang.sql_utils import fetch_one_dict
from products.models import Product

"""
File này đang chứa cả:
1) Route chính của app.
2) Các view (xử lý yêu cầu/phản hồi).
3) Một số hàm tiện ích để định dạng/phân tích dữ liệu.

Mục tiêu ghi chú:
- Giải thích "hàm này làm gì".
- Chỉ ra "điểm cần lưu ý" (phân quyền, transaction, validate, lock dữ liệu).
- Giữ nguyên logic hiện tại, chỉ thêm chú thích để dễ học và bảo trì.
"""


def _format_currency_vnd(value):
    """
    Hàm tiện ích: đổi số tiền sang chuỗi định dạng VND.

    Đầu vào:
    - value: có thể là int/str/None.

    Đầu ra:
    - Chuỗi kiểu "1.200.000 đ".

    Lưu ý:
    - Nếu value rỗng/None -> ép về 0.
    - Dùng int() để đảm bảo không còn phần thập phân khi hiển thị.
    """
    amount = int(value or 0)
    return f"{amount:,}".replace(",", ".") + " đ"


def _build_querystring(request, **updates):
    """
    Hàm tiện ích: tạo lại query string dựa trên request hiện tại và giá trị cập nhật.

    Cách dùng:
    - Truyền key=value để đặt/cập nhật.
    - Truyền key=None hoặc key="" để xóa key đó khỏi URL.

    Ví dụ:
    - URL hiện tại: ?category=A&price=under_500k
    - _build_querystring(..., price=None) -> ?category=A

    Lưu ý:
    - Trả về "?" nếu không còn tham số nào, giúp giao diện bật/tắt bộ lọc đồng nhất.
    """
    # Sao chép tham số truy vấn hiện tại để thao tác (không sửa trực tiếp `request.GET`).
    query_params = request.GET.copy()

    # Gộp các cập nhật mới vào tập tham số truy vấn.
    for key, value in updates.items():
        if value in (None, ""):
            query_params.pop(key, None)
        else:
            query_params[key] = value

    # Mã hóa lại thành chuỗi URL.
    encoded = query_params.urlencode()
    return f"?{encoded}" if encoded else "?"


def _build_toggle_filter_options(request, param_name, definitions, selected_value):
    """
    Hàm tiện ích: dựng danh sách lựa chọn cho bộ lọc kiểu bật/tắt.

    Ý tưởng bật/tắt:
    - Nếu lựa chọn đang bật, bấm lại sẽ bỏ lọc (set None).
    - Nếu lựa chọn chưa bật, bấm sẽ bật lọc đó.

    Đầu vào:
    - param_name: tên tham số truy vấn (vd: "price", "stock").
    - definitions: danh sách tuple (value, label) để hiển thị giao diện.
    - selected_value: giá trị đang được chọn hiện tại.

    Đầu ra:
    - Danh sách dict để template hiển thị (label, is_active, querystring...).
    """
    options = []
    for value, label in definitions:
        # Đánh dấu lựa chọn hiện tại có đang được chọn hay không.
        is_active = selected_value == value

        # Bấm lại lựa chọn đang bật => bỏ lọc; ngược lại => bật lọc.
        next_value = None if is_active else value
        options.append(
            {
                "value": value,
                "label": label,
                "is_active": is_active,
                # Giữ nguyên các bộ lọc khác, chỉ đổi tham số hiện tại.
                "querystring": _build_querystring(request, **{param_name: next_value}),
            }
        )
    return options


def _parse_vnd_amount(amount_raw: str) -> int | None:
    """
    Hàm tiện ích: phân tích số tiền nhập từ form về số nguyên dương.

    Mục tiêu:
    - Cho phép user nhập có dấu "." hoặc "," (ngăn cách hàng nghìn).
    - Loại bỏ khoảng trắng dư.
    - Chỉ chấp nhận số nguyên > 0.

    Trả về:
    - int nếu hợp lệ.
    - None nếu không hợp lệ.
    """
    # Chuẩn hóa chuỗi tiền tệ về chỉ còn chữ số.
    cleaned = (amount_raw or "").strip().replace(".", "").replace(",", "")
    if not cleaned.isdigit():
        return None
    amount = int(cleaned)
    return amount if amount > 0 else None


def home(request):
    """
    View trang chủ.

    Chức năng chính:
    - Đọc bộ lọc từ querystring: category, price, stock.
    - Tạo dữ liệu bộ lọc để template hiển thị UI lọc.
    - Truyền `product_slots` giả lập cho giao diện (chưa truy vấn danh sách sản phẩm thật).

    Điểm cần lưu ý:
    - Filter hiện tại mới ở mức chuẩn bị dữ liệu UI.
    - Chưa áp dụng truy vấn lọc sản phẩm theo các điều kiện này trong view.
    """
    # Lấy giá trị bộ lọc mà user đang chọn trên URL.
    selected_category = request.GET.get("category", "").strip()
    selected_price = request.GET.get("price", "").strip()
    selected_stock = request.GET.get("stock", "").strip()

    # Lấy danh mục duy nhất từ DB để hiển thị bộ lọc category.
    categories = [
        category
        for category in Product.objects.order_by("category")
        .values_list("category", flat=True)
        .distinct()
        if category
    ]

    # Mục "Tất cả danh mục": bật khi không chọn category nào.
    category_filters = [
        {
            "label": "Tất cả danh mục",
            "value": "",
            "icon": "apps",
            "is_active": not selected_category,
            "querystring": _build_querystring(request, category=None),
        }
    ]

    # Các mục category cụ thể; bấm lần nữa sẽ bỏ bộ lọc category đang chọn.
    for category in categories:
        category_filters.append(
            {
                "label": category,
                "value": category,
                "icon": "category",
                "is_active": selected_category == category,
                "querystring": _build_querystring(
                    request,
                    category=None if selected_category == category else category,
                ),
            }
        )

    # Dựng các nhóm bộ lọc phụ: khoảng giá và tồn kho.
    filter_sections = [
        {
            "key": "price",
            "title": "Khoảng giá",
            "options": _build_toggle_filter_options(
                request,
                "price",
                [
                    ("under_500k", "Dưới 500.000đ"),
                    ("500k_1m", "500.000đ - 1.000.000đ"),
                    ("1m_3m", "1.000.000đ - 3.000.000đ"),
                    ("above_3m", "Trên 3.000.000đ"),
                ],
                selected_price,
            ),
        },
        {
            "key": "stock",
            "title": "Tồn kho",
            "options": _build_toggle_filter_options(
                request,
                "stock",
                [
                    ("in_stock", "Còn hàng"),
                    ("out_stock", "Hết hàng"),
                ],
                selected_stock,
            ),
        },
    ]

    # Dữ liệu tổng cho template.
    context = {
        "category_filters": category_filters,
        "filter_sections": filter_sections,
        # Cờ này dùng để hiển thị trạng thái "đang có bộ lọc".
        "has_active_filters": bool(selected_category or selected_price or selected_stock),
        # Khung trống 12 ô sản phẩm cho giao diện.
        "product_slots": list(range(12)),
    }
    return render(request, "home.html", context)


def topup_request(request):
    """
    View cho khách hàng gửi yêu cầu nạp tiền.

    Luồng chính:
    1) Bắt buộc đăng nhập.
    2) Nếu là staff thì chuyển sang trang duyệt (không gửi yêu cầu như khách).
    3) Kiểm tra hồ sơ Customer tương ứng user.
    4) Nếu POST: kiểm tra amount + note, sau đó tạo TopUpRequest.
    5) Luôn trả về lịch sử yêu cầu gần nhất của user (tối đa 30 dòng).

    Điểm cần lưu ý:
    - Đây chỉ là "gửi yêu cầu", chưa cộng tiền ngay vào ví.
    - Tiền chỉ được cộng khi staff duyệt ở `topup_admin_review`.
    """
    # Chặn user chưa đăng nhập.
    if not request.user.is_authenticated:
        messages.info(request, "Vui lòng đăng nhập để gửi yêu cầu nạp tiền.")
        return redirect("login")

    # Staff đi thẳng tới trang duyệt để tránh sai vai trò sử dụng.
    if request.user.is_staff:
        return redirect("topup_admin_review")

    # Tìm hồ sơ khách hàng; nếu thiếu hồ sơ thì không thể gửi yêu cầu.
    customer = Customer.objects.filter(user=request.user).first()
    if customer is None:
        messages.error(request, "Không tìm thấy hồ sơ khách hàng cho tài khoản này.")
        return redirect("home")

    # Khi user gửi form.
    if request.method == "POST":
        # Phân tích amount về số nguyên dương; note được cắt khoảng trắng.
        amount = _parse_vnd_amount(request.POST.get("amount"))
        note = (request.POST.get("note") or "").strip()

        # Kiểm tra dữ liệu đầu vào.
        if amount is None:
            messages.error(request, "Số tiền nạp phải là số nguyên dương (VND).")
        elif not note:
            messages.error(request, "Vui lòng nhập lý do nạp tiền.")
        else:
            # Tạo yêu cầu mới ở trạng thái mặc định (thường là PENDING).
            TopUpRequest.objects.create(customer=customer, amount=amount, note=note)
            messages.success(request, "Đã gửi yêu cầu nạp tiền thành công.")
            return redirect("topup_request")

    # Lấy lịch sử yêu cầu gần đây của user hiện tại.
    request_rows = (
        TopUpRequest.objects.filter(customer=customer)
        .order_by("-id")
        .values("id", "amount", "note", "status")[:30]
    )

    # Đổi amount -> amount_display để template hiển thị dễ đọc.
    topup_rows = [
        {
            **row,
            "amount_display": _format_currency_vnd(row["amount"]),
        }
        for row in request_rows
    ]
    return render(request, "topup_request.html", {"topup_rows": topup_rows})


def topup_admin_review(request):
    """
    View cho staff (duyệt/từ chối) yêu cầu nạp tiền.

    Luồng GET:
    - Hiển thị danh sách yêu cầu đang chờ (PENDING) và đã xử lý gần đây.

    Luồng POST:
    - Nhận request_id + action (APPROVE/REJECT).
    - Khóa bản ghi bằng select_for_update trong transaction.
    - Chỉ xử lý khi trạng thái còn PENDING.
    - Nếu APPROVE: chuyển trạng thái APPROVED và cộng tiền vào ví.
    - Nếu REJECT: chuyển trạng thái REJECTED.

    Điểm cần lưu ý quan trọng:
    - `transaction.atomic()` + `select_for_update()` giúp tránh duyệt trùng khi nhiều staff/admin thao tác đồng thời.
    - Cộng tiền dùng `F("balance") + topup.amount` để cập nhật an toàn ở phía cơ sở dữ liệu.
    """
    # Chỉ staff đã đăng nhập mới có quyền vào trang này.
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang xử lý nạp tiền.")
        return redirect("home")

    # Khi staff gửi thao tác duyệt/từ chối.
    if request.method == "POST":
        request_id_raw = request.POST.get("request_id", "").strip()
        action = (request.POST.get("action") or "").strip().upper()

        # request_id phải là số hợp lệ.
        if not request_id_raw.isdigit():
            messages.error(request, "Yêu cầu không hợp lệ.")
            return redirect("topup_admin_review")

        request_id = int(request_id_raw)
        try:
            # Mở giao dịch để đảm bảo đồng nhất cho cả đổi trạng thái + cộng ví.
            with transaction.atomic():
                # Khóa bản ghi yêu cầu nạp tiền để ngăn xử lý đồng thời.
                topup = (
                    TopUpRequest.objects.select_for_update()
                    .select_related("customer")
                    .get(pk=request_id)
                )

                # Chỉ xử lý yêu cầu còn chờ; tránh bấm duyệt lại nhiều lần.
                if topup.status != TopUpRequest.Status.PENDING:
                    messages.warning(request, "Yêu cầu này đã được xử lý trước đó.")
                    return redirect("topup_admin_review")

                if action == "APPROVE":
                    # Duyệt yêu cầu: đổi trạng thái -> cộng tiền ví.
                    topup.status = TopUpRequest.Status.APPROVED
                    topup.save(update_fields=["status"])
                    Wallet.objects.filter(customer=topup.customer).update(
                        balance=F("balance") + topup.amount
                    )
                    messages.success(
                        request,
                        f"Đã chấp nhận yêu cầu #{topup.id} và cộng {_format_currency_vnd(topup.amount)}.",
                    )
                elif action == "REJECT":
                    # Từ chối yêu cầu: chỉ đổi trạng thái, không cộng ví.
                    topup.status = TopUpRequest.Status.REJECTED
                    topup.save(update_fields=["status"])
                    messages.info(request, f"Đã từ chối yêu cầu #{topup.id}.")
                else:
                    messages.error(request, "Hành động không hợp lệ.")
        except TopUpRequest.DoesNotExist:
            # request_id không tồn tại trong DB.
            messages.error(request, "Không tìm thấy yêu cầu nạp tiền.")

        # Dù thành công hay lỗi đều quay về trang duyệt để hiển thị thông báo.
        return redirect("topup_admin_review")

    # Danh sách yêu cầu đang chờ xử lý.
    pending_rows = (
        TopUpRequest.objects.filter(status=TopUpRequest.Status.PENDING)
        .select_related("customer__user")
        .order_by("-id")
        .values("id", "amount", "note", "status", "customer__full_name", "customer__user__username")
    )

    # Danh sách yêu cầu đã xử lý gần đây (30 dòng).
    recent_rows = (
        TopUpRequest.objects.exclude(status=TopUpRequest.Status.PENDING)
        .select_related("customer__user")
        .order_by("-id")
        .values("id", "amount", "note", "status", "customer__full_name", "customer__user__username")[:30]
    )

    def _to_view_rows(rows):
        """Đổi dữ liệu DB thô sang dữ liệu phù hợp để template hiển thị."""
        return [
            {
                "id": row["id"],
                "amount_display": _format_currency_vnd(row["amount"]),
                "note": row["note"],
                "status": row["status"],
                "full_name": row["customer__full_name"],
                "username": row["customer__user__username"],
            }
            for row in rows
        ]

    # Context trả về cho template trang duyệt.
    context = {
        "pending_rows": _to_view_rows(pending_rows),
        "recent_rows": _to_view_rows(recent_rows),
    }
    return render(request, "topup_admin_review.html", context)


def admin_sales_stats(request):
    """
    Hàm thống kê bán hàng cho staff.

    Chức năng chính:
    - Kiểm tra quyền staff.
    - Đọc số liệu tổng hợp từ file SQL `admin_sales_stats.sql`.
    - Chuẩn hóa dữ liệu về int/chuỗi tiền trước khi hiển thị.

    Điểm cần lưu ý:
    - Nếu SQL trả về None/thiếu field, code vẫn dự phòng về 0 để tránh lỗi template.
    """
    # Chỉ staff đã đăng nhập mới xem được thống kê.
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang thống kê bán hàng.")
        return redirect("home")

    # Đọc dữ liệu thống kê (dạng từ điển) từ câu SQL đặt riêng trong file.
    stats = fetch_one_dict("admin_sales_stats.sql") or {}
    context = {
        "registered_customers": int(stats.get("customer_count") or 0),
        "sold_orders": int(stats.get("order_count") or 0),
        "total_products": int(stats.get("product_count") or 0),
        "revenue_display": _format_currency_vnd(stats.get("total_revenue")),
        # Thời điểm tạo thống kê để hiển thị trong UI.
        "generated_at": timezone.localtime().strftime("%H:%M %d/%m/%Y"),
    }
    return render(request, "admin_sales_stats.html", context)


def login_view(request):
    """
    View đăng nhập.

    Luồng chính:
    - Nếu POST: lấy username/password.
    - Kiểm tra dữ liệu không rỗng.
    - Kiểm tra user có tồn tại và còn active qua SQL (`auth_user_lookup.sql`).
    - Xác thực mật khẩu bằng `authenticate`.
    - Thành công thì `login` và chuyển về home.

    Điểm cần lưu ý:
    - Dù đã kiểm tra SQL, vẫn bắt buộc gọi `authenticate` để xác thực chuẩn Django.
    """
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # Chặn trường hợp thiếu thông tin đăng nhập.
        if not username or not password:
            messages.error(request, "Vui long nhap day du ten dang nhap va mat khau.")
        else:
            # Kiểm tra nhanh tài khoản có tồn tại/active bằng hàm tiện ích SQL.
            account_row = fetch_one_dict("auth_user_lookup.sql", [username])
            if account_row is None or not account_row.get("is_active"):
                messages.error(request, "Ten dang nhap hoac mat khau khong dung.")
            else:
                # Xác thực đúng chuẩn Django (kiểm tra hash password, backend...).
                user = authenticate(request, username=username, password=password)
                if user is None:
                    messages.error(request, "Ten dang nhap hoac mat khau khong dung.")
                else:
                    # Tạo phiên đăng nhập.
                    login(request, user)
                    return redirect("home")

    # GET hoặc POST lỗi đều trả lại form đăng nhập.
    return render(request, "login.html")


def logout_view(request):
    """
    View đăng xuất.

    Chức năng:
    - Nếu đang đăng nhập thì hủy session.
    - Hiển thị thông báo thành công.
    - Điều hướng về trang chủ.
    """
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Ban da dang xuat thanh cong.")
    return redirect("home")


def register_view(request):
    """
    View đăng ký tài khoản mới.

    Luồng chính:
    - GET: hiển thị form trống.
    - POST: kiểm tra form.
    - Nếu hợp lệ: tạo User + Customer + Wallet trong 1 transaction.
    - Thành công: báo và chuyển sang login.

    Điểm cần lưu ý:
    - Dùng `transaction.atomic()` để tránh trạng thái dở dang
      (vd tạo User xong nhưng lỗi khi tạo Customer/Wallet).
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            # Tạo đồng bộ nhiều bảng trong cùng transaction.
            with transaction.atomic():
                user = get_user_model().objects.create_user(
                    username=cleaned["username"],
                    email=cleaned["email"],
                    password=cleaned["password1"],
                )

                # Hồ sơ khách hàng gắn với tài khoản vừa tạo.
                customer = Customer.objects.create(
                    user=user,
                    full_name=cleaned["full_name"],
                    phone_number=cleaned["phone_number"],
                    address=cleaned.get("address") or None,
                    date_of_birth=cleaned.get("date_of_birth"),
                    gender=cleaned.get("gender") or Customer.Gender.OTHER,
                )

                # Tạo ví ban đầu cho khách hàng.
                Wallet.objects.create(customer=customer)

            messages.success(request, "Dang ky thanh cong. Vui long dang nhap.")
            return redirect("login")

        # Form không hợp lệ: báo lỗi chung, chi tiết trường hiển thị tại lỗi của form.
        messages.error(request, "Vui long kiem tra lai thong tin dang ky.")
    else:
        # GET: hiển thị form rỗng.
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


urlpatterns = [
    # Danh sách route chính của app.
    # Route sản phẩm được tách sang file URLs riêng của app `products`.
    path("san-pham/", include("products.urls")),
    # Route gio hang va mua ngay tách riêng trong app `orders`.
    path("", include("orders.urls")),
    # Trang thống kê bán hàng cho quản trị/staff.
    path("admin/thong-ke-ban-hang/", admin_sales_stats, name="admin_sales_stats"),
    # Trang khách hàng gửi yêu cầu nạp tiền.
    path("nap-tien/", topup_request, name="topup_request"),
    # Trang staff duyệt/từ chối yêu cầu nạp tiền.
    path("admin/duyet-nap-tien/", topup_admin_review, name="topup_admin_review"),
    # Trang chủ.
    path("", home, name="home"),
    # Đăng nhập.
    path("login/", login_view, name="login"),
    # Đăng xuất.
    path("logout/", logout_view, name="logout"),
    # Đăng ký tài khoản mới.
    path("register/", register_view, name="register"),
]


