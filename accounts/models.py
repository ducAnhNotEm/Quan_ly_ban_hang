from django.conf import settings
from django.db import models


class Customer(models.Model):
    class Gender(models.TextChoices):
        MALE = "Nam", "Nam"
        FEMALE = "Nu", "Nu"
        OTHER = "Khac", "Khac"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.OTHER)


class Wallet(models.Model):
    customer = models.OneToOneField("accounts.Customer", on_delete=models.CASCADE, related_name="wallet")
    balance = models.BigIntegerField(default=0)


class TopUpRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "PENDING"
        APPROVED = "APPROVED", "APPROVED"
        REJECTED = "REJECTED", "REJECTED"

    customer = models.ForeignKey("accounts.Customer", on_delete=models.CASCADE, related_name="topup_requests")
    amount = models.BigIntegerField()
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

