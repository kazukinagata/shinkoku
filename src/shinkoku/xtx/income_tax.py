"""Income tax form xtx field builders (申告書B 第一表・第二表).

IncomeTaxResult / DeductionsResult モデルから ABB コード辞書を生成する。
"""

from __future__ import annotations

from typing import Any

from shinkoku.models import IncomeTaxResult
from shinkoku.xtx.field_codes import (
    DEDUCTION_CODES,
    INCOME_AMOUNT_CODES,
    INCOME_DETAIL_CODES,
    INCOME_DETAIL_TOTAL_CODE,
    INCOME_REVENUE_CODES,
    OTHER_P1_CODES,
    TAX_CALCULATION_CODES,
)

# 控除タイプ → ABBコードキー
_DEDUCTION_TYPE_MAP: dict[str, str] = {
    "social_insurance": "social_insurance",
    "life_insurance": "life_insurance",
    "earthquake_insurance": "earthquake_insurance",
    "medical_expense": "medical_expense",
    "small_enterprise": "small_enterprise",
    "ideco": "small_enterprise",
    "donation": "donation",
    "furusato_nozei": "donation",
    "spouse": "spouse",
    "spouse_special": "spouse",
    "dependent": "dependent",
    "basic": "basic",
    "casualty_loss": "casualty_loss",
    "widow": "widow_single_parent",
    "single_parent": "widow_single_parent",
    "disability": "student_disability",
    "working_student": "student_disability",
    "specified_relative": "specified_relative",
}


def _add_if_nonzero(fields: dict[str, int | str], code: str, value: int) -> None:
    """0 でなければフィールドに追加する。"""
    if value:
        fields[code] = value


def build_income_tax_p1_fields(
    result: IncomeTaxResult,
    *,
    salary_revenue: int = 0,
    business_revenue: int = 0,
    blue_return_deduction: int = 0,
) -> dict[str, int | str]:
    """第一表の ABB コード辞書を生成する。

    Args:
        result: 所得税計算結果
        salary_revenue: 給与収入金額（オプション、ResultにないためIncomeTaxInputから渡す）
        business_revenue: 営業等収入金額（オプション）
        blue_return_deduction: 青色申告特別控除額（オプション）

    Returns:
        {ABBコード: 値} の辞書。0 の値は含まない。
    """
    fields: dict[str, int | str] = {}

    # --- 収入金額等 ---
    _add_if_nonzero(fields, INCOME_REVENUE_CODES["business_revenue"], business_revenue)
    _add_if_nonzero(fields, INCOME_REVENUE_CODES["salary_revenue"], salary_revenue)

    # --- 所得金額等 ---
    _add_if_nonzero(fields, INCOME_AMOUNT_CODES["business_income"], result.business_income)
    _add_if_nonzero(
        fields, INCOME_AMOUNT_CODES["salary_income"], result.salary_income_after_deduction
    )
    _add_if_nonzero(fields, INCOME_AMOUNT_CODES["total_income"], result.total_income)

    # --- 所得控除 ---
    if result.deductions_detail:
        for item in result.deductions_detail.income_deductions:
            code_key = _DEDUCTION_TYPE_MAP.get(item.type)
            if code_key and code_key in DEDUCTION_CODES:
                abb_code = DEDUCTION_CODES[code_key]
                # 同じコードに複数の控除がマッピングされる場合は合算
                fields[abb_code] = fields.get(abb_code, 0) + item.amount  # type: ignore[operator]

    _add_if_nonzero(fields, DEDUCTION_CODES["total_deductions"], result.total_income_deductions)

    # --- 税金の計算 ---
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["taxable_income"], result.taxable_income)
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["tax_on_taxable_income"], result.income_tax_base)
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["dividend_credit"], result.dividend_credit)
    _add_if_nonzero(
        fields, TAX_CALCULATION_CODES["housing_loan_credit"], result.housing_loan_credit
    )
    _add_if_nonzero(
        fields,
        TAX_CALCULATION_CODES["income_tax_after_credits"],
        result.income_tax_after_credits,
    )
    _add_if_nonzero(
        fields, TAX_CALCULATION_CODES["income_tax_net"], result.income_tax_after_credits
    )
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["reconstruction_tax"], result.reconstruction_tax)
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["total_income_tax"], result.total_tax)
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["withheld_tax"], result.withheld_tax)
    _add_if_nonzero(fields, TAX_CALCULATION_CODES["estimated_tax"], result.estimated_tax_payment)

    # 申告納税額
    tax_due = result.tax_due
    if tax_due > 0:
        fields[TAX_CALCULATION_CODES["tax_due"]] = tax_due
        fields[TAX_CALCULATION_CODES["tax_to_pay"]] = tax_due
    elif tax_due < 0:
        fields[TAX_CALCULATION_CODES["tax_refund"]] = abs(tax_due)

    # --- その他 ---
    _add_if_nonzero(fields, OTHER_P1_CODES["blue_return_deduction"], blue_return_deduction)
    _add_if_nonzero(fields, OTHER_P1_CODES["loss_carryforward"], result.loss_carryforward_applied)

    return fields


def build_income_tax_p2_fields(
    *,
    income_details: list[dict[str, Any]] | None = None,
    withheld_tax_total: int = 0,
    social_insurance_details: list[dict[str, Any]] | None = None,
    life_insurance_premiums: dict[str, int] | None = None,
    earthquake_insurance_premiums: dict[str, int] | None = None,
    donation_details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """第二表のフィールドとリピーティンググループを生成する。

    Returns:
        {"fields": {ABBコード: 値}, "repeating_groups": {親コード: [...]}}
    """
    fields: dict[str, int | str] = {}
    repeating_groups: dict[str, list[dict[str, Any]]] = {}

    # --- 所得の内訳 ---
    if income_details:
        items = []
        for detail in income_details:
            item: dict[str, Any] = {}
            if detail.get("income_type"):
                item[INCOME_DETAIL_CODES["income_type"]] = detail["income_type"]
            if detail.get("category"):
                item[INCOME_DETAIL_CODES["category"]] = detail["category"]
            if detail.get("payer_name"):
                item[INCOME_DETAIL_CODES["payer_name"]] = detail["payer_name"]
            if detail.get("revenue"):
                item[INCOME_DETAIL_CODES["revenue"]] = detail["revenue"]
            if detail.get("withheld_tax"):
                item[INCOME_DETAIL_CODES["withheld_tax"]] = detail["withheld_tax"]
            items.append(item)
        repeating_groups["ABD00010"] = items

    if withheld_tax_total:
        fields[INCOME_DETAIL_TOTAL_CODE] = withheld_tax_total

    # --- 社会保険料等の明細 ---
    if social_insurance_details:
        items = []
        for si in social_insurance_details:
            item = {}
            if si.get("insurance_type"):
                item["ABH00130"] = si["insurance_type"]
            if si.get("amount"):
                item["ABH00140"] = si["amount"]
            items.append(item)
        repeating_groups["ABH00120"] = items

    return {
        "fields": fields,
        "repeating_groups": repeating_groups,
    }
