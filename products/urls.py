from django.urls import path

from products import views

app_name = "products"

urlpatterns = [
    path("admin/them-san-pham/", views.admin_product_create, name="admin_product_create"),
    path("preview/", views.product_detail_preview, name="detail_preview"),
    path("<int:product_id>/", views.product_detail, name="detail"),
]
