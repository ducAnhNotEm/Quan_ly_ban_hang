from pathlib import Path
from typing import Any

from django.conf import settings
from django.db import connection

SQL_DIR = Path(settings.BASE_DIR) / "sql"


def _read_sql(filename: str) -> str:
    path = SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8-sig")


def fetch_one_dict(filename: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    query = _read_sql(filename)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row, strict=False))


def fetch_all_dicts(filename: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    query = _read_sql(filename)
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row, strict=False)) for row in rows]

