"""
Cấu hình ASGI cho dự án `banhang`.

Biến module-level `application` được máy chủ ASGI sử dụng để phục vụ app.
Tài liệu: https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banhang.settings')

application = get_asgi_application()

