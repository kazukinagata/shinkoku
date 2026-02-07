"""Tests to verify shared test fixtures work correctly."""

from tests.helpers.assertion_helpers import assert_amount_is_integer_yen
from tests.helpers.db_helpers import insert_fiscal_year, insert_journal, load_master_accounts


def test_in_memory_db_has_tables(in_memory_db):
    """in_memory_db fixture should have all schema tables."""
    cursor = in_memory_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    expected = {
        "schema_version", "fiscal_years", "accounts", "journals",
        "journal_lines", "fixed_assets", "deductions", "withholding_slips",
    }
    assert expected.issubset(tables)


def test_in_memory_db_with_accounts(in_memory_db_with_accounts):
    """in_memory_db_with_accounts should have accounts loaded."""
    count = in_memory_db_with_accounts.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    assert count > 40


def test_sample_journals_fixture(sample_journals):
    """sample_journals should have pre-loaded journal entries."""
    count = sample_journals.execute("SELECT COUNT(*) FROM journals").fetchone()[0]
    assert count == 3
    line_count = sample_journals.execute("SELECT COUNT(*) FROM journal_lines").fetchone()[0]
    assert line_count == 6


def test_sample_journals_debit_equals_credit(sample_journals):
    """Debit and credit totals should match in sample data."""
    debit = sample_journals.execute(
        "SELECT SUM(amount) FROM journal_lines WHERE side='debit'"
    ).fetchone()[0]
    credit = sample_journals.execute(
        "SELECT SUM(amount) FROM journal_lines WHERE side='credit'"
    ).fetchone()[0]
    assert debit == credit


def test_tax_params_2025(tax_params_2025):
    """tax_params_2025 fixture should have required keys."""
    assert tax_params_2025["fiscal_year"] == 2025
    assert len(tax_params_2025["basic_deduction_table"]) > 0
    assert len(tax_params_2025["income_tax_table"]) > 0
    assert tax_params_2025["salary_deduction_min"] == 650_000
    assert tax_params_2025["blue_return_deduction"] == 650_000


def test_output_dir(output_dir):
    """output_dir fixture should be a writable directory."""
    assert output_dir.is_dir()
    test_file = output_dir / "test.txt"
    test_file.write_text("hello")
    assert test_file.read_text() == "hello"


def test_assert_amount_is_integer_yen():
    """Custom assertion should pass for int, fail for float."""
    assert_amount_is_integer_yen(100, "test")
    assert_amount_is_integer_yen(0, "test")
    assert_amount_is_integer_yen(-500, "test")
    import pytest
    with pytest.raises(AssertionError, match="must be an integer"):
        assert_amount_is_integer_yen(100.5, "test")
    with pytest.raises(AssertionError, match="must be an integer"):
        assert_amount_is_integer_yen("100", "test")


def test_db_helpers_insert_journal(in_memory_db_with_accounts):
    """db_helpers.insert_journal should create journal and lines."""
    db = in_memory_db_with_accounts
    insert_fiscal_year(db, 2025)
    journal_id = insert_journal(
        db, 2025, "2025-03-01", "テスト仕訳",
        [("debit", "1001", 10000), ("credit", "4001", 10000)],
    )
    assert journal_id > 0
    lines = db.execute(
        "SELECT side, account_code, amount FROM journal_lines WHERE journal_id=?",
        (journal_id,),
    ).fetchall()
    assert len(lines) == 2
