from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import Customer
from accounts.forms import AdminCustomerForm

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_customer_list(request):
    """
    View hiển thị danh sách khách hàng cho Admin/Staff.
    """
    customers = Customer.objects.select_related("user", "wallet").all().order_by("-id")
    return render(request, "admin_custom/customer_list.html", {"customers": customers})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_customer_edit(request, customer_id):
    """
    View để Admin/Staff sửa thông tin khách hàng.
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    
    if request.method == "POST":
        form = AdminCustomerForm(request.POST, instance=customer, user=customer.user)
        if form.is_valid():
            # Lưu Customer
            form.save()
            # Cập nhật email trong User
            new_email = form.cleaned_data.get("email")
            if new_email and customer.user.email != new_email:
                customer.user.email = new_email
                customer.user.save(update_fields=["email"])
            
            messages.success(request, f"Đã cập nhật thông tin khách hàng {customer.full_name} thành công.")
            return redirect("admin_customer_list")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin nhập.")
    else:
        form = AdminCustomerForm(instance=customer, user=customer.user)

    return render(request, "admin_custom/customer_edit.html", {"form": form, "customer": customer})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_customer_toggle_active(request, customer_id):
    """
    View để khóa/mở khóa tài khoản khách hàng.
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    user = customer.user
    
    # Đảo ngược trạng thái is_active
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    
    status_text = "mở khóa" if user.is_active else "khóa"
    messages.success(request, f"Đã {status_text} tài khoản của khách hàng {customer.full_name}.")
    
    return redirect("admin_customer_list")
