"""Database initialization and connection management."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
CURRENT_SCHEMA_VERSION = 1


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _has_schema_version_table(conn: sqlite3.Connection) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    return cursor.fetchone() is not None


def migrate(conn: sqlite3.Connection) -> int:
    """Apply schema migrations. Returns the current schema version."""
    if _has_schema_version_table(conn):
        row = conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ).fetchone()
        if row and row[0] >= CURRENT_SCHEMA_VERSION:
            return row[0]

    # Apply initial schema
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)

    # Record version (use INSERT OR IGNORE to be idempotent)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (CURRENT_SCHEMA_VERSION,),
    )
    conn.commit()
    return CURRENT_SCHEMA_VERSION


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the database: create file, apply schema, return connection."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    migrate(conn)
    return conn
