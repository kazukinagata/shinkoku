"""Consumption tax xtx field builder (消費税申告書).

ConsumptionTaxResult モデルから AAJ/AAK コード辞書を生成する。
"""

from __future__ import annotations

from shinkoku.models import ConsumptionTaxResult
from shinkoku.xtx.field_codes import (
    CONSUMPTION_TAX_CODES,
    LOCAL_CONSUMPTION_TAX_CODES,
)


def _add_if_nonzero(fields: dict[str, int | str], code: str, value: int) -> None:
    if value:
        fields[code] = value


def build_consumption_tax_fields(
    result: ConsumptionTaxResult,
) -> dict[str, int | str]:
    """消費税申告書の AAJ/AAK コード辞書を生成する。

    Args:
        result: 消費税計算結果

    Returns:
        {ABBコード: 値} の辞書。0 の値は含まない。
    """
    fields: dict[str, int | str] = {}

    # --- 消費税額の計算 (AAJ) ---
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["taxable_base"], result.taxable_sales_total)
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["consumption_tax"], result.tax_on_sales)
    _add_if_nonzero(
        fields, CONSUMPTION_TAX_CODES["deductible_purchase_tax"], result.tax_on_purchases
    )
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["net_tax"], result.tax_due)
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["tax_due"], result.tax_due)

    # --- 地方消費税額の計算 (AAK) ---
    _add_if_nonzero(fields, LOCAL_CONSUMPTION_TAX_CODES["transfer_tax"], result.local_tax_due)
    _add_if_nonzero(fields, LOCAL_CONSUMPTION_TAX_CODES["local_tax_due"], result.local_tax_due)
    _add_if_nonzero(fields, LOCAL_CONSUMPTION_TAX_CODES["total_tax_due"], result.total_due)

    return fields
