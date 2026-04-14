from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Customer, TopUpRequest, Wallet

"""
Test suite cho app `accounts` và các luồng auth/topup liên quan.

Ý nghĩa:
- Bảo vệ rule dữ liệu của model `Customer`, `Wallet`, `TopUpRequest`.
- Bảo vệ luồng login/register/logout.
- Bảo vệ cách trang home hiển thị dữ liệu topup theo vai trò user/staff.
"""


class AccountsModelTests(TestCase):
    """Kiểm thử các ràng buộc mô hình dữ liệu (model) cơ bản của app accounts."""

    def setUp(self):
        """Tạo tài khoản nền dùng chung cho các bài kiểm thử mô hình dữ liệu (model)."""
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="testpass123",
        )

    def test_create_customer_with_default_gender(self):
        """Không truyền gender thì Customer phải mặc định là `Khac`."""
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )

        self.assertEqual(customer.gender, Customer.Gender.OTHER)
        self.assertEqual(self.user.customer_profile, customer)

    def test_wallet_defaults_and_reverse_relation(self):
        """Wallet mới tạo có số dư 0 và liên kết ngược với Customer đúng."""
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )

        wallet = Wallet.objects.create(customer=customer)

        self.assertEqual(wallet.balance, 0)
        self.assertEqual(customer.wallet, wallet)

    def test_topup_request_defaults_to_pending(self):
        """TopUpRequest mới tạo phải có trạng thái mặc định là PENDING."""
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
            date_of_birth=date(2000, 1, 1),
            gender=Customer.Gender.FEMALE,
        )

        topup = TopUpRequest.objects.create(
            customer=customer,
            amount=500000,
            note="Nap tien lan 1",
        )

        self.assertEqual(topup.status, TopUpRequest.Status.PENDING)
        self.assertEqual(customer.topup_requests.count(), 1)

    def test_customer_requires_unique_user(self):
        """Mỗi tài khoản chỉ được gắn tối đa 1 hồ sơ Customer (OneToOne)."""
        Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )

        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                user=self.user,
                full_name="Alice Clone",
                phone_number="0911111111",
            )

    def test_deleting_customer_cascades_wallet_and_topups(self):
        """Xóa Customer phải xóa theo Wallet và TopUpRequest liên quan."""
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )
        Wallet.objects.create(customer=customer, balance=1000)
        TopUpRequest.objects.create(customer=customer, amount=300000)

        customer.delete()

        self.assertEqual(Wallet.objects.count(), 0)
        self.assertEqual(TopUpRequest.objects.count(), 0)


class LoginViewTests(TestCase):
    """Kiểm thử luồng đăng nhập và các route xác thực liên quan."""

    def test_staff_login_redirects_home(self):
        """Staff đăng nhập thành công phải được tạo phiên và chuyển về trang chủ."""
        staff_user = get_user_model().objects.create_user(
            username="admin01",
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

        response = self.client.post(
            reverse("login"),
            data={"username": "admin01", "password": "testpass123"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertTrue("_auth_user_id" in self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), staff_user.id)

    def test_admin_and_dashboard_routes_return_404(self):
        """Các route cũ `/admin/` và `/admin-dashboard/` hiện chưa ánh xạ view."""
        response_admin = self.client.get("/admin/")
        response_dashboard = self.client.get("/admin-dashboard/")

        self.assertEqual(response_admin.status_code, 404)
        self.assertEqual(response_dashboard.status_code, 404)


class RegisterViewTests(TestCase):
    """Kiểm thử luồng đăng ký user account."""

    def test_register_missing_required_fields_shows_errors(self):
        """Gửi form rỗng phải hiển thị đầy đủ thông báo lỗi bắt buộc."""
        response = self.client.post(reverse("register"), data={})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vui long nhap ten dang nhap.")
        self.assertContains(response, "Vui long nhap ho va ten.")
        self.assertContains(response, "Vui long nhap email.")
        self.assertContains(response, "Vui long nhap so dien thoai.")

    def test_register_password_mismatch_shows_error(self):
        """Mật khẩu xác nhận không trùng phải báo lỗi tại form."""
        response = self.client.post(
            reverse("register"),
            data={
                "username": "newuser",
                "full_name": "New User",
                "email": "newuser@example.com",
                "phone_number": "0900001234",
                "password1": "pass123456",
                "password2": "pass1234567",
                "gender": "Nam",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mat khau xac nhan khong khop.")

    def test_register_success_creates_user_customer_wallet_and_redirects(self):
        """Đăng ký hợp lệ phải tạo đồng bộ tài khoản, hồ sơ khách hàng và ví."""
        response = self.client.post(
            reverse("register"),
            data={
                "username": "newuser",
                "full_name": "New User",
                "email": "newuser@example.com",
                "phone_number": "0900001234",
                "password1": "pass123456",
                "password2": "pass123456",
                "address": "HCM",
                "date_of_birth": "2000-01-02",
                "gender": "Nu",
            },
        )

        self.assertRedirects(response, reverse("login"))

        user = get_user_model().objects.get(username="newuser")
        customer = Customer.objects.get(user=user)

        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(customer.full_name, "New User")
        self.assertEqual(customer.gender, Customer.Gender.FEMALE)
        self.assertTrue(Wallet.objects.filter(customer=customer).exists())


class LogoutViewTests(TestCase):
    """Kiểm thử luồng đăng xuất."""

    def test_logout_clears_session_and_redirects_home(self):
        """Đăng xuất phải xóa session auth và redirect về home."""
        user = get_user_model().objects.create_user(
            username="logout_user",
            email="logout@example.com",
            password="testpass123",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)


class HomeTopupSectionTests(TestCase):
    """Kiểm thử phần topup trên home theo từng vai trò đăng nhập."""

    def setUp(self):
        """Tạo dữ liệu staff, khách hàng và topup request mẫu."""
        user_model = get_user_model()

        self.staff_user = user_model.objects.create_user(
            username="staff_home",
            email="staff_home@example.com",
            password="testpass123",
            is_staff=True,
        )

        self.customer_user = user_model.objects.create_user(
            username="customer_home",
            email="customer_home@example.com",
            password="testpass123",
        )
        self.other_user = user_model.objects.create_user(
            username="other_home",
            email="other_home@example.com",
            password="testpass123",
        )

        customer = Customer.objects.create(
            user=self.customer_user,
            full_name="Customer Home",
            phone_number="0900111000",
        )
        other_customer = Customer.objects.create(
            user=self.other_user,
            full_name="Other Home",
            phone_number="0900222000",
        )

        TopUpRequest.objects.create(
            customer=customer,
            amount=100000,
            note="PENDING_NOTE",
            status=TopUpRequest.Status.PENDING,
        )
        TopUpRequest.objects.create(
            customer=customer,
            amount=120000,
            note="APPROVED_NOTE",
            status=TopUpRequest.Status.APPROVED,
        )
        TopUpRequest.objects.create(
            customer=other_customer,
            amount=130000,
            note="OTHER_USER_NOTE",
            status=TopUpRequest.Status.PENDING,
        )

    def test_admin_sees_topup_requests_only(self):
        """Staff phải thấy danh sách yêu cầu đang chờ xử lý trên trang chủ."""
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Yêu cầu nạp tiền")
        self.assertContains(response, "PENDING_NOTE")
        self.assertContains(response, "OTHER_USER_NOTE")
        self.assertNotContains(response, "APPROVED_NOTE")

    def test_customer_sees_own_topup_history(self):
        """Customer thường chỉ thấy lịch sử topup của chính mình."""
        self.client.force_login(self.customer_user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Lịch sử yêu cầu nạp tiền")
        self.assertContains(response, "PENDING_NOTE")
        self.assertContains(response, "APPROVED_NOTE")
        self.assertNotContains(response, "OTHER_USER_NOTE")



