from django import forms

from accounts.models import Customer
from banhang.sql_utils import fetch_one_dict

"""
Tầng form cho app `accounts`.

File này tập trung vào form đăng ký:
- validate field theo từng bước.
- chuẩn hóa dữ liệu đầu vào.
- trả lỗi rõ ràng để view hiển thị thông báo cho user.
"""


class RegisterForm(forms.Form):
    """
    Form đăng ký tài khoản khách hàng.

    Luồng tổng quan:
    1) Nhận dữ liệu từ request.POST.
    2) Chạy validate theo từng field (`clean_<field>`).
    3) Chạy validate tổng thể (`clean`).
    4) Nếu hợp lệ, view dùng `cleaned_data` để tạo User/Customer/Wallet.
    """

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
        """
        Chuẩn hóa và kiểm tra trùng username.

        Chi tiết:
        - Trim khoảng trắng đầu/cuối.
        - Query bảng `auth_user` qua SQL helper.
        - Nếu đã tồn tại thì chặn đăng ký.
        """
        username = self.cleaned_data["username"].strip()
        existing_user = fetch_one_dict("auth_user_exists_username.sql", [username])
        if existing_user is not None:
            raise forms.ValidationError("Ten dang nhap da ton tai.")
        return username

    def clean_email(self):
        """
        Chuẩn hóa và kiểm tra trùng email.

        Chi tiết:
        - Trim + lower email để so sánh không phân biệt hoa/thường.
        - Query SQL xem email đã được sử dụng hay chưa.
        """
        email = self.cleaned_data["email"].strip().lower()
        existing_email = fetch_one_dict("auth_user_exists_email.sql", [email])
        if existing_email is not None:
            raise forms.ValidationError("Email da duoc su dung.")
        return email

    def clean_phone_number(self):
        """
        Validate số điện thoại ở mức cơ bản.

        Rule hiện tại:
        - Sau khi trim, độ dài phải >= 8 ký tự.
        """
        phone_number = self.cleaned_data["phone_number"].strip()
        if len(phone_number) < 8:
            raise forms.ValidationError("So dien thoai phai co it nhat 8 ky tu.")
        return phone_number

    def clean(self):
        """
        Validate chéo các field sau khi field-level validate xong.

        Rule:
        - `password1` và `password2` phải giống nhau.
        - Nếu không khớp, gắn lỗi vào `password2` để hiển thị đúng vị trí.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Mat khau xac nhan khong khop.")

        return cleaned_data

