"""サニティチェックのユニットテスト。"""

from __future__ import annotations

from shinkoku.models import IncomeTaxInput, IncomeTaxResult
from shinkoku.tools.tax_calc import sanity_check_income_tax


def _make_input(**kwargs) -> IncomeTaxInput:
    defaults = {"fiscal_year": 2025}
    defaults.update(kwargs)
    return IncomeTaxInput(**defaults)


def _make_result(**kwargs) -> IncomeTaxResult:
    defaults = {"fiscal_year": 2025, "tax_due": 0}
    defaults.update(kwargs)
    return IncomeTaxResult(**defaults)


# --- 1. BLUE_DEDUCTION_ON_LOSS ---


def test_blue_deduction_on_loss() -> None:
    """赤字なのに控除適用 → error。"""
    inp = _make_input(business_revenue=100_000, business_expenses=200_000)
    res = _make_result(effective_blue_return_deduction=50_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "BLUE_DEDUCTION_ON_LOSS" in codes
    assert not check.passed


def test_no_blue_deduction_on_loss() -> None:
    """赤字で控除0 → OK。"""
    inp = _make_input(business_revenue=100_000, business_expenses=200_000)
    res = _make_result(effective_blue_return_deduction=0)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "BLUE_DEDUCTION_ON_LOSS" not in codes


# --- 2. BLUE_DEDUCTION_EXCEEDS_PROFIT ---


def test_blue_deduction_exceeds_profit() -> None:
    """控除が利益超過 → error。"""
    inp = _make_input(business_revenue=500_000, business_expenses=200_000)
    # 利益=300,000 だが控除が400,000（通常はキャップされるが、手動構築を想定）
    res = _make_result(effective_blue_return_deduction=400_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "BLUE_DEDUCTION_EXCEEDS_PROFIT" in codes


def test_blue_deduction_within_profit() -> None:
    """控除が利益以下 → OK。"""
    inp = _make_input(business_revenue=3_000_000, business_expenses=1_000_000)
    res = _make_result(effective_blue_return_deduction=650_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "BLUE_DEDUCTION_EXCEEDS_PROFIT" not in codes


# --- 3. LARGE_BUSINESS_LOSS ---


def test_large_business_loss() -> None:
    """事業損失が1,000万円超 → warning。"""
    inp = _make_input(business_revenue=1_000_000, business_expenses=12_000_000)
    res = _make_result(business_income=-11_000_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "LARGE_BUSINESS_LOSS" in codes


def test_moderate_business_loss() -> None:
    """事業損失が1,000万以下 → OK。"""
    inp = _make_input(business_revenue=1_000_000, business_expenses=5_000_000)
    res = _make_result(business_income=-4_000_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "LARGE_BUSINESS_LOSS" not in codes


# --- 4. TAX_ON_ZERO_INCOME ---


def test_tax_on_zero_income() -> None:
    """課税所得0なのに税額発生 → error。"""
    inp = _make_input()
    res = _make_result(taxable_income=0, income_tax_base=10_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "TAX_ON_ZERO_INCOME" in codes


def test_no_tax_on_zero_income() -> None:
    """課税所得0で税額0 → OK。"""
    inp = _make_input()
    res = _make_result(taxable_income=0, income_tax_base=0)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "TAX_ON_ZERO_INCOME" not in codes


# --- 5. NEGATIVE_TOTAL_INCOME ---


def test_negative_total_income() -> None:
    """合計所得が負 → info。"""
    inp = _make_input()
    res = _make_result(
        salary_income_after_deduction=100_000,
        business_income=-500_000,
    )
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "NEGATIVE_TOTAL_INCOME" in codes


def test_positive_total_income() -> None:
    """合計所得が正 → OK。"""
    inp = _make_input()
    res = _make_result(
        salary_income_after_deduction=3_000_000,
        business_income=500_000,
    )
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "NEGATIVE_TOTAL_INCOME" not in codes


# --- 6. TAXABLE_INCOME_ROUNDING ---


def test_taxable_income_rounding_error() -> None:
    """課税所得が1,000円単位でない → error。"""
    inp = _make_input()
    res = _make_result(taxable_income=1_234_567)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "TAXABLE_INCOME_ROUNDING" in codes


def test_taxable_income_properly_rounded() -> None:
    """課税所得が1,000円単位 → OK。"""
    inp = _make_input()
    res = _make_result(taxable_income=1_234_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "TAXABLE_INCOME_ROUNDING" not in codes


# --- 7. RECONSTRUCTION_TAX_MISMATCH ---


def test_reconstruction_tax_mismatch() -> None:
    """復興特別所得税の計算不一致 → error。"""
    inp = _make_input()
    res = _make_result(
        income_tax_after_credits=100_000,
        reconstruction_tax=9_999,  # 正しくは 100,000 * 21 // 1000 = 2,100
    )
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "RECONSTRUCTION_TAX_MISMATCH" in codes


def test_reconstruction_tax_correct() -> None:
    """復興特別所得税が正しい → OK。"""
    inp = _make_input()
    res = _make_result(
        income_tax_after_credits=100_000,
        reconstruction_tax=2_100,
    )
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "RECONSTRUCTION_TAX_MISMATCH" not in codes


# --- 8. CREDITS_EXCEED_TAX ---


def test_credits_exceed_tax() -> None:
    """税額控除が算出税額超過 → warning。"""
    inp = _make_input()
    res = _make_result(
        income_tax_base=50_000,
        total_tax_credits=100_000,
    )
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "CREDITS_EXCEED_TAX" in codes


def test_credits_within_tax() -> None:
    """税額控除が算出税額以下 → OK。"""
    inp = _make_input()
    res = _make_result(
        income_tax_base=200_000,
        total_tax_credits=100_000,
    )
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "CREDITS_EXCEED_TAX" not in codes


# --- 9. NO_WITHHOLDING_ON_SALARY ---


def test_no_withholding_on_salary() -> None:
    """給与ありなのに源泉徴収0 → warning。"""
    inp = _make_input(salary_income=5_000_000, withheld_tax=0)
    res = _make_result()
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "NO_WITHHOLDING_ON_SALARY" in codes


def test_withholding_on_salary() -> None:
    """給与ありで源泉徴収あり → OK。"""
    inp = _make_input(salary_income=5_000_000, withheld_tax=100_000)
    res = _make_result()
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "NO_WITHHOLDING_ON_SALARY" not in codes


# --- 10. REFUND_EXCEEDS_WITHHELD ---


def test_refund_exceeds_withheld() -> None:
    """還付額が源泉徴収+予定納税の合計超過 → error。"""
    inp = _make_input(withheld_tax=100_000, estimated_tax_payment=50_000)
    res = _make_result(tax_due=-200_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "REFUND_EXCEEDS_WITHHELD" in codes


def test_refund_within_withheld() -> None:
    """還付額が合計以下 → OK。"""
    inp = _make_input(withheld_tax=100_000, estimated_tax_payment=50_000)
    res = _make_result(tax_due=-100_000)
    check = sanity_check_income_tax(inp, res)
    codes = [item.code for item in check.items]
    assert "REFUND_EXCEEDS_WITHHELD" not in codes


# --- 全チェック pass のケース ---


def test_all_pass() -> None:
    """正常な入出力 → passed=True, items=[]。"""
    inp = _make_input(
        business_revenue=3_000_000,
        business_expenses=1_000_000,
        salary_income=5_000_000,
        withheld_tax=100_000,
    )
    res = _make_result(
        salary_income_after_deduction=3_560_000,
        business_income=1_350_000,
        effective_blue_return_deduction=650_000,
        taxable_income=3_000_000,
        income_tax_base=202_500,
        total_tax_credits=0,
        income_tax_after_credits=202_500,
        reconstruction_tax=4_252,
    )
    check = sanity_check_income_tax(inp, res)
    assert check.passed
    assert check.error_count == 0
