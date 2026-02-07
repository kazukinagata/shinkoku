"""Ledger management tools for the shinkoku MCP server."""

from __future__ import annotations

import sqlite3

from shinkoku.db import init_db, get_connection
from shinkoku.master_accounts import MASTER_ACCOUNTS
from shinkoku.models import JournalEntry, JournalSearchParams


def register(mcp) -> None:
    """Register ledger tools with the MCP server."""

    @mcp.tool()
    def mcp_ledger_init(fiscal_year: int, db_path: str) -> dict:
        """Initialize a ledger database for the given fiscal year."""
        return ledger_init(fiscal_year=fiscal_year, db_path=db_path)

    @mcp.tool()
    def mcp_ledger_add_journal(
        db_path: str, fiscal_year: int, entry: dict
    ) -> dict:
        """Add a single journal entry."""
        parsed = JournalEntry(**entry)
        return ledger_add_journal(
            db_path=db_path, fiscal_year=fiscal_year, entry=parsed
        )


def ledger_init(*, fiscal_year: int, db_path: str) -> dict:
    """Initialize DB, insert master accounts, create fiscal year."""
    conn = init_db(db_path)
    try:
        # Insert master accounts (idempotent via INSERT OR IGNORE)
        for a in MASTER_ACCOUNTS:
            conn.execute(
                "INSERT OR IGNORE INTO accounts "
                "(code, name, category, sub_category, tax_category) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    a["code"],
                    a["name"],
                    a["category"],
                    a["sub_category"],
                    a.get("tax_category"),
                ),
            )
        # Insert fiscal year (idempotent)
        conn.execute(
            "INSERT OR IGNORE INTO fiscal_years (year) VALUES (?)",
            (fiscal_year,),
        )
        conn.commit()

        accounts_count = conn.execute(
            "SELECT COUNT(*) FROM accounts"
        ).fetchone()[0]

        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "accounts_loaded": accounts_count,
            "db_path": db_path,
        }
    finally:
        conn.close()


def _validate_journal(
    conn: sqlite3.Connection, fiscal_year: int, entry: JournalEntry
) -> str | None:
    """Validate a journal entry. Returns error message or None."""
    # Check fiscal year exists
    row = conn.execute(
        "SELECT year FROM fiscal_years WHERE year = ?", (fiscal_year,)
    ).fetchone()
    if row is None:
        return f"Fiscal year {fiscal_year} not found"

    # Check debit == credit balance
    debit_total = sum(
        line.amount for line in entry.lines if line.side == "debit"
    )
    credit_total = sum(
        line.amount for line in entry.lines if line.side == "credit"
    )
    if debit_total != credit_total:
        return (
            f"Debit/credit not balanced: "
            f"debit={debit_total}, credit={credit_total}"
        )

    # Check all account codes exist
    for line in entry.lines:
        row = conn.execute(
            "SELECT code FROM accounts WHERE code = ?",
            (line.account_code,),
        ).fetchone()
        if row is None:
            return f"Account code not found: {line.account_code}"

    return None


def ledger_add_journal(
    *, db_path: str, fiscal_year: int, entry: JournalEntry
) -> dict:
    """Add a single journal entry to the ledger."""
    conn = get_connection(db_path)
    try:
        error = _validate_journal(conn, fiscal_year, entry)
        if error:
            return {"status": "error", "message": error}

        conn.execute(
            "INSERT INTO journals "
            "(fiscal_year, date, description, source, source_file, "
            "is_adjustment) VALUES (?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                entry.date,
                entry.description,
                entry.source,
                entry.source_file,
                1 if entry.is_adjustment else 0,
            ),
        )
        journal_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        for line in entry.lines:
            conn.execute(
                "INSERT INTO journal_lines "
                "(journal_id, side, account_code, amount, "
                "tax_category, tax_amount) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    journal_id,
                    line.side,
                    line.account_code,
                    line.amount,
                    line.tax_category,
                    line.tax_amount,
                ),
            )

        conn.commit()
        return {
            "status": "ok",
            "journal_id": journal_id,
            "fiscal_year": fiscal_year,
        }
    finally:
        conn.close()
