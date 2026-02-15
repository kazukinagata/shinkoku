"""Attachment xtx field builders (医療費・家賃・住宅ローン・控除明細).

各種明細データから ABB コード辞書を生成する。
"""

from __future__ import annotations

from typing import Any

from shinkoku.xtx.field_codes import (
    HOUSING_LOAN_CODES,
    MEDICAL_EXPENSE_DETAIL_CODES,
    MEDICAL_EXPENSE_SUMMARY_CODES,
)


def _add_if_nonzero(fields: dict[str, int | str], code: str, value: int) -> None:
    if value:
        fields[code] = value


def build_medical_expense_fields(
    *,
    expenses: list[dict[str, Any]] | None = None,
    total_paid: int = 0,
    total_insurance: int = 0,
    total_income: int = 0,
    medical_deduction: int = 0,
) -> dict[str, Any]:
    """医療費控除明細書の DHC/DHD コード辞書を生成する。

    Returns:
        {"fields": {...}, "repeating_groups": {...}}
    """
    fields: dict[str, int | str] = {}
    repeating_groups: dict[str, list[dict[str, Any]]] = {}

    # 明細行（繰り返し）
    if expenses:
        items = []
        for exp in expenses:
            item: dict[str, Any] = {}
            if exp.get("patient_name"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["patient_name"]] = exp["patient_name"]
            if exp.get("institution_name"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["institution_name"]] = exp["institution_name"]
            if exp.get("amount_paid"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["amount_paid"]] = exp["amount_paid"]
            if exp.get("insurance_amount"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["insurance_amount"]] = exp["insurance_amount"]
            items.append(item)
        repeating_groups["DHC00010"] = items

    # 集計
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["total_paid"], total_paid)
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["total_insurance"], total_insurance)

    net = total_paid - total_insurance
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["net_amount"], net)
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["total_income"], total_income)
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["medical_deduction"], medical_deduction)

    return {
        "fields": fields,
        "repeating_groups": repeating_groups,
    }


def build_housing_loan_fields(
    *,
    credit_amount: int = 0,
    address: str = "",
    name: str = "",
) -> dict[str, int | str]:
    """住宅借入金等特別控除額の計算明細書フィールドを生成する。

    Returns:
        {ABBコード: 値} の辞書
    """
    fields: dict[str, int | str] = {}

    if address:
        fields[HOUSING_LOAN_CODES["address"]] = address
    if name:
        fields[HOUSING_LOAN_CODES["name"]] = name
    _add_if_nonzero(fields, HOUSING_LOAN_CODES["credit_amount"], credit_amount)

    return fields
