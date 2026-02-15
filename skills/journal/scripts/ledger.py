#!/usr/bin/env python3
"""帳簿管理 CLI スクリプト.

仕訳CRUD、残高試算表、PL/BS、各種マスタCRUD（67サブコマンド）を提供する。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# プロジェクトルートを sys.path に追加（スクリプト直接実行対応）
_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.models import (  # noqa: E402
    BusinessWithholdingInput,
    CryptoIncomeInput,
    DependentInput,
    DonationRecordInput,
    FXLossCarryforwardInput,
    FXTradingInput,
    HousingLoanDetailInput,
    InsurancePolicyInput,
    InventoryInput,
    JournalEntry,
    JournalSearchParams,
    LossCarryforwardInput,
    MedicalExpenseInput,
    OtherIncomeInput,
    ProfessionalFeeInput,
    RentDetailInput,
    SocialInsuranceItemInput,
    SpouseInput,
    StockLossCarryforwardInput,
    StockTradingAccountInput,
    WithholdingSlipInput,
)
from shinkoku.tools.ledger import (  # noqa: E402
    ledger_add_business_withholding,
    ledger_add_crypto_income,
    ledger_add_dependent,
    ledger_add_donation,
    ledger_add_fx_loss_carryforward,
    ledger_add_fx_trading,
    ledger_add_housing_loan_detail,
    ledger_add_insurance_policy,
    ledger_add_journal,
    ledger_add_journals_batch,
    ledger_add_loss_carryforward,
    ledger_add_medical_expense,
    ledger_add_other_income,
    ledger_add_professional_fee,
    ledger_add_rent_detail,
    ledger_add_social_insurance_item,
    ledger_add_stock_loss_carryforward,
    ledger_add_stock_trading_account,
    ledger_bs,
    ledger_check_duplicates,
    ledger_delete_business_withholding,
    ledger_delete_crypto_income,
    ledger_delete_dependent,
    ledger_delete_donation,
    ledger_delete_fx_loss_carryforward,
    ledger_delete_fx_trading,
    ledger_delete_housing_loan_detail,
    ledger_delete_insurance_policy,
    ledger_delete_inventory,
    ledger_delete_journal,
    ledger_delete_loss_carryforward,
    ledger_delete_medical_expense,
    ledger_delete_other_income,
    ledger_delete_professional_fee,
    ledger_delete_rent_detail,
    ledger_delete_social_insurance_item,
    ledger_delete_stock_loss_carryforward,
    ledger_delete_stock_trading_account,
    ledger_delete_spouse,
    ledger_delete_withholding_slip,
    ledger_get_spouse,
    ledger_init,
    ledger_list_business_withholding,
    ledger_list_crypto_income,
    ledger_list_dependents,
    ledger_list_donations,
    ledger_list_fx_loss_carryforward,
    ledger_list_fx_trading,
    ledger_list_housing_loan_details,
    ledger_list_insurance_policies,
    ledger_list_inventory,
    ledger_list_loss_carryforward,
    ledger_list_medical_expenses,
    ledger_list_other_income,
    ledger_list_professional_fees,
    ledger_list_rent_details,
    ledger_list_social_insurance_items,
    ledger_list_stock_loss_carryforward,
    ledger_list_stock_trading_accounts,
    ledger_list_withholding_slips,
    ledger_pl,
    ledger_save_withholding_slip,
    ledger_search,
    ledger_set_inventory,
    ledger_set_spouse,
    ledger_trial_balance,
    ledger_update_journal,
)


def _load_json(path: str) -> Any:
    """JSON ファイルを読み込んで返す。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _output(result: dict) -> int:
    """結果を JSON で stdout に出力し、終了コードを返す。"""
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") != "error" else 1


def _error(message: str) -> int:
    """エラーを JSON で stdout に出力し、終了コード 1 を返す。"""
    print(json.dumps({"status": "error", "message": message}, ensure_ascii=False))
    return 1


# ============================================================
# サブコマンドハンドラ
# ============================================================


def cmd_init(args: argparse.Namespace) -> int:
    return _output(ledger_init(fiscal_year=args.fiscal_year, db_path=args.db_path))


def cmd_journal_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    entry = JournalEntry(**data)
    return _output(
        ledger_add_journal(
            db_path=args.db_path,
            fiscal_year=args.fiscal_year,
            entry=entry,
            force=args.force,
        )
    )


def cmd_journal_batch_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    if not isinstance(data, list):
        return _error("Input must be a JSON array of journal entries")
    entries = [JournalEntry(**e) for e in data]
    return _output(
        ledger_add_journals_batch(
            db_path=args.db_path,
            fiscal_year=args.fiscal_year,
            entries=entries,
            force=args.force,
        )
    )


def cmd_search(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    params = JournalSearchParams(**data)
    return _output(ledger_search(db_path=args.db_path, params=params))


def cmd_journal_update(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    entry = JournalEntry(**data)
    return _output(
        ledger_update_journal(
            db_path=args.db_path,
            journal_id=args.journal_id,
            fiscal_year=args.fiscal_year,
            entry=entry,
        )
    )


def cmd_journal_delete(args: argparse.Namespace) -> int:
    return _output(ledger_delete_journal(db_path=args.db_path, journal_id=args.journal_id))


def cmd_trial_balance(args: argparse.Namespace) -> int:
    return _output(ledger_trial_balance(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_pl(args: argparse.Namespace) -> int:
    return _output(ledger_pl(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_bs(args: argparse.Namespace) -> int:
    return _output(ledger_bs(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_check_duplicates(args: argparse.Namespace) -> int:
    return _output(
        ledger_check_duplicates(
            db_path=args.db_path,
            fiscal_year=args.fiscal_year,
            threshold=args.threshold,
        )
    )


# --- Business Withholding ---


def cmd_bw_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = BusinessWithholdingInput(**data)
    return _output(
        ledger_add_business_withholding(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_bw_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_business_withholding(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_bw_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_business_withholding(db_path=args.db_path, withholding_id=args.withholding_id)
    )


# --- Loss Carryforward ---


def cmd_lc_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = LossCarryforwardInput(**data)
    return _output(
        ledger_add_loss_carryforward(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_lc_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_loss_carryforward(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_lc_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_loss_carryforward(
            db_path=args.db_path, loss_carryforward_id=args.loss_carryforward_id
        )
    )


# --- Medical Expense ---


def cmd_me_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = MedicalExpenseInput(**data)
    return _output(
        ledger_add_medical_expense(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_me_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_medical_expenses(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_me_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_medical_expense(
            db_path=args.db_path, medical_expense_id=args.medical_expense_id
        )
    )


# --- Rent Detail ---


def cmd_rd_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = RentDetailInput(**data)
    return _output(
        ledger_add_rent_detail(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_rd_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_rent_details(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_rd_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_rent_detail(db_path=args.db_path, rent_detail_id=args.rent_detail_id)
    )


# --- Housing Loan Detail ---


def cmd_hl_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = HousingLoanDetailInput(**data)
    return _output(
        ledger_add_housing_loan_detail(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_hl_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_housing_loan_details(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_hl_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_housing_loan_detail(
            db_path=args.db_path, housing_loan_detail_id=args.housing_loan_detail_id
        )
    )


# --- Spouse ---


def cmd_spouse_set(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = SpouseInput(**data)
    return _output(
        ledger_set_spouse(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_spouse_get(args: argparse.Namespace) -> int:
    return _output(ledger_get_spouse(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_spouse_delete(args: argparse.Namespace) -> int:
    return _output(ledger_delete_spouse(db_path=args.db_path, fiscal_year=args.fiscal_year))


# --- Dependent ---


def cmd_dep_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = DependentInput(**data)
    return _output(
        ledger_add_dependent(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_dep_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_dependents(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_dep_delete(args: argparse.Namespace) -> int:
    return _output(ledger_delete_dependent(db_path=args.db_path, dependent_id=args.dependent_id))


# --- Withholding Slip ---


def cmd_ws_save(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = WithholdingSlipInput(**data)
    return _output(
        ledger_save_withholding_slip(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_ws_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_withholding_slips(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_ws_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_withholding_slip(
            db_path=args.db_path, withholding_slip_id=args.withholding_slip_id
        )
    )


# --- Other Income ---


def cmd_oi_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = OtherIncomeInput(**data)
    return _output(
        ledger_add_other_income(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_oi_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_other_income(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_oi_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_other_income(db_path=args.db_path, other_income_id=args.other_income_id)
    )


# --- Crypto Income ---


def cmd_ci_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = CryptoIncomeInput(**data)
    return _output(
        ledger_add_crypto_income(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_ci_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_crypto_income(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_ci_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_crypto_income(db_path=args.db_path, crypto_income_id=args.crypto_income_id)
    )


# --- Inventory ---


def cmd_inv_set(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = InventoryInput(**data)
    return _output(
        ledger_set_inventory(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_inv_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_inventory(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_inv_delete(args: argparse.Namespace) -> int:
    return _output(ledger_delete_inventory(db_path=args.db_path, inventory_id=args.inventory_id))


# --- Professional Fee ---


def cmd_pf_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = ProfessionalFeeInput(**data)
    return _output(
        ledger_add_professional_fee(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_pf_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_professional_fees(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_pf_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_professional_fee(
            db_path=args.db_path, professional_fee_id=args.professional_fee_id
        )
    )


# --- Stock Trading Account ---


def cmd_sta_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = StockTradingAccountInput(**data)
    return _output(
        ledger_add_stock_trading_account(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_sta_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_stock_trading_accounts(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_sta_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_stock_trading_account(
            db_path=args.db_path,
            stock_trading_account_id=args.stock_trading_account_id,
        )
    )


# --- Stock Loss Carryforward ---


def cmd_slc_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = StockLossCarryforwardInput(**data)
    return _output(
        ledger_add_stock_loss_carryforward(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_slc_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_stock_loss_carryforward(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_slc_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_stock_loss_carryforward(
            db_path=args.db_path,
            stock_loss_carryforward_id=args.stock_loss_carryforward_id,
        )
    )


# --- FX Trading ---


def cmd_fx_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = FXTradingInput(**data)
    return _output(
        ledger_add_fx_trading(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_fx_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_fx_trading(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_fx_delete(args: argparse.Namespace) -> int:
    return _output(ledger_delete_fx_trading(db_path=args.db_path, fx_trading_id=args.fx_trading_id))


# --- FX Loss Carryforward ---


def cmd_fxlc_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = FXLossCarryforwardInput(**data)
    return _output(
        ledger_add_fx_loss_carryforward(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_fxlc_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_fx_loss_carryforward(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_fxlc_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_fx_loss_carryforward(
            db_path=args.db_path,
            fx_loss_carryforward_id=args.fx_loss_carryforward_id,
        )
    )


# --- Social Insurance Item ---


def cmd_si_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = SocialInsuranceItemInput(**data)
    return _output(
        ledger_add_social_insurance_item(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_si_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_social_insurance_items(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_si_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_social_insurance_item(
            db_path=args.db_path,
            social_insurance_item_id=args.social_insurance_item_id,
        )
    )


# --- Insurance Policy ---


def cmd_ip_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = InsurancePolicyInput(**data)
    return _output(
        ledger_add_insurance_policy(
            db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail
        )
    )


def cmd_ip_list(args: argparse.Namespace) -> int:
    return _output(
        ledger_list_insurance_policies(db_path=args.db_path, fiscal_year=args.fiscal_year)
    )


def cmd_ip_delete(args: argparse.Namespace) -> int:
    return _output(
        ledger_delete_insurance_policy(
            db_path=args.db_path, insurance_policy_id=args.insurance_policy_id
        )
    )


# --- Donation ---


def cmd_don_add(args: argparse.Namespace) -> int:
    data = _load_json(args.input)
    detail = DonationRecordInput(**data)
    return _output(
        ledger_add_donation(db_path=args.db_path, fiscal_year=args.fiscal_year, detail=detail)
    )


def cmd_don_list(args: argparse.Namespace) -> int:
    return _output(ledger_list_donations(db_path=args.db_path, fiscal_year=args.fiscal_year))


def cmd_don_delete(args: argparse.Namespace) -> int:
    return _output(ledger_delete_donation(db_path=args.db_path, donation_id=args.donation_id))


# ============================================================
# argparse 定義
# ============================================================


def _add_db_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--db-path", required=True, help="DB ファイルパス")


def _add_fy_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--fiscal-year", required=True, type=int, help="会計年度")


def _add_input_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument("--input", required=True, help="JSON ファイルパス")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="帳簿管理 CLI（仕訳CRUD・財務諸表・各種マスタ）",
    )
    sub = parser.add_subparsers(dest="command")

    # --- init ---
    p = sub.add_parser("init", help="DB初期化")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_init)

    # --- journal CRUD ---
    p = sub.add_parser("journal-add", help="仕訳追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.add_argument("--force", action="store_true", help="類似重複を無視")
    p.set_defaults(func=cmd_journal_add)

    p = sub.add_parser("journal-batch-add", help="仕訳一括追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.add_argument("--force", action="store_true", help="類似重複を無視")
    p.set_defaults(func=cmd_journal_batch_add)

    p = sub.add_parser("search", help="仕訳検索")
    _add_db_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("journal-update", help="仕訳更新")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.add_argument("--journal-id", required=True, type=int)
    _add_input_arg(p)
    p.set_defaults(func=cmd_journal_update)

    p = sub.add_parser("journal-delete", help="仕訳削除")
    _add_db_arg(p)
    p.add_argument("--journal-id", required=True, type=int)
    p.set_defaults(func=cmd_journal_delete)

    # --- 財務諸表 ---
    p = sub.add_parser("trial-balance", help="残高試算表")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_trial_balance)

    p = sub.add_parser("pl", help="損益計算書")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_pl)

    p = sub.add_parser("bs", help="貸借対照表")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_bs)

    p = sub.add_parser("check-duplicates", help="重複チェック")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.add_argument("--threshold", type=int, default=70)
    p.set_defaults(func=cmd_check_duplicates)

    # --- Business Withholding ---
    p = sub.add_parser("bw-add", help="事業源泉徴収追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_bw_add)

    p = sub.add_parser("bw-list", help="事業源泉徴収一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_bw_list)

    p = sub.add_parser("bw-delete", help="事業源泉徴収削除")
    _add_db_arg(p)
    p.add_argument("--withholding-id", required=True, type=int)
    p.set_defaults(func=cmd_bw_delete)

    # --- Loss Carryforward ---
    p = sub.add_parser("lc-add", help="損失繰越追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_lc_add)

    p = sub.add_parser("lc-list", help="損失繰越一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_lc_list)

    p = sub.add_parser("lc-delete", help="損失繰越削除")
    _add_db_arg(p)
    p.add_argument("--loss-carryforward-id", required=True, type=int)
    p.set_defaults(func=cmd_lc_delete)

    # --- Medical Expense ---
    p = sub.add_parser("me-add", help="医療費明細追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_me_add)

    p = sub.add_parser("me-list", help="医療費明細一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_me_list)

    p = sub.add_parser("me-delete", help="医療費明細削除")
    _add_db_arg(p)
    p.add_argument("--medical-expense-id", required=True, type=int)
    p.set_defaults(func=cmd_me_delete)

    # --- Rent Detail ---
    p = sub.add_parser("rd-add", help="地代家賃追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_rd_add)

    p = sub.add_parser("rd-list", help="地代家賃一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_rd_list)

    p = sub.add_parser("rd-delete", help="地代家賃削除")
    _add_db_arg(p)
    p.add_argument("--rent-detail-id", required=True, type=int)
    p.set_defaults(func=cmd_rd_delete)

    # --- Housing Loan Detail ---
    p = sub.add_parser("hl-add", help="住宅ローン控除追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_hl_add)

    p = sub.add_parser("hl-list", help="住宅ローン控除一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_hl_list)

    p = sub.add_parser("hl-delete", help="住宅ローン控除削除")
    _add_db_arg(p)
    p.add_argument("--housing-loan-detail-id", required=True, type=int)
    p.set_defaults(func=cmd_hl_delete)

    # --- Spouse ---
    p = sub.add_parser("spouse-set", help="配偶者情報設定")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_spouse_set)

    p = sub.add_parser("spouse-get", help="配偶者情報取得")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_spouse_get)

    p = sub.add_parser("spouse-delete", help="配偶者情報削除")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_spouse_delete)

    # --- Dependent ---
    p = sub.add_parser("dep-add", help="扶養親族追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_dep_add)

    p = sub.add_parser("dep-list", help="扶養親族一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_dep_list)

    p = sub.add_parser("dep-delete", help="扶養親族削除")
    _add_db_arg(p)
    p.add_argument("--dependent-id", required=True, type=int)
    p.set_defaults(func=cmd_dep_delete)

    # --- Withholding Slip ---
    p = sub.add_parser("ws-save", help="源泉徴収票保存")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_ws_save)

    p = sub.add_parser("ws-list", help="源泉徴収票一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_ws_list)

    p = sub.add_parser("ws-delete", help="源泉徴収票削除")
    _add_db_arg(p)
    p.add_argument("--withholding-slip-id", required=True, type=int)
    p.set_defaults(func=cmd_ws_delete)

    # --- Other Income ---
    p = sub.add_parser("oi-add", help="その他所得追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_oi_add)

    p = sub.add_parser("oi-list", help="その他所得一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_oi_list)

    p = sub.add_parser("oi-delete", help="その他所得削除")
    _add_db_arg(p)
    p.add_argument("--other-income-id", required=True, type=int)
    p.set_defaults(func=cmd_oi_delete)

    # --- Crypto Income ---
    p = sub.add_parser("ci-add", help="仮想通貨所得追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_ci_add)

    p = sub.add_parser("ci-list", help="仮想通貨所得一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_ci_list)

    p = sub.add_parser("ci-delete", help="仮想通貨所得削除")
    _add_db_arg(p)
    p.add_argument("--crypto-income-id", required=True, type=int)
    p.set_defaults(func=cmd_ci_delete)

    # --- Inventory ---
    p = sub.add_parser("inv-set", help="在庫棚卸設定")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_inv_set)

    p = sub.add_parser("inv-list", help="在庫棚卸一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_inv_list)

    p = sub.add_parser("inv-delete", help="在庫棚卸削除")
    _add_db_arg(p)
    p.add_argument("--inventory-id", required=True, type=int)
    p.set_defaults(func=cmd_inv_delete)

    # --- Professional Fee ---
    p = sub.add_parser("pf-add", help="税理士等報酬追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_pf_add)

    p = sub.add_parser("pf-list", help="税理士等報酬一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_pf_list)

    p = sub.add_parser("pf-delete", help="税理士等報酬削除")
    _add_db_arg(p)
    p.add_argument("--professional-fee-id", required=True, type=int)
    p.set_defaults(func=cmd_pf_delete)

    # --- Stock Trading Account ---
    p = sub.add_parser("sta-add", help="株式取引口座追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_sta_add)

    p = sub.add_parser("sta-list", help="株式取引口座一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_sta_list)

    p = sub.add_parser("sta-delete", help="株式取引口座削除")
    _add_db_arg(p)
    p.add_argument("--stock-trading-account-id", required=True, type=int)
    p.set_defaults(func=cmd_sta_delete)

    # --- Stock Loss Carryforward ---
    p = sub.add_parser("slc-add", help="株式損失繰越追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_slc_add)

    p = sub.add_parser("slc-list", help="株式損失繰越一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_slc_list)

    p = sub.add_parser("slc-delete", help="株式損失繰越削除")
    _add_db_arg(p)
    p.add_argument("--stock-loss-carryforward-id", required=True, type=int)
    p.set_defaults(func=cmd_slc_delete)

    # --- FX Trading ---
    p = sub.add_parser("fx-add", help="FX取引追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_fx_add)

    p = sub.add_parser("fx-list", help="FX取引一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_fx_list)

    p = sub.add_parser("fx-delete", help="FX取引削除")
    _add_db_arg(p)
    p.add_argument("--fx-trading-id", required=True, type=int)
    p.set_defaults(func=cmd_fx_delete)

    # --- FX Loss Carryforward ---
    p = sub.add_parser("fxlc-add", help="FX損失繰越追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_fxlc_add)

    p = sub.add_parser("fxlc-list", help="FX損失繰越一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_fxlc_list)

    p = sub.add_parser("fxlc-delete", help="FX損失繰越削除")
    _add_db_arg(p)
    p.add_argument("--fx-loss-carryforward-id", required=True, type=int)
    p.set_defaults(func=cmd_fxlc_delete)

    # --- Social Insurance Item ---
    p = sub.add_parser("si-add", help="社会保険料追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_si_add)

    p = sub.add_parser("si-list", help="社会保険料一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_si_list)

    p = sub.add_parser("si-delete", help="社会保険料削除")
    _add_db_arg(p)
    p.add_argument("--social-insurance-item-id", required=True, type=int)
    p.set_defaults(func=cmd_si_delete)

    # --- Insurance Policy ---
    p = sub.add_parser("ip-add", help="保険契約追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_ip_add)

    p = sub.add_parser("ip-list", help="保険契約一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_ip_list)

    p = sub.add_parser("ip-delete", help="保険契約削除")
    _add_db_arg(p)
    p.add_argument("--insurance-policy-id", required=True, type=int)
    p.set_defaults(func=cmd_ip_delete)

    # --- Donation ---
    p = sub.add_parser("don-add", help="寄附金追加")
    _add_db_arg(p)
    _add_fy_arg(p)
    _add_input_arg(p)
    p.set_defaults(func=cmd_don_add)

    p = sub.add_parser("don-list", help="寄附金一覧")
    _add_db_arg(p)
    _add_fy_arg(p)
    p.set_defaults(func=cmd_don_list)

    p = sub.add_parser("don-delete", help="寄附金削除")
    _add_db_arg(p)
    p.add_argument("--donation-id", required=True, type=int)
    p.set_defaults(func=cmd_don_delete)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    try:
        return args.func(args)
    except Exception as e:
        return _error(str(e))


if __name__ == "__main__":
    sys.exit(main())
