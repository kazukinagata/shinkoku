"""Tests for pension deduction and retirement income calculations."""

from __future__ import annotations

from shinkoku.models import PensionDeductionInput, RetirementIncomeInput
from shinkoku.tools.tax_calc import calc_pension_deduction, calc_retirement_income


class TestPensionDeduction:
    """公的年金等控除のテスト。"""

    def test_under_65_zero_pension(self):
        result = calc_pension_deduction(PensionDeductionInput(pension_income=0, is_over_65=False))
        assert result.deduction_amount == 0
        assert result.taxable_pension_income == 0

    def test_under_65_below_600k(self):
        """65歳未満、60万以下は全額控除。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=500_000, is_over_65=False)
        )
        assert result.deduction_amount == 500_000
        assert result.taxable_pension_income == 0

    def test_under_65_at_600k(self):
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=600_000, is_over_65=False)
        )
        assert result.deduction_amount == 600_000
        assert result.taxable_pension_income == 0

    def test_under_65_between_60_130(self):
        """65歳未満、60万超〜130万: 控除額60万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=1_000_000, is_over_65=False)
        )
        assert result.deduction_amount == 600_000
        assert result.taxable_pension_income == 400_000

    def test_under_65_between_130_410(self):
        """65歳未満、130万超〜410万: 年金×25%+37.5万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=2_000_000, is_over_65=False)
        )
        # 2,000,000 * 25 // 100 + 375,000 = 500,000 + 375,000 = 875,000
        assert result.deduction_amount == 875_000
        assert result.taxable_pension_income == 1_125_000

    def test_under_65_between_410_770(self):
        """65歳未満、410万超〜770万: 年金×15%+78.5万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=5_000_000, is_over_65=False)
        )
        # 5,000,000 * 15 // 100 + 785,000 = 750,000 + 785,000 = 1,535,000
        assert result.deduction_amount == 1_535_000
        assert result.taxable_pension_income == 3_465_000

    def test_under_65_between_770_1000(self):
        """65歳未満、770万超〜1000万: 年金×5%+155.5万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=8_000_000, is_over_65=False)
        )
        # 8,000,000 * 5 // 100 + 1,555,000 = 400,000 + 1,555,000 = 1,955,000
        assert result.deduction_amount == 1_955_000
        assert result.taxable_pension_income == 6_045_000

    def test_under_65_over_10m(self):
        """65歳未満、1000万超: 上限205.5万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=15_000_000, is_over_65=False)
        )
        assert result.deduction_amount == 2_055_000
        assert result.taxable_pension_income == 12_945_000

    def test_over_65_below_110k(self):
        """65歳以上、110万以下は全額控除。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=1_000_000, is_over_65=True)
        )
        assert result.deduction_amount == 1_000_000
        assert result.taxable_pension_income == 0

    def test_over_65_at_110k(self):
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=1_100_000, is_over_65=True)
        )
        assert result.deduction_amount == 1_100_000
        assert result.taxable_pension_income == 0

    def test_over_65_between_110_330(self):
        """65歳以上、110万超〜330万: 控除額110万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=2_500_000, is_over_65=True)
        )
        assert result.deduction_amount == 1_100_000
        assert result.taxable_pension_income == 1_400_000

    def test_over_65_between_330_410(self):
        """65歳以上、330万超〜410万: 年金×25%+37.5万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(pension_income=3_500_000, is_over_65=True)
        )
        # 3,500,000 * 25 // 100 + 375,000 = 875,000 + 375,000 = 1,250,000
        assert result.deduction_amount == 1_250_000
        assert result.taxable_pension_income == 2_250_000

    def test_other_income_adjustment_over_10m(self):
        """所得金額調整: 他の所得が1,000万超で控除-10万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(
                pension_income=2_000_000,
                is_over_65=True,
                other_income=15_000_000,
            )
        )
        # 110万 - 10万 = 100万
        assert result.deduction_amount == 1_000_000
        assert result.other_income_adjustment == 100_000

    def test_other_income_adjustment_over_20m(self):
        """所得金額調整: 他の所得が2,000万超で控除-20万。"""
        result = calc_pension_deduction(
            PensionDeductionInput(
                pension_income=2_000_000,
                is_over_65=True,
                other_income=25_000_000,
            )
        )
        # 110万 - 20万 = 90万
        assert result.deduction_amount == 900_000
        assert result.other_income_adjustment == 200_000

    def test_other_income_at_10m_no_adjustment(self):
        """所得金額調整: 他の所得がちょうど1,000万は調整なし。"""
        result = calc_pension_deduction(
            PensionDeductionInput(
                pension_income=2_000_000,
                is_over_65=True,
                other_income=10_000_000,
            )
        )
        assert result.deduction_amount == 1_100_000
        assert result.other_income_adjustment == 0


class TestRetirementIncome:
    """退職所得のテスト。"""

    def test_basic_under_20_years(self):
        """勤続20年以下: 40万×勤続年数。"""
        result = calc_retirement_income(
            RetirementIncomeInput(severance_pay=10_000_000, years_of_service=10)
        )
        # 控除: 400,000 × 10 = 4,000,000
        # 退職所得: (10,000,000 - 4,000,000) / 2 = 3,000,000
        assert result.retirement_income_deduction == 4_000_000
        assert result.taxable_retirement_income == 3_000_000
        assert result.half_taxation_applied is True

    def test_minimum_deduction(self):
        """最低控除額80万。"""
        result = calc_retirement_income(
            RetirementIncomeInput(severance_pay=1_000_000, years_of_service=1)
        )
        # 控除: max(400,000 × 1, 800,000) = 800,000
        # 退職所得: (1,000,000 - 800,000) / 2 = 100,000
        assert result.retirement_income_deduction == 800_000
        assert result.taxable_retirement_income == 100_000

    def test_over_20_years(self):
        """勤続20年超: 800万+70万×(勤続年数-20)。"""
        result = calc_retirement_income(
            RetirementIncomeInput(severance_pay=30_000_000, years_of_service=30)
        )
        # 控除: 8,000,000 + 700,000 × 10 = 15,000,000
        # 退職所得: (30,000,000 - 15,000,000) / 2 = 7,500,000
        assert result.retirement_income_deduction == 15_000_000
        assert result.taxable_retirement_income == 7_500_000
        assert result.half_taxation_applied is True

    def test_disability_retirement(self):
        """障害退職: +100万加算。"""
        result = calc_retirement_income(
            RetirementIncomeInput(
                severance_pay=5_000_000,
                years_of_service=10,
                is_disability_retirement=True,
            )
        )
        # 控除: 400,000 × 10 + 1,000,000 = 5,000,000
        # 退職所得: (5,000,000 - 5,000,000) / 2 = 0
        assert result.retirement_income_deduction == 5_000_000
        assert result.taxable_retirement_income == 0

    def test_officer_short_service(self):
        """役員等の短期退職（5年以下）: 1/2適用なし。"""
        result = calc_retirement_income(
            RetirementIncomeInput(
                severance_pay=10_000_000,
                years_of_service=3,
                is_officer=True,
            )
        )
        # 控除: max(400,000 × 3, 800,000) = 1,200,000
        # 退職所得: 10,000,000 - 1,200,000 = 8,800,000（1/2なし）
        assert result.retirement_income_deduction == 1_200_000
        assert result.taxable_retirement_income == 8_800_000
        assert result.half_taxation_applied is False

    def test_general_short_service_under_3m(self):
        """一般の短期退職（5年以下）: 300万以下は1/2適用。"""
        result = calc_retirement_income(
            RetirementIncomeInput(
                severance_pay=3_000_000,
                years_of_service=3,
            )
        )
        # 控除: max(400,000 × 3, 800,000) = 1,200,000
        # excess = 3,000,000 - 1,200,000 = 1,800,000 (≤300万)
        # 退職所得: 1,800,000 / 2 = 900,000
        assert result.retirement_income_deduction == 1_200_000
        assert result.taxable_retirement_income == 900_000

    def test_general_short_service_over_3m(self):
        """一般の短期退職（5年以下）: 300万超は部分的1/2（R4改正）。"""
        result = calc_retirement_income(
            RetirementIncomeInput(
                severance_pay=10_000_000,
                years_of_service=3,
            )
        )
        # 控除: max(400,000 × 3, 800,000) = 1,200,000
        # excess = 10,000,000 - 1,200,000 = 8,800,000
        # 300万以下部分: 3,000,000 / 2 = 1,500,000
        # 300万超部分: 8,800,000 - 3,000,000 = 5,800,000
        # 退職所得: 1,500,000 + 5,800,000 = 7,300,000
        assert result.retirement_income_deduction == 1_200_000
        assert result.taxable_retirement_income == 7_300_000
        assert result.half_taxation_applied is False

    def test_pay_less_than_deduction(self):
        """退職金が控除額以下の場合、退職所得は0。"""
        result = calc_retirement_income(
            RetirementIncomeInput(
                severance_pay=500_000,
                years_of_service=10,
            )
        )
        assert result.retirement_income_deduction == 4_000_000
        assert result.taxable_retirement_income == 0

    def test_exactly_20_years(self):
        """勤続ちょうど20年: 40万×20 = 800万。"""
        result = calc_retirement_income(
            RetirementIncomeInput(severance_pay=20_000_000, years_of_service=20)
        )
        # 控除: 400,000 × 20 = 8,000,000
        # 退職所得: (20,000,000 - 8,000,000) / 2 = 6,000,000
        assert result.retirement_income_deduction == 8_000_000
        assert result.taxable_retirement_income == 6_000_000
        assert result.half_taxation_applied is True

    def test_officer_over_5_years(self):
        """役員等でも勤続6年以上は通常の1/2適用。"""
        result = calc_retirement_income(
            RetirementIncomeInput(
                severance_pay=10_000_000,
                years_of_service=6,
                is_officer=True,
            )
        )
        # 控除: 400,000 × 6 = 2,400,000
        # 退職所得: (10,000,000 - 2,400,000) / 2 = 3,800,000
        assert result.retirement_income_deduction == 2_400_000
        assert result.taxable_retirement_income == 3_800_000
        assert result.half_taxation_applied is True
