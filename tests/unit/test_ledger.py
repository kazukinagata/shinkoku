"""Tests for ledger tools."""
import sqlite3
import pytest
from shinkoku.models import JournalEntry, JournalLine, JournalSearchParams
from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journal,
    ledger_add_journals_batch,
    ledger_search,
)


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


# ============================================================
# Task 8: ledger_add_journals_batch + ledger_search
# ============================================================


class TestLedgerAddJournalsBatch:
    def test_batch_success(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entries = [
            JournalEntry(
                date="2025-01-10", description="売上1",
                lines=[
                    JournalLine(side="debit", account_code="1001", amount=10000),
                    JournalLine(side="credit", account_code="4001", amount=10000),
                ],
            ),
            JournalEntry(
                date="2025-01-11", description="売上2",
                lines=[
                    JournalLine(side="debit", account_code="1002", amount=20000),
                    JournalLine(side="credit", account_code="4001", amount=20000),
                ],
            ),
        ]
        result = ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries
        )
        assert result["status"] == "ok"
        assert result["count"] == 2
        assert len(result["journal_ids"]) == 2

    def test_batch_all_or_nothing(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entries = [
            JournalEntry(
                date="2025-01-10", description="ok",
                lines=[
                    JournalLine(side="debit", account_code="1001", amount=10000),
                    JournalLine(side="credit", account_code="4001", amount=10000),
                ],
            ),
            JournalEntry(
                date="2025-01-11", description="bad balance",
                lines=[
                    JournalLine(side="debit", account_code="1001", amount=10000),
                    JournalLine(side="credit", account_code="4001", amount=9999),
                ],
            ),
        ]
        result = ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries
        )
        assert result["status"] == "error"
        # Verify rollback: no journals should exist
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM journals").fetchone()[0]
        assert count == 0
        conn.close()

    def test_batch_empty(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        result = ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=[]
        )
        assert result["status"] == "ok"
        assert result["count"] == 0


class TestLedgerSearch:
    def _setup_data(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entries = [
            JournalEntry(
                date="2025-01-10", description="ウェブ開発報酬",
                source="manual",
                lines=[
                    JournalLine(side="debit", account_code="1001", amount=100000),
                    JournalLine(side="credit", account_code="4001", amount=100000),
                ],
            ),
            JournalEntry(
                date="2025-02-15", description="サーバー代",
                source="csv_import",
                lines=[
                    JournalLine(side="debit", account_code="5140", amount=5000),
                    JournalLine(side="credit", account_code="1002", amount=5000),
                ],
            ),
            JournalEntry(
                date="2025-03-20", description="文房具購入",
                source="manual",
                lines=[
                    JournalLine(side="debit", account_code="5190", amount=3000),
                    JournalLine(side="credit", account_code="1001", amount=3000),
                ],
            ),
        ]
        ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries
        )
        return db_path

    def test_search_all(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(fiscal_year=2025)
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 3
        assert len(result["journals"]) == 3

    def test_search_by_date_range(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(
            fiscal_year=2025, date_from="2025-02-01", date_to="2025-02-28"
        )
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 1
        assert result["journals"][0]["description"] == "サーバー代"

    def test_search_by_account(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(
            fiscal_year=2025, account_code="5140"
        )
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 1

    def test_search_by_description(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(
            fiscal_year=2025, description_contains="文房具"
        )
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 1

    def test_search_by_source(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(
            fiscal_year=2025, source="csv_import"
        )
        result = ledger_search(db_path=db_path, params=params)
        assert result["total_count"] == 1

    def test_search_pagination(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(fiscal_year=2025, limit=2, offset=0)
        result = ledger_search(db_path=db_path, params=params)
        assert len(result["journals"]) == 2
        assert result["total_count"] == 3

        params2 = JournalSearchParams(fiscal_year=2025, limit=2, offset=2)
        result2 = ledger_search(db_path=db_path, params=params2)
        assert len(result2["journals"]) == 1
        assert result2["total_count"] == 3

    def test_search_includes_lines(self, tmp_path):
        db_path = self._setup_data(tmp_path)
        params = JournalSearchParams(fiscal_year=2025, limit=1)
        result = ledger_search(db_path=db_path, params=params)
        journal = result["journals"][0]
        assert "lines" in journal
        assert len(journal["lines"]) >= 2
