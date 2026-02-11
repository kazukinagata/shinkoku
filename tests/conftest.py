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
    conn.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")
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
def tax_params_2025():
    """令和7年分 (2025) の税額計算パラメータ。"""
    return {
        "fiscal_year": 2025,
        # 基礎控除（令和7年改正: 段階表）
        "basic_deduction_table": [
            # (所得上限, 控除額)
            (1_320_000, 950_000),
            (1_560_000, 880_000),
            (2_100_000, 680_000),
            (2_350_000, 630_000),
            (2_400_000, 580_000),
            (2_450_000, 480_000),
            (2_500_000, 320_000),
            (2_545_000, 160_000),
            # 2,545万超: 0
        ],
        # 給与所得控除（令和7年改正: 最低保障65万円）
        "salary_deduction_min": 650_000,
        "salary_deduction_table": [
            # (給与収入上限, 控除率, 控除加算額)
            (1_625_000, 1.0, 0),  # 全額控除（最低65万）
            (1_800_000, 0.4, -100_000),
            (3_600_000, 0.3, 80_000),
            (6_600_000, 0.2, 440_000),
            (8_500_000, 0.1, 1_100_000),
            # 850万超: 195万円
        ],
        "salary_deduction_max": 1_950_000,
        # 所得税速算表
        "income_tax_table": [
            # (課税所得上限, 税率, 控除額)
            (1_950_000, 0.05, 0),
            (3_300_000, 0.10, 97_500),
            (6_950_000, 0.20, 427_500),
            (9_000_000, 0.23, 636_000),
            (18_000_000, 0.33, 1_536_000),
            (40_000_000, 0.40, 2_796_000),
            (float("inf"), 0.45, 4_796_000),
        ],
        # 復興特別所得税率
        "reconstruction_tax_rate": 0.021,
        # 青色申告特別控除
        "blue_return_deduction": 650_000,
    }


@pytest.fixture
def output_dir(tmp_path):
    """Temporary directory for PDF output."""
    d = tmp_path / "output"
    d.mkdir()
    return d
