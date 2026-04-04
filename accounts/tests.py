from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from accounts.models import Customer, TopUpRequest, Wallet


class AccountsModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="testpass123",
        )

    def test_create_customer_with_default_gender(self):
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )

        self.assertEqual(customer.gender, Customer.Gender.OTHER)
        self.assertEqual(self.user.customer_profile, customer)

    def test_wallet_defaults_and_reverse_relation(self):
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )

        wallet = Wallet.objects.create(customer=customer)

        self.assertEqual(wallet.balance, 0)
        self.assertEqual(customer.wallet, wallet)

    def test_topup_request_defaults_to_pending(self):
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
            date_of_birth=date(2000, 1, 1),
            gender=Customer.Gender.FEMALE,
        )

        topup = TopUpRequest.objects.create(
            customer=customer,
            amount=500000,
            note="Nap tien lan 1",
        )

        self.assertEqual(topup.status, TopUpRequest.Status.PENDING)
        self.assertEqual(customer.topup_requests.count(), 1)

    def test_customer_requires_unique_user(self):
        Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )

        with self.assertRaises(IntegrityError):
            Customer.objects.create(
                user=self.user,
                full_name="Alice Clone",
                phone_number="0911111111",
            )

    def test_deleting_customer_cascades_wallet_and_topups(self):
        customer = Customer.objects.create(
            user=self.user,
            full_name="Alice Nguyen",
            phone_number="0900000000",
        )
        Wallet.objects.create(customer=customer, balance=1000)
        TopUpRequest.objects.create(customer=customer, amount=300000)

        customer.delete()

        self.assertEqual(Wallet.objects.count(), 0)
        self.assertEqual(TopUpRequest.objects.count(), 0)