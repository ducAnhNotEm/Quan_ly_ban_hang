"""
Cấu hình WSGI cho dự án `banhang`.

Biến module-level `application` được máy chủ WSGI sử dụng để phục vụ app.
Tài liệu: https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banhang.settings')

application = get_wsgi_application()

