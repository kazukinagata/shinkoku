"""Root conftest - shared fixtures available to all tests."""

import sqlite3

import pytest

from shinkoku.db import SCHEMA_PATH
from shinkoku.master_accounts import MASTER_ACCOUNTS


@pytest.fixture
def in_memory_db():
    """In-memory SQLite database with schema applied. For unit tests."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (4)")
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def in_memory_db_with_accounts(in_memory_db):
    """In-memory DB with master accounts loaded."""
    for a in MASTER_ACCOUNTS:
        in_memory_db.execute(
            "INSERT INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    in_memory_db.commit()
    return in_memory_db


@pytest.fixture
def sample_journals(in_memory_db_with_accounts):
    """DB pre-loaded with sample journal entries for testing."""
    db = in_memory_db_with_accounts
    # Create fiscal year
    db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    # Sample journal 1: 売上 100,000円 (現金)
    db.execute(
        "INSERT INTO journals (fiscal_year, date, description, source) "
        "VALUES (2025, '2025-01-15', 'ウェブ開発報酬', 'manual')"
    )
    journal_id_1 = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute(
        "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
        "VALUES (?, 'debit', '1001', 100000)",
        (journal_id_1,),
    )
    db.execute(
        "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
        "VALUES (?, 'credit', '4001', 100000)",
        (journal_id_1,),
    )
    # Sample journal 2: 通信費 5,000円 (普通預金)
    db.execute(
        "INSERT INTO journals (fiscal_year, date, description, source) "
        "VALUES (2025, '2025-01-20', 'インターネット回線', 'manual')"
    )
    journal_id_2 = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute(
        "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
        "VALUES (?, 'debit', '5140', 5000)",
        (journal_id_2,),
    )
    db.execute(
        "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
        "VALUES (?, 'credit', '1002', 5000)",
        (journal_id_2,),
    )
    # Sample journal 3: 消耗品費 3,000円 (現金)
    db.execute(
        "INSERT INTO journals (fiscal_year, date, description, source) "
        "VALUES (2025, '2025-02-10', '文房具購入', 'manual')"
    )
    journal_id_3 = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute(
        "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
        "VALUES (?, 'debit', '5190', 3000)",
        (journal_id_3,),
    )
    db.execute(
        "INSERT INTO journal_lines (journal_id, side, account_code, amount) "
        "VALUES (?, 'credit', '1001', 3000)",
        (journal_id_3,),
    )
    db.commit()
    return db


@pytest.fixture
def sample_furusato_donations(in_memory_db_with_accounts):
    """DB pre-loaded with sample furusato donations for testing."""
    db = in_memory_db_with_accounts
    db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    donations = [
        (2025, "北海道旭川市", "北海道", 30000, "2025-03-15", "R-001", 0),
        (2025, "福岡県福岡市", "福岡県", 50000, "2025-06-20", "R-002", 1),
        (2025, "沖縄県那覇市", "沖縄県", 20000, "2025-09-10", "R-003", 0),
    ]
    for d in donations:
        db.execute(
            "INSERT INTO furusato_donations "
            "(fiscal_year, municipality_name, municipality_prefecture, "
            "amount, date, receipt_number, one_stop_applied) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            d,
        )
    db.commit()
    return db


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory for PDF output."""
    d = tmp_path / "output"
    d.mkdir()
    return d
