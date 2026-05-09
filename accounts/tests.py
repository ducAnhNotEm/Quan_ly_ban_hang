from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Customer, Wallet

class AccountsSimpleTests(TestCase):
    """
    Kiểm thử đơn giản cho hệ thống tài khoản và người dùng.
    """

    def setUp(self):
        """Khởi tạo dữ liệu mẫu cho các bài kiểm thử."""
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )

    def test_customer_creation(self):
        """Kiểm tra việc tạo hồ sơ khách hàng (Customer)."""
        customer = Customer.objects.create(
            user=self.user,
            full_name="Người Dùng Thử",
            phone_number="0123456789"
        )
        self.assertEqual(customer.user.username, "testuser")
        self.assertEqual(customer.full_name, "Người Dùng Thử")

    def test_wallet_creation(self):
        """Kiểm tra việc tạo ví tiền (Wallet) cho khách hàng."""
        customer = Customer.objects.create(
            user=self.user,
            full_name="Người Dùng Thử"
        )
        wallet = Wallet.objects.create(customer=customer, balance=100000)
        self.assertEqual(wallet.balance, 100000)
        self.assertEqual(wallet.customer.user.username, "testuser")

    def test_login_page_load(self):
        """Kiểm tra trang đăng nhập có tải thành công không."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_register_page_load(self):
        """Kiểm tra trang đăng ký có tải thành công không."""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_home_page_load(self):
        """Kiểm tra trang chủ có tải thành công không."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
