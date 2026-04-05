from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path

from accounts.forms import RegisterForm
from accounts.models import Customer, Wallet
from banhang.sql_utils import fetch_all_dicts, fetch_one_dict


def _format_currency_vnd(value: Decimal) -> str:
    amount = int(value or 0)
    return f"{amount:,}".replace(",", ".") + " đ"


def home(request):
    stats = fetch_one_dict("dashboard_stats.sql") or {}
    total_revenue = stats.get("total_revenue") or Decimal("0")

    topup_section_title = "Lịch sử yêu cầu nạp tiền"
    topup_empty_message = "Chưa có yêu cầu nạp tiền nào."

    if request.user.is_authenticated:
        if request.user.is_staff:
            topup_rows = fetch_all_dicts("topup_requests_staff.sql", [8])
            topup_section_title = "Yêu cầu nạp tiền"
            topup_empty_message = "Chưa có yêu cầu nạp tiền nào đang chờ."
        else:
            topup_rows = fetch_all_dicts("topup_history_by_user.sql", [request.user.id, 8])
    else:
        topup_rows = []

    context = {
        "meta_title": "Sales Management - Giai phap quan ly ban hang chuyen nghiep",
        "meta_description": (
            "Theo doi san pham, khach hang, don hang va lich su yeu cau nap tien "
            "tren mot he thong truc quan, de su dung."
        ),
        "product_count": int(stats.get("product_count") or 0),
        "customer_count": int(stats.get("customer_count") or 0),
        "order_count": int(stats.get("order_count") or 0),
        "revenue_display": _format_currency_vnd(total_revenue),
        "topup_requests": topup_rows,
        "topup_section_title": topup_section_title,
        "topup_empty_message": topup_empty_message,
    }
    return render(request, "home.html", context)


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
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
]

