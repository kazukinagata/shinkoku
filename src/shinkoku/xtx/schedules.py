"""Schedule xtx field builders (第三表・第四表・減価償却).

SeparateTaxResult モデルから ABL コード辞書を生成する。
"""

from __future__ import annotations

from shinkoku.models import SeparateTaxResult
from shinkoku.xtx.field_codes import (
    SEPARATE_INCOME_CODES,
    SEPARATE_TAX_CODES,
)


def _add_if_nonzero(fields: dict[str, int | str], code: str, value: int) -> None:
    if value:
        fields[code] = value


def build_schedule3_fields(
    result: SeparateTaxResult,
) -> dict[str, int | str]:
    """第三表（分離課税用）の ABL コード辞書を生成する。

    Args:
        result: 分離課税計算結果

    Returns:
        {ABLコード: 値} の辞書。0 の値は含まない。
    """
    fields: dict[str, int | str] = {}

    # --- 分離課税 所得金額 ---
    # 株式: stock_taxable_income → 上場株式等の譲渡 (73)
    _add_if_nonzero(fields, SEPARATE_INCOME_CODES["listed_stock"], result.stock_taxable_income)

    # FX: fx_taxable_income → 先物取引 (75)
    _add_if_nonzero(fields, SEPARATE_INCOME_CODES["futures"], result.fx_taxable_income)

    # --- 課税所得 ---
    _add_if_nonzero(fields, SEPARATE_TAX_CODES["taxable_stock"], result.stock_taxable_income)
    _add_if_nonzero(fields, SEPARATE_TAX_CODES["taxable_futures"], result.fx_taxable_income)

    return fields
