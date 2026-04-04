from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path


def home(request):
    return redirect('login')


def login_view(request):
    return render(request, 'login.html')


def register_view(request):
    return render(request, 'register.html')


urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('admin/', admin.site.urls),
]
