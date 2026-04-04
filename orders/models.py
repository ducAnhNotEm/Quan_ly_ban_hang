from django.db import models


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


class OrderDetail(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="details")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="order_details")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

