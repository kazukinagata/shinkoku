"""Tests for opening balance CRUD and BS integration."""

from __future__ import annotations

from shinkoku.models import OpeningBalanceInput
from shinkoku.tools.ledger import (
    ledger_bs,
    ledger_delete_opening_balance,
    ledger_list_opening_balances,
    ledger_set_opening_balance,
    ledger_set_opening_balances_batch,
)


def test_set_opening_balance_insert(tmp_path, in_memory_db_with_accounts):
    """新規登録ができること。"""
    db = in_memory_db_with_accounts
    db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    db.commit()
    db_path = str(tmp_path / "ob_test.db")
    # in_memory_db は使えないので、実ファイルで再現
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    detail = OpeningBalanceInput(account_code="1001", amount=500000)
    result = ledger_set_opening_balance(db_path=db_path, fiscal_year=2025, detail=detail)
    assert result["status"] == "ok"
    assert result["account_code"] == "1001"

    # 確認
    listed = ledger_list_opening_balances(db_path=db_path, fiscal_year=2025)
    assert listed["count"] == 1
    assert listed["records"][0]["amount"] == 500000


def test_set_opening_balance_upsert(tmp_path):
    """同一科目の上書きができること。"""
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    db_path = str(tmp_path / "ob_upsert.db")
    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    detail1 = OpeningBalanceInput(account_code="1001", amount=100000)
    ledger_set_opening_balance(db_path=db_path, fiscal_year=2025, detail=detail1)

    detail2 = OpeningBalanceInput(account_code="1001", amount=200000)
    result = ledger_set_opening_balance(db_path=db_path, fiscal_year=2025, detail=detail2)
    assert result["status"] == "ok"

    listed = ledger_list_opening_balances(db_path=db_path, fiscal_year=2025)
    assert listed["count"] == 1
    assert listed["records"][0]["amount"] == 200000


def test_list_opening_balances(tmp_path):
    """一覧取得ができること。"""
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    db_path = str(tmp_path / "ob_list.db")
    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    balances = [
        OpeningBalanceInput(account_code="1001", amount=100000),
        OpeningBalanceInput(account_code="1002", amount=300000),
    ]
    ledger_set_opening_balances_batch(db_path=db_path, fiscal_year=2025, balances=balances)

    result = ledger_list_opening_balances(db_path=db_path, fiscal_year=2025)
    assert result["status"] == "ok"
    assert result["count"] == 2
    assert result["records"][0]["account_code"] == "1001"
    assert result["records"][1]["account_code"] == "1002"


def test_delete_opening_balance(tmp_path):
    """削除ができること。"""
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    db_path = str(tmp_path / "ob_delete.db")
    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    detail = OpeningBalanceInput(account_code="1001", amount=100000)
    ledger_set_opening_balance(db_path=db_path, fiscal_year=2025, detail=detail)

    listed = ledger_list_opening_balances(db_path=db_path, fiscal_year=2025)
    ob_id = listed["records"][0]["id"]

    result = ledger_delete_opening_balance(db_path=db_path, opening_balance_id=ob_id)
    assert result["status"] == "ok"

    listed2 = ledger_list_opening_balances(db_path=db_path, fiscal_year=2025)
    assert listed2["count"] == 0


def test_delete_opening_balance_not_found(tmp_path):
    """存在しないIDの削除はエラーになること。"""
    from shinkoku.db import init_db

    db_path = str(tmp_path / "ob_notfound.db")
    conn = init_db(db_path)
    conn.close()

    result = ledger_delete_opening_balance(db_path=db_path, opening_balance_id=999)
    assert result["status"] == "error"


def test_set_opening_balances_batch(tmp_path):
    """一括登録ができること。"""
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    db_path = str(tmp_path / "ob_batch.db")
    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    balances = [
        OpeningBalanceInput(account_code="1001", amount=100000),
        OpeningBalanceInput(account_code="1002", amount=200000),
        OpeningBalanceInput(account_code="2001", amount=50000),
    ]
    result = ledger_set_opening_balances_batch(db_path=db_path, fiscal_year=2025, balances=balances)
    assert result["status"] == "ok"
    assert result["count"] == 3

    listed = ledger_list_opening_balances(db_path=db_path, fiscal_year=2025)
    assert listed["count"] == 3


def test_ledger_bs_includes_opening_balances(tmp_path):
    """ledger_bs() が期首データを返すこと。"""
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    db_path = str(tmp_path / "ob_bs.db")
    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    # 期首残高を設定
    balances = [
        OpeningBalanceInput(account_code="1001", amount=100000),  # 現金（資産）
        OpeningBalanceInput(account_code="2001", amount=50000),  # 買掛金（負債）
        OpeningBalanceInput(account_code="3001", amount=50000),  # 元入金（純資産）
    ]
    ledger_set_opening_balances_batch(db_path=db_path, fiscal_year=2025, balances=balances)

    result = ledger_bs(db_path=db_path, fiscal_year=2025)
    assert result["status"] == "ok"

    # 期首データが含まれること
    assert len(result["opening_assets"]) == 1
    assert result["opening_assets"][0]["account_code"] == "1001"
    assert result["opening_assets"][0]["amount"] == 100000
    assert result["opening_total_assets"] == 100000

    assert len(result["opening_liabilities"]) == 1
    assert result["opening_liabilities"][0]["amount"] == 50000
    assert result["opening_total_liabilities"] == 50000

    assert len(result["opening_equity"]) == 1
    assert result["opening_equity"][0]["amount"] == 50000
    assert result["opening_total_equity"] == 50000


def test_ledger_bs_no_opening_balances(tmp_path):
    """期首データ未登録時は空リストを返すこと。"""
    from shinkoku.db import init_db
    from shinkoku.master_accounts import MASTER_ACCOUNTS

    db_path = str(tmp_path / "ob_empty.db")
    conn = init_db(db_path)
    for a in MASTER_ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts (code, name, category, sub_category, tax_category) "
            "VALUES (?, ?, ?, ?, ?)",
            (a["code"], a["name"], a["category"], a["sub_category"], a["tax_category"]),
        )
    conn.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn.commit()
    conn.close()

    result = ledger_bs(db_path=db_path, fiscal_year=2025)
    assert result["status"] == "ok"
    assert result["opening_assets"] == []
    assert result["opening_liabilities"] == []
    assert result["opening_equity"] == []
    assert result["opening_total_assets"] == 0
    assert result["opening_total_liabilities"] == 0
    assert result["opening_total_equity"] == 0
