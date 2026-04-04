from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

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

    def test_cart_item_relations_and_defaults(self):
        cart = Cart.objects.create(customer=self.customer)
        product = Product.objects.create(
            product_name="Banh mi",
            category="Do an",
            slug="banh-mi",
            price=Decimal("15000.00"),
            stock_quantity=20,
        )

        item = CartItem.objects.create(cart=cart, product=product, quantity=2)

        self.assertTrue(item.is_selected)
        self.assertEqual(item.sub_total, Decimal("0"))
        self.assertEqual(item.discount_amount, Decimal("0"))
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(product.cart_items.count(), 1)

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