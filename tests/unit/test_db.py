import sqlite3

import pytest

from shinkoku.db import init_db


def test_init_db_creates_file(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    assert (tmp_path / "test.db").exists()
    conn.close()


def test_init_db_creates_all_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    expected = {
        "schema_version",
        "fiscal_years",
        "accounts",
        "journals",
        "journal_lines",
        "fixed_assets",
        "deductions",
        "withholding_slips",
    }
    assert expected.issubset(tables)
    conn.close()


def test_init_db_idempotent(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn1 = init_db(db_path)
    conn1.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn1.commit()
    conn1.close()
    conn2 = init_db(db_path)
    row = conn2.execute("SELECT year FROM fiscal_years").fetchone()
    assert row[0] == 2025
    conn2.close()


def test_foreign_keys_enabled(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1
    conn.close()


def test_wal_mode_enabled(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    result = conn.execute("PRAGMA journal_mode").fetchone()
    assert result[0] == "wal"
    conn.close()


def test_journal_lines_reference_journals(tmp_path):
    """journal_lines の foreign key が journals を参照していることを確認。"""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    # journal_id が存在しない journal_lines は挿入できない
    conn.execute("INSERT INTO accounts (code, name, category) VALUES ('1001', 'cash', 'asset')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
            "VALUES (999, 'debit', '1001', 1000)"
        )
    conn.close()


def test_schema_version_recorded(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    row = conn.execute(
        "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row[0] >= 1
    conn.close()
