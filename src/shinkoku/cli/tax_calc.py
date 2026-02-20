"""税額計算 CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

from shinkoku.models import (
    ConsumptionTaxInput,
    DependentInfo,
    DonationRecordRecord,
    HousingLoanDetail,
    IncomeTaxInput,
    IncomeTaxResult,
    LifeInsurancePremiumInput,
    PensionDeductionInput,
    RetirementIncomeInput,
    SmallBusinessMutualAidInput,
)
from shinkoku.tools.tax_calc import (
    calc_consumption_tax,
    calc_deductions,
    calc_depreciation_declining_balance,
    calc_depreciation_straight_line,
    calc_furusato_deduction_limit,
    calc_income_tax,
    calc_pension_deduction,
    calc_retirement_income,
    sanity_check_income_tax,
)


def _load_json(path: str) -> dict:
    """JSON ファイルを読み込んで dict を返す。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _output_json(data: dict) -> None:
    """dict を JSON として stdout に出力する。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _error_exit(message: str) -> NoReturn:
    """エラーメッセージを JSON で stdout に出力して終了する。"""
    _output_json({"status": "error", "message": message})
    sys.exit(1)


# ============================================================
# Subcommand handlers
# ============================================================


def _handle_calc_deductions(args: argparse.Namespace) -> None:
    """calc-deductions: 控除額計算。"""
    params = _load_json(args.input)

    # ネストされた Pydantic モデルの構築
    life_insurance_detail = None
    if "life_insurance_detail" in params and params["life_insurance_detail"]:
        life_insurance_detail = LifeInsurancePremiumInput(**params.pop("life_insurance_detail"))
    else:
        params.pop("life_insurance_detail", None)

    housing_loan_detail = None
    if "housing_loan_detail" in params and params["housing_loan_detail"]:
        housing_loan_detail = HousingLoanDetail(**params.pop("housing_loan_detail"))
    else:
        params.pop("housing_loan_detail", None)

    dependents = None
    if "dependents" in params and params["dependents"]:
        dependents = [DependentInfo(**d) for d in params.pop("dependents")]
    else:
        params.pop("dependents", None)

    donations = None
    if "donations" in params and params["donations"]:
        donations = [DonationRecordRecord(**d) for d in params.pop("donations")]
    else:
        params.pop("donations", None)

    result = calc_deductions(
        **params,
        life_insurance_detail=life_insurance_detail,
        housing_loan_detail=housing_loan_detail,
        dependents=dependents,
        donations=donations,
    )
    _output_json(result.model_dump())


def _handle_calc_income(args: argparse.Namespace) -> None:
    """calc-income: 所得税計算。"""
    params = _load_json(args.input)

    # ネストされた Pydantic モデルの構築
    if "life_insurance_detail" in params and params["life_insurance_detail"]:
        params["life_insurance_detail"] = LifeInsurancePremiumInput(
            **params["life_insurance_detail"]
        )
    else:
        params.pop("life_insurance_detail", None)

    if "housing_loan_detail" in params and params["housing_loan_detail"]:
        params["housing_loan_detail"] = HousingLoanDetail(**params["housing_loan_detail"])
    else:
        params.pop("housing_loan_detail", None)

    if "dependents" in params and params["dependents"]:
        params["dependents"] = [DependentInfo(**d) for d in params["dependents"]]
    else:
        params.pop("dependents", None)

    if "small_business_mutual_aid" in params and params["small_business_mutual_aid"]:
        params["small_business_mutual_aid"] = SmallBusinessMutualAidInput(
            **params["small_business_mutual_aid"]
        )
    else:
        params.pop("small_business_mutual_aid", None)

    input_data = IncomeTaxInput(**params)
    result = calc_income_tax(input_data)
    _output_json(result.model_dump())


def _handle_calc_depreciation(args: argparse.Namespace) -> None:
    """calc-depreciation: 減価償却計算。"""
    params = _load_json(args.input)
    method = params.pop("method", "straight_line")

    if method == "declining_balance":
        book_value = params.get("book_value")
        declining_rate = params.get("declining_rate")
        if book_value is None or declining_rate is None:
            _error_exit("book_value and declining_rate required for declining balance")
        amount = calc_depreciation_declining_balance(
            book_value=book_value,
            declining_rate=declining_rate,
            business_use_ratio=params.get("business_use_ratio", 100),
            months=params.get("months", 12),
        )
    else:
        amount = calc_depreciation_straight_line(
            acquisition_cost=params.get("acquisition_cost", 0),
            useful_life=params.get("useful_life", 1),
            business_use_ratio=params.get("business_use_ratio", 100),
            months=params.get("months", 12),
        )

    _output_json(
        {
            "method": method,
            "depreciation_amount": amount,
            "acquisition_cost": params.get("acquisition_cost", 0),
            "useful_life": params.get("useful_life", 0),
            "business_use_ratio": params.get("business_use_ratio", 100),
            "months": params.get("months", 12),
        }
    )


def _handle_calc_consumption(args: argparse.Namespace) -> None:
    """calc-consumption: 消費税計算。"""
    params = _load_json(args.input)
    input_data = ConsumptionTaxInput(**params)
    result = calc_consumption_tax(input_data)
    _output_json(result.model_dump())


def _handle_calc_furusato_limit(args: argparse.Namespace) -> None:
    """calc-furusato-limit: ふるさと納税控除上限推定。"""
    params = _load_json(args.input)
    limit = calc_furusato_deduction_limit(**params)
    _output_json({"estimated_limit": limit})


def _handle_calc_pension(args: argparse.Namespace) -> None:
    """calc-pension: 公的年金等控除計算。"""
    params = _load_json(args.input)
    input_data = PensionDeductionInput(**params)
    result = calc_pension_deduction(input_data)
    _output_json(result.model_dump())


def _handle_calc_retirement(args: argparse.Namespace) -> None:
    """calc-retirement: 退職所得計算。"""
    params = _load_json(args.input)
    input_data = RetirementIncomeInput(**params)
    result = calc_retirement_income(input_data)
    _output_json(result.model_dump())


def _handle_sanity_check(args: argparse.Namespace) -> None:
    """sanity-check: 所得税計算結果のサニティチェック。"""
    params = _load_json(args.input)

    if "input" not in params or "result" not in params:
        _error_exit("JSON には 'input' と 'result' の両キーが必要です")

    input_raw = params["input"]
    result_raw = params["result"]

    # ネストされた Pydantic モデルの構築（IncomeTaxInput）
    if "life_insurance_detail" in input_raw and input_raw["life_insurance_detail"]:
        input_raw["life_insurance_detail"] = LifeInsurancePremiumInput(
            **input_raw["life_insurance_detail"]
        )
    else:
        input_raw.pop("life_insurance_detail", None)

    if "housing_loan_detail" in input_raw and input_raw["housing_loan_detail"]:
        input_raw["housing_loan_detail"] = HousingLoanDetail(**input_raw["housing_loan_detail"])
    else:
        input_raw.pop("housing_loan_detail", None)

    if "dependents" in input_raw and input_raw["dependents"]:
        input_raw["dependents"] = [DependentInfo(**d) for d in input_raw["dependents"]]
    else:
        input_raw.pop("dependents", None)

    if "small_business_mutual_aid" in input_raw and input_raw["small_business_mutual_aid"]:
        input_raw["small_business_mutual_aid"] = SmallBusinessMutualAidInput(
            **input_raw["small_business_mutual_aid"]
        )
    else:
        input_raw.pop("small_business_mutual_aid", None)

    input_data = IncomeTaxInput(**input_raw)
    tax_result = IncomeTaxResult(**result_raw)
    check_result = sanity_check_income_tax(input_data, tax_result)
    _output_json(check_result.model_dump())


_HANDLERS: dict[str, Callable[[argparse.Namespace], None]] = {
    "calc-deductions": _handle_calc_deductions,
    "calc-income": _handle_calc_income,
    "calc-depreciation": _handle_calc_depreciation,
    "calc-consumption": _handle_calc_consumption,
    "calc-furusato-limit": _handle_calc_furusato_limit,
    "calc-pension": _handle_calc_pension,
    "calc-retirement": _handle_calc_retirement,
    "sanity-check": _handle_sanity_check,
}


def _dispatch(args: argparse.Namespace) -> None:
    """サブコマンドをディスパッチする。"""
    handler = _HANDLERS.get(args.subcommand)
    if handler is None:
        _error_exit(f"Unknown command: {args.subcommand}")
    try:
        handler(args)
    except Exception as e:
        _error_exit(str(e))


def register(parent_subparsers: argparse._SubParsersAction) -> None:
    """tax サブコマンドを親パーサーに登録する。"""
    parser = parent_subparsers.add_parser(
        "tax",
        description="税額計算 CLI",
        help="税額計算",
    )
    sub = parser.add_subparsers(dest="subcommand")

    for name in [
        "calc-deductions",
        "calc-income",
        "calc-depreciation",
        "calc-consumption",
        "calc-furusato-limit",
        "calc-pension",
        "calc-retirement",
        "sanity-check",
    ]:
        p = sub.add_parser(name)
        p.add_argument("--input", required=True, help="入力 JSON ファイルパス")
        p.set_defaults(func=_dispatch)

    parser.set_defaults(func=lambda args: parser.print_help() or sys.exit(1))
