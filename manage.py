#!/usr/bin/env python
"""Tiện ích dòng lệnh của Django cho các tác vụ quản trị."""
import os
import sys


def main():
    """
    Chạy lệnh Django theo tham số từ dòng lệnh.

    Luồng xử lý:
    1) Gán biến môi trường `DJANGO_SETTINGS_MODULE` nếu chưa có.
    2) Import hàm `execute_from_command_line` của Django.
    3) Đẩy toàn bộ `sys.argv` vào Django để thực thi lệnh
       (ví dụ: `runserver`, `migrate`, `test`, ...).
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banhang.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
