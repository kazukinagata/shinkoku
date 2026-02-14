"""Tests for tax_calc module."""

from shinkoku.tools.tax_calc import (
    calc_basic_deduction,
    calc_salary_deduction,
    calc_deductions,
    calc_life_insurance_deduction,
    calc_spouse_deduction,
    calc_furusato_deduction,
    calc_housing_loan_credit,
    calc_depreciation_straight_line,
    calc_depreciation_declining_balance,
    calc_income_tax,
    calc_consumption_tax,
)
from shinkoku.models import (
    DeductionsResult,
    IncomeTaxInput,
    IncomeTaxResult,
    ConsumptionTaxInput,
    ConsumptionTaxResult,
)
from tests.helpers.assertion_helpers import assert_amount_is_integer_yen


class TestBasicDeduction:
    """Basic deduction table (Reiwa 7-8, time-limited 租特法41条の16の2)."""

    def test_income_zero(self):
        assert calc_basic_deduction(0) == 950_000

    def test_income_at_1320000(self):
        assert calc_basic_deduction(1_320_000) == 950_000

    def test_income_above_1320000(self):
        assert calc_basic_deduction(1_320_001) == 880_000

    def test_income_at_3360000(self):
        assert calc_basic_deduction(3_360_000) == 880_000

    def test_income_above_3360000(self):
        assert calc_basic_deduction(3_360_001) == 680_000

    def test_income_at_4890000(self):
        assert calc_basic_deduction(4_890_000) == 680_000

    def test_income_above_4890000(self):
        assert calc_basic_deduction(4_890_001) == 630_000

    def test_income_at_6550000(self):
        assert calc_basic_deduction(6_550_000) == 630_000

    def test_income_above_6550000(self):
        assert calc_basic_deduction(6_550_001) == 580_000

    def test_income_at_23500000(self):
        assert calc_basic_deduction(23_500_000) == 580_000

    def test_income_above_23500000(self):
        assert calc_basic_deduction(23_500_001) == 480_000

    def test_income_at_24000000(self):
        assert calc_basic_deduction(24_000_000) == 480_000

    def test_income_above_24000000(self):
        assert calc_basic_deduction(24_000_001) == 320_000

    def test_income_at_24500000(self):
        assert calc_basic_deduction(24_500_000) == 320_000

    def test_income_above_24500000(self):
        assert calc_basic_deduction(24_500_001) == 160_000

    def test_income_at_25000000(self):
        assert calc_basic_deduction(25_000_000) == 160_000

    def test_income_over_25000000(self):
        assert calc_basic_deduction(25_000_001) == 0

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
    """Spouse deduction (Reiwa 7~, NTA No.1195)."""

    def test_spouse_deduction_basic(self):
        # 配偶者控除: spouse income ≤58万, taxpayer ≤900万 → 38万
        assert calc_spouse_deduction(5_000_000, 480_000) == 380_000
        assert calc_spouse_deduction(5_000_000, 580_000) == 380_000

    def test_special_full_amount(self):
        # 配偶者特別控除（満額）: spouse income 58万超〜95万 → 38万
        assert calc_spouse_deduction(5_000_000, 800_000) == 380_000
        assert calc_spouse_deduction(5_000_000, 950_000) == 380_000

    def test_special_gradual(self):
        # 配偶者特別控除（段階）: spouse income 95万超〜100万 → 36万
        assert calc_spouse_deduction(5_000_000, 960_000) == 360_000
        assert calc_spouse_deduction(5_000_000, 1_000_000) == 360_000

    def test_special_mid(self):
        # 110万超〜115万 → 21万
        assert calc_spouse_deduction(5_000_000, 1_120_000) == 210_000

    def test_special_low(self):
        # 130万超〜133万 → 3万
        assert calc_spouse_deduction(5_000_000, 1_310_000) == 30_000

    def test_high_spouse(self):
        assert calc_spouse_deduction(5_000_000, 1_330_001) == 0
        assert calc_spouse_deduction(5_000_000, 1_500_000) == 0

    def test_high_taxpayer(self):
        assert calc_spouse_deduction(11_000_000, 480_000) == 0

    def test_none(self):
        assert calc_spouse_deduction(5_000_000, None) == 0

    def test_taxpayer_9m_bracket(self):
        # taxpayer 900万超〜950万, spouse ≤58万 → 26万
        assert calc_spouse_deduction(9_200_000, 480_000) == 260_000
        # spouse 58万超〜95万 → 26万 (满额)
        assert calc_spouse_deduction(9_200_000, 800_000) == 260_000

    def test_taxpayer_10m_bracket(self):
        # taxpayer 950万超〜1000万, spouse ≤58万 → 13万
        assert calc_spouse_deduction(9_800_000, 480_000) == 130_000


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
        assert b[0].amount == 630_000  # 489万超〜655万: 63万

    def test_basic_low_income(self):
        r = calc_deductions(total_income=1_000_000)
        b = [d for d in r.income_deductions if d.type == "basic"]
        assert b[0].amount == 950_000  # ≤132万: 95万

    def test_combined(self):
        r = calc_deductions(
            total_income=5_000_000,
            social_insurance=800_000,
            life_insurance_premium=100_000,
            furusato_nozei=50_000,
            housing_loan_balance=35_000_000,
        )
        assert r.total_income_deductions > 0
        assert r.total_tax_credits == 245_000

    def test_medical_low_income_threshold(self):
        # 所得200万未満: threshold = income * 5% = 1,500,000 * 5% = 75,000
        r = calc_deductions(total_income=1_500_000, medical_expenses=80_000)
        m = [d for d in r.income_deductions if d.type == "medical"]
        assert len(m) == 1
        assert m[0].amount == 80_000 - 75_000  # 5,000円

    def test_medical_high_income_threshold(self):
        # 所得200万以上: threshold = 100,000
        r = calc_deductions(total_income=5_000_000, medical_expenses=150_000)
        m = [d for d in r.income_deductions if d.type == "medical"]
        assert len(m) == 1
        assert m[0].amount == 50_000  # 150,000 - 100,000

    def test_medical_below_threshold_low_income(self):
        # 所得100万、医療費4万: threshold = 50,000 > 40,000 → 控除なし
        r = calc_deductions(total_income=1_000_000, medical_expenses=40_000)
        m = [d for d in r.income_deductions if d.type == "medical"]
        assert len(m) == 0

    def test_model_type(self):
        assert isinstance(calc_deductions(total_income=5_000_000), DeductionsResult)

    def test_integer_amounts(self):
        r = calc_deductions(
            total_income=5_000_000,
            social_insurance=500_000,
            life_insurance_premium=80_000,
            furusato_nozei=30_000,
        )
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


# ============================================================
# Task 15: Salary Deduction (Reiwa 7)
# ============================================================


class TestSalaryDeduction:
    def test_zero(self):
        assert calc_salary_deduction(0) == 0

    def test_low_income(self):
        assert calc_salary_deduction(1_000_000) == 650_000

    def test_boundary_1625000(self):
        assert calc_salary_deduction(1_625_000) == 650_000

    def test_1800000(self):
        # 1,800,000 * 40% - 100,000 = 620,000
        assert calc_salary_deduction(1_800_000) == 620_000

    def test_3600000(self):
        # 3,600,000 * 30% + 80,000 = 1,160,000
        assert calc_salary_deduction(3_600_000) == 1_160_000

    def test_6000000(self):
        # 6,000,000 * 20% + 440,000 = 1,640,000
        assert calc_salary_deduction(6_000_000) == 1_640_000

    def test_8500000(self):
        # 8,500,000 * 10% + 1,100,000 = 1,950,000
        assert calc_salary_deduction(8_500_000) == 1_950_000

    def test_over_8500000(self):
        assert calc_salary_deduction(10_000_000) == 1_950_000

    def test_returns_integer(self):
        assert_amount_is_integer_yen(calc_salary_deduction(5_555_555), "salary_ded")


# ============================================================
# Task 15: Income Tax Full Calculation - 5 Scenarios
# ============================================================


class TestIncomeTaxScenario1:
    """Salary 6M + Side business revenue 3M, blue, furusato 50K.

    total_income = 6,710,000 → basic deduction = 580,000 (655万超〜2,350万)
    """

    def test_full_calculation(self):
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                business_expenses=0,
                furusato_nozei=50_000,
                withheld_tax=466_800,
            )
        )
        assert r.salary_income_after_deduction == 4_360_000
        assert r.business_income == 2_350_000
        assert r.total_income == 6_710_000
        # basic=580,000 + furusato=48,000 = 628,000
        assert r.total_income_deductions == 628_000
        # taxable = 6,710,000 - 628,000 = 6,082,000
        assert r.taxable_income == 6_082_000
        # 6,082,000 * 20% - 427,500 = 788,900
        assert r.income_tax_base == 788_900
        assert r.income_tax_after_credits == 788_900
        # 788,900 * 21/1000 = 16,566
        assert r.reconstruction_tax == 16_566
        # (788,900 + 16,566) = 805,466 → 805,400
        assert r.total_tax == 805_400
        assert r.tax_due == 338_600


class TestIncomeTaxScenario2:
    """Salary 8M + Side 2M, blue, housing loan 35M, furusato 100K, spouse.

    total_income = 7,450,000 → basic deduction = 580,000 (655万超〜2,350万)
    spouse_income=0 → 配偶者控除 380,000
    """

    def test_full_calculation(self):
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=8_000_000,
                business_revenue=2_000_000,
                business_expenses=0,
                furusato_nozei=100_000,
                housing_loan_balance=35_000_000,
                spouse_income=0,
                withheld_tax=720_200,
            )
        )
        assert r.salary_income_after_deduction == 6_100_000
        assert r.business_income == 1_350_000
        assert r.total_income == 7_450_000
        # basic=580,000 + spouse=380,000 + furusato=98,000 = 1,058,000
        assert r.total_income_deductions == 1_058_000
        # taxable = 7,450,000 - 1,058,000 = 6,392,000
        assert r.taxable_income == 6_392_000
        # 6,392,000 * 20% - 427,500 = 850,900
        assert r.income_tax_base == 850_900
        assert r.total_tax_credits == 245_000
        # 850,900 - 245,000 = 605,900
        assert r.income_tax_after_credits == 605_900
        # 605,900 * 21/1000 = 12,723
        assert r.reconstruction_tax == 12_723
        # (605,900 + 12,723) = 618,623 → 618,600
        assert r.total_tax == 618_600
        assert r.tax_due == -101_600


class TestIncomeTaxScenario3:
    """Salary 1.8M + Side 500K, blue, low income — loss offset applies.

    business_income = 500K - 650K = -150K (negative, offset against salary).
    total_income = max(0, 1,180K + (-150K)) = 1,030K.
    """

    def test_full_calculation(self):
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=1_800_000,
                business_revenue=500_000,
                business_expenses=0,
                withheld_tax=36_700,
            )
        )
        assert r.salary_income_after_deduction == 1_180_000
        assert r.business_income == -150_000  # 500K - 650K blue = 損益通算で負値
        assert r.total_income == 1_030_000  # max(0, 1,180K + (-150K))
        # basic deduction for 1,030K = 950,000 (≤132万)
        assert r.taxable_income == 80_000  # 1,030K - 950K
        assert r.income_tax_base == 4_000  # 80K * 5%
        assert r.reconstruction_tax == 84  # 4,000 * 21/1000
        assert r.total_tax == 4_000  # (4,000 + 84) = 4,084 → 4,000
        assert r.tax_due == -32_700  # 4,000 - 36,700


class TestIncomeTaxScenario4:
    """Salary 7M + Side 15M, blue, furusato 150K.

    total_income = 19,550,000 → basic deduction = 580,000 (655万超〜2,350万)
    """

    def test_full_calculation(self):
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=7_000_000,
                business_revenue=15_000_000,
                business_expenses=0,
                furusato_nozei=150_000,
                withheld_tax=1_883_600,
            )
        )
        assert r.salary_income_after_deduction == 5_200_000
        assert r.business_income == 14_350_000
        assert r.total_income == 19_550_000
        # basic=580,000 + furusato=148,000 = 728,000
        # taxable = 19,550,000 - 728,000 = 18,822,000
        assert r.taxable_income == 18_822_000
        # 18,822,000 * 40% - 2,796,000 = 4,732,800
        assert r.income_tax_base == 4_732_800
        # 4,732,800 * 21/1000 = 99,388
        assert r.reconstruction_tax == 99_388
        # (4,732,800 + 99,388) = 4,832,188 → 4,832,100
        assert r.total_tax == 4_832_100
        assert r.tax_due == 2_948_500


class TestIncomeTaxScenario5:
    """Salary 5M + Side 1M, blue, housing loan 25M, furusato 30K.

    total_income = 3,910,000 → basic deduction = 680,000 (336万超〜489万)
    """

    def test_full_calculation(self):
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=1_000_000,
                business_expenses=0,
                furusato_nozei=30_000,
                housing_loan_balance=25_000_000,
                withheld_tax=128_200,
            )
        )
        assert r.salary_income_after_deduction == 3_560_000
        assert r.business_income == 350_000
        assert r.total_income == 3_910_000
        # basic=680,000 + furusato=28,000 = 708,000
        # taxable = 3,910,000 - 708,000 = 3,202,000
        assert r.taxable_income == 3_202_000
        # 3,202,000 * 10% - 97,500 = 222,700
        assert r.income_tax_base == 222_700
        assert r.total_tax_credits == 175_000
        # 222,700 - 175,000 = 47,700
        assert r.income_tax_after_credits == 47_700
        # 47,700 * 21/1000 = 1,001
        assert r.reconstruction_tax == 1_001
        # (47,700 + 1,001) = 48,701 → 48,700
        assert r.total_tax == 48_700
        assert r.tax_due == -79_500


class TestIncomeTaxIntegerConstraints:
    """Verify all output amounts are int."""

    def test_all_amounts_integer(self):
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
            )
        )
        assert isinstance(r, IncomeTaxResult)
        for field in [
            r.salary_income_after_deduction,
            r.business_income,
            r.total_income,
            r.total_income_deductions,
            r.taxable_income,
            r.income_tax_base,
            r.total_tax_credits,
            r.income_tax_after_credits,
            r.reconstruction_tax,
            r.total_tax,
            r.withheld_tax,
            r.tax_due,
        ]:
            assert_amount_is_integer_yen(field)


# ============================================================
# Task 16: Consumption Tax
# ============================================================


class TestConsumptionTaxSpecial20pct:
    """2-wari special: sales tax * 20%."""

    def test_basic(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="special_20pct",
                taxable_sales_10=5_500_000,
            )
        )
        # tax_on_sales = 5,500,000 * 10/110 = 500,000
        assert r.tax_on_sales == 500_000
        # national = 100,000 * 78/100 = 78,000
        assert r.tax_due == 78_000
        # local = 78,000 * 22/78 = 22,000
        assert r.local_tax_due == 22_000
        assert r.total_due == 100_000

    def test_with_8pct_sales(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="special_20pct",
                taxable_sales_10=3_300_000,
                taxable_sales_8=1_080_000,
            )
        )
        # 10%: 3,300,000 * 10/110 = 300,000
        # 8%: 1,080,000 * 8/108 = 80,000
        # total sales tax = 380,000
        assert r.tax_on_sales == 380_000
        assert r.total_due > 0

    def test_returns_model(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025, method="special_20pct", taxable_sales_10=1_100_000
            )
        )
        assert isinstance(r, ConsumptionTaxResult)
        assert r.method == "special_20pct"


class TestConsumptionTaxSimplified:
    """Simplified: tax * (1 - deemed ratio)."""

    def test_service_type5(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="simplified",
                taxable_sales_10=5_500_000,
                simplified_business_type=5,
            )
        )
        # tax_on_sales = 500,000, deemed 50%, due = 250,000
        assert r.tax_on_sales == 500_000
        # national = 250,000 * 78/100 = 195,000
        assert r.tax_due == 195_000
        # local = 195,000 * 22/78 = 55,000
        assert r.local_tax_due == 55_000
        assert r.total_due == 250_000

    def test_wholesale_type1(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="simplified",
                taxable_sales_10=11_000_000,
                simplified_business_type=1,
            )
        )
        # tax = 1,000,000, deemed 90%, due = 100,000
        assert r.tax_on_sales == 1_000_000
        # national = 100,000 * 78/100 = 78,000
        assert r.tax_due == 78_000

    def test_retail_type2(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="simplified",
                taxable_sales_10=5_500_000,
                simplified_business_type=2,
            )
        )
        # tax = 500,000, deemed 80%, due = 100,000
        assert r.tax_on_sales == 500_000


class TestConsumptionTaxStandard:
    """Standard: sales tax - purchase tax."""

    def test_basic(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=5_500_000,
                taxable_purchases_10=2_200_000,
            )
        )
        # sales tax = 500,000, purchase tax = 200,000
        assert r.tax_on_sales == 500_000
        assert r.tax_on_purchases == 200_000
        # due = 300,000
        # national = 300,000 * 78/100 = 234,000
        assert r.tax_due == 234_000
        # local = 234,000 * 22/78 = 66,000
        assert r.local_tax_due == 66_000
        assert r.total_due == 300_000

    def test_mixed_rates(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=5_500_000,
                taxable_sales_8=1_080_000,
                taxable_purchases_10=1_100_000,
                taxable_purchases_8=540_000,
            )
        )
        # sales: 500,000 + 80,000 = 580,000
        # purchases: 100,000 + 40,000 = 140,000
        assert r.tax_on_sales == 580_000
        assert r.tax_on_purchases == 140_000
        assert r.total_due > 0

    def test_truncation_to_100(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=5_500_000,
                taxable_purchases_10=2_200_000,
            )
        )
        assert r.tax_due % 100 == 0
        assert r.local_tax_due % 100 == 0

    def test_all_amounts_integer(self):
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="special_20pct",
                taxable_sales_10=5_500_000,
            )
        )
        assert_amount_is_integer_yen(r.tax_on_sales)
        assert_amount_is_integer_yen(r.tax_on_purchases)
        assert_amount_is_integer_yen(r.tax_due)
        assert_amount_is_integer_yen(r.local_tax_due)
        assert_amount_is_integer_yen(r.total_due)


# ============================================================
# Loss Offset (損益通算)
# ============================================================


class TestLossOffset:
    """事業赤字 + 給与所得 → 損益通算が正しく計算されるか。"""

    def test_business_loss_offsets_salary(self):
        """事業赤字を給与所得と通算する。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=1_000_000,
                business_expenses=2_000_000,
                blue_return_deduction=650_000,
            )
        )
        # business_income = 1,000K - 2,000K - 650K = -1,650K
        assert r.business_income == -1_650_000
        # salary_income_after = 5,000K - 1,440K(給与所得控除) = 3,560K
        assert r.salary_income_after_deduction == 3_560_000
        # total_income = max(0, 3,560K + (-1,650K)) = 1,910K
        assert r.total_income == 1_910_000

    def test_business_loss_exceeds_salary(self):
        """事業赤字が給与所得を超える場合、total_income は 0。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=2_000_000,
                business_revenue=0,
                business_expenses=3_000_000,
                blue_return_deduction=650_000,
            )
        )
        # business_income = 0 - 3,000K - 650K = -3,650K
        assert r.business_income == -3_650_000
        # salary_income_after = 2,000K - 680K = 1,320K
        assert r.salary_income_after_deduction == 1_320_000
        # total_income = max(0, 1,320K + (-3,650K)) = 0
        assert r.total_income == 0
        # 所得0 → 税額0
        assert r.total_tax == 0

    def test_business_income_stored_as_negative(self):
        """business_income フィールドは負値で保持される（損益通算の内訳表示用）。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=3_000_000,
                business_revenue=200_000,
                business_expenses=500_000,
                blue_return_deduction=650_000,
            )
        )
        assert r.business_income < 0


# ============================================================
# Estimated Tax Payment (予定納税)
# ============================================================


class TestEstimatedTaxPayment:
    """予定納税がある場合の税額計算。"""

    def test_estimated_tax_reduces_tax_due(self):
        """予定納税額が tax_due から差し引かれる。"""
        base = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
            )
        )
        with_estimated = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                estimated_tax_payment=100_000,
            )
        )
        # total_tax は同じ（予定納税は税額計算に影響しない）
        assert with_estimated.total_tax == base.total_tax
        # tax_due は予定納税分だけ減る
        assert with_estimated.tax_due == base.tax_due - 100_000
        assert with_estimated.estimated_tax_payment == 100_000

    def test_estimated_tax_zero_backward_compatible(self):
        """予定納税なし（デフォルト0）→ 従来の計算と同じ結果。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                estimated_tax_payment=0,
            )
        )
        assert r.estimated_tax_payment == 0
        assert r.tax_due == r.total_tax - r.withheld_tax

    def test_estimated_tax_causes_refund(self):
        """予定納税により還付になるケース。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                estimated_tax_payment=500_000,
            )
        )
        # total_tax = 805,400 (same as scenario 1)
        # tax_due = 805,400 - 466,800 - 500,000 = -161,400
        assert r.tax_due < 0  # 還付

    def test_estimated_tax_in_result(self):
        """estimated_tax_payment が結果モデルに含まれる。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=1_000_000,
                estimated_tax_payment=50_000,
            )
        )
        assert r.estimated_tax_payment == 50_000
