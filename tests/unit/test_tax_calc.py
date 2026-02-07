"""Tests for tax_calc module."""
import pytest
from shinkoku.tools.tax_calc import (
    calc_basic_deduction, calc_salary_deduction, calc_deductions,
    calc_life_insurance_deduction, calc_spouse_deduction,
    calc_furusato_deduction, calc_housing_loan_credit,
    calc_depreciation_straight_line, calc_depreciation_declining_balance,
)
from shinkoku.models import DeductionsResult
from tests.helpers.assertion_helpers import assert_amount_is_integer_yen

class TestBasicDeduction:
    def test_income_below_1320000(self):
        assert calc_basic_deduction(0) == 950_000
        assert calc_basic_deduction(1_320_000) == 950_000
    def test_income_up_to_23500000(self):
        assert calc_basic_deduction(1_320_001) == 880_000
        assert calc_basic_deduction(23_500_000) == 880_000
    def test_income_up_to_24000000(self):
        assert calc_basic_deduction(23_500_001) == 680_000
    def test_income_up_to_24500000(self):
        assert calc_basic_deduction(24_500_000) == 630_000
    def test_income_up_to_25000000(self):
        assert calc_basic_deduction(25_000_000) == 580_000
    def test_income_up_to_25450000(self):
        assert calc_basic_deduction(25_450_000) == 480_000
    def test_income_up_to_25950000(self):
        assert calc_basic_deduction(25_950_000) == 320_000
    def test_income_up_to_26450000(self):
        assert calc_basic_deduction(26_450_000) == 160_000
    def test_income_over_26450000(self):
        assert calc_basic_deduction(26_450_001) == 0
    def test_returns_integer(self):
        assert_amount_is_integer_yen(calc_basic_deduction(5_000_000), "basic")

class TestSocialInsurance:
    def test_full_amount(self):
        r = calc_deductions(total_income=5_000_000, social_insurance=800_000)
        s = [d for d in r.income_deductions if d.type == "social_insurance"]
        assert len(s) == 1 and s[0].amount == 800_000
    def test_zero(self):
        r = calc_deductions(total_income=5_000_000, social_insurance=0)
        assert not [d for d in r.income_deductions if d.type == "social_insurance"]

class TestLifeInsurance:
    def test_low(self):
        assert calc_life_insurance_deduction(15_000) == 15_000
    def test_mid(self):
        assert calc_life_insurance_deduction(30_000) == 25_000
    def test_upper_mid(self):
        assert calc_life_insurance_deduction(60_000) == 35_000
    def test_max(self):
        assert calc_life_insurance_deduction(100_000) == 40_000
    def test_zero(self):
        assert calc_life_insurance_deduction(0) == 0

class TestSpouseDeduction:
    def test_basic(self):
        assert calc_spouse_deduction(5_000_000, 480_000) == 380_000
    def test_special(self):
        r = calc_spouse_deduction(5_000_000, 900_000)
        assert 0 < r < 380_000
    def test_high_spouse(self):
        assert calc_spouse_deduction(5_000_000, 1_500_000) == 0
    def test_high_taxpayer(self):
        assert calc_spouse_deduction(11_000_000, 480_000) == 0
    def test_none(self):
        assert calc_spouse_deduction(5_000_000, None) == 0

class TestFurusato:
    def test_basic(self):
        assert calc_furusato_deduction(50_000) == 48_000
    def test_min(self):
        assert calc_furusato_deduction(2_000) == 0
    def test_zero(self):
        assert calc_furusato_deduction(0) == 0

class TestHousingLoan:
    def test_basic(self):
        assert calc_housing_loan_credit(35_000_000) == 245_000
    def test_zero(self):
        assert calc_housing_loan_credit(0) == 0
    def test_truncation(self):
        assert calc_housing_loan_credit(12_345_678) == 86_419

class TestCalcDeductions:
    def test_basic_included(self):
        r = calc_deductions(total_income=5_000_000)
        b = [d for d in r.income_deductions if d.type == "basic"]
        assert b[0].amount == 880_000
    def test_combined(self):
        r = calc_deductions(total_income=5_000_000, social_insurance=800_000,
            life_insurance_premium=100_000, furusato_nozei=50_000,
            housing_loan_balance=35_000_000)
        assert r.total_income_deductions > 0
        assert r.total_tax_credits == 245_000
    def test_model_type(self):
        assert isinstance(calc_deductions(total_income=5_000_000), DeductionsResult)
    def test_integer_amounts(self):
        r = calc_deductions(total_income=5_000_000, social_insurance=500_000,
            life_insurance_premium=80_000, furusato_nozei=30_000)
        assert_amount_is_integer_yen(r.total_income_deductions)
        for d in r.income_deductions:
            assert_amount_is_integer_yen(d.amount, d.type)


# ============================================================
# Task 14: Depreciation
# ============================================================

class TestDepreciationStraightLine:
    def test_basic_full_year(self):
        # 1,000,000 / 4 years * 100% * 12/12 = 250,000
        assert calc_depreciation_straight_line(1_000_000, 4, 100, 12) == 250_000

    def test_partial_year(self):
        # 1,000,000 / 4 * 100% * 6/12 = 125,000
        assert calc_depreciation_straight_line(1_000_000, 4, 100, 6) == 125_000

    def test_business_use_ratio(self):
        # 1,000,000 / 4 * 50% * 12/12 = 125,000
        assert calc_depreciation_straight_line(1_000_000, 4, 50, 12) == 125_000

    def test_combined_partial_and_ratio(self):
        # 1,200,000 / 5 * 80% * 9/12 = 144,000
        assert calc_depreciation_straight_line(1_200_000, 5, 80, 9) == 144_000

    def test_zero_months(self):
        assert calc_depreciation_straight_line(1_000_000, 4, 100, 0) == 0

    def test_zero_useful_life(self):
        assert calc_depreciation_straight_line(1_000_000, 0, 100, 12) == 0

    def test_returns_integer(self):
        result = calc_depreciation_straight_line(999_999, 7, 75, 10)
        assert_amount_is_integer_yen(result, "straight_line_depreciation")


class TestDepreciationDecliningBalance:
    def test_basic_full_year(self):
        # book_value=1,000,000, rate=500(50.0%), ratio=100%, 12 months
        # 1,000,000 * 500/1000 * 100/100 * 12/12 = 500,000
        assert calc_depreciation_declining_balance(1_000_000, 500, 100, 12) == 500_000

    def test_partial_year(self):
        # 1,000,000 * 500/1000 * 100/100 * 6/12 = 250,000
        assert calc_depreciation_declining_balance(1_000_000, 500, 100, 6) == 250_000

    def test_business_use_ratio(self):
        # 1,000,000 * 500/1000 * 60/100 * 12/12 = 300,000
        assert calc_depreciation_declining_balance(1_000_000, 500, 60, 12) == 300_000

    def test_zero_book_value(self):
        assert calc_depreciation_declining_balance(0, 500, 100, 12) == 0

    def test_returns_integer(self):
        result = calc_depreciation_declining_balance(777_777, 333, 80, 7)
        assert_amount_is_integer_yen(result, "declining_balance_depreciation")
