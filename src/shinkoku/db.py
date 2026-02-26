"""Database initialization and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the database: create file, apply schema, return connection."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    _migrate(conn)
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """既存DBに新しいカラム・テーブルを追加するマイグレーション。"""
    # journals.counterparty カラム追加（電帳法 検索機能要件: 取引先検索）
    cols = {row[1] for row in conn.execute("PRAGMA table_info(journals)").fetchall()}
    if "counterparty" not in cols:
        conn.execute("ALTER TABLE journals ADD COLUMN counterparty TEXT")
