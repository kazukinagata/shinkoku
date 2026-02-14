"""Ledger management tools for the shinkoku MCP server."""

from __future__ import annotations

import sqlite3

from shinkoku.db import init_db, get_connection
from shinkoku.duplicate_detection import check_duplicate_on_insert, find_duplicate_pairs
from shinkoku.hashing import compute_journal_hash
from shinkoku.master_accounts import MASTER_ACCOUNTS
from shinkoku.models import (
    BusinessWithholdingInput,
    HousingLoanDetailInput,
    JournalEntry,
    JournalSearchParams,
    LossCarryforwardInput,
    MedicalExpenseInput,
    RentDetailInput,
)


def register(mcp) -> None:
    """Register ledger tools with the MCP server."""

    @mcp.tool()
    def mcp_ledger_init(fiscal_year: int, db_path: str) -> dict:
        """Initialize a ledger database for the given fiscal year."""
        return ledger_init(fiscal_year=fiscal_year, db_path=db_path)

    @mcp.tool()
    def mcp_ledger_add_journal(
        db_path: str, fiscal_year: int, entry: dict, force: bool = False
    ) -> dict:
        """Add a single journal entry."""
        parsed = JournalEntry(**entry)
        return ledger_add_journal(
            db_path=db_path, fiscal_year=fiscal_year, entry=parsed, force=force
        )

    @mcp.tool()
    def mcp_ledger_add_journals_batch(
        db_path: str,
        fiscal_year: int,
        entries: list[dict],
        force: bool = False,
    ) -> dict:
        """Add multiple journal entries in a single transaction."""
        parsed = [JournalEntry(**e) for e in entries]
        return ledger_add_journals_batch(
            db_path=db_path, fiscal_year=fiscal_year, entries=parsed, force=force
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
            db_path=db_path,
            journal_id=journal_id,
            fiscal_year=fiscal_year,
            entry=parsed,
        )

    @mcp.tool()
    def mcp_ledger_delete_journal(db_path: str, journal_id: int) -> dict:
        """Delete a journal entry and its lines."""
        return ledger_delete_journal(db_path=db_path, journal_id=journal_id)

    @mcp.tool()
    def mcp_ledger_trial_balance(db_path: str, fiscal_year: int) -> dict:
        """Generate trial balance for a fiscal year."""
        return ledger_trial_balance(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_pl(db_path: str, fiscal_year: int) -> dict:
        """Generate profit and loss statement."""
        return ledger_pl(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_bs(db_path: str, fiscal_year: int) -> dict:
        """Generate balance sheet."""
        return ledger_bs(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_check_duplicates(db_path: str, fiscal_year: int, threshold: int = 70) -> dict:
        """Scan all journals for duplicate pairs."""
        return ledger_check_duplicates(
            db_path=db_path, fiscal_year=fiscal_year, threshold=threshold
        )

    # --- Business Withholding CRUD ---

    @mcp.tool()
    def mcp_ledger_add_business_withholding(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a per-client business withholding entry."""
        parsed = BusinessWithholdingInput(**detail)
        return ledger_add_business_withholding(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_business_withholding(db_path: str, fiscal_year: int) -> dict:
        """List all per-client business withholding entries for a fiscal year."""
        return ledger_list_business_withholding(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_business_withholding(db_path: str, withholding_id: int) -> dict:
        """Delete a business withholding entry."""
        return ledger_delete_business_withholding(db_path=db_path, withholding_id=withholding_id)

    # --- Loss Carryforward CRUD ---

    @mcp.tool()
    def mcp_ledger_add_loss_carryforward(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a loss carryforward entry."""
        parsed = LossCarryforwardInput(**detail)
        return ledger_add_loss_carryforward(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_loss_carryforward(db_path: str, fiscal_year: int) -> dict:
        """List all loss carryforward entries for a fiscal year."""
        return ledger_list_loss_carryforward(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_loss_carryforward(db_path: str, loss_carryforward_id: int) -> dict:
        """Delete a loss carryforward entry."""
        return ledger_delete_loss_carryforward(
            db_path=db_path, loss_carryforward_id=loss_carryforward_id
        )

    # --- Medical Expense Details CRUD ---

    @mcp.tool()
    def mcp_ledger_add_medical_expense(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a medical expense detail entry."""
        parsed = MedicalExpenseInput(**detail)
        return ledger_add_medical_expense(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_medical_expenses(db_path: str, fiscal_year: int) -> dict:
        """List all medical expense details for a fiscal year."""
        return ledger_list_medical_expenses(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_medical_expense(db_path: str, medical_expense_id: int) -> dict:
        """Delete a medical expense detail entry."""
        return ledger_delete_medical_expense(db_path=db_path, medical_expense_id=medical_expense_id)

    # --- Rent Details CRUD ---

    @mcp.tool()
    def mcp_ledger_add_rent_detail(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a rent payment detail entry."""
        parsed = RentDetailInput(**detail)
        return ledger_add_rent_detail(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_rent_details(db_path: str, fiscal_year: int) -> dict:
        """List all rent payment details for a fiscal year."""
        return ledger_list_rent_details(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_rent_detail(db_path: str, rent_detail_id: int) -> dict:
        """Delete a rent payment detail entry."""
        return ledger_delete_rent_detail(db_path=db_path, rent_detail_id=rent_detail_id)

    # --- Housing Loan Details CRUD ---

    @mcp.tool()
    def mcp_ledger_add_housing_loan_detail(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a housing loan detail entry for a fiscal year."""
        parsed = HousingLoanDetailInput(**detail)
        return ledger_add_housing_loan_detail(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_housing_loan_details(db_path: str, fiscal_year: int) -> dict:
        """List all housing loan details for a fiscal year."""
        return ledger_list_housing_loan_details(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_housing_loan_detail(db_path: str, housing_loan_detail_id: int) -> dict:
        """Delete a housing loan detail entry."""
        return ledger_delete_housing_loan_detail(
            db_path=db_path, housing_loan_detail_id=housing_loan_detail_id
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

        accounts_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]

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
    row = conn.execute("SELECT year FROM fiscal_years WHERE year = ?", (fiscal_year,)).fetchone()
    if row is None:
        return f"Fiscal year {fiscal_year} not found"

    # Check debit == credit balance
    debit_total = sum(line.amount for line in entry.lines if line.side == "debit")
    credit_total = sum(line.amount for line in entry.lines if line.side == "credit")
    if debit_total != credit_total:
        return f"Debit/credit not balanced: debit={debit_total}, credit={credit_total}"

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
    *,
    db_path: str,
    fiscal_year: int,
    entry: JournalEntry,
    force: bool = False,
) -> dict:
    """Add a single journal entry to the ledger."""
    conn = get_connection(db_path)
    try:
        error = _validate_journal(conn, fiscal_year, entry)
        if error:
            return {"status": "error", "message": error}

        # 重複チェック
        content_hash = compute_journal_hash(entry.date, entry.lines)
        warning = check_duplicate_on_insert(conn, fiscal_year, entry)
        if warning:
            if warning.match_type == "exact":
                return {
                    "status": "error",
                    "message": warning.reason,
                    "duplicate": warning.model_dump(),
                }
            if warning.match_type == "similar" and not force:
                return {
                    "status": "warning",
                    "message": warning.reason,
                    "duplicate": warning.model_dump(),
                }

        journal_id = _insert_journal_in_transaction(
            conn, fiscal_year, entry, content_hash=content_hash
        )

        conn.commit()
        result: dict = {
            "status": "ok",
            "journal_id": journal_id,
            "fiscal_year": fiscal_year,
        }
        if warning and warning.match_type == "similar" and force:
            result["warnings"] = [warning.model_dump()]
        return result
    finally:
        conn.close()


def _insert_journal_in_transaction(
    conn: sqlite3.Connection,
    fiscal_year: int,
    entry: JournalEntry,
    content_hash: str | None = None,
) -> int:
    """Insert a journal within an existing transaction. Returns journal_id."""
    cursor = conn.execute(
        "INSERT INTO journals "
        "(fiscal_year, date, description, source, source_file, "
        "is_adjustment, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            fiscal_year,
            entry.date,
            entry.description,
            entry.source,
            entry.source_file,
            1 if entry.is_adjustment else 0,
            content_hash,
        ),
    )
    journal_id: int = cursor.lastrowid  # type: ignore[assignment]

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
    *,
    db_path: str,
    fiscal_year: int,
    entries: list[JournalEntry],
    force: bool = False,
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

        # 重複チェック: compute hashes and check within-batch + against DB
        hashes: list[str] = []
        warnings: list[dict] = []
        for i, entry in enumerate(entries):
            h = compute_journal_hash(entry.date, entry.lines)
            # バッチ内重複チェック（完全一致はforce=Trueでも常にブロック）
            if h in hashes:
                dup_idx = hashes.index(h)
                return {
                    "status": "error",
                    "message": (
                        f"Entry {i}: バッチ内で重複しています (Entry {dup_idx} と同一内容)"
                    ),
                    "failed_index": i,
                }
            hashes.append(h)

            # DB重複チェック
            warning = check_duplicate_on_insert(conn, fiscal_year, entry)
            if warning:
                if warning.match_type == "exact":
                    return {
                        "status": "error",
                        "message": f"Entry {i}: {warning.reason}",
                        "failed_index": i,
                        "duplicate": warning.model_dump(),
                    }
                if warning.match_type == "similar" and not force:
                    return {
                        "status": "warning",
                        "message": f"Entry {i}: {warning.reason}",
                        "failed_index": i,
                        "duplicate": warning.model_dump(),
                    }
                if warning.match_type == "similar" and force:
                    warnings.append(
                        {
                            "entry_index": i,
                            **warning.model_dump(),
                        }
                    )

        # Insert all in a single transaction
        journal_ids = []
        for entry, h in zip(entries, hashes):
            jid = _insert_journal_in_transaction(conn, fiscal_year, entry, content_hash=h)
            journal_ids.append(jid)

        conn.commit()
        result: dict = {
            "status": "ok",
            "count": len(journal_ids),
            "journal_ids": journal_ids,
        }
        if warnings:
            result["warnings"] = warnings
        return result
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
        rows = conn.execute(select_sql, bind_params + [params.limit, params.offset]).fetchall()

        journals = []
        for row in rows:
            journal_id = row[0]
            lines = conn.execute(
                "SELECT id, side, account_code, amount, "
                "tax_category, tax_amount "
                "FROM journal_lines WHERE journal_id = ?",
                (journal_id,),
            ).fetchall()

            journals.append(
                {
                    "id": row[0],
                    "fiscal_year": row[1],
                    "date": row[2],
                    "description": row[3],
                    "source": row[4],
                    "source_file": row[5],
                    "is_adjustment": bool(row[6]),
                    "lines": [
                        {
                            "id": li[0],
                            "side": li[1],
                            "account_code": li[2],
                            "amount": li[3],
                            "tax_category": li[4],
                            "tax_amount": li[5],
                        }
                        for li in lines
                    ],
                }
            )

        return {
            "status": "ok",
            "journals": journals,
            "total_count": total_count,
        }
    finally:
        conn.close()


def ledger_update_journal(
    *,
    db_path: str,
    journal_id: int,
    fiscal_year: int,
    entry: JournalEntry,
) -> dict:
    """Update a journal entry (replace lines with re-validation)."""
    conn = get_connection(db_path)
    try:
        # Check journal exists
        row = conn.execute("SELECT id FROM journals WHERE id = ?", (journal_id,)).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Journal {journal_id} not found",
            }

        # Validate the new entry
        error = _validate_journal(conn, fiscal_year, entry)
        if error:
            return {"status": "error", "message": error}

        # content_hash を再計算し、他の仕訳との衝突をチェック
        content_hash = compute_journal_hash(entry.date, entry.lines)
        collision = conn.execute(
            "SELECT id FROM journals WHERE fiscal_year = ? AND content_hash = ? AND id != ?",
            (fiscal_year, content_hash, journal_id),
        ).fetchone()
        if collision:
            return {
                "status": "error",
                "message": f"更新後の内容が既存の仕訳 (ID: {collision[0]}) と一致します",
            }

        # Update journal header
        conn.execute(
            "UPDATE journals SET date=?, description=?, source=?, "
            "source_file=?, is_adjustment=?, content_hash=?, "
            "updated_at=datetime('now') WHERE id=?",
            (
                entry.date,
                entry.description,
                entry.source,
                entry.source_file,
                1 if entry.is_adjustment else 0,
                content_hash,
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
        row = conn.execute("SELECT id FROM journals WHERE id = ?", (journal_id,)).fetchone()
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


def ledger_check_duplicates(*, db_path: str, fiscal_year: int, threshold: int = 70) -> dict:
    """Scan all journals in a fiscal year for potential duplicates."""
    conn = get_connection(db_path)
    try:
        result = find_duplicate_pairs(conn, fiscal_year, threshold)
        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            **result.model_dump(),
        }
    finally:
        conn.close()


def ledger_trial_balance(*, db_path: str, fiscal_year: int) -> dict:
    """Generate trial balance: aggregate debits/credits by account."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT a.code, a.name, a.category, "
            "COALESCE(SUM(CASE WHEN jl.side='debit' THEN jl.amount ELSE 0 END), 0) "
            "AS debit_total, "
            "COALESCE(SUM(CASE WHEN jl.side='credit' THEN jl.amount ELSE 0 END), 0) "
            "AS credit_total "
            "FROM journal_lines jl "
            "INNER JOIN journals j ON j.id = jl.journal_id "
            "INNER JOIN accounts a ON a.code = jl.account_code "
            "WHERE j.fiscal_year = ? "
            "GROUP BY a.code, a.name, a.category "
            "ORDER BY a.code",
            (fiscal_year,),
        ).fetchall()

        accounts = []
        total_debit = 0
        total_credit = 0
        for row in rows:
            debit = row[3]
            credit = row[4]
            balance = debit - credit
            accounts.append(
                {
                    "account_code": row[0],
                    "account_name": row[1],
                    "category": row[2],
                    "debit_total": debit,
                    "credit_total": credit,
                    "balance": balance,
                }
            )
            total_debit += debit
            total_credit += credit

        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "accounts": accounts,
            "total_debit": total_debit,
            "total_credit": total_credit,
        }
    finally:
        conn.close()


def ledger_pl(*, db_path: str, fiscal_year: int) -> dict:
    """Generate profit and loss statement (revenue 4xxx - expense 5xxx)."""
    conn = get_connection(db_path)
    try:
        # Revenue accounts (4xxx): credit - debit = net revenue
        rev_rows = conn.execute(
            "SELECT a.code, a.name, "
            "COALESCE(SUM(CASE WHEN jl.side='credit' THEN jl.amount ELSE 0 END), 0) - "
            "COALESCE(SUM(CASE WHEN jl.side='debit' THEN jl.amount ELSE 0 END), 0) "
            "AS amount "
            "FROM journal_lines jl "
            "INNER JOIN journals j ON j.id = jl.journal_id "
            "INNER JOIN accounts a ON a.code = jl.account_code "
            "WHERE j.fiscal_year = ? AND a.category = 'revenue' "
            "GROUP BY a.code, a.name "
            "HAVING amount != 0 "
            "ORDER BY a.code",
            (fiscal_year,),
        ).fetchall()

        # Expense accounts (5xxx): debit - credit = net expense
        exp_rows = conn.execute(
            "SELECT a.code, a.name, "
            "COALESCE(SUM(CASE WHEN jl.side='debit' THEN jl.amount ELSE 0 END), 0) - "
            "COALESCE(SUM(CASE WHEN jl.side='credit' THEN jl.amount ELSE 0 END), 0) "
            "AS amount "
            "FROM journal_lines jl "
            "INNER JOIN journals j ON j.id = jl.journal_id "
            "INNER JOIN accounts a ON a.code = jl.account_code "
            "WHERE j.fiscal_year = ? AND a.category = 'expense' "
            "GROUP BY a.code, a.name "
            "HAVING amount != 0 "
            "ORDER BY a.code",
            (fiscal_year,),
        ).fetchall()

        revenues = [{"account_code": r[0], "account_name": r[1], "amount": r[2]} for r in rev_rows]
        expenses = [{"account_code": r[0], "account_name": r[1], "amount": r[2]} for r in exp_rows]

        total_revenue = sum(r["amount"] for r in revenues)
        total_expense = sum(e["amount"] for e in expenses)
        net_income = total_revenue - total_expense

        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "revenues": revenues,
            "expenses": expenses,
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_income": net_income,
        }
    finally:
        conn.close()


def ledger_bs(*, db_path: str, fiscal_year: int) -> dict:
    """Generate balance sheet.

    Assets (1xxx) = Liabilities (2xxx) + Equity (3xxx) + Net Income.
    Net income is computed from PL (revenue - expense).
    """
    conn = get_connection(db_path)
    try:

        def _get_balances(category: str, normal_side: str) -> list[dict]:
            """Get net balances for accounts in a category."""
            if normal_side == "debit":
                expr = (
                    "COALESCE(SUM(CASE WHEN jl.side='debit' "
                    "THEN jl.amount ELSE 0 END), 0) - "
                    "COALESCE(SUM(CASE WHEN jl.side='credit' "
                    "THEN jl.amount ELSE 0 END), 0)"
                )
            else:
                expr = (
                    "COALESCE(SUM(CASE WHEN jl.side='credit' "
                    "THEN jl.amount ELSE 0 END), 0) - "
                    "COALESCE(SUM(CASE WHEN jl.side='debit' "
                    "THEN jl.amount ELSE 0 END), 0)"
                )
            rows = conn.execute(
                f"SELECT a.code, a.name, {expr} AS amount "
                "FROM journal_lines jl "
                "INNER JOIN journals j ON j.id = jl.journal_id "
                "INNER JOIN accounts a ON a.code = jl.account_code "
                "WHERE j.fiscal_year = ? AND a.category = ? "
                "GROUP BY a.code, a.name "
                "HAVING amount != 0 "
                "ORDER BY a.code",
                (fiscal_year, category),
            ).fetchall()
            return [{"account_code": r[0], "account_name": r[1], "amount": r[2]} for r in rows]

        assets = _get_balances("asset", "debit")
        liabilities = _get_balances("liability", "credit")
        equity = _get_balances("equity", "credit")

        total_assets = sum(a["amount"] for a in assets)
        total_liabilities = sum(li["amount"] for li in liabilities)
        total_equity_accounts = sum(e["amount"] for e in equity)

        # Compute net income from PL to include in equity
        # (revenue credit - revenue debit) - (expense debit - expense credit)
        rev_net = (
            conn.execute(
                "SELECT COALESCE(SUM(CASE WHEN jl.side='credit' "
                "THEN jl.amount ELSE 0 END), 0) - "
                "COALESCE(SUM(CASE WHEN jl.side='debit' "
                "THEN jl.amount ELSE 0 END), 0) "
                "FROM journal_lines jl "
                "INNER JOIN journals j ON j.id = jl.journal_id "
                "INNER JOIN accounts a ON a.code = jl.account_code "
                "WHERE j.fiscal_year = ? AND a.category = 'revenue'",
                (fiscal_year,),
            ).fetchone()[0]
            or 0
        )

        exp_net = (
            conn.execute(
                "SELECT COALESCE(SUM(CASE WHEN jl.side='debit' "
                "THEN jl.amount ELSE 0 END), 0) - "
                "COALESCE(SUM(CASE WHEN jl.side='credit' "
                "THEN jl.amount ELSE 0 END), 0) "
                "FROM journal_lines jl "
                "INNER JOIN journals j ON j.id = jl.journal_id "
                "INNER JOIN accounts a ON a.code = jl.account_code "
                "WHERE j.fiscal_year = ? AND a.category = 'expense'",
                (fiscal_year,),
            ).fetchone()[0]
            or 0
        )

        net_income = rev_net - exp_net
        total_equity = total_equity_accounts + net_income

        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "net_income": net_income,
        }
    finally:
        conn.close()


# ============================================================
# 地代家賃の内訳 (Rent Details)
# ============================================================


def ledger_add_rent_detail(*, db_path: str, fiscal_year: int, detail: RentDetailInput) -> dict:
    """Add a rent payment detail entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO rent_details "
            "(fiscal_year, property_type, usage, landlord_name, landlord_address, "
            "monthly_rent, annual_rent, deposit, business_ratio) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.property_type,
                detail.usage,
                detail.landlord_name,
                detail.landlord_address,
                detail.monthly_rent,
                detail.annual_rent,
                detail.deposit,
                detail.business_ratio,
            ),
        )
        conn.commit()
        return {
            "status": "ok",
            "rent_detail_id": cursor.lastrowid,
            "fiscal_year": fiscal_year,
        }
    finally:
        conn.close()


def ledger_list_rent_details(*, db_path: str, fiscal_year: int) -> dict:
    """List all rent payment details for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, property_type, usage, landlord_name, "
            "landlord_address, monthly_rent, annual_rent, deposit, business_ratio "
            "FROM rent_details WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        details = [
            {
                "id": r[0],
                "fiscal_year": r[1],
                "property_type": r[2],
                "usage": r[3],
                "landlord_name": r[4],
                "landlord_address": r[5],
                "monthly_rent": r[6],
                "annual_rent": r[7],
                "deposit": r[8],
                "business_ratio": r[9],
            }
            for r in rows
        ]
        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "count": len(details),
            "details": details,
        }
    finally:
        conn.close()


def ledger_delete_rent_detail(*, db_path: str, rent_detail_id: int) -> dict:
    """Delete a rent payment detail entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT id FROM rent_details WHERE id = ?", (rent_detail_id,)).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Rent detail {rent_detail_id} not found",
            }
        conn.execute("DELETE FROM rent_details WHERE id = ?", (rent_detail_id,))
        conn.commit()
        return {"status": "ok", "rent_detail_id": rent_detail_id}
    finally:
        conn.close()


# ============================================================
# 事業所得の源泉徴収 (Business Withholding)
# ============================================================


def ledger_add_business_withholding(
    *, db_path: str, fiscal_year: int, detail: BusinessWithholdingInput
) -> dict:
    """Add a per-client business withholding entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO business_withholding "
            "(fiscal_year, client_name, gross_amount, withholding_tax) "
            "VALUES (?, ?, ?, ?)",
            (
                fiscal_year,
                detail.client_name,
                detail.gross_amount,
                detail.withholding_tax,
            ),
        )
        conn.commit()
        return {
            "status": "ok",
            "withholding_id": cursor.lastrowid,
            "fiscal_year": fiscal_year,
        }
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return {
                "status": "error",
                "message": f"取引先 '{detail.client_name}' は既に登録されています",
            }
        raise
    finally:
        conn.close()


def ledger_list_business_withholding(*, db_path: str, fiscal_year: int) -> dict:
    """List all per-client business withholding entries for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, client_name, gross_amount, withholding_tax "
            "FROM business_withholding WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        details = [
            {
                "id": r[0],
                "fiscal_year": r[1],
                "client_name": r[2],
                "gross_amount": r[3],
                "withholding_tax": r[4],
            }
            for r in rows
        ]
        total_gross = sum(d["gross_amount"] for d in details)
        total_withholding = sum(d["withholding_tax"] for d in details)
        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "count": len(details),
            "total_gross_amount": total_gross,
            "total_withholding_tax": total_withholding,
            "details": details,
        }
    finally:
        conn.close()


def ledger_delete_business_withholding(*, db_path: str, withholding_id: int) -> dict:
    """Delete a business withholding entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM business_withholding WHERE id = ?", (withholding_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Business withholding {withholding_id} not found",
            }
        conn.execute("DELETE FROM business_withholding WHERE id = ?", (withholding_id,))
        conn.commit()
        return {"status": "ok", "withholding_id": withholding_id}
    finally:
        conn.close()


# ============================================================
# 損失繰越 (Loss Carryforward)
# ============================================================


def ledger_add_loss_carryforward(
    *, db_path: str, fiscal_year: int, detail: LossCarryforwardInput
) -> dict:
    """Add a loss carryforward entry."""
    conn = get_connection(db_path)
    try:
        # 青色申告の3年繰越チェック
        if detail.loss_year < fiscal_year - 3:
            return {
                "status": "error",
                "message": (
                    f"繰越損失の対象は過去3年以内です "
                    f"(損失年: {detail.loss_year}, 申告年: {fiscal_year})"
                ),
            }
        cursor = conn.execute(
            "INSERT INTO loss_carryforward "
            "(fiscal_year, loss_year, amount, used_amount) "
            "VALUES (?, ?, ?, 0)",
            (fiscal_year, detail.loss_year, detail.amount),
        )
        conn.commit()
        return {
            "status": "ok",
            "loss_carryforward_id": cursor.lastrowid,
            "fiscal_year": fiscal_year,
        }
    finally:
        conn.close()


def ledger_list_loss_carryforward(*, db_path: str, fiscal_year: int) -> dict:
    """List all loss carryforward entries for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, loss_year, amount, used_amount "
            "FROM loss_carryforward WHERE fiscal_year = ? ORDER BY loss_year",
            (fiscal_year,),
        ).fetchall()
        details = [
            {
                "id": r[0],
                "fiscal_year": r[1],
                "loss_year": r[2],
                "amount": r[3],
                "used_amount": r[4],
                "remaining": r[3] - r[4],
            }
            for r in rows
        ]
        total_amount = sum(d["amount"] for d in details)
        total_remaining = sum(d["remaining"] for d in details)
        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "count": len(details),
            "total_amount": total_amount,
            "total_remaining": total_remaining,
            "details": details,
        }
    finally:
        conn.close()


def ledger_delete_loss_carryforward(*, db_path: str, loss_carryforward_id: int) -> dict:
    """Delete a loss carryforward entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM loss_carryforward WHERE id = ?", (loss_carryforward_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Loss carryforward {loss_carryforward_id} not found",
            }
        conn.execute("DELETE FROM loss_carryforward WHERE id = ?", (loss_carryforward_id,))
        conn.commit()
        return {"status": "ok", "loss_carryforward_id": loss_carryforward_id}
    finally:
        conn.close()


# ============================================================
# 医療費明細 (Medical Expense Details)
# ============================================================


def ledger_add_medical_expense(
    *, db_path: str, fiscal_year: int, detail: MedicalExpenseInput
) -> dict:
    """Add a medical expense detail entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO medical_expense_details "
            "(fiscal_year, date, patient_name, medical_institution, "
            "amount, insurance_reimbursement, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.date,
                detail.patient_name,
                detail.medical_institution,
                detail.amount,
                detail.insurance_reimbursement,
                detail.description,
            ),
        )
        conn.commit()
        return {
            "status": "ok",
            "medical_expense_id": cursor.lastrowid,
            "fiscal_year": fiscal_year,
        }
    finally:
        conn.close()


def ledger_list_medical_expenses(*, db_path: str, fiscal_year: int) -> dict:
    """List all medical expense details for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, date, patient_name, medical_institution, "
            "amount, insurance_reimbursement, description "
            "FROM medical_expense_details WHERE fiscal_year = ? ORDER BY date, id",
            (fiscal_year,),
        ).fetchall()
        details = [
            {
                "id": r[0],
                "fiscal_year": r[1],
                "date": r[2],
                "patient_name": r[3],
                "medical_institution": r[4],
                "amount": r[5],
                "insurance_reimbursement": r[6],
                "description": r[7],
            }
            for r in rows
        ]
        total_amount = sum(d["amount"] for d in details)
        total_reimbursement = sum(d["insurance_reimbursement"] for d in details)
        net_amount = total_amount - total_reimbursement
        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "count": len(details),
            "total_amount": total_amount,
            "total_reimbursement": total_reimbursement,
            "net_amount": net_amount,
            "details": details,
        }
    finally:
        conn.close()


def ledger_delete_medical_expense(*, db_path: str, medical_expense_id: int) -> dict:
    """Delete a medical expense detail entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM medical_expense_details WHERE id = ?", (medical_expense_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Medical expense {medical_expense_id} not found",
            }
        conn.execute("DELETE FROM medical_expense_details WHERE id = ?", (medical_expense_id,))
        conn.commit()
        return {"status": "ok", "medical_expense_id": medical_expense_id}
    finally:
        conn.close()


# ============================================================
# 住宅ローン控除詳細 (Housing Loan Details)
# ============================================================


def ledger_add_housing_loan_detail(
    *, db_path: str, fiscal_year: int, detail: HousingLoanDetailInput
) -> dict:
    """Add a housing loan detail entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO housing_loan_details "
            "(fiscal_year, housing_type, housing_category, move_in_date, "
            "year_end_balance, is_new_construction) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.housing_type,
                detail.housing_category,
                detail.move_in_date,
                detail.year_end_balance,
                1 if detail.is_new_construction else 0,
            ),
        )
        conn.commit()
        return {
            "status": "ok",
            "housing_loan_detail_id": cursor.lastrowid,
            "fiscal_year": fiscal_year,
        }
    finally:
        conn.close()


def ledger_list_housing_loan_details(*, db_path: str, fiscal_year: int) -> dict:
    """List all housing loan details for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, housing_type, housing_category, "
            "move_in_date, year_end_balance, is_new_construction "
            "FROM housing_loan_details WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        details = [
            {
                "id": r[0],
                "fiscal_year": r[1],
                "housing_type": r[2],
                "housing_category": r[3],
                "move_in_date": r[4],
                "year_end_balance": r[5],
                "is_new_construction": bool(r[6]),
            }
            for r in rows
        ]
        return {
            "status": "ok",
            "fiscal_year": fiscal_year,
            "count": len(details),
            "details": details,
        }
    finally:
        conn.close()


def ledger_delete_housing_loan_detail(*, db_path: str, housing_loan_detail_id: int) -> dict:
    """Delete a housing loan detail entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM housing_loan_details WHERE id = ?", (housing_loan_detail_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Housing loan detail {housing_loan_detail_id} not found",
            }
        conn.execute("DELETE FROM housing_loan_details WHERE id = ?", (housing_loan_detail_id,))
        conn.commit()
        return {"status": "ok", "housing_loan_detail_id": housing_loan_detail_id}
    finally:
        conn.close()
