from django.urls import path

from products import views

app_name = "products"

urlpatterns = [
    path("admin/san-pham/", views.admin_product_list, name="admin_product_list"),
    path("admin/san-pham/<int:product_id>/sua/", views.admin_product_edit, name="admin_product_edit"),
    path("admin/san-pham/<int:product_id>/xoa/", views.admin_product_delete, name="admin_product_delete"),
    path("admin/them-san-pham/", views.admin_product_create, name="admin_product_create"),
    path("preview/", views.product_detail_preview, name="detail_preview"),
    path("<int:product_id>/", views.product_detail, name="detail"),
]
