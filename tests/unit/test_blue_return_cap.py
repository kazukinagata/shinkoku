"""青色申告特別控除の自動キャップのユニットテスト。"""

from __future__ import annotations

from shinkoku.models import IncomeTaxInput
from shinkoku.tools.tax_calc import calc_income_tax


def test_profit_less_than_deduction() -> None:
    """利益 < 控除 → 実効控除 = 利益、business_income = 0。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=500_000,
            business_expenses=200_000,
            blue_return_deduction=650_000,
        )
    )
    # 利益 = 500,000 - 200,000 = 300,000
    assert result.effective_blue_return_deduction == 300_000
    assert result.business_income == 0


def test_loss_means_zero_deduction() -> None:
    """赤字 → 実効控除 = 0、business_income = 赤字額。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=165_000,
            business_expenses=350_779,
            blue_return_deduction=650_000,
        )
    )
    assert result.effective_blue_return_deduction == 0
    assert result.business_income == 165_000 - 350_779  # -185,779


def test_profit_exceeds_deduction() -> None:
    """利益 > 控除 → 実効控除 = 控除全額。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=3_000_000,
            business_expenses=1_000_000,
            blue_return_deduction=650_000,
        )
    )
    # 利益 = 2,000,000 > 650,000
    assert result.effective_blue_return_deduction == 650_000
    assert result.business_income == 2_000_000 - 650_000


def test_profit_equals_deduction() -> None:
    """利益 = 控除 → business_income = 0。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=1_000_000,
            business_expenses=350_000,
            blue_return_deduction=650_000,
        )
    )
    assert result.effective_blue_return_deduction == 650_000
    assert result.business_income == 0


def test_zero_revenue_zero_expenses() -> None:
    """収入0・経費0 → 実効控除 = 0。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=0,
            business_expenses=0,
            blue_return_deduction=650_000,
        )
    )
    assert result.effective_blue_return_deduction == 0
    assert result.business_income == 0


def test_warning_on_auto_adjustment() -> None:
    """自動調整時に warnings が出力される。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=500_000,
            business_expenses=200_000,
            blue_return_deduction=650_000,
        )
    )
    assert len(result.warnings) == 1
    assert "自動調整" in result.warnings[0]


def test_no_warning_when_no_adjustment() -> None:
    """調整なしの場合は warnings が空。"""
    result = calc_income_tax(
        IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=3_000_000,
            business_expenses=1_000_000,
            blue_return_deduction=650_000,
        )
    )
    assert len(result.warnings) == 0
