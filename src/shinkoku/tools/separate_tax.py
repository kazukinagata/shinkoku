"""Separate taxation (分離課税) calculations for stocks and FX.

Stock trading: 20.315% (income tax 15% + residential tax 5% + reconstruction 0.315%)
FX trading: 20.315% (先物取引に係る雑所得等)
Stock and FX losses cannot offset each other (separate pools).
"""

from __future__ import annotations

from shinkoku.models import SeparateTaxInput, SeparateTaxResult
from shinkoku.tax_constants import (
    RECONSTRUCTION_TAX_DENOMINATOR,
    RECONSTRUCTION_TAX_RATE,
    SEPARATE_TAX_INCOME_RATE,
    SEPARATE_TAX_RESIDENTIAL_RATE,
)


def calc_separate_tax(input_data: SeparateTaxInput) -> SeparateTaxResult:
    """Calculate separate taxation for stock and FX trading.

    Stock:
    1. Net gain = gains - losses
    2. 損益通算: 配当（分離課税選択）と株式譲渡損を通算
    3. 繰越損失の適用（3年）
    4. 税率: 所得税15% + 住民税5% + 復興特別所得税0.315%
    5. 源泉徴収済み税額の差引

    FX:
    1. Net income = realized_gains + swap_income - expenses
    2. 繰越損失の適用（3年）
    3. 税率: 同上
    """
    # === Stock ===
    stock_net = input_data.stock_gains - input_data.stock_losses

    # 損益通算: 株式譲渡損と分離課税配当
    stock_dividend_offset = 0
    if stock_net < 0 and input_data.stock_dividend_separate > 0:
        # 譲渡損で配当を相殺
        stock_dividend_offset = min(-stock_net, input_data.stock_dividend_separate)
        stock_taxable_base = input_data.stock_dividend_separate - stock_dividend_offset
    elif stock_net >= 0:
        stock_taxable_base = stock_net + input_data.stock_dividend_separate
    else:
        stock_taxable_base = max(0, input_data.stock_dividend_separate + stock_net)
        stock_dividend_offset = min(-stock_net, input_data.stock_dividend_separate)

    # 繰越損失の適用
    stock_loss_used = 0
    if input_data.stock_loss_carryforward > 0 and stock_taxable_base > 0:
        stock_loss_used = min(input_data.stock_loss_carryforward, stock_taxable_base)
        stock_taxable_base -= stock_loss_used

    stock_taxable = max(0, stock_taxable_base)

    # 税額計算
    stock_income_tax = stock_taxable * SEPARATE_TAX_INCOME_RATE // 100
    stock_residential_tax = stock_taxable * SEPARATE_TAX_RESIDENTIAL_RATE // 100
    # 復興特別所得税 = 所得税 × 2.1%
    stock_reconstruction = int(stock_income_tax * RECONSTRUCTION_TAX_RATE // RECONSTRUCTION_TAX_DENOMINATOR)
    stock_total = stock_income_tax + stock_residential_tax + stock_reconstruction

    # 源泉徴収差引
    stock_withheld = (
        input_data.stock_withheld_income_tax + input_data.stock_withheld_residential_tax
    )
    stock_due = stock_total - stock_withheld

    # === FX ===
    fx_net = input_data.fx_gains - input_data.fx_expenses

    # 繰越損失の適用
    fx_loss_used = 0
    if input_data.fx_loss_carryforward > 0 and fx_net > 0:
        fx_loss_used = min(input_data.fx_loss_carryforward, fx_net)
        fx_net -= fx_loss_used

    fx_taxable = max(0, fx_net)

    # 税額計算
    fx_income_tax = fx_taxable * SEPARATE_TAX_INCOME_RATE // 100
    fx_residential_tax = fx_taxable * SEPARATE_TAX_RESIDENTIAL_RATE // 100
    fx_reconstruction = int(fx_income_tax * RECONSTRUCTION_TAX_RATE // RECONSTRUCTION_TAX_DENOMINATOR)
    fx_total = fx_income_tax + fx_residential_tax + fx_reconstruction
    fx_due = fx_total  # FX は源泉徴収なし

    return SeparateTaxResult(
        fiscal_year=input_data.fiscal_year,
        # Stock
        stock_net_gain=input_data.stock_gains - input_data.stock_losses,
        stock_dividend_offset=stock_dividend_offset,
        stock_taxable_income=stock_taxable,
        stock_loss_carryforward_used=stock_loss_used,
        stock_income_tax=stock_income_tax,
        stock_residential_tax=stock_residential_tax,
        stock_reconstruction_tax=stock_reconstruction,
        stock_total_tax=stock_total,
        stock_withheld_total=stock_withheld,
        stock_tax_due=stock_due,
        # FX
        fx_net_income=input_data.fx_gains - input_data.fx_expenses,
        fx_taxable_income=fx_taxable,
        fx_loss_carryforward_used=fx_loss_used,
        fx_income_tax=fx_income_tax,
        fx_residential_tax=fx_residential_tax,
        fx_reconstruction_tax=fx_reconstruction,
        fx_total_tax=fx_total,
        fx_tax_due=fx_due,
        # Total
        total_separate_tax=stock_total + fx_total,
    )


def register(mcp) -> None:
    """Register separate tax tools with the MCP server."""

    @mcp.tool()
    def tax_calc_separate(
        fiscal_year: int,
        stock_gains: int = 0,
        stock_losses: int = 0,
        stock_dividend_separate: int = 0,
        stock_withheld_income_tax: int = 0,
        stock_withheld_residential_tax: int = 0,
        stock_loss_carryforward: int = 0,
        fx_gains: int = 0,
        fx_expenses: int = 0,
        fx_loss_carryforward: int = 0,
    ) -> dict:
        """Calculate separate taxation for stock and FX trading."""
        input_data = SeparateTaxInput(
            fiscal_year=fiscal_year,
            stock_gains=stock_gains,
            stock_losses=stock_losses,
            stock_dividend_separate=stock_dividend_separate,
            stock_withheld_income_tax=stock_withheld_income_tax,
            stock_withheld_residential_tax=stock_withheld_residential_tax,
            stock_loss_carryforward=stock_loss_carryforward,
            fx_gains=fx_gains,
            fx_expenses=fx_expenses,
            fx_loss_carryforward=fx_loss_carryforward,
        )
        result = calc_separate_tax(input_data)
        return result.model_dump()
