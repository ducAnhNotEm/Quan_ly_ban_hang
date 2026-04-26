from django.urls import path

from orders import views

urlpatterns = [
    path("gio-hang/", views.cart_view, name="cart_view"),
    path("gio-hang/them/", views.cart_add, name="cart_add"),
    path("gio-hang/cap-nhat/", views.cart_update, name="cart_update"),
    path("gio-hang/xoa/", views.cart_remove, name="cart_remove"),
    path("gio-hang/chon/", views.cart_select, name="cart_select"),
    path("mua-ngay/chuan-bi/", views.buy_now_prepare, name="buy_now_prepare"),
]
