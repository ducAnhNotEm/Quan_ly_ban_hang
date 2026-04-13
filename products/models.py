from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Quy uoc lam tron tien ve 2 chu so thap phan.
MONEY_QUANTIZE = Decimal("0.01")
# Co so de tinh phan tram giam gia.
PERCENT_BASE = Decimal("100")


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock_quantity = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.product_name} ({self.slug})"

    @property
    def discounted_price(self) -> Decimal:
        discount_percent = self.discount_percent or Decimal("0")
        discount_amount = (self.price * discount_percent / PERCENT_BASE).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )
        final_price = self.price - discount_amount
        return max(final_price, Decimal("0")).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)

    @property
    def formatted_price(self) -> str:
        rounded = self.discounted_price.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        amount = int(rounded)
        return f"{amount:,}".replace(",", ".") + " đ"

    def clean(self) -> None:
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
    customer = models.OneToOneField("accounts.Customer", on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Cart #{self.pk} - Customer {self.customer_id}"

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self) -> Decimal:
        return sum((item.sub_total for item in self.items.all()), Decimal("0"))


class CartItem(models.Model):
    cart = models.ForeignKey("products.Cart", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    is_selected = models.BooleanField(default=True)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str:
        return f"CartItem #{self.pk} - Cart {self.cart_id} - Product {self.product_id}"

    @property
    def line_total_before_discount(self) -> Decimal:
        if not self.product_id:
            return Decimal("0")

        return (self.product.price * Decimal(self.quantity or 0)).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

    def clean(self) -> None:
        errors = {}

        # Kiem tra so luong theo ton kho hien tai cua san pham.
        if self.quantity < 1:
            errors["quantity"] = "So luong phai lon hon 0."

        if self.product_id and self.quantity > self.product.stock_quantity:
            errors["quantity"] = "So luong vuot qua ton kho hien tai."

        if errors:
            raise ValidationError(errors)

    def recalculate_amounts(self) -> None:
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
        # Tu dong cap nhat tien giam va thanh tien truoc khi luu.
        self.recalculate_amounts()
        super().save(*args, **kwargs)


class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    used_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code

    @property
    def is_usage_limit_reached(self) -> bool:
        return self.usage_limit is not None and self.used_count >= self.usage_limit

    def clean(self) -> None:
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
        if self.is_usage_limit_reached:
            raise ValidationError({"usage_limit": "Ma giam gia da dat gioi han su dung."})

        self.used_count += 1

        if save:
            self.save(update_fields=["used_count"])
