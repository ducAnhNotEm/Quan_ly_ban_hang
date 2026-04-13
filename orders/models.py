from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models

# Quy uoc lam tron tien ve 2 chu so thap phan.
MONEY_QUANTIZE = Decimal("0.01")
# Co so de tinh phan tram giam gia.
PERCENT_BASE = Decimal("100")


class Order(models.Model):
    class Status(models.TextChoices):
        PAID = "PAID", "PAID"
        CANCELLED = "CANCELLED", "CANCELLED"

    customer = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE, related_name="orders")
    sub_total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=100, blank=True, default="")
    coupon_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return f"Order #{self.pk} - {self.customer_id} - {self.status}"

    @property
    def is_paid(self) -> bool:
        return self.status == self.Status.PAID

    def recalculate_totals(self, save: bool = True) -> None:
        gross_sub_total = Decimal("0")
        total_discount = Decimal("0")

        # Tong hop tong tien goc va tong giam gia tu tung dong chi tiet.
        for detail in self.details.all():
            gross_sub_total += detail.line_total_before_discount
            total_discount += detail.discount_amount or Decimal("0")

        coupon_discount = self.coupon_discount_amount or Decimal("0")
        net_total = gross_sub_total - total_discount - coupon_discount

        self.sub_total_amount = gross_sub_total.quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)
        self.discount_amount = total_discount.quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)
        # Khong de tong tien am neu coupon lon hon tong gia tri don.
        self.total_amount = max(net_total, Decimal("0")).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

        if save:
            self.save(update_fields=["sub_total_amount", "discount_amount", "total_amount"])


class OrderDetail(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="details")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="order_details")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"OrderDetail #{self.pk} - Order {self.order_id} - Product {self.product_id}"

    @property
    def line_total_before_discount(self) -> Decimal:
        unit_price = self.unit_price or Decimal("0")
        quantity = Decimal(self.quantity or 0)
        return (unit_price * quantity).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)

    def clean(self) -> None:
        errors = {}

        # Rang buoc du lieu dau vao theo nghiep vu mua hang.
        if self.quantity < 1:
            errors["quantity"] = "So luong phai lon hon 0."

        if self.unit_price is not None and self.unit_price < 0:
            errors["unit_price"] = "Don gia khong duoc am."

        if self.discount_percent is not None and (
            self.discount_percent < 0 or self.discount_percent > PERCENT_BASE
        ):
            errors["discount_percent"] = "Phan tram giam gia phai tu 0 den 100."

        if errors:
            raise ValidationError(errors)

    def recalculate_amounts(self) -> None:
        gross_amount = self.line_total_before_discount
        discount_percent = self.discount_percent or Decimal("0")
        discount_amount = (gross_amount * discount_percent / PERCENT_BASE).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

        # Chan so tien giam toi da bang tien goc cua dong.
        if discount_amount > gross_amount:
            discount_amount = gross_amount

        self.discount_amount = discount_amount
        self.sub_total = (gross_amount - discount_amount).quantize(
            MONEY_QUANTIZE,
            rounding=ROUND_HALF_UP,
        )

    def save(self, *args, **kwargs):
        # Tu dong cap nhat so tien truoc khi luu de tranh sai lech du lieu.
        self.recalculate_amounts()
        super().save(*args, **kwargs)
