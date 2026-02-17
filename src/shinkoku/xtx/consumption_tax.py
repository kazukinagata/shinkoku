"""Consumption tax xtx field builder (消費税申告書).

ConsumptionTaxResult モデルから AAJ/AAK コード辞書を生成する。

フィールドマッピング（消費税法に基づく正しい対応）:
  AAJ00010 (課税標準額)   ← taxable_base_10 + taxable_base_8（税抜, 1000円切捨済）
  AAJ00020 (消費税額)     ← national_tax_on_sales（国税7.8%+6.24%部分）
  AAJ00050 (控除対象仕入税額) ← tax_on_purchases
  AAJ00090 (控除不足還付税額) ← refund_shortfall（還付の場合）
  AAJ00100 (差引税額)     ← net_tax（100円切捨, 正の場合のみ）
  AAJ00110 (中間納付税額) ← interim_payment
  AAJ00120 (納付税額)     ← tax_due（正の場合）
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
    # AAJ00010: 課税標準額 = 税抜課税標準額の合計（1,000円切捨済）
    taxable_base = result.taxable_base_10 + result.taxable_base_8
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["taxable_base"], taxable_base)

    # AAJ00020: 消費税額 = 国税部分（7.8% + 6.24%）
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["consumption_tax"], result.national_tax_on_sales)

    # AAJ00050: 控除対象仕入税額
    _add_if_nonzero(
        fields, CONSUMPTION_TAX_CODES["deductible_purchase_tax"], result.tax_on_purchases
    )

    # AAJ00090: 控除不足還付税額（仕入税額 > 売上税額の場合）
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["refund_shortfall"], result.refund_shortfall)

    # AAJ00100: 差引税額（100円切捨, 正の場合のみ）
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["net_tax"], result.net_tax)

    # AAJ00110: 中間納付税額
    _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["interim_payment"], result.interim_payment)

    # AAJ00120: 納付税額
    if result.tax_due > 0:
        _add_if_nonzero(fields, CONSUMPTION_TAX_CODES["tax_due"], result.tax_due)

    # --- 地方消費税額の計算 (AAK) ---
    _add_if_nonzero(fields, LOCAL_CONSUMPTION_TAX_CODES["transfer_tax"], abs(result.local_tax_due))
    _add_if_nonzero(fields, LOCAL_CONSUMPTION_TAX_CODES["local_tax_due"], abs(result.local_tax_due))
    _add_if_nonzero(fields, LOCAL_CONSUMPTION_TAX_CODES["total_tax_due"], result.total_due)

    return fields
