from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

"""
Module models cho app `products`.

Nhóm model chính:
- Product: thông tin sản phẩm bán ra.
- Cart, CartItem: giỏ hàng và các dòng sản phẩm trong giỏ.
- DiscountCode: mã giảm giá áp cho đơn hàng.
"""

# Quy uoc lam tron tien ve 2 chu so thap phan.
MONEY_QUANTIZE = Decimal("0.01")
# Co so de tinh phan tram giam gia.
PERCENT_BASE = Decimal("100")


class Product(models.Model):
    """Thông tin một sản phẩm trong hệ thống."""

    # Thuộc tính mô tả và định danh sản phẩm.
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    # Thuộc tính giá/bán hàng.
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock_quantity = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Chuỗi đại diện gọn cho sản phẩm trong trang quản trị/nhật ký."""
        return f"{self.product_name} ({self.slug})"

    @property
    def discounted_price(self) -> Decimal:
        """
        Giá sau giảm của sản phẩm.

        Công thức:
        - discount_amount = price * discount_percent / 100
        - discounted_price = price - discount_amount (không âm)
        """
        discount_percent = self.discount_percent or Decimal("0")
        discount_amount = (self.price * discount_percent / PERCENT_BASE).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )
        final_price = self.price - discount_amount
        return max(final_price, Decimal("0")).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)

    @property
    def formatted_price(self) -> str:
        """Giá đã giảm, định dạng chuỗi VND để hiển thị UI."""
        rounded = self.discounted_price.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        amount = int(rounded)
        return f"{amount:,}".replace(",", ".") + " đ"

    def clean(self) -> None:
        """
        Validate dữ liệu sản phẩm theo rule nghiệp vụ.

        Các rule:
        - price >= 0
        - stock_quantity >= 0
        - 0 <= discount_percent <= 100
        """
        errors = {}

        # Rang buoc gia, ton kho va ty le giam gia.
        if self.price is not None and self.price < 0:
            errors["price"] = "Gia ban khong duoc am."

        if self.stock_quantity is not None and self.stock_quantity < 0:
            errors["stock_quantity"] = "So luong ton kho khong duoc am."

        if self.discount_percent is not None and (
            self.discount_percent < 0 or self.discount_percent > PERCENT_BASE
        ):
            errors["discount_percent"] = "Phan tram giam gia phai tu 0 den 100."

        if errors:
            raise ValidationError(errors)


class Cart(models.Model):
    """Giỏ hàng của một khách hàng (mỗi khách 1 giỏ)."""

    customer = models.OneToOneField("accounts.Customer", on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Chuỗi đại diện gọn cho Cart."""
        return f"Cart #{self.pk} - Customer {self.customer_id}"

    @property
    def total_items(self) -> int:
        """Tổng số lượng sản phẩm trong giỏ (cộng quantity từng dòng)."""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self) -> Decimal:
        """Tổng tiền giỏ hàng (cộng sub_total của tất cả dòng)."""
        return sum((item.sub_total for item in self.items.all()), Decimal("0"))


class CartItem(models.Model):
    """Một dòng sản phẩm trong giỏ hàng."""

    # Quan hệ tới giỏ hàng và sản phẩm.
    cart = models.ForeignKey("products.Cart", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="cart_items")
    # Dữ liệu tính tiền của dòng giỏ hàng.
    quantity = models.PositiveIntegerField(default=1)
    is_selected = models.BooleanField(default=True)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str:
        """Chuỗi đại diện gọn cho CartItem."""
        return f"CartItem #{self.pk} - Cart {self.cart_id} - Product {self.product_id}"

    @property
    def line_total_before_discount(self) -> Decimal:
        """Tiền gốc dòng giỏ hàng trước giảm giá = giá sản phẩm * quantity."""
        if not self.product_id:
            return Decimal("0")

        return (self.product.price * Decimal(self.quantity or 0)).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

    def clean(self) -> None:
        """
        Validate dữ liệu dòng giỏ hàng.

        Các rule:
        - quantity >= 1
        - quantity không vượt quá tồn kho hiện tại của sản phẩm
        """
        errors = {}

        # Kiem tra so luong theo ton kho hien tai cua san pham.
        if self.quantity < 1:
            errors["quantity"] = "So luong phai lon hon 0."

        if self.product_id and self.quantity > self.product.stock_quantity:
            errors["quantity"] = "So luong vuot qua ton kho hien tai."

        if errors:
            raise ValidationError(errors)

    def recalculate_amounts(self) -> None:
        """
        Tính lại `discount_amount` và `sub_total` cho CartItem.

        Lưu ý:
        - Nếu chưa gắn sản phẩm thì tiền = 0.
        - Tiền giảm không vượt quá tiền gốc dòng.
        """
        if not self.product_id:
            self.discount_amount = Decimal("0")
            self.sub_total = Decimal("0")
            return

        gross_amount = self.line_total_before_discount
        discount_percent = self.product.discount_percent or Decimal("0")
        discount_amount = (gross_amount * discount_percent / PERCENT_BASE).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

        # Chan so tien giam toi da bang tien goc cua dong gio hang.
        if discount_amount > gross_amount:
            discount_amount = gross_amount

        self.discount_amount = discount_amount
        self.sub_total = (gross_amount - discount_amount).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

    def save(self, *args, **kwargs):
        """Ghi đè save để luôn cập nhật tiền tự động trước khi lưu."""
        # Tu dong cap nhat tien giam va thanh tien truoc khi luu.
        self.recalculate_amounts()
        super().save(*args, **kwargs)


class DiscountCode(models.Model):
    """Mã giảm giá có thể áp dụng theo điều kiện thời gian và lượt sử dụng."""

    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """Trả về mã giảm giá để hiển thị gọn trong trang quản trị/nhật ký."""
        return self.code

    @property
    def is_usage_limit_reached(self) -> bool:
        """Kiểm tra mã đã chạm giới hạn số lần dùng hay chưa."""
        return self.usage_limit is not None and self.used_count >= self.usage_limit

    def clean(self) -> None:
        """
        Validate dữ liệu mã giảm giá.

        Các rule:
        - 0 <= discount_percent <= 100
        - valid_from <= valid_to
        - used_count <= usage_limit (nếu có giới hạn)
        """
        errors = {}

        # Rang buoc tinh hop le cua ma giam gia theo thoi gian va gioi han su dung.
        if self.discount_percent is not None and (
            self.discount_percent < 0 or self.discount_percent > PERCENT_BASE
        ):
            errors["discount_percent"] = "Phan tram giam gia phai tu 0 den 100."

        if self.valid_from and self.valid_to and self.valid_from > self.valid_to:
            errors["valid_to"] = "Thoi gian ket thuc phai sau thoi gian bat dau."

        if self.usage_limit is not None and self.used_count > self.usage_limit:
            errors["used_count"] = "So lan da dung khong duoc vuot qua gioi han su dung."

        if errors:
            raise ValidationError(errors)

    def is_valid(self, at_time=None) -> bool:
        """
        Kiểm tra mã giảm giá có hợp lệ tại thời điểm `at_time` hay không.

        Điều kiện hợp lệ:
        - is_active = True
        - nằm trong khoảng hiệu lực (nếu có đặt mốc thời gian)
        - chưa vượt usage_limit
        """
        current_time = at_time or timezone.now()

        if not self.is_active:
            return False

        if self.valid_from and current_time < self.valid_from:
            return False

        if self.valid_to and current_time > self.valid_to:
            return False

        if self.is_usage_limit_reached:
            return False

        return True

    def mark_as_used(self, save: bool = True) -> None:
        """
        Tăng số lần sử dụng mã lên 1.

        Lưu ý:
        - Nếu đã đạt giới hạn thì raise ValidationError.
        - `save=True` sẽ lưu ngay `used_count`.
        """
        if self.is_usage_limit_reached:
            raise ValidationError({"usage_limit": "Ma giam gia da dat gioi han su dung."})

        self.used_count += 1

        if save:
            self.save(update_fields=["used_count"])
