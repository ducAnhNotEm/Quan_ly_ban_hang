from django.conf import settings
from django.db import models

"""
Module models cho app `accounts`.

Các model chính:
- Customer: hồ sơ khách hàng gắn 1-1 với tài khoản đăng nhập.
- Wallet: ví tiền của khách hàng, mỗi khách có đúng 1 ví.
- TopUpRequest: yêu cầu nạp tiền do khách gửi, chờ staff duyệt.
"""


class Customer(models.Model):
    """Lưu thông tin hồ sơ cá nhân của người mua hàng."""

    class Gender(models.TextChoices):
        """Danh sách giới tính hợp lệ dùng cho lựa chọn trong form."""

        MALE = "Nam", "Nam"
        FEMALE = "Nu", "Nu"
        OTHER = "Khac", "Khac"

    # 1 tài khoản user Django tương ứng đúng 1 hồ sơ khách hàng.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    # Thông tin liên hệ/hồ sơ cơ bản.
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.OTHER)


class Wallet(models.Model):
    """
    Ví tiền của khách hàng.

    Lưu ý:
    - Quan hệ OneToOne với Customer để đảm bảo mỗi khách chỉ có 1 ví.
    - `balance` dùng BigInteger để chứa số tiền VND dạng số nguyên.
    """

    customer = models.OneToOneField("accounts.Customer", on_delete=models.CASCADE, related_name="wallet")
    balance = models.BigIntegerField(default=0)


class TopUpRequest(models.Model):
    """Yêu cầu nạp tiền do khách hàng gửi để staff duyệt."""

    class Status(models.TextChoices):
        """Trạng thái xử lý yêu cầu nạp tiền."""

        PENDING = "PENDING", "PENDING"
        APPROVED = "APPROVED", "APPROVED"
        REJECTED = "REJECTED", "REJECTED"

    # Một khách có thể tạo nhiều yêu cầu nạp tiền theo thời gian.
    customer = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE, related_name="topup_requests")
    # Số tiền đề nghị nạp (VND, số nguyên).
    amount = models.BigIntegerField()
    # Lý do nạp, cho phép bỏ trống.
    note = models.TextField(blank=True, null=True)
    # Trạng thái mặc định là đang chờ duyệt.
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)


