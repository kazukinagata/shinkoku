"""Ledger management tools for the shinkoku MCP server."""

from __future__ import annotations

import sqlite3

from shinkoku.db import init_db, get_connection
from shinkoku.duplicate_detection import check_duplicate_on_insert, find_duplicate_pairs
from shinkoku.hashing import compute_journal_hash
from shinkoku.master_accounts import MASTER_ACCOUNTS
from shinkoku.models import (
    BusinessWithholdingInput,
    CryptoIncomeInput,
    DependentInput,
    FXLossCarryforwardInput,
    FXTradingInput,
    HousingLoanDetailInput,
    InventoryInput,
    JournalEntry,
    JournalSearchParams,
    LossCarryforwardInput,
    MedicalExpenseInput,
    OtherIncomeInput,
    ProfessionalFeeInput,
    RentDetailInput,
    SpouseInput,
    StockLossCarryforwardInput,
    StockTradingAccountInput,
    WithholdingSlipInput,
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

    # --- Spouse CRUD (Phase 2) ---

    @mcp.tool()
    def mcp_ledger_set_spouse(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Set spouse information for a fiscal year (upsert)."""
        parsed = SpouseInput(**detail)
        return ledger_set_spouse(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_get_spouse(db_path: str, fiscal_year: int) -> dict:
        """Get spouse information for a fiscal year."""
        return ledger_get_spouse(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_spouse(db_path: str, fiscal_year: int) -> dict:
        """Delete spouse information for a fiscal year."""
        return ledger_delete_spouse(db_path=db_path, fiscal_year=fiscal_year)

    # --- Dependent CRUD (Phase 2) ---

    @mcp.tool()
    def mcp_ledger_add_dependent(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a dependent for a fiscal year."""
        parsed = DependentInput(**detail)
        return ledger_add_dependent(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_dependents(db_path: str, fiscal_year: int) -> dict:
        """List all dependents for a fiscal year."""
        return ledger_list_dependents(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_dependent(db_path: str, dependent_id: int) -> dict:
        """Delete a dependent entry."""
        return ledger_delete_dependent(db_path=db_path, dependent_id=dependent_id)

    # --- Withholding Slip CRUD (Phase 6) ---

    @mcp.tool()
    def mcp_ledger_save_withholding_slip(
        db_path: str, fiscal_year: int, detail: dict
    ) -> dict:
        """Save a withholding slip (源泉徴収票) with full fields."""
        parsed = WithholdingSlipInput(**detail)
        return ledger_save_withholding_slip(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_withholding_slips(db_path: str, fiscal_year: int) -> dict:
        """List all withholding slips for a fiscal year."""
        return ledger_list_withholding_slips(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_withholding_slip(db_path: str, withholding_slip_id: int) -> dict:
        """Delete a withholding slip entry."""
        return ledger_delete_withholding_slip(
            db_path=db_path, withholding_slip_id=withholding_slip_id
        )

    # --- Other Income CRUD (Phase 10) ---

    @mcp.tool()
    def mcp_ledger_add_other_income(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add an other income item (miscellaneous/dividend/one-time)."""
        parsed = OtherIncomeInput(**detail)
        return ledger_add_other_income(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_other_income(db_path: str, fiscal_year: int) -> dict:
        """List all other income items for a fiscal year."""
        return ledger_list_other_income(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_other_income(db_path: str, other_income_id: int) -> dict:
        """Delete an other income item."""
        return ledger_delete_other_income(db_path=db_path, other_income_id=other_income_id)

    # --- Crypto Income CRUD (Phase 11) ---

    @mcp.tool()
    def mcp_ledger_add_crypto_income(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a crypto income record."""
        parsed = CryptoIncomeInput(**detail)
        return ledger_add_crypto_income(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_crypto_income(db_path: str, fiscal_year: int) -> dict:
        """List all crypto income records for a fiscal year."""
        return ledger_list_crypto_income(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_crypto_income(db_path: str, crypto_income_id: int) -> dict:
        """Delete a crypto income record."""
        return ledger_delete_crypto_income(db_path=db_path, crypto_income_id=crypto_income_id)

    # --- Inventory CRUD (Phase 14) ---

    @mcp.tool()
    def mcp_ledger_set_inventory(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Set inventory record (upsert by fiscal_year + period)."""
        parsed = InventoryInput(**detail)
        return ledger_set_inventory(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_inventory(db_path: str, fiscal_year: int) -> dict:
        """List inventory records for a fiscal year."""
        return ledger_list_inventory(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_inventory(db_path: str, inventory_id: int) -> dict:
        """Delete an inventory record."""
        return ledger_delete_inventory(db_path=db_path, inventory_id=inventory_id)

    # --- Professional Fee CRUD (Phase 15) ---

    @mcp.tool()
    def mcp_ledger_add_professional_fee(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add a professional fee (tax accountant etc.) entry."""
        parsed = ProfessionalFeeInput(**detail)
        return ledger_add_professional_fee(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_professional_fees(db_path: str, fiscal_year: int) -> dict:
        """List all professional fee entries for a fiscal year."""
        return ledger_list_professional_fees(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_professional_fee(db_path: str, professional_fee_id: int) -> dict:
        """Delete a professional fee entry."""
        return ledger_delete_professional_fee(
            db_path=db_path, professional_fee_id=professional_fee_id
        )

    # --- Stock Trading CRUD (Phase 12) ---

    @mcp.tool()
    def mcp_ledger_add_stock_trading_account(
        db_path: str, fiscal_year: int, detail: dict
    ) -> dict:
        """Add a stock trading account entry."""
        parsed = StockTradingAccountInput(**detail)
        return ledger_add_stock_trading_account(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_stock_trading_accounts(db_path: str, fiscal_year: int) -> dict:
        """List all stock trading accounts for a fiscal year."""
        return ledger_list_stock_trading_accounts(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_stock_trading_account(
        db_path: str, stock_trading_account_id: int
    ) -> dict:
        """Delete a stock trading account entry."""
        return ledger_delete_stock_trading_account(
            db_path=db_path, stock_trading_account_id=stock_trading_account_id
        )

    @mcp.tool()
    def mcp_ledger_add_stock_loss_carryforward(
        db_path: str, fiscal_year: int, detail: dict
    ) -> dict:
        """Add a stock loss carryforward entry."""
        parsed = StockLossCarryforwardInput(**detail)
        return ledger_add_stock_loss_carryforward(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_stock_loss_carryforward(db_path: str, fiscal_year: int) -> dict:
        """List all stock loss carryforward entries for a fiscal year."""
        return ledger_list_stock_loss_carryforward(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_stock_loss_carryforward(
        db_path: str, stock_loss_carryforward_id: int
    ) -> dict:
        """Delete a stock loss carryforward entry."""
        return ledger_delete_stock_loss_carryforward(
            db_path=db_path, stock_loss_carryforward_id=stock_loss_carryforward_id
        )

    # --- FX Trading CRUD (Phase 13) ---

    @mcp.tool()
    def mcp_ledger_add_fx_trading(db_path: str, fiscal_year: int, detail: dict) -> dict:
        """Add an FX trading record."""
        parsed = FXTradingInput(**detail)
        return ledger_add_fx_trading(db_path=db_path, fiscal_year=fiscal_year, detail=parsed)

    @mcp.tool()
    def mcp_ledger_list_fx_trading(db_path: str, fiscal_year: int) -> dict:
        """List all FX trading records for a fiscal year."""
        return ledger_list_fx_trading(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_fx_trading(db_path: str, fx_trading_id: int) -> dict:
        """Delete an FX trading record."""
        return ledger_delete_fx_trading(db_path=db_path, fx_trading_id=fx_trading_id)

    @mcp.tool()
    def mcp_ledger_add_fx_loss_carryforward(
        db_path: str, fiscal_year: int, detail: dict
    ) -> dict:
        """Add an FX loss carryforward entry."""
        parsed = FXLossCarryforwardInput(**detail)
        return ledger_add_fx_loss_carryforward(
            db_path=db_path, fiscal_year=fiscal_year, detail=parsed
        )

    @mcp.tool()
    def mcp_ledger_list_fx_loss_carryforward(db_path: str, fiscal_year: int) -> dict:
        """List all FX loss carryforward entries for a fiscal year."""
        return ledger_list_fx_loss_carryforward(db_path=db_path, fiscal_year=fiscal_year)

    @mcp.tool()
    def mcp_ledger_delete_fx_loss_carryforward(
        db_path: str, fx_loss_carryforward_id: int
    ) -> dict:
        """Delete an FX loss carryforward entry."""
        return ledger_delete_fx_loss_carryforward(
            db_path=db_path, fx_loss_carryforward_id=fx_loss_carryforward_id
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


# ============================================================
# Spouse CRUD (Phase 2)
# ============================================================


def ledger_set_spouse(*, db_path: str, fiscal_year: int, detail: SpouseInput) -> dict:
    """Upsert spouse info for a fiscal year."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO spouse_info "
            "(fiscal_year, name, date_of_birth, income, disability, cohabiting, "
            "other_taxpayer_dependent) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(fiscal_year) DO UPDATE SET "
            "name=excluded.name, date_of_birth=excluded.date_of_birth, "
            "income=excluded.income, disability=excluded.disability, "
            "cohabiting=excluded.cohabiting, "
            "other_taxpayer_dependent=excluded.other_taxpayer_dependent",
            (
                fiscal_year,
                detail.name,
                detail.date_of_birth,
                detail.income,
                detail.disability,
                1 if detail.cohabiting else 0,
                1 if detail.other_taxpayer_dependent else 0,
            ),
        )
        conn.commit()
        return {"status": "ok", "fiscal_year": fiscal_year}
    finally:
        conn.close()


def ledger_get_spouse(*, db_path: str, fiscal_year: int) -> dict:
    """Get spouse info for a fiscal year."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id, fiscal_year, name, date_of_birth, income, disability, "
            "cohabiting, other_taxpayer_dependent FROM spouse_info WHERE fiscal_year = ?",
            (fiscal_year,),
        ).fetchone()
        if row is None:
            return {"status": "ok", "spouse": None}
        return {
            "status": "ok",
            "spouse": {
                "id": row[0],
                "fiscal_year": row[1],
                "name": row[2],
                "date_of_birth": row[3],
                "income": row[4],
                "disability": row[5],
                "cohabiting": bool(row[6]),
                "other_taxpayer_dependent": bool(row[7]),
            },
        }
    finally:
        conn.close()


def ledger_delete_spouse(*, db_path: str, fiscal_year: int) -> dict:
    """Delete spouse info for a fiscal year."""
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM spouse_info WHERE fiscal_year = ?", (fiscal_year,))
        conn.commit()
        return {"status": "ok", "fiscal_year": fiscal_year}
    finally:
        conn.close()


# ============================================================
# Dependent CRUD (Phase 2)
# ============================================================


def ledger_add_dependent(*, db_path: str, fiscal_year: int, detail: DependentInput) -> dict:
    """Add a dependent."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO dependents "
            "(fiscal_year, name, relationship, date_of_birth, income, disability, cohabiting) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.name,
                detail.relationship,
                detail.date_of_birth,
                detail.income,
                detail.disability,
                1 if detail.cohabiting else 0,
            ),
        )
        conn.commit()
        return {"status": "ok", "dependent_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_dependents(*, db_path: str, fiscal_year: int) -> dict:
    """List dependents for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, name, relationship, date_of_birth, "
            "income, disability, cohabiting FROM dependents WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0],
                "fiscal_year": r[1],
                "name": r[2],
                "relationship": r[3],
                "date_of_birth": r[4],
                "income": r[5],
                "disability": r[6],
                "cohabiting": bool(r[7]),
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "dependents": items}
    finally:
        conn.close()


def ledger_delete_dependent(*, db_path: str, dependent_id: int) -> dict:
    """Delete a dependent."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT id FROM dependents WHERE id = ?", (dependent_id,)).fetchone()
        if row is None:
            return {"status": "error", "message": f"Dependent {dependent_id} not found"}
        conn.execute("DELETE FROM dependents WHERE id = ?", (dependent_id,))
        conn.commit()
        return {"status": "ok", "dependent_id": dependent_id}
    finally:
        conn.close()


# ============================================================
# Withholding Slip CRUD (Phase 6)
# ============================================================


def ledger_save_withholding_slip(
    *, db_path: str, fiscal_year: int, detail: WithholdingSlipInput
) -> dict:
    """Save a withholding slip."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO withholding_slips "
            "(fiscal_year, payer_name, payment_amount, withheld_tax, social_insurance, "
            "life_insurance_deduction, earthquake_insurance_deduction, housing_loan_deduction, "
            "spouse_deduction, dependent_deduction, basic_deduction, "
            "life_insurance_general_new, life_insurance_general_old, "
            "life_insurance_medical_care, life_insurance_annuity_new, "
            "life_insurance_annuity_old, national_pension_premium, "
            "old_long_term_insurance_premium, source_file) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.payer_name,
                detail.payment_amount,
                detail.withheld_tax,
                detail.social_insurance,
                detail.life_insurance_deduction,
                detail.earthquake_insurance_deduction,
                detail.housing_loan_deduction,
                detail.spouse_deduction,
                detail.dependent_deduction,
                detail.basic_deduction,
                detail.life_insurance_general_new,
                detail.life_insurance_general_old,
                detail.life_insurance_medical_care,
                detail.life_insurance_annuity_new,
                detail.life_insurance_annuity_old,
                detail.national_pension_premium,
                detail.old_long_term_insurance_premium,
                detail.source_file,
            ),
        )
        conn.commit()
        return {"status": "ok", "withholding_slip_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_withholding_slips(*, db_path: str, fiscal_year: int) -> dict:
    """List withholding slips for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, payer_name, payment_amount, withheld_tax, "
            "social_insurance, life_insurance_deduction, earthquake_insurance_deduction, "
            "housing_loan_deduction, spouse_deduction, dependent_deduction, basic_deduction, "
            "life_insurance_general_new, life_insurance_general_old, "
            "life_insurance_medical_care, life_insurance_annuity_new, "
            "life_insurance_annuity_old, national_pension_premium, "
            "old_long_term_insurance_premium, source_file "
            "FROM withholding_slips WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0], "fiscal_year": r[1], "payer_name": r[2],
                "payment_amount": r[3], "withheld_tax": r[4], "social_insurance": r[5],
                "life_insurance_deduction": r[6], "earthquake_insurance_deduction": r[7],
                "housing_loan_deduction": r[8], "spouse_deduction": r[9],
                "dependent_deduction": r[10], "basic_deduction": r[11],
                "life_insurance_general_new": r[12], "life_insurance_general_old": r[13],
                "life_insurance_medical_care": r[14], "life_insurance_annuity_new": r[15],
                "life_insurance_annuity_old": r[16], "national_pension_premium": r[17],
                "old_long_term_insurance_premium": r[18], "source_file": r[19],
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "slips": items}
    finally:
        conn.close()


def ledger_delete_withholding_slip(*, db_path: str, withholding_slip_id: int) -> dict:
    """Delete a withholding slip."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM withholding_slips WHERE id = ?", (withholding_slip_id,)
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"Withholding slip {withholding_slip_id} not found"}
        conn.execute("DELETE FROM withholding_slips WHERE id = ?", (withholding_slip_id,))
        conn.commit()
        return {"status": "ok", "withholding_slip_id": withholding_slip_id}
    finally:
        conn.close()


# ============================================================
# Other Income CRUD (Phase 10)
# ============================================================


def ledger_add_other_income(
    *, db_path: str, fiscal_year: int, detail: OtherIncomeInput
) -> dict:
    """Add an other income item."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO other_income_items "
            "(fiscal_year, income_type, description, revenue, expenses, "
            "withheld_tax, payer_name, payer_address) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.income_type,
                detail.description,
                detail.revenue,
                detail.expenses,
                detail.withheld_tax,
                detail.payer_name,
                detail.payer_address,
            ),
        )
        conn.commit()
        return {"status": "ok", "other_income_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_other_income(*, db_path: str, fiscal_year: int) -> dict:
    """List other income items for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, income_type, description, revenue, expenses, "
            "withheld_tax, payer_name, payer_address "
            "FROM other_income_items WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0], "fiscal_year": r[1], "income_type": r[2],
                "description": r[3], "revenue": r[4], "expenses": r[5],
                "withheld_tax": r[6], "payer_name": r[7], "payer_address": r[8],
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "items": items}
    finally:
        conn.close()


def ledger_delete_other_income(*, db_path: str, other_income_id: int) -> dict:
    """Delete an other income item."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM other_income_items WHERE id = ?", (other_income_id,)
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"Other income {other_income_id} not found"}
        conn.execute("DELETE FROM other_income_items WHERE id = ?", (other_income_id,))
        conn.commit()
        return {"status": "ok", "other_income_id": other_income_id}
    finally:
        conn.close()


# ============================================================
# Crypto Income CRUD (Phase 11)
# ============================================================


def ledger_add_crypto_income(
    *, db_path: str, fiscal_year: int, detail: CryptoIncomeInput
) -> dict:
    """Add a crypto income record (upsert by exchange)."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO crypto_income_records "
            "(fiscal_year, exchange_name, gains, expenses) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(fiscal_year, exchange_name) DO UPDATE SET "
            "gains=excluded.gains, expenses=excluded.expenses",
            (fiscal_year, detail.exchange_name, detail.gains, detail.expenses),
        )
        conn.commit()
        return {"status": "ok", "crypto_income_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_crypto_income(*, db_path: str, fiscal_year: int) -> dict:
    """List crypto income records for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, exchange_name, gains, expenses "
            "FROM crypto_income_records WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {"id": r[0], "fiscal_year": r[1], "exchange_name": r[2], "gains": r[3], "expenses": r[4]}
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "records": items}
    finally:
        conn.close()


def ledger_delete_crypto_income(*, db_path: str, crypto_income_id: int) -> dict:
    """Delete a crypto income record."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM crypto_income_records WHERE id = ?", (crypto_income_id,)
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"Crypto income {crypto_income_id} not found"}
        conn.execute("DELETE FROM crypto_income_records WHERE id = ?", (crypto_income_id,))
        conn.commit()
        return {"status": "ok", "crypto_income_id": crypto_income_id}
    finally:
        conn.close()


# ============================================================
# Inventory CRUD (Phase 14)
# ============================================================


def ledger_set_inventory(*, db_path: str, fiscal_year: int, detail: InventoryInput) -> dict:
    """Upsert inventory record by fiscal_year + period."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO inventory_records "
            "(fiscal_year, period, amount, method, details) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(fiscal_year, period) DO UPDATE SET "
            "amount=excluded.amount, method=excluded.method, details=excluded.details",
            (fiscal_year, detail.period, detail.amount, detail.method, detail.details),
        )
        conn.commit()
        return {"status": "ok", "fiscal_year": fiscal_year, "period": detail.period}
    finally:
        conn.close()


def ledger_list_inventory(*, db_path: str, fiscal_year: int) -> dict:
    """List inventory records for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, period, amount, method, details "
            "FROM inventory_records WHERE fiscal_year = ? ORDER BY period",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0], "fiscal_year": r[1], "period": r[2],
                "amount": r[3], "method": r[4], "details": r[5],
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "records": items}
    finally:
        conn.close()


def ledger_delete_inventory(*, db_path: str, inventory_id: int) -> dict:
    """Delete an inventory record."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM inventory_records WHERE id = ?", (inventory_id,)
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"Inventory record {inventory_id} not found"}
        conn.execute("DELETE FROM inventory_records WHERE id = ?", (inventory_id,))
        conn.commit()
        return {"status": "ok", "inventory_id": inventory_id}
    finally:
        conn.close()


# ============================================================
# Professional Fee CRUD (Phase 15)
# ============================================================


def ledger_add_professional_fee(
    *, db_path: str, fiscal_year: int, detail: ProfessionalFeeInput
) -> dict:
    """Add a professional fee entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO professional_fees "
            "(fiscal_year, payer_address, payer_name, fee_amount, "
            "expense_deduction, withheld_tax) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                fiscal_year,
                detail.payer_address,
                detail.payer_name,
                detail.fee_amount,
                detail.expense_deduction,
                detail.withheld_tax,
            ),
        )
        conn.commit()
        return {"status": "ok", "professional_fee_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_professional_fees(*, db_path: str, fiscal_year: int) -> dict:
    """List professional fees for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, payer_address, payer_name, fee_amount, "
            "expense_deduction, withheld_tax "
            "FROM professional_fees WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0], "fiscal_year": r[1], "payer_address": r[2],
                "payer_name": r[3], "fee_amount": r[4],
                "expense_deduction": r[5], "withheld_tax": r[6],
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "fees": items}
    finally:
        conn.close()


def ledger_delete_professional_fee(*, db_path: str, professional_fee_id: int) -> dict:
    """Delete a professional fee entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM professional_fees WHERE id = ?", (professional_fee_id,)
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"Professional fee {professional_fee_id} not found"}
        conn.execute("DELETE FROM professional_fees WHERE id = ?", (professional_fee_id,))
        conn.commit()
        return {"status": "ok", "professional_fee_id": professional_fee_id}
    finally:
        conn.close()


# ============================================================
# Stock Trading CRUD (Phase 12)
# ============================================================


def ledger_add_stock_trading_account(
    *, db_path: str, fiscal_year: int, detail: StockTradingAccountInput
) -> dict:
    """Add a stock trading account (upsert by account_type + broker)."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO stock_trading_accounts "
            "(fiscal_year, account_type, broker_name, gains, losses, "
            "withheld_income_tax, withheld_residential_tax, "
            "dividend_income, dividend_withheld_tax) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(fiscal_year, account_type, broker_name) DO UPDATE SET "
            "gains=excluded.gains, losses=excluded.losses, "
            "withheld_income_tax=excluded.withheld_income_tax, "
            "withheld_residential_tax=excluded.withheld_residential_tax, "
            "dividend_income=excluded.dividend_income, "
            "dividend_withheld_tax=excluded.dividend_withheld_tax",
            (
                fiscal_year,
                detail.account_type,
                detail.broker_name,
                detail.gains,
                detail.losses,
                detail.withheld_income_tax,
                detail.withheld_residential_tax,
                detail.dividend_income,
                detail.dividend_withheld_tax,
            ),
        )
        conn.commit()
        return {"status": "ok", "stock_trading_account_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_stock_trading_accounts(*, db_path: str, fiscal_year: int) -> dict:
    """List stock trading accounts for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, account_type, broker_name, gains, losses, "
            "withheld_income_tax, withheld_residential_tax, "
            "dividend_income, dividend_withheld_tax "
            "FROM stock_trading_accounts WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0], "fiscal_year": r[1], "account_type": r[2],
                "broker_name": r[3], "gains": r[4], "losses": r[5],
                "withheld_income_tax": r[6], "withheld_residential_tax": r[7],
                "dividend_income": r[8], "dividend_withheld_tax": r[9],
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "accounts": items}
    finally:
        conn.close()


def ledger_delete_stock_trading_account(
    *, db_path: str, stock_trading_account_id: int
) -> dict:
    """Delete a stock trading account."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM stock_trading_accounts WHERE id = ?", (stock_trading_account_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Stock trading account {stock_trading_account_id} not found",
            }
        conn.execute(
            "DELETE FROM stock_trading_accounts WHERE id = ?", (stock_trading_account_id,)
        )
        conn.commit()
        return {"status": "ok", "stock_trading_account_id": stock_trading_account_id}
    finally:
        conn.close()


def ledger_add_stock_loss_carryforward(
    *, db_path: str, fiscal_year: int, detail: StockLossCarryforwardInput
) -> dict:
    """Add a stock loss carryforward entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO stock_loss_carryforward "
            "(fiscal_year, loss_year, amount) VALUES (?, ?, ?)",
            (fiscal_year, detail.loss_year, detail.amount),
        )
        conn.commit()
        return {"status": "ok", "stock_loss_carryforward_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_stock_loss_carryforward(*, db_path: str, fiscal_year: int) -> dict:
    """List stock loss carryforward entries for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, loss_year, amount, used_amount "
            "FROM stock_loss_carryforward WHERE fiscal_year = ? ORDER BY loss_year",
            (fiscal_year,),
        ).fetchall()
        items = [
            {"id": r[0], "fiscal_year": r[1], "loss_year": r[2], "amount": r[3], "used_amount": r[4]}
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "entries": items}
    finally:
        conn.close()


def ledger_delete_stock_loss_carryforward(
    *, db_path: str, stock_loss_carryforward_id: int
) -> dict:
    """Delete a stock loss carryforward entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM stock_loss_carryforward WHERE id = ?", (stock_loss_carryforward_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"Stock loss carryforward {stock_loss_carryforward_id} not found",
            }
        conn.execute(
            "DELETE FROM stock_loss_carryforward WHERE id = ?", (stock_loss_carryforward_id,)
        )
        conn.commit()
        return {"status": "ok", "stock_loss_carryforward_id": stock_loss_carryforward_id}
    finally:
        conn.close()


# ============================================================
# FX Trading CRUD (Phase 13)
# ============================================================


def ledger_add_fx_trading(*, db_path: str, fiscal_year: int, detail: FXTradingInput) -> dict:
    """Add an FX trading record (upsert by broker)."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO fx_trading_records "
            "(fiscal_year, broker_name, realized_gains, swap_income, expenses) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(fiscal_year, broker_name) DO UPDATE SET "
            "realized_gains=excluded.realized_gains, swap_income=excluded.swap_income, "
            "expenses=excluded.expenses",
            (
                fiscal_year,
                detail.broker_name,
                detail.realized_gains,
                detail.swap_income,
                detail.expenses,
            ),
        )
        conn.commit()
        return {"status": "ok", "fx_trading_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_fx_trading(*, db_path: str, fiscal_year: int) -> dict:
    """List FX trading records for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, broker_name, realized_gains, swap_income, expenses "
            "FROM fx_trading_records WHERE fiscal_year = ? ORDER BY id",
            (fiscal_year,),
        ).fetchall()
        items = [
            {
                "id": r[0], "fiscal_year": r[1], "broker_name": r[2],
                "realized_gains": r[3], "swap_income": r[4], "expenses": r[5],
            }
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "records": items}
    finally:
        conn.close()


def ledger_delete_fx_trading(*, db_path: str, fx_trading_id: int) -> dict:
    """Delete an FX trading record."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM fx_trading_records WHERE id = ?", (fx_trading_id,)
        ).fetchone()
        if row is None:
            return {"status": "error", "message": f"FX trading {fx_trading_id} not found"}
        conn.execute("DELETE FROM fx_trading_records WHERE id = ?", (fx_trading_id,))
        conn.commit()
        return {"status": "ok", "fx_trading_id": fx_trading_id}
    finally:
        conn.close()


def ledger_add_fx_loss_carryforward(
    *, db_path: str, fiscal_year: int, detail: FXLossCarryforwardInput
) -> dict:
    """Add an FX loss carryforward entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO fx_loss_carryforward "
            "(fiscal_year, loss_year, amount) VALUES (?, ?, ?)",
            (fiscal_year, detail.loss_year, detail.amount),
        )
        conn.commit()
        return {"status": "ok", "fx_loss_carryforward_id": cursor.lastrowid}
    finally:
        conn.close()


def ledger_list_fx_loss_carryforward(*, db_path: str, fiscal_year: int) -> dict:
    """List FX loss carryforward entries for a fiscal year."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, fiscal_year, loss_year, amount, used_amount "
            "FROM fx_loss_carryforward WHERE fiscal_year = ? ORDER BY loss_year",
            (fiscal_year,),
        ).fetchall()
        items = [
            {"id": r[0], "fiscal_year": r[1], "loss_year": r[2], "amount": r[3], "used_amount": r[4]}
            for r in rows
        ]
        return {"status": "ok", "fiscal_year": fiscal_year, "count": len(items), "entries": items}
    finally:
        conn.close()


def ledger_delete_fx_loss_carryforward(
    *, db_path: str, fx_loss_carryforward_id: int
) -> dict:
    """Delete an FX loss carryforward entry."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM fx_loss_carryforward WHERE id = ?", (fx_loss_carryforward_id,)
        ).fetchone()
        if row is None:
            return {
                "status": "error",
                "message": f"FX loss carryforward {fx_loss_carryforward_id} not found",
            }
        conn.execute(
            "DELETE FROM fx_loss_carryforward WHERE id = ?", (fx_loss_carryforward_id,)
        )
        conn.commit()
        return {"status": "ok", "fx_loss_carryforward_id": fx_loss_carryforward_id}
    finally:
        conn.close()
