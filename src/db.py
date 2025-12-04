from __future__ import annotations

import sqlite3
from pathlib import Path

from src.settings import settings


DB_PATH = Path(settings.db_path)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row factory as dict-like rows."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection
