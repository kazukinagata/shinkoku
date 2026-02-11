"""Tests for ledger tools."""
import sqlite3
import pytest
from shinkoku.models import JournalEntry, JournalLine, JournalSearchParams
from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journal,
    ledger_add_journals_batch,
    ledger_search,
    ledger_update_journal,
    ledger_delete_journal,
    ledger_trial_balance,
    ledger_pl,
    ledger_bs,
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


# ============================================================
# Task 9: ledger_update_journal + ledger_delete_journal
# ============================================================


class TestLedgerUpdateJournal:
    def _create_journal(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-01-15", description="original",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=10000),
                JournalLine(side="credit", account_code="4001", amount=10000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        return db_path, result["journal_id"]

    def test_update_journal(self, tmp_path):
        db_path, journal_id = self._create_journal(tmp_path)
        updated = JournalEntry(
            date="2025-01-20", description="updated",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=20000),
                JournalLine(side="credit", account_code="4001", amount=20000),
            ],
        )
        result = ledger_update_journal(
            db_path=db_path, journal_id=journal_id,
            fiscal_year=2025, entry=updated,
        )
        assert result["status"] == "ok"
        # Verify updated data
        params = JournalSearchParams(fiscal_year=2025)
        found = ledger_search(db_path=db_path, params=params)
        j = found["journals"][0]
        assert j["description"] == "updated"
        assert j["date"] == "2025-01-20"
        debit_line = [li for li in j["lines"] if li["side"] == "debit"][0]
        assert debit_line["amount"] == 20000

    def test_update_revalidates_balance(self, tmp_path):
        db_path, journal_id = self._create_journal(tmp_path)
        updated = JournalEntry(
            date="2025-01-20", description="bad",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=20000),
                JournalLine(side="credit", account_code="4001", amount=19999),
            ],
        )
        result = ledger_update_journal(
            db_path=db_path, journal_id=journal_id,
            fiscal_year=2025, entry=updated,
        )
        assert result["status"] == "error"

    def test_update_nonexistent_journal(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        updated = JournalEntry(
            date="2025-01-20", description="x",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=10000),
                JournalLine(side="credit", account_code="4001", amount=10000),
            ],
        )
        result = ledger_update_journal(
            db_path=db_path, journal_id=99999,
            fiscal_year=2025, entry=updated,
        )
        assert result["status"] == "error"


class TestLedgerDeleteJournal:
    def _create_journal(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        entry = JournalEntry(
            date="2025-01-15", description="to delete",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=10000),
                JournalLine(side="credit", account_code="4001", amount=10000),
            ],
        )
        result = ledger_add_journal(
            db_path=db_path, fiscal_year=2025, entry=entry
        )
        return db_path, result["journal_id"]

    def test_delete_journal(self, tmp_path):
        db_path, journal_id = self._create_journal(tmp_path)
        result = ledger_delete_journal(
            db_path=db_path, journal_id=journal_id
        )
        assert result["status"] == "ok"
        # Verify deletion
        params = JournalSearchParams(fiscal_year=2025)
        found = ledger_search(db_path=db_path, params=params)
        assert found["total_count"] == 0

    def test_delete_cascades_lines(self, tmp_path):
        db_path, journal_id = self._create_journal(tmp_path)
        ledger_delete_journal(db_path=db_path, journal_id=journal_id)
        conn = sqlite3.connect(db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM journal_lines WHERE journal_id=?",
            (journal_id,),
        ).fetchone()[0]
        assert count == 0
        conn.close()

    def test_delete_nonexistent(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        ledger_init(fiscal_year=2025, db_path=db_path)
        result = ledger_delete_journal(
            db_path=db_path, journal_id=99999
        )
        assert result["status"] == "error"


# ============================================================
# Task 10: ledger_trial_balance + ledger_pl + ledger_bs
# ============================================================


def _setup_full_ledger(tmp_path):
    """Create a DB with comprehensive journal entries for reports."""
    db_path = str(tmp_path / "test.db")
    ledger_init(fiscal_year=2025, db_path=db_path)
    entries = [
        # Revenue: 売上 300,000 (現金)
        JournalEntry(
            date="2025-01-15", description="売上1",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=300000),
                JournalLine(side="credit", account_code="4001", amount=300000),
            ],
        ),
        # Revenue: 雑収入 10,000 (普通預金)
        JournalEntry(
            date="2025-02-01", description="受取利息等",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=10000),
                JournalLine(side="credit", account_code="4110", amount=10000),
            ],
        ),
        # Expense: 通信費 20,000 (普通預金)
        JournalEntry(
            date="2025-02-15", description="通信費",
            lines=[
                JournalLine(side="debit", account_code="5140", amount=20000),
                JournalLine(side="credit", account_code="1002", amount=20000),
            ],
        ),
        # Expense: 消耗品費 10,000 (現金)
        JournalEntry(
            date="2025-03-01", description="消耗品",
            lines=[
                JournalLine(side="debit", account_code="5190", amount=10000),
                JournalLine(side="credit", account_code="1001", amount=10000),
            ],
        ),
        # Liability: 未払金 5,000 (with expense)
        JournalEntry(
            date="2025-03-10", description="未払経費",
            lines=[
                JournalLine(side="debit", account_code="5270", amount=5000),
                JournalLine(side="credit", account_code="2030", amount=5000),
            ],
        ),
        # Equity: 元入金 100,000
        JournalEntry(
            date="2025-01-01", description="元入金",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=100000),
                JournalLine(side="credit", account_code="3001", amount=100000),
            ],
        ),
    ]
    ledger_add_journals_batch(
        db_path=db_path, fiscal_year=2025, entries=entries
    )
    return db_path


class TestLedgerTrialBalance:
    def test_trial_balance_debit_equals_credit(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_trial_balance(
            db_path=db_path, fiscal_year=2025
        )
        assert result["status"] == "ok"
        assert result["total_debit"] == result["total_credit"]

    def test_trial_balance_has_accounts(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_trial_balance(
            db_path=db_path, fiscal_year=2025
        )
        assert len(result["accounts"]) > 0
        # Check that each account has required fields
        for acct in result["accounts"]:
            assert "account_code" in acct
            assert "account_name" in acct
            assert "category" in acct
            assert "debit_total" in acct
            assert "credit_total" in acct

    def test_trial_balance_amounts_integer(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_trial_balance(
            db_path=db_path, fiscal_year=2025
        )
        assert isinstance(result["total_debit"], int)
        assert isinstance(result["total_credit"], int)
        for acct in result["accounts"]:
            assert isinstance(acct["debit_total"], int)
            assert isinstance(acct["credit_total"], int)


class TestLedgerPL:
    def test_pl_net_income_equals_revenue_minus_expense(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_pl(db_path=db_path, fiscal_year=2025)
        assert result["status"] == "ok"
        # Revenue: 300,000 + 10,000 = 310,000
        assert result["total_revenue"] == 310000
        # Expense: 20,000 + 10,000 + 5,000 = 35,000
        assert result["total_expense"] == 35000
        # Net income
        assert result["net_income"] == 310000 - 35000

    def test_pl_has_items(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_pl(db_path=db_path, fiscal_year=2025)
        assert len(result["revenues"]) > 0
        assert len(result["expenses"]) > 0

    def test_pl_amounts_integer(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_pl(db_path=db_path, fiscal_year=2025)
        assert isinstance(result["total_revenue"], int)
        assert isinstance(result["total_expense"], int)
        assert isinstance(result["net_income"], int)


class TestLedgerBS:
    def test_bs_assets_equal_liabilities_plus_equity(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_bs(db_path=db_path, fiscal_year=2025)
        assert result["status"] == "ok"
        # A = L + E (equity includes net_income)
        assert result["total_assets"] == (
            result["total_liabilities"] + result["total_equity"]
        )

    def test_bs_net_income_consistent_with_pl(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        ledger_pl(db_path=db_path, fiscal_year=2025)
        bs_result = ledger_bs(db_path=db_path, fiscal_year=2025)
        # BS total_equity should include net_income from PL
        # Check that net_income is embedded in BS equity
        assert bs_result["total_equity"] > 0
        # Assets should match: cash + deposits - outflows
        # 300,000 (cash in) - 10,000 (cash out) = 290,000 cash
        # 10,000 (deposit in) - 20,000 (deposit out) + 100,000 (equity in) = 90,000 deposit
        # Total assets = 290,000 + 90,000 = 380,000
        assert bs_result["total_assets"] == 380000

    def test_bs_amounts_integer(self, tmp_path):
        db_path = _setup_full_ledger(tmp_path)
        result = ledger_bs(db_path=db_path, fiscal_year=2025)
        assert isinstance(result["total_assets"], int)
        assert isinstance(result["total_liabilities"], int)
        assert isinstance(result["total_equity"], int)
