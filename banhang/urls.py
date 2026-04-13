from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import include, path
from django.utils import timezone

from accounts.forms import RegisterForm
from accounts.models import Customer, Wallet
from banhang.sql_utils import fetch_one_dict
from products.models import Product


def _format_currency_vnd(value):
    amount = int(value or 0)
    return f"{amount:,}".replace(",", ".") + " đ"


def _build_querystring(request, **updates):
    query_params = request.GET.copy()
    for key, value in updates.items():
        if value in (None, ""):
            query_params.pop(key, None)
        else:
            query_params[key] = value
    encoded = query_params.urlencode()
    return f"?{encoded}" if encoded else "?"


def _build_toggle_filter_options(request, param_name, definitions, selected_value):
    options = []
    for value, label in definitions:
        is_active = selected_value == value
        next_value = None if is_active else value
        options.append(
            {
                "value": value,
                "label": label,
                "is_active": is_active,
                "querystring": _build_querystring(request, **{param_name: next_value}),
            }
        )
    return options


def home(request):
    selected_category = request.GET.get("category", "").strip()
    selected_price = request.GET.get("price", "").strip()
    selected_stock = request.GET.get("stock", "").strip()

    categories = [
        category
        for category in Product.objects.order_by("category")
        .values_list("category", flat=True)
        .distinct()
        if category
    ]

    category_filters = [
        {
            "label": "Tất cả danh mục",
            "value": "",
            "icon": "apps",
            "is_active": not selected_category,
            "querystring": _build_querystring(request, category=None),
        }
    ]
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

    context = {
        "category_filters": category_filters,
        "filter_sections": filter_sections,
        "has_active_filters": bool(selected_category or selected_price or selected_stock),
        "product_slots": list(range(12)),
    }
    return render(request, "home.html", context)


def admin_sales_stats(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang thống kê bán hàng.")
        return redirect("home")

    stats = fetch_one_dict("dashboard_stats.sql") or {}
    context = {
        "registered_customers": int(stats.get("customer_count") or 0),
        "sold_orders": int(stats.get("order_count") or 0),
        "total_products": int(stats.get("product_count") or 0),
        "revenue_display": _format_currency_vnd(stats.get("total_revenue")),
        "generated_at": timezone.localtime().strftime("%H:%M %d/%m/%Y"),
    }
    return render(request, "admin_sales_stats.html", context)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Vui long nhap day du ten dang nhap va mat khau.")
        else:
            account_row = fetch_one_dict("auth_user_lookup.sql", [username])
            if account_row is None or not account_row.get("is_active"):
                messages.error(request, "Ten dang nhap hoac mat khau khong dung.")
            else:
                user = authenticate(request, username=username, password=password)
                if user is None:
                    messages.error(request, "Ten dang nhap hoac mat khau khong dung.")
                else:
                    login(request, user)
                    return redirect("home")

    return render(request, "login.html")


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Ban da dang xuat thanh cong.")
    return redirect("home")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            with transaction.atomic():
                user = get_user_model().objects.create_user(
                    username=cleaned["username"],
                    email=cleaned["email"],
                    password=cleaned["password1"],
                )

                customer = Customer.objects.create(
                    user=user,
                    full_name=cleaned["full_name"],
                    phone_number=cleaned["phone_number"],
                    address=cleaned.get("address") or None,
                    date_of_birth=cleaned.get("date_of_birth"),
                    gender=cleaned.get("gender") or Customer.Gender.OTHER,
                )
                Wallet.objects.create(customer=customer)

            messages.success(request, "Dang ky thanh cong. Vui long dang nhap.")
            return redirect("login")

        messages.error(request, "Vui long kiem tra lai thong tin dang ky.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


urlpatterns = [
    path("san-pham/", include("products.urls")),
    path("admin/thong-ke-ban-hang/", admin_sales_stats, name="admin_sales_stats"),
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
]
