#!/usr/bin/env python3
"""税額計算 CLI スクリプト."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.tools.tax_calc import (  # noqa: E402
    calc_deductions,
    calc_income_tax,
    calc_depreciation_straight_line,
    calc_depreciation_declining_balance,
    calc_consumption_tax,
    calc_furusato_deduction_limit,
    calc_pension_deduction,
    calc_retirement_income,
)
from shinkoku.models import (  # noqa: E402
    IncomeTaxInput,
    ConsumptionTaxInput,
    PensionDeductionInput,
    RetirementIncomeInput,
    LifeInsurancePremiumInput,
    HousingLoanDetail,
    DependentInfo,
    DonationRecordRecord,
    SmallBusinessMutualAidInput,
)


def _load_json(path: str) -> dict:
    """JSON ファイルを読み込んで dict を返す。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _output_json(data: dict) -> None:
    """dict を JSON として stdout に出力する。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _error_exit(message: str) -> None:
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


# ============================================================
# CLI setup
# ============================================================


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="税額計算 CLI")
    sub = parser.add_subparsers(dest="command")

    for name in [
        "calc-deductions",
        "calc-income",
        "calc-depreciation",
        "calc-consumption",
        "calc-furusato-limit",
        "calc-pension",
        "calc-retirement",
    ]:
        p = sub.add_parser(name)
        p.add_argument("--input", required=True, help="入力 JSON ファイルパス")

    return parser


_HANDLERS: dict[str, callable] = {
    "calc-deductions": _handle_calc_deductions,
    "calc-income": _handle_calc_income,
    "calc-depreciation": _handle_calc_depreciation,
    "calc-consumption": _handle_calc_consumption,
    "calc-furusato-limit": _handle_calc_furusato_limit,
    "calc-pension": _handle_calc_pension,
    "calc-retirement": _handle_calc_retirement,
}


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = _HANDLERS.get(args.command)
    if handler is None:
        _error_exit(f"Unknown command: {args.command}")

    try:
        handler(args)
    except Exception as e:
        _error_exit(str(e))


if __name__ == "__main__":
    main()
