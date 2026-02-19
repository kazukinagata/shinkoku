"""Tests for ledger.py CLI script (67 subcommands)."""

from __future__ import annotations

import json
from pathlib import Path

from .conftest import run_cli, write_json

# ============================================================
# ヘルパー
# ============================================================


def run_ledger(*args: str) -> dict:
    """Run ledger subcommand and parse JSON output."""
    result = run_cli("ledger", *args)
    assert result.stdout, f"No stdout. stderr={result.stderr}"
    return json.loads(result.stdout)


def run_ledger_raw(*args: str):
    """Run ledger subcommand and return raw CompletedProcess."""
    return run_cli("ledger", *args)


def add_journal(db: str, tmp: Path, name: str = "j.json") -> dict:
    """Add a simple journal entry and return parsed output."""
    f = write_json(
        tmp,
        {
            "date": "2025-01-15",
            "description": "Test entry",
            "lines": [
                {"side": "debit", "account_code": "5200", "amount": 1000},
                {"side": "credit", "account_code": "1100", "amount": 1000},
            ],
        },
        name,
    )
    return run_ledger(
        "journal-add",
        "--db-path",
        db,
        "--fiscal-year",
        "2025",
        "--input",
        f,
    )


# ============================================================
# init
# ============================================================


class TestInit:
    def test_init_creates_db(self, tmp_path):
        db = str(tmp_path / "new.db")
        out = run_ledger("init", "--db-path", db, "--fiscal-year", "2025")
        assert out["status"] == "ok"
        assert out["fiscal_year"] == 2025
        assert out["accounts_loaded"] > 0
        assert Path(db).exists()

    def test_init_idempotent(self, db_path):
        out = run_ledger("init", "--db-path", db_path, "--fiscal-year", "2025")
        assert out["status"] == "ok"


# ============================================================
# journal CRUD
# ============================================================


class TestJournalAdd:
    def test_add_single(self, db_path, tmp_path):
        out = add_journal(db_path, tmp_path)
        assert out["status"] == "ok"
        assert "journal_id" in out

    def test_add_unbalanced(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "date": "2025-01-15",
                "description": "Bad",
                "lines": [
                    {"side": "debit", "account_code": "5200", "amount": 1000},
                    {"side": "credit", "account_code": "1100", "amount": 999},
                ],
            },
        )
        out = run_ledger(
            "journal-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "error"
        assert "balanced" in out["message"].lower()


class TestJournalBatchAdd:
    def test_batch_add(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            [
                {
                    "date": "2025-02-01",
                    "description": "Batch 1",
                    "lines": [
                        {"side": "debit", "account_code": "5200", "amount": 500},
                        {"side": "credit", "account_code": "1100", "amount": 500},
                    ],
                },
                {
                    "date": "2025-02-02",
                    "description": "Batch 2",
                    "lines": [
                        {"side": "debit", "account_code": "5300", "amount": 300},
                        {"side": "credit", "account_code": "1100", "amount": 300},
                    ],
                },
            ],
        )
        out = run_ledger(
            "journal-batch-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        assert out["count"] == 2


class TestSearch:
    def test_search_empty(self, db_path, tmp_path):
        f = write_json(tmp_path, {"fiscal_year": 2025})
        out = run_ledger("search", "--db-path", db_path, "--input", f)
        assert out["status"] == "ok"
        assert out["total_count"] == 0

    def test_search_after_add(self, db_path, tmp_path):
        add_journal(db_path, tmp_path, "j1.json")
        f = write_json(tmp_path, {"fiscal_year": 2025}, "search.json")
        out = run_ledger("search", "--db-path", db_path, "--input", f)
        assert out["status"] == "ok"
        assert out["total_count"] == 1


class TestJournalUpdate:
    def test_update(self, db_path, tmp_path):
        added = add_journal(db_path, tmp_path, "j1.json")
        jid = added["journal_id"]
        f = write_json(
            tmp_path,
            {
                "date": "2025-01-20",
                "description": "Updated",
                "lines": [
                    {"side": "debit", "account_code": "5200", "amount": 2000},
                    {"side": "credit", "account_code": "1100", "amount": 2000},
                ],
            },
            "upd.json",
        )
        out = run_ledger(
            "journal-update",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--journal-id",
            str(jid),
            "--input",
            f,
        )
        assert out["status"] == "ok"

    def test_update_nonexistent(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "date": "2025-01-20",
                "description": "X",
                "lines": [
                    {"side": "debit", "account_code": "5200", "amount": 100},
                    {"side": "credit", "account_code": "1100", "amount": 100},
                ],
            },
        )
        out = run_ledger(
            "journal-update",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--journal-id",
            "9999",
            "--input",
            f,
        )
        assert out["status"] == "error"


class TestJournalDelete:
    def test_delete(self, db_path, tmp_path):
        added = add_journal(db_path, tmp_path)
        jid = added["journal_id"]
        out = run_ledger(
            "journal-delete",
            "--db-path",
            db_path,
            "--journal-id",
            str(jid),
        )
        assert out["status"] == "ok"

    def test_delete_nonexistent(self, db_path):
        out = run_ledger(
            "journal-delete",
            "--db-path",
            db_path,
            "--journal-id",
            "9999",
        )
        assert out["status"] == "error"


# ============================================================
# 財務諸表
# ============================================================


class TestTrialBalance:
    def test_empty(self, db_path):
        out = run_ledger(
            "trial-balance",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["total_debit"] == 0

    def test_with_journal(self, db_path, tmp_path):
        add_journal(db_path, tmp_path)
        out = run_ledger(
            "trial-balance",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["total_debit"] == out["total_credit"]


class TestPL:
    def test_pl(self, db_path, tmp_path):
        add_journal(db_path, tmp_path)
        out = run_ledger("pl", "--db-path", db_path, "--fiscal-year", "2025")
        assert out["status"] == "ok"
        assert "total_expense" in out


class TestBS:
    def test_bs(self, db_path, tmp_path):
        add_journal(db_path, tmp_path)
        out = run_ledger("bs", "--db-path", db_path, "--fiscal-year", "2025")
        assert out["status"] == "ok"
        assert "total_assets" in out


class TestCheckDuplicates:
    def test_no_duplicates(self, db_path):
        out = run_ledger(
            "check-duplicates",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["exact_count"] == 0


# ============================================================
# Business Withholding CRUD
# ============================================================


class TestBusinessWithholding:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "client_name": "Acme Corp",
                "gross_amount": 100000,
                "withholding_tax": 10210,
            },
        )
        out = run_ledger(
            "bw-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        wid = out["withholding_id"]

        out = run_ledger(
            "bw-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "bw-delete",
            "--db-path",
            db_path,
            "--withholding-id",
            str(wid),
        )
        assert out["status"] == "ok"


# ============================================================
# Loss Carryforward CRUD
# ============================================================


class TestLossCarryforward:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "loss_year": 2023,
                "amount": 500000,
            },
        )
        out = run_ledger(
            "lc-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        lid = out["loss_carryforward_id"]

        out = run_ledger(
            "lc-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "lc-delete",
            "--db-path",
            db_path,
            "--loss-carryforward-id",
            str(lid),
        )
        assert out["status"] == "ok"


# ============================================================
# Medical Expense CRUD
# ============================================================


class TestMedicalExpense:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "date": "2025-03-01",
                "patient_name": "山田太郎",
                "medical_institution": "東京病院",
                "amount": 5000,
                "insurance_reimbursement": 0,
            },
        )
        out = run_ledger(
            "me-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        mid = out["medical_expense_id"]

        out = run_ledger(
            "me-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "me-delete",
            "--db-path",
            db_path,
            "--medical-expense-id",
            str(mid),
        )
        assert out["status"] == "ok"


# ============================================================
# Rent Detail CRUD
# ============================================================


class TestRentDetail:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "property_type": "事務所",
                "usage": "事務所",
                "landlord_name": "田中",
                "landlord_address": "東京都渋谷区",
                "monthly_rent": 80000,
                "annual_rent": 960000,
                "deposit": 0,
                "business_ratio": 50,
            },
        )
        out = run_ledger(
            "rd-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        rid = out["rent_detail_id"]

        out = run_ledger(
            "rd-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "rd-delete",
            "--db-path",
            db_path,
            "--rent-detail-id",
            str(rid),
        )
        assert out["status"] == "ok"


# ============================================================
# Housing Loan Detail CRUD
# ============================================================


class TestHousingLoanDetail:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "housing_type": "new_custom",
                "housing_category": "general",
                "move_in_date": "2024-04-01",
                "year_end_balance": 30000000,
                "is_new_construction": True,
            },
        )
        out = run_ledger(
            "hl-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        hid = out["housing_loan_detail_id"]

        out = run_ledger(
            "hl-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "hl-delete",
            "--db-path",
            db_path,
            "--housing-loan-detail-id",
            str(hid),
        )
        assert out["status"] == "ok"


# ============================================================
# Spouse CRUD
# ============================================================


class TestSpouse:
    def test_set_get_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "name": "山田花子",
                "date_of_birth": "1990-05-15",
                "income": 500000,
            },
        )
        out = run_ledger(
            "spouse-set",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"

        out = run_ledger(
            "spouse-get",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["spouse"]["name"] == "山田花子"

        out = run_ledger(
            "spouse-delete",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"


# ============================================================
# Dependent CRUD
# ============================================================


class TestDependent:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "name": "山田一郎",
                "relationship": "子",
                "date_of_birth": "2015-08-10",
                "income": 0,
            },
        )
        out = run_ledger(
            "dep-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        did = out["dependent_id"]

        out = run_ledger(
            "dep-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "dep-delete",
            "--db-path",
            db_path,
            "--dependent-id",
            str(did),
        )
        assert out["status"] == "ok"


# ============================================================
# Withholding Slip CRUD
# ============================================================


class TestWithholdingSlip:
    def test_save_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "payer_name": "株式会社テスト",
                "payment_amount": 5000000,
                "withheld_tax": 150000,
                "social_insurance": 700000,
            },
        )
        out = run_ledger(
            "ws-save",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        wid = out["withholding_slip_id"]

        out = run_ledger(
            "ws-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "ws-delete",
            "--db-path",
            db_path,
            "--withholding-slip-id",
            str(wid),
        )
        assert out["status"] == "ok"


# ============================================================
# Other Income CRUD
# ============================================================


class TestOtherIncome:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "income_type": "miscellaneous",
                "description": "副業収入",
                "revenue": 200000,
                "expenses": 50000,
            },
        )
        out = run_ledger(
            "oi-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        oid = out["other_income_id"]

        out = run_ledger(
            "oi-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "oi-delete",
            "--db-path",
            db_path,
            "--other-income-id",
            str(oid),
        )
        assert out["status"] == "ok"


# ============================================================
# Crypto Income CRUD
# ============================================================


class TestCryptoIncome:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "exchange_name": "Coincheck",
                "gains": 100000,
                "expenses": 5000,
            },
        )
        out = run_ledger(
            "ci-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        cid = out["crypto_income_id"]

        out = run_ledger(
            "ci-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "ci-delete",
            "--db-path",
            db_path,
            "--crypto-income-id",
            str(cid),
        )
        assert out["status"] == "ok"


# ============================================================
# Inventory CRUD
# ============================================================


class TestInventory:
    def test_set_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "period": "ending",
                "amount": 150000,
                "method": "cost",
            },
        )
        out = run_ledger(
            "inv-set",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        assert out["period"] == "ending"

        out = run_ledger(
            "inv-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] >= 1
        # inv-set は upsert なので id を list から取得して削除
        iid = out["records"][0]["id"]

        out = run_ledger(
            "inv-delete",
            "--db-path",
            db_path,
            "--inventory-id",
            str(iid),
        )
        assert out["status"] == "ok"


# ============================================================
# Professional Fee CRUD
# ============================================================


class TestProfessionalFee:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "payer_address": "東京都千代田区",
                "payer_name": "税理士法人テスト",
                "fee_amount": 200000,
                "withheld_tax": 20420,
            },
        )
        out = run_ledger(
            "pf-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        pid = out["professional_fee_id"]

        out = run_ledger(
            "pf-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "pf-delete",
            "--db-path",
            db_path,
            "--professional-fee-id",
            str(pid),
        )
        assert out["status"] == "ok"


# ============================================================
# Stock Trading Account CRUD
# ============================================================


class TestStockTradingAccount:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "account_type": "tokutei_withholding",
                "broker_name": "SBI証券",
                "gains": 300000,
                "losses": 50000,
                "withheld_income_tax": 37968,
                "withheld_residential_tax": 12500,
            },
        )
        out = run_ledger(
            "sta-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        sid = out["stock_trading_account_id"]

        out = run_ledger(
            "sta-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "sta-delete",
            "--db-path",
            db_path,
            "--stock-trading-account-id",
            str(sid),
        )
        assert out["status"] == "ok"


# ============================================================
# Stock Loss Carryforward CRUD
# ============================================================


class TestStockLossCarryforward:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "loss_year": 2023,
                "amount": 200000,
            },
        )
        out = run_ledger(
            "slc-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        sid = out["stock_loss_carryforward_id"]

        out = run_ledger(
            "slc-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "slc-delete",
            "--db-path",
            db_path,
            "--stock-loss-carryforward-id",
            str(sid),
        )
        assert out["status"] == "ok"


# ============================================================
# FX Trading CRUD
# ============================================================


class TestFXTrading:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "broker_name": "GMOクリック証券",
                "realized_gains": 500000,
                "swap_income": 20000,
                "expenses": 3000,
            },
        )
        out = run_ledger(
            "fx-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        fid = out["fx_trading_id"]

        out = run_ledger(
            "fx-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "fx-delete",
            "--db-path",
            db_path,
            "--fx-trading-id",
            str(fid),
        )
        assert out["status"] == "ok"


# ============================================================
# FX Loss Carryforward CRUD
# ============================================================


class TestFXLossCarryforward:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "loss_year": 2024,
                "amount": 100000,
            },
        )
        out = run_ledger(
            "fxlc-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        fid = out["fx_loss_carryforward_id"]

        out = run_ledger(
            "fxlc-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "fxlc-delete",
            "--db-path",
            db_path,
            "--fx-loss-carryforward-id",
            str(fid),
        )
        assert out["status"] == "ok"


# ============================================================
# Social Insurance Item CRUD
# ============================================================


class TestSocialInsuranceItem:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "insurance_type": "national_health",
                "name": "国民健康保険",
                "amount": 450000,
            },
        )
        out = run_ledger(
            "si-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        sid = out["social_insurance_item_id"]

        out = run_ledger(
            "si-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "si-delete",
            "--db-path",
            db_path,
            "--social-insurance-item-id",
            str(sid),
        )
        assert out["status"] == "ok"


# ============================================================
# Insurance Policy CRUD
# ============================================================


class TestInsurancePolicy:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "policy_type": "life_general_new",
                "company_name": "日本生命",
                "premium": 80000,
            },
        )
        out = run_ledger(
            "ip-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        iid = out["insurance_policy_id"]

        out = run_ledger(
            "ip-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "ip-delete",
            "--db-path",
            db_path,
            "--insurance-policy-id",
            str(iid),
        )
        assert out["status"] == "ok"


# ============================================================
# Donation CRUD
# ============================================================


class TestDonation:
    def test_add_list_delete(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            {
                "donation_type": "public_interest",
                "recipient_name": "日本赤十字社",
                "amount": 10000,
                "date": "2025-06-01",
            },
        )
        out = run_ledger(
            "don-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        did = out["donation_id"]

        out = run_ledger(
            "don-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1

        out = run_ledger(
            "don-delete",
            "--db-path",
            db_path,
            "--donation-id",
            str(did),
        )
        assert out["status"] == "ok"


# ============================================================
# Opening Balance CRUD
# ============================================================


class TestOpeningBalance:
    def test_set_list_delete(self, db_path, tmp_path):
        f = write_json(tmp_path, {"account_code": "1001", "amount": 500000}, name="ob.json")
        out = run_ledger(
            "ob-set",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        assert out["account_code"] == "1001"

        out = run_ledger(
            "ob-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 1
        ob_id = out["records"][0]["id"]

        out = run_ledger(
            "ob-delete",
            "--db-path",
            db_path,
            "--opening-balance-id",
            str(ob_id),
        )
        assert out["status"] == "ok"

    def test_set_batch(self, db_path, tmp_path):
        f = write_json(
            tmp_path,
            [
                {"account_code": "1001", "amount": 100000},
                {"account_code": "1002", "amount": 200000},
            ],
            name="ob_batch.json",
        )
        out = run_ledger(
            "ob-set-batch",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f,
        )
        assert out["status"] == "ok"
        assert out["count"] == 2

        out = run_ledger(
            "ob-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["status"] == "ok"
        assert out["count"] == 2

    def test_upsert(self, db_path, tmp_path):
        f1 = write_json(tmp_path, {"account_code": "1001", "amount": 100000}, name="ob1.json")
        run_ledger(
            "ob-set",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f1,
        )

        f2 = write_json(tmp_path, {"account_code": "1001", "amount": 999000}, name="ob2.json")
        run_ledger(
            "ob-set",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            f2,
        )

        out = run_ledger(
            "ob-list",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
        )
        assert out["count"] == 1
        assert out["records"][0]["amount"] == 999000


# ============================================================
# Error handling
# ============================================================


class TestErrorHandling:
    def test_no_subcommand(self):
        r = run_ledger_raw()
        assert r.returncode == 1

    def test_invalid_json(self, db_path, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json at all")
        r = run_ledger_raw(
            "journal-add",
            "--db-path",
            db_path,
            "--fiscal-year",
            "2025",
            "--input",
            str(bad_file),
        )
        assert r.returncode == 1
        out = json.loads(r.stdout)
        assert out["status"] == "error"
