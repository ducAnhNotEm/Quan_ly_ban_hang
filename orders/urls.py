from django.urls import path

from orders import views

urlpatterns = [
    path("thanh-toan/gio-hang/", views.cart_checkout, name="cart_checkout"),
    path("thanh-toan/mua-ngay/", views.buy_now_checkout, name="buy_now_checkout"),
    path("don-hang/", views.orders_list, name="orders_list"),
    path("don-hang/<int:order_id>/", views.order_detail, name="order_detail"),
    path("vi/", views.wallet_view, name="wallet_view"),
    path("gio-hang/", views.cart_view, name="cart_view"),
    path("gio-hang/them/", views.cart_add, name="cart_add"),
    path("gio-hang/cap-nhat/", views.cart_update, name="cart_update"),
    path("gio-hang/xoa/", views.cart_remove, name="cart_remove"),
    path("gio-hang/chon/", views.cart_select, name="cart_select"),
    path("mua-ngay/chuan-bi/", views.buy_now_prepare, name="buy_now_prepare"),
]
