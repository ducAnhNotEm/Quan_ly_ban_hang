from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import connection

SQL_DIR = Path(settings.BASE_DIR) / "sql"


"""
Helper truy vấn SQL thuần từ file `.sql`.

Mục tiêu:
- Tách query SQL khỏi code Python để dễ bảo trì.
- Đồng nhất kiểu dữ liệu trả về dạng dict.
- Hạn chế lặp lại boilerplate cursor/columns mapping.
"""


def _read_sql(filename: str) -> str:
    """
    Đọc nội dung file SQL từ thư mục `sql/`.

    Luồng:
    1) Nối `SQL_DIR` + `filename`.
    2) Kiểm tra tồn tại file.
    3) Đọc text với `utf-8-sig` để tự động bỏ BOM nếu có.
    """
    path = SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8-sig")


def fetch_one_dict(filename: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    """
    Thực thi query và lấy 1 dòng kết quả đầu tiên dưới dạng dict.

    Luồng:
    1) Đọc query từ file SQL.
    2) Execute query với `params`.
    3) Nếu không có kết quả -> trả `None`.
    4) Nếu có kết quả -> map tên cột sang giá trị và trả dict.
    """
    query = _read_sql(filename)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row, strict=False))


def fetch_all_dicts(filename: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    """
    Thực thi query và lấy toàn bộ kết quả dưới dạng list[dict].

    Luồng:
    1) Đọc query từ file SQL.
    2) Execute query với params.
    3) Fetch tất cả row.
    4) Map tên cột sang giá trị cho mỗi row.
    """
    query = _read_sql(filename)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row, strict=False)) for row in rows]
