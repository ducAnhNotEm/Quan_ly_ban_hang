from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Customer
from products.models import Cart, CartItem, DiscountCode, Product


class ProductsModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="bob",
            email="bob@example.com",
            password="testpass123",
        )
        self.customer = Customer.objects.create(
            user=self.user,
            full_name="Bob Tran",
            phone_number="0911222333",
        )

    def test_product_created_with_expected_defaults(self):
        product = Product.objects.create(
            product_name="Sua tuoi",
            category="Do uong",
            slug="sua-tuoi",
            price=Decimal("25000.00"),
        )

        self.assertEqual(product.discount_percent, Decimal("0"))
        self.assertEqual(product.stock_quantity, 0)
        self.assertEqual(product.discounted_price, Decimal("25000.00"))

    def test_product_price_helpers(self):
        product = Product.objects.create(
            product_name="Ca phe sua",
            category="Do uong",
            slug="ca-phe-sua",
            price=Decimal("100000.00"),
            discount_percent=Decimal("12.50"),
        )

        self.assertEqual(product.discounted_price, Decimal("87500.00"))
        self.assertEqual(product.formatted_price, "87.500 đ")

    def test_product_slug_must_be_unique(self):
        Product.objects.create(
            product_name="Sua tuoi",
            category="Do uong",
            slug="sua-tuoi",
            price=Decimal("25000.00"),
        )

        with self.assertRaises(IntegrityError):
            Product.objects.create(
                product_name="Sua tuoi 2",
                category="Do uong",
                slug="sua-tuoi",
                price=Decimal("30000.00"),
            )

    def test_cart_item_relations_and_auto_amounts(self):
        cart = Cart.objects.create(customer=self.customer)
        product = Product.objects.create(
            product_name="Banh mi",
            category="Do an",
            slug="banh-mi",
            price=Decimal("15000.00"),
            discount_percent=Decimal("10.00"),
            stock_quantity=20,
        )

        item = CartItem.objects.create(cart=cart, product=product, quantity=2)

        self.assertTrue(item.is_selected)
        self.assertEqual(item.discount_amount, Decimal("3000.00"))
        self.assertEqual(item.sub_total, Decimal("27000.00"))
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(product.cart_items.count(), 1)

    def test_cart_totals_helpers(self):
        cart = Cart.objects.create(customer=self.customer)
        product_a = Product.objects.create(
            product_name="Tra dao",
            category="Do uong",
            slug="tra-dao",
            price=Decimal("30000.00"),
            discount_percent=Decimal("10.00"),
            stock_quantity=30,
        )
        product_b = Product.objects.create(
            product_name="Banh ngan lop",
            category="Do an",
            slug="banh-ngan-lop",
            price=Decimal("20000.00"),
            discount_percent=Decimal("0.00"),
            stock_quantity=30,
        )

        CartItem.objects.create(cart=cart, product=product_a, quantity=2)
        CartItem.objects.create(cart=cart, product=product_b, quantity=1)

        self.assertEqual(cart.total_items, 3)
        self.assertEqual(cart.total_amount, Decimal("74000.00"))

    def test_discount_code_defaults_and_unique_code(self):
        code = DiscountCode.objects.create(
            code="SALE10",
            discount_percent=Decimal("10.00"),
        )

        self.assertTrue(code.is_active)
        self.assertEqual(code.used_count, 0)

        with self.assertRaises(IntegrityError):
            DiscountCode.objects.create(
                code="SALE10",
                discount_percent=Decimal("5.00"),
            )

    def test_discount_code_is_valid_and_mark_as_used(self):
        now = timezone.now()
        code = DiscountCode.objects.create(
            code="SALE20",
            discount_percent=Decimal("20.00"),
            valid_from=now - timedelta(hours=1),
            valid_to=now + timedelta(hours=1),
            usage_limit=1,
        )

        self.assertTrue(code.is_valid(now))

        code.mark_as_used()
        code.refresh_from_db()

        self.assertEqual(code.used_count, 1)
        self.assertFalse(code.is_valid(now))

        with self.assertRaises(ValidationError):
            code.mark_as_used()

    def test_discount_code_clean_rejects_invalid_period(self):
        now = timezone.now()
        code = DiscountCode(
            code="INVALID_TIME",
            discount_percent=Decimal("10.00"),
            valid_from=now + timedelta(days=1),
            valid_to=now,
        )

        with self.assertRaises(ValidationError):
            code.full_clean()

    def test_delete_product_cascades_cart_items(self):
        cart = Cart.objects.create(customer=self.customer)
        product = Product.objects.create(
            product_name="Tra sua",
            category="Do uong",
            slug="tra-sua",
            price=Decimal("40000.00"),
        )
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        product.delete()

        self.assertEqual(CartItem.objects.count(), 0)
