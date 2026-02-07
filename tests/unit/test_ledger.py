"""Tests for ledger tools - Task 7: init and add_journal."""
import sqlite3
import pytest
from shinkoku.models import JournalEntry, JournalLine
from shinkoku.tools.ledger import ledger_init, ledger_add_journal


class TestLedgerInit:
    def test_init_creates_db(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        result = ledger_init(fiscal_year=2025, db_path=db_path)
        assert result["status"] == "ok"
        assert result["fiscal_year"] == 2025
        assert result["accounts_loaded"] > 40

    def test_init_idempotent(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        r2 = ledger_init(fiscal_year=2025, db_path=db_path)
        assert r2["status"] == "ok"

    def test_init_multiple_years(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2024, db_path=db_path)
        ledger_init(fiscal_year=2025, db_path=db_path)
        conn = sqlite3.connect(db_path)
        years = conn.execute(
            "SELECT year FROM fiscal_years ORDER BY year"
        ).fetchall()
        assert [r[0] for r in years] == [2024, 2025]
        conn.close()


class TestLedgerAddJournal:
    def test_add_simple(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-01-15",
            description="売上",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=100000),
                JournalLine(side="credit", account_code="4001", amount=100000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        assert result["status"] == "ok"
        assert result["journal_id"] > 0

    def test_balance_check(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-01-15",
            description="x",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=100000),
                JournalLine(side="credit", account_code="4001", amount=99999),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        assert result["status"] == "error"

    def test_zero_amount(self, tmp_path):
        with pytest.raises(Exception):
            JournalLine(side="debit", account_code="1001", amount=0)

    def test_negative_amount(self, tmp_path):
        with pytest.raises(Exception):
            JournalLine(side="debit", account_code="1001", amount=-1000)

    def test_invalid_account(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-01-15",
            description="x",
            lines=[
                JournalLine(side="debit", account_code="9999", amount=10000),
                JournalLine(side="credit", account_code="4001", amount=10000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        assert result["status"] == "error"

    def test_invalid_fiscal_year(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2024-01-15",
            description="x",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=10000),
                JournalLine(side="credit", account_code="4001", amount=10000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2024, entry=entry
        )
        assert result["status"] == "error"

    def test_compound_entry(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-03-01",
            description="複合",
            lines=[
                JournalLine(side="debit", account_code="5140", amount=3000),
                JournalLine(side="debit", account_code="5120", amount=2000),
                JournalLine(side="credit", account_code="1002", amount=5000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        assert result["status"] == "ok"

    def test_integer_amounts(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-01-15",
            description="int",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=50000),
                JournalLine(side="credit", account_code="4001", amount=50000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        assert result["status"] == "ok"
        conn = sqlite3.connect(db_path)
        lines = conn.execute(
            "SELECT amount FROM journal_lines WHERE journal_id=?",
            (result["journal_id"],),
        ).fetchall()
        for line in lines:
            assert isinstance(line[0], int)
        conn.close()
