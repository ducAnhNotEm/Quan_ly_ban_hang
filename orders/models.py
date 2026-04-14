from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models

"""
Module models cho app `orders`.

Mục tiêu:
- Quản lý đơn hàng (`Order`) và chi tiết từng dòng sản phẩm (`OrderDetail`).
- Chuẩn hóa cách tính tiền để tránh lệch dữ liệu khi làm tròn/áp dụng giảm giá.
"""

# Quy uoc lam tron tien ve 2 chu so thap phan.
MONEY_QUANTIZE = Decimal("0.01")
# Co so de tinh phan tram giam gia.
PERCENT_BASE = Decimal("100")


class Order(models.Model):
    """Đại diện một đơn hàng của khách hàng."""

    class Status(models.TextChoices):
        """Trạng thái nghiệp vụ hiện tại của đơn hàng."""

        PAID = "PAID", "PAID"
        CANCELLED = "CANCELLED", "CANCELLED"

    # Chủ đơn hàng.
    customer = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE, related_name="orders")
    # Các trường tổng tiền của đơn (đều lưu kiểu Decimal có 2 chữ số thập phân).
    sub_total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=100, blank=True, default="")
    coupon_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Mặc định hiển thị đơn mới nhất trước.
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        """Chuỗi đại diện gọn của đơn hàng để hiển thị trong nhật ký/trang quản trị."""
        return f"Order #{self.pk} - {self.customer_id} - {self.status}"

    @property
    def is_paid(self) -> bool:
        """Kiểm tra nhanh đơn đã thanh toán hay chưa."""
        return self.status == self.Status.PAID

    def recalculate_totals(self, save: bool = True) -> None:
        """
        Tính lại các trường tiền tổng của đơn hàng từ danh sách `details`.

        Công thức:
        - sub_total_amount = tổng tiền gốc của các dòng.
        - discount_amount = tổng tiền giảm giá theo từng dòng.
        - total_amount = sub_total_amount - discount_amount - coupon_discount_amount.

        Lưu ý:
        - Có làm tròn theo `MONEY_QUANTIZE`.
        - Không cho tổng tiền âm.
        - `save=True` sẽ lưu trực tiếp các trường vừa tính.
        """
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
    """Dòng chi tiết sản phẩm trong một đơn hàng."""

    # Mỗi dòng thuộc về một đơn và một sản phẩm.
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="details")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="order_details")
    # Thông tin tính tiền trên từng dòng.
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        # Giữ thứ tự dòng theo ID tăng dần.
        ordering = ("id",)

    def __str__(self) -> str:
        """Chuỗi đại diện gọn của OrderDetail để debug nhanh."""
        return f"OrderDetail #{self.pk} - Order {self.order_id} - Product {self.product_id}"

    @property
    def line_total_before_discount(self) -> Decimal:
        """Tiền gốc của dòng trước giảm giá = unit_price * quantity."""
        unit_price = self.unit_price or Decimal("0")
        quantity = Decimal(self.quantity or 0)
        return (unit_price * quantity).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)

    def clean(self) -> None:
        """
        Validate dữ liệu đầu vào theo rule nghiệp vụ.

        Các rule chính:
        - quantity >= 1
        - unit_price >= 0
        - 0 <= discount_percent <= 100
        """
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
        """
        Tính lại `discount_amount` và `sub_total` cho dòng chi tiết.

        Lưu ý:
        - discount_amount được chặn không vượt quá tiền gốc dòng.
        - sub_total = tiền gốc - giảm giá.
        """
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
        """
        Ghi đè save để luôn tính lại tiền trước khi lưu.

        Mục đích:
        - Tránh sai lệch dữ liệu nếu bên ngoài quên gọi hàm tính tiền.
        """
        # Tu dong cap nhat so tien truoc khi luu de tranh sai lech du lieu.
        self.recalculate_amounts()
        super().save(*args, **kwargs)
