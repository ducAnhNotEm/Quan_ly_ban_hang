from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Customer, Wallet
from products.models import Product
from orders.models import Order, OrderDetail

class OrdersSimpleTests(TestCase):
    """
    Kiểm thử đơn giản cho đơn hàng và thanh toán.
    """

    def setUp(self):
        """Khởi tạo dữ liệu mẫu."""
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password123"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            full_name="Người Dùng Thử"
        )
        self.product = Product.objects.create(
            product_name="Sản phẩm mẫu",
            price=Decimal("50000.00"),
            stock_quantity=100
        )
        self.client.force_login(self.user)

    def test_order_creation(self):
        """Kiểm tra việc tạo một đơn hàng (Order)."""
        order = Order.objects.create(
            customer=self.customer,
            total_amount=Decimal("50000.00")
        )
        self.assertEqual(order.customer.full_name, "Người Dùng Thử")
        self.assertEqual(order.total_amount, Decimal("50000.00"))

    def test_order_detail_creation(self):
        """Kiểm tra tạo chi tiết đơn hàng (OrderDetail)."""
        order = Order.objects.create(customer=self.customer)
        detail = OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("50000.00"),
            sub_total=Decimal("50000.00")
        )
        self.assertEqual(detail.product.product_name, "Sản phẩm mẫu")
        self.assertEqual(detail.sub_total, Decimal("50000.00"))

    def test_cart_page_load(self):
        """Kiểm tra trang giỏ hàng có tải thành công không."""
        response = self.client.get(reverse("cart_view"))
        self.assertEqual(response.status_code, 200)

    def test_orders_list_page_load(self):
        """Kiểm tra trang danh sách đơn hàng có tải thành công không."""
        response = self.client.get(reverse("orders_list"))
        self.assertEqual(response.status_code, 200)

    def test_order_detail_page_load(self):
        """Kiểm tra trang chi tiết đơn hàng có tải thành công không."""
        order = Order.objects.create(customer=self.customer)
        response = self.client.get(reverse("order_detail", args=[order.id]))
        self.assertEqual(response.status_code, 200)

    def test_checkout_with_sufficient_balance(self):
        """Khách hàng có đủ tiền có thể đặt hàng và bị trừ tiền ví."""
        Wallet.objects.create(customer=self.customer, balance=100000)
        
        response = self.client.post(reverse("confirm_order"), {
            "source": "BUY_NOW",
            "product_id": self.product.id,
            "quantity": 1
        })
        
        self.assertEqual(Order.objects.count(), 1)
        self.customer.wallet.refresh_from_db()
        self.assertEqual(self.customer.wallet.balance, 50000)

    def test_checkout_with_insufficient_balance(self):
        """Khách hàng không đủ tiền không thể đặt hàng."""
        Wallet.objects.create(customer=self.customer, balance=10000)
        
        response = self.client.post(reverse("confirm_order"), {
            "source": "BUY_NOW",
            "product_id": self.product.id,
            "quantity": 1
        })
        
        self.assertEqual(Order.objects.count(), 0)
        self.customer.wallet.refresh_from_db()
        self.assertEqual(self.customer.wallet.balance, 10000)
