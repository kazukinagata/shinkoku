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


def test_v4_tables_exist(tmp_path):
    """v4 マイグレーションで追加されたテーブルが存在すること。"""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    v4_tables = {"social_insurance_items", "insurance_policies", "donation_records"}
    assert v4_tables.issubset(tables)
    conn.close()


def test_v4_dependents_other_taxpayer_column(tmp_path):
    """dependents テーブルに other_taxpayer_dependent 列が存在すること。"""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute("PRAGMA table_info(dependents)")
    columns = {row[1] for row in cursor.fetchall()}
    assert "other_taxpayer_dependent" in columns
    conn.close()


def test_v4_housing_loan_new_columns(tmp_path):
    """housing_loan_details テーブルに Gap 6 の新列が存在すること。"""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute("PRAGMA table_info(housing_loan_details)")
    columns = {row[1] for row in cursor.fetchall()}
    expected_new = {
        "purchase_date",
        "purchase_price",
        "total_floor_area",
        "residential_floor_area",
        "property_number",
        "application_submitted",
    }
    assert expected_new.issubset(columns)
    conn.close()


def test_migrate_v3_to_v4(tmp_path):
    """既存 v3 DB が v4 に正常マイグレーションされること。"""
    from shinkoku.db import _migrate_v3_to_v4

    db_path = str(tmp_path / "v3.db")
    # v3 DB を手動構築（新テーブル・新列なし）
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    # v3 のスキーマを部分的に作成
    conn.executescript("""
        CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
        INSERT INTO schema_version (version) VALUES (3);
        CREATE TABLE dependents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fiscal_year INTEGER NOT NULL,
            name TEXT NOT NULL,
            relationship TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            income INTEGER NOT NULL DEFAULT 0,
            disability TEXT,
            cohabiting INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE housing_loan_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fiscal_year INTEGER NOT NULL,
            housing_type TEXT NOT NULL,
            housing_category TEXT NOT NULL DEFAULT 'general',
            move_in_date TEXT NOT NULL,
            year_end_balance INTEGER NOT NULL,
            is_new_construction INTEGER NOT NULL DEFAULT 1,
            is_childcare_household INTEGER NOT NULL DEFAULT 0,
            has_pre_r6_building_permit INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    # マイグレーション実行
    _migrate_v3_to_v4(conn)
    # 新列の存在を確認
    dep_cols = {r[1] for r in conn.execute("PRAGMA table_info(dependents)").fetchall()}
    assert "other_taxpayer_dependent" in dep_cols
    hl_cols = {r[1] for r in conn.execute("PRAGMA table_info(housing_loan_details)").fetchall()}
    assert "purchase_date" in hl_cols
    assert "purchase_price" in hl_cols
    # 新テーブルの存在を確認
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "social_insurance_items" in tables
    assert "insurance_policies" in tables
    assert "donation_records" in tables
    conn.close()
