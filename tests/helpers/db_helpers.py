"""Database helper functions for tests."""

import sqlite3

from shinkoku.master_accounts import MASTER_ACCOUNTS


def load_master_accounts(conn: sqlite3.Connection) -> None:
    """Insert all master accounts into the database."""
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.commit()


def insert_fiscal_year(conn: sqlite3.Connection, year: int) -> None:
    """Insert a fiscal year record."""
    conn.execute("INSERT OR IGNORE INTO fiscal_years (year) VALUES (?)", (year,))
    conn.commit()


def insert_journal(
    conn: sqlite3.Connection,
    fiscal_year: int,
    date: str,
    description: str,
    lines: list[tuple[str, str, int]],
    source: str = "manual",
) -> int:
    """Insert a journal entry with lines.

    Args:
        conn: Database connection.
        fiscal_year: Fiscal year.
        date: Journal date (YYYY-MM-DD).
        description: Journal description.
        lines: List of (side, account_code, amount) tuples.
        source: Source of the journal entry.

    Returns:
        The journal ID.
    """
    conn.execute(
        "INSERT INTO journals (fiscal_year, date, description, source) VALUES (?, ?, ?, ?)",
        (fiscal_year, date, description, source),
    )
    journal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for side, account_code, amount in lines:
        conn.execute(
            "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
            "VALUES (?, ?, ?, ?)",
            (journal_id, side, account_code, amount),
        )
    conn.commit()
    return journal_id
