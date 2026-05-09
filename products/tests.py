from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from products.models import Product, Cart, CartItem
from accounts.models import Customer
from django.contrib.auth import get_user_model

class ProductsSimpleTests(TestCase):
    """
    Kiểm thử đơn giản cho sản phẩm và giỏ hàng.
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
            category="Điện tử",

            price=Decimal("100000.00"),
            stock_quantity=10
        )

    def test_product_creation(self):
        """Kiểm tra tạo sản phẩm mới."""
        self.assertEqual(self.product.product_name, "Sản phẩm mẫu")
        self.assertEqual(self.product.price, Decimal("100000.00"))
        self.assertEqual(str(self.product), "Sản phẩm mẫu")

    def test_cart_creation(self):
        """Kiểm tra tạo giỏ hàng cho khách hàng."""
        cart = Cart.objects.create(customer=self.customer)
        self.assertEqual(cart.customer.full_name, "Người Dùng Thử")

    def test_cart_item_creation(self):
        """Kiểm tra thêm sản phẩm vào giỏ hàng."""
        cart = Cart.objects.create(customer=self.customer)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart_item.product.product_name, "Sản phẩm mẫu")
        self.assertEqual(cart_item.quantity, 2)

    def test_product_detail_page_load(self):
        """Kiểm tra trang chi tiết sản phẩm có tải thành công không."""
        response = self.client.get(reverse("products:detail", args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sản phẩm mẫu")
