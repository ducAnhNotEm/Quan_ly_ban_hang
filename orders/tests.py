from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Customer
from orders.models import Order, OrderDetail
from products.models import Product

"""
Test suite cho app `orders`.

Mục tiêu:
- Xác nhận giá trị mặc định của đơn hàng.
- Xác nhận quan hệ FK và logic tính tiền tự động.
- Bảo vệ rule tổng tiền không âm và cascade delete.
"""


class OrdersModelTests(TestCase):
    """Kiểm thử mô hình dữ liệu (model) `Order` và `OrderDetail`."""

    def setUp(self):
        """Tạo tài khoản/khách hàng/sản phẩm mẫu để dùng lại cho tất cả bài kiểm thử."""
        self.user = get_user_model().objects.create_user(
            username="charlie",
            email="charlie@example.com",
            password="testpass123",
        )
        self.customer = Customer.objects.create(
            user=self.user,
            full_name="Charlie Le",
            phone_number="0988777666",
        )
        self.product = Product.objects.create(
            product_name="Ca phe",
            category="Do uong",
            slug="ca-phe",
            price=Decimal("30000.00"),
            stock_quantity=100,
        )
        self.product_2 = Product.objects.create(
            product_name="Tra dao",
            category="Do uong",
            slug="tra-dao",
            price=Decimal("50000.00"),
            stock_quantity=100,
        )

    def test_order_defaults(self):
        """Đơn hàng mới tạo phải có trạng thái/tiền mặc định đúng theo mô hình dữ liệu (model)."""
        order = Order.objects.create(customer=self.customer)

        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.sub_total_amount, Decimal("0"))
        self.assertEqual(order.discount_amount, Decimal("0"))
        self.assertEqual(order.coupon_code, "")
        self.assertEqual(order.total_amount, Decimal("0"))

    def test_order_detail_relations(self):
        """OrderDetail phải nối đúng với Order và Product qua reverse relation."""
        order = Order.objects.create(
            customer=self.customer,
            sub_total_amount=Decimal("60000.00"),
            total_amount=Decimal("60000.00"),
        )

        detail = OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("30000.00"),
            discount_percent=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            sub_total=Decimal("60000.00"),
        )

        self.assertEqual(order.details.count(), 1)
        self.assertEqual(self.product.order_details.count(), 1)
        self.assertEqual(detail.quantity, 2)

    def test_order_detail_auto_calculates_amounts(self):
        """`save()` của OrderDetail phải tự động tính discount_amount/sub_total."""
        order = Order.objects.create(customer=self.customer)

        detail = OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("30000.00"),
            discount_percent=Decimal("10.00"),
        )

        self.assertEqual(detail.discount_amount, Decimal("6000.00"))
        self.assertEqual(detail.sub_total, Decimal("54000.00"))

    def test_recalculate_order_totals_from_details(self):
        """`recalculate_totals()` phải tổng hợp đúng gross/discount/coupon => total."""
        order = Order.objects.create(
            customer=self.customer,
            coupon_code="SALE5K",
            coupon_discount_amount=Decimal("5000.00"),
        )

        OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("30000.00"),
            discount_percent=Decimal("10.00"),
        )
        OrderDetail.objects.create(
            order=order,
            product=self.product_2,
            quantity=1,
            unit_price=Decimal("50000.00"),
            discount_percent=Decimal("0.00"),
        )

        order.recalculate_totals()
        order.refresh_from_db()

        self.assertEqual(order.sub_total_amount, Decimal("110000.00"))
        self.assertEqual(order.discount_amount, Decimal("6000.00"))
        self.assertEqual(order.total_amount, Decimal("99000.00"))

    def test_recalculate_order_total_not_negative(self):
        """Tổng tiền sau coupon không được âm, phải bị chặn về 0."""
        order = Order.objects.create(
            customer=self.customer,
            coupon_code="SALE200K",
            coupon_discount_amount=Decimal("200000.00"),
        )

        OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("30000.00"),
            discount_percent=Decimal("0.00"),
        )

        order.recalculate_totals()
        order.refresh_from_db()

        self.assertEqual(order.sub_total_amount, Decimal("30000.00"))
        self.assertEqual(order.discount_amount, Decimal("0.00"))
        self.assertEqual(order.total_amount, Decimal("0.00"))

    def test_delete_order_cascades_order_details(self):
        """Xóa Order phải xóa toàn bộ OrderDetail liên quan."""
        order = Order.objects.create(customer=self.customer)
        OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("30000.00"),
            sub_total=Decimal("30000.00"),
        )

        order.delete()

        self.assertEqual(OrderDetail.objects.count(), 0)

    def test_delete_product_cascades_order_details(self):
        """Xóa Product phải xóa OrderDetail đang FK tới Product đó."""
        order = Order.objects.create(customer=self.customer)
        OrderDetail.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("30000.00"),
            sub_total=Decimal("30000.00"),
        )

        self.product.delete()

        self.assertEqual(OrderDetail.objects.count(), 0)


