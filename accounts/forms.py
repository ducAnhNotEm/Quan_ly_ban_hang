from django import forms

from accounts.models import Customer
from banhang.sql_utils import fetch_one_dict


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        error_messages={"required": "Vui long nhap ten dang nhap."},
    )
    full_name = forms.CharField(
        max_length=255,
        required=True,
        error_messages={"required": "Vui long nhap ho va ten."},
    )
    email = forms.EmailField(
        required=True,
        error_messages={
            "required": "Vui long nhap email.",
            "invalid": "Email khong hop le.",
        },
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        error_messages={"required": "Vui long nhap so dien thoai."},
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        error_messages={"required": "Vui long nhap mat khau."},
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        error_messages={"required": "Vui long xac nhan mat khau."},
    )
    address = forms.CharField(required=False)
    date_of_birth = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        error_messages={"invalid": "Ngay sinh khong hop le."},
    )
    gender = forms.ChoiceField(
        required=False,
        choices=Customer.Gender.choices,
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        existing_user = fetch_one_dict("auth_user_exists_username.sql", [username])
        if existing_user is not None:
            raise forms.ValidationError("Ten dang nhap da ton tai.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing_email = fetch_one_dict("auth_user_exists_email.sql", [email])
        if existing_email is not None:
            raise forms.ValidationError("Email da duoc su dung.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()
        if len(phone_number) < 8:
            raise forms.ValidationError("So dien thoai phai co it nhat 8 ky tu.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Mat khau xac nhan khong khop.")

        return cleaned_data
