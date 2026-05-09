from django.urls import path
from accounts import views

urlpatterns = [
    path("admin/khach-hang/", views.admin_customer_list, name="admin_customer_list"),
    path("admin/khach-hang/<int:customer_id>/sua/", views.admin_customer_edit, name="admin_customer_edit"),
    path("admin/khach-hang/<int:customer_id>/khoa-mo-khoa/", views.admin_customer_toggle_active, name="admin_customer_toggle_active"),
]
