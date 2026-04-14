"""
Cấu hình Django cho dự án `banhang`.

File này được tạo từ lệnh `django-admin startproject` (Django 6.0.3).
Tài liệu tham khảo:
- https://docs.djangoproject.com/en/6.0/topics/settings/
- https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import os
from pathlib import Path

# Route gốc của dự án, dùng để ghép các route con.
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(env_path: Path) -> None:
    """Nạp các cặp `key=value` từ file `.env` vào `os.environ`."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(BASE_DIR / '.env')


# Cấu hình khởi tạo nhanh cho môi trường phát triển (không dùng cho production).
# Xem thêm: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# CẢNH BÁO BẢO MẬT: phải giữ bí mật khóa SECRET_KEY khi triển khai thật.
SECRET_KEY = 'django-insecure-pq2e+-4#jy+6==6!s-53xj!!)!fzfx5^5_w%o01sf!rto$w(a='

# CẢNH BÁO BẢO MẬT: không bật DEBUG trong môi trường production.
DEBUG = True

ALLOWED_HOSTS = []


# Khai báo app cài đặt trong dự án.

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'products',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'banhang.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'banhang.wsgi.application'


# Cấu hình cơ sở dữ liệu.
# Xem thêm: https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'quan_ly_ban_hang_db'),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'),
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


# Cấu hình kiểm tra độ mạnh mật khẩu.
# Xem thêm: https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Cấu hình ngôn ngữ và múi giờ.
# Xem thêm: https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Cấu hình file tĩnh (CSS, JavaScript, hình ảnh).
# Xem thêm: https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

