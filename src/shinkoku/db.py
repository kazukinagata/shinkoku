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

    # housing_loan_details: 重複適用（中古購入＋リフォーム同時）対応カラム追加
    hl_cols = {row[1] for row in conn.execute("PRAGMA table_info(housing_loan_details)").fetchall()}
    if "dual_application_group" not in hl_cols:
        conn.execute("ALTER TABLE housing_loan_details ADD COLUMN dual_application_group TEXT")
    if "cost_for_proration" not in hl_cols:
        conn.execute(
            "ALTER TABLE housing_loan_details "
            "ADD COLUMN cost_for_proration INTEGER NOT NULL DEFAULT 0"
        )
