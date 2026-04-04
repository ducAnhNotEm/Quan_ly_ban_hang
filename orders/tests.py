from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Customer
from orders.models import Order, OrderDetail
from products.models import Product


class OrdersModelTests(TestCase):
    def setUp(self):
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

    def test_order_defaults(self):
        order = Order.objects.create(customer=self.customer)

        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.sub_total_amount, Decimal("0"))
        self.assertEqual(order.discount_amount, Decimal("0"))
        self.assertEqual(order.coupon_code, "")
        self.assertEqual(order.total_amount, Decimal("0"))

    def test_order_detail_relations(self):
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

    def test_delete_order_cascades_order_details(self):
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