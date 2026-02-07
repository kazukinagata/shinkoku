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

    @mcp.tool()
    def mcp_ledger_add_journals_batch(
        db_path: str, fiscal_year: int, entries: list[dict]
    ) -> dict:
        """Add multiple journal entries in a single transaction."""
        parsed = [JournalEntry(**e) for e in entries]
        return ledger_add_journals_batch(
            db_path=db_path, fiscal_year=fiscal_year, entries=parsed
        )

    @mcp.tool()
    def mcp_ledger_search(db_path: str, params: dict) -> dict:
        """Search journal entries with filters and pagination."""
        parsed = JournalSearchParams(**params)
        return ledger_search(db_path=db_path, params=parsed)

    @mcp.tool()
    def mcp_ledger_update_journal(
        db_path: str, journal_id: int, fiscal_year: int, entry: dict
    ) -> dict:
        """Update a journal entry with re-validation."""
        parsed = JournalEntry(**entry)
        return ledger_update_journal(
            db_path=db_path, journal_id=journal_id,
            fiscal_year=fiscal_year, entry=parsed,
        )

    @mcp.tool()
    def mcp_ledger_delete_journal(
        db_path: str, journal_id: int
    ) -> dict:
        """Delete a journal entry and its lines."""
        return ledger_delete_journal(
            db_path=db_path, journal_id=journal_id
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


def _insert_journal_in_transaction(
    conn: sqlite3.Connection, fiscal_year: int, entry: JournalEntry
) -> int:
    """Insert a journal within an existing transaction. Returns journal_id."""
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
    journal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

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
    return journal_id


def ledger_add_journals_batch(
    *, db_path: str, fiscal_year: int, entries: list[JournalEntry]
) -> dict:
    """Add multiple journal entries in a single transaction.

    All-or-nothing: if any entry is invalid, all are rolled back.
    """
    if not entries:
        return {"status": "ok", "count": 0, "journal_ids": []}

    conn = get_connection(db_path)
    try:
        # Validate all entries first
        for i, entry in enumerate(entries):
            error = _validate_journal(conn, fiscal_year, entry)
            if error:
                return {
                    "status": "error",
                    "message": f"Entry {i}: {error}",
                    "failed_index": i,
                }

        # Insert all in a single transaction
        journal_ids = []
        for entry in entries:
            jid = _insert_journal_in_transaction(conn, fiscal_year, entry)
            journal_ids.append(jid)

        conn.commit()
        return {
            "status": "ok",
            "count": len(journal_ids),
            "journal_ids": journal_ids,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ledger_search(*, db_path: str, params: JournalSearchParams) -> dict:
    """Search journal entries with various filters and pagination."""
    conn = get_connection(db_path)
    try:
        # Build WHERE clause
        conditions = ["j.fiscal_year = ?"]
        bind_params: list = [params.fiscal_year]

        if params.date_from:
            conditions.append("j.date >= ?")
            bind_params.append(params.date_from)
        if params.date_to:
            conditions.append("j.date <= ?")
            bind_params.append(params.date_to)
        if params.description_contains:
            conditions.append("j.description LIKE ?")
            bind_params.append(f"%{params.description_contains}%")
        if params.source:
            conditions.append("j.source = ?")
            bind_params.append(params.source)

        where_clause = " AND ".join(conditions)

        # If filtering by account_code, join journal_lines
        if params.account_code:
            base_query = (
                "FROM journals j "
                "INNER JOIN journal_lines jl ON jl.journal_id = j.id "
                f"WHERE {where_clause} AND jl.account_code = ?"
            )
            bind_params.append(params.account_code)
        else:
            base_query = f"FROM journals j WHERE {where_clause}"

        # Count total
        count_sql = f"SELECT COUNT(DISTINCT j.id) {base_query}"
        total_count = conn.execute(count_sql, bind_params).fetchone()[0]

        # Fetch journal IDs with pagination
        select_sql = (
            f"SELECT DISTINCT j.id, j.fiscal_year, j.date, "
            f"j.description, j.source, j.source_file, j.is_adjustment "
            f"{base_query} "
            f"ORDER BY j.date, j.id "
            f"LIMIT ? OFFSET ?"
        )
        rows = conn.execute(
            select_sql, bind_params + [params.limit, params.offset]
        ).fetchall()

        journals = []
        for row in rows:
            journal_id = row[0]
            lines = conn.execute(
                "SELECT id, side, account_code, amount, "
                "tax_category, tax_amount "
                "FROM journal_lines WHERE journal_id = ?",
                (journal_id,),
            ).fetchall()

            journals.append({
                "id": row[0],
                "fiscal_year": row[1],
                "date": row[2],
                "description": row[3],
                "source": row[4],
                "source_file": row[5],
                "is_adjustment": bool(row[6]),
                "lines": [
                    {
                        "id": l[0],
                        "side": l[1],
                        "account_code": l[2],
                        "amount": l[3],
                        "tax_category": l[4],
                        "tax_amount": l[5],
                    }
                    for l in lines
                ],
            })

        return {
            "status": "ok",
            "journals": journals,
            "total_count": total_count,
        }
    finally:
        conn.close()


def ledger_update_journal(
    *, db_path: str, journal_id: int, fiscal_year: int,
    entry: JournalEntry,
) -> dict:
    """Update a journal entry (replace lines with re-validation)."""
    conn = get_connection(db_path)
    try:
        # Check journal exists
        row = conn.execute(
            "SELECT id FROM journals WHERE id = ?", (journal_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Journal {journal_id} not found",
            }

        # Validate the new entry
        error = _validate_journal(conn, fiscal_year, entry)
        if error:
            return {"status": "error", "message": error}

        # Update journal header
        conn.execute(
            "UPDATE journals SET date=?, description=?, source=?, "
            "source_file=?, is_adjustment=?, "
            "updated_at=datetime('now') WHERE id=?",
            (
                entry.date,
                entry.description,
                entry.source,
                entry.source_file,
                1 if entry.is_adjustment else 0,
                journal_id,
            ),
        )

        # Delete old lines (CASCADE would handle this, but explicit)
        conn.execute(
            "DELETE FROM journal_lines WHERE journal_id = ?",
            (journal_id,),
        )

        # Insert new lines
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
        return {"status": "ok", "journal_id": journal_id}
    finally:
        conn.close()


def ledger_delete_journal(*, db_path: str, journal_id: int) -> dict:
    """Delete a journal entry and its lines (CASCADE)."""
    conn = get_connection(db_path)
    try:
        # Check journal exists
        row = conn.execute(
            "SELECT id FROM journals WHERE id = ?", (journal_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Journal {journal_id} not found",
            }

        # Delete (journal_lines will CASCADE)
        conn.execute("DELETE FROM journals WHERE id = ?", (journal_id,))
        conn.commit()
        return {"status": "ok", "journal_id": journal_id}
    finally:
        conn.close()
