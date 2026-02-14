"""Tests for tax_calc module."""

from shinkoku.tools.tax_calc import (
    calc_basic_deduction,
    calc_salary_deduction,
    calc_deductions,
    calc_dependents_deduction,
    calc_life_insurance_deduction,
    calc_life_insurance_deduction_old,
    calc_life_insurance_category,
    calc_life_insurance_total,
    calc_earthquake_insurance_deduction,
    calc_widow_deduction,
    calc_disability_deduction_self,
    calc_working_student_deduction,
    calc_self_medication_deduction,
    calc_dividend_tax_credit,
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
    DependentInfo,
    HousingLoanDetail,
    IncomeTaxInput,
    IncomeTaxResult,
    LifeInsurancePremiumInput,
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
        # 令和7年改正: ≤190万は一律65万
        assert calc_salary_deduction(1_800_000) == 650_000

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
    total_income = max(0, 1,150K + (-150K)) = 1,000K.
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
        # 令和7年改正: ≤190万は一律65万 → 1,800K - 650K = 1,150K
        assert r.salary_income_after_deduction == 1_150_000
        assert r.business_income == -150_000  # 500K - 650K blue = 損益通算で負値
        assert r.total_income == 1_000_000  # max(0, 1,150K + (-150K))
        # basic deduction for 1,000K = 950,000 (≤132万)
        assert r.taxable_income == 50_000  # 1,000K - 950K
        assert r.income_tax_base == 2_500  # 50K * 5%
        assert r.reconstruction_tax == 52  # 2,500 * 21/1000
        assert r.total_tax == 2_500  # (2,500 + 52) = 2,552 → 2,500
        assert r.tax_due == -34_200  # 2,500 - 36,700


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


# ============================================================
# iDeCo（小規模企業共済等掛金控除）
# ============================================================


class TestIDeCoDeduction:
    """iDeCo掛金は全額所得控除。"""

    def test_ideco_full_deduction(self):
        """iDeCo掛金が全額控除される。"""
        r = calc_deductions(total_income=5_000_000, ideco_contribution=276_000)
        ideco = [d for d in r.income_deductions if d.type == "small_business_mutual_aid"]
        assert len(ideco) == 1
        assert ideco[0].amount == 276_000
        assert ideco[0].details == "iDeCo"

    def test_ideco_zero(self):
        """iDeCo掛金0の場合は控除項目に含まれない。"""
        r = calc_deductions(total_income=5_000_000, ideco_contribution=0)
        ideco = [d for d in r.income_deductions if d.type == "small_business_mutual_aid"]
        assert len(ideco) == 0

    def test_ideco_in_total_deductions(self):
        """iDeCo掛金がtotal_income_deductionsに含まれる。"""
        without = calc_deductions(total_income=5_000_000)
        with_ideco = calc_deductions(total_income=5_000_000, ideco_contribution=276_000)
        assert with_ideco.total_income_deductions == without.total_income_deductions + 276_000

    def test_ideco_reduces_income_tax(self):
        """iDeCo掛金により所得税が減少する。"""
        base = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
            )
        )
        with_ideco = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                ideco_contribution=276_000,
            )
        )
        # total_income は変わらない
        assert with_ideco.total_income == base.total_income
        # 所得控除が増える
        assert with_ideco.total_income_deductions == base.total_income_deductions + 276_000
        # 税額が減る
        assert with_ideco.total_tax < base.total_tax

    def test_ideco_max_self_employed(self):
        """自営業の場合の上限額（816,000円/年）でも全額控除される。"""
        r = calc_deductions(total_income=10_000_000, ideco_contribution=816_000)
        ideco = [d for d in r.income_deductions if d.type == "small_business_mutual_aid"]
        assert ideco[0].amount == 816_000


# ============================================================
# 扶養控除・障害者控除
# ============================================================


class TestDependentsDeduction:
    """扶養控除の計算テスト。"""

    def test_general_dependent(self):
        """一般扶養親族（16歳以上、特定扶養でない） → 38万円。"""
        # 2025年末時点で17歳 → 一般扶養
        deps = [DependentInfo(name="太郎", relationship="子", birth_date="2008-06-01")]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 1
        assert dep_items[0].amount == 380_000
        assert "一般扶養" in (dep_items[0].details or "")

    def test_specific_dependent(self):
        """特定扶養親族（19歳以上23歳未満） → 63万円。"""
        deps = [DependentInfo(name="花子", relationship="子", birth_date="2004-03-15")]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 1
        assert dep_items[0].amount == 630_000
        assert "特定扶養" in (dep_items[0].details or "")

    def test_elderly_cohabiting(self):
        """老人扶養親族（70歳以上・同居） → 58万円。"""
        deps = [
            DependentInfo(name="祖母", relationship="親", birth_date="1950-01-01", cohabiting=True)
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 1
        assert dep_items[0].amount == 580_000
        assert "同居" in (dep_items[0].details or "")

    def test_elderly_not_cohabiting(self):
        """老人扶養親族（70歳以上・別居） → 48万円。"""
        deps = [
            DependentInfo(name="祖父", relationship="親", birth_date="1950-01-01", cohabiting=False)
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 1
        assert dep_items[0].amount == 480_000
        assert "別居" in (dep_items[0].details or "")

    def test_under_16_no_deduction(self):
        """16歳未満は扶養控除なし。"""
        deps = [DependentInfo(name="次郎", relationship="子", birth_date="2012-09-01")]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 0

    def test_income_over_580000_excluded(self):
        """所得58万超の親族は扶養控除対象外（令和7年改正: 48万→58万）。"""
        deps = [
            DependentInfo(name="太郎", relationship="子", birth_date="2005-06-01", income=590_000)
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        assert len(items) == 0

    def test_spouse_excluded(self):
        """配偶者は扶養控除ではなく配偶者控除で処理するため除外。"""
        deps = [DependentInfo(name="妻", relationship="配偶者", birth_date="1990-01-01")]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        assert len(items) == 0

    def test_disability_general(self):
        """一般障害者 → 27万円。"""
        deps = [
            DependentInfo(
                name="次郎",
                relationship="子",
                birth_date="2012-09-01",
                disability="general",
            )
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dis = [i for i in items if i.type == "disability"]
        assert len(dis) == 1
        assert dis[0].amount == 270_000

    def test_disability_special(self):
        """特別障害者 → 40万円。"""
        deps = [
            DependentInfo(
                name="太郎",
                relationship="子",
                birth_date="2005-06-01",
                disability="special",
            )
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dis = [i for i in items if i.type == "disability"]
        assert len(dis) == 1
        assert dis[0].amount == 400_000

    def test_disability_special_cohabiting(self):
        """同居特別障害者 → 75万円。"""
        deps = [
            DependentInfo(
                name="母",
                relationship="親",
                birth_date="1950-01-01",
                disability="special_cohabiting",
            )
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dis = [i for i in items if i.type == "disability"]
        assert len(dis) == 1
        assert dis[0].amount == 750_000

    def test_disability_under_16_still_applies(self):
        """16歳未満でも障害者控除は適用される。"""
        deps = [
            DependentInfo(
                name="三郎",
                relationship="子",
                birth_date="2015-01-01",
                disability="general",
            )
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        # 扶養控除なし（16歳未満）
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 0
        # 障害者控除あり
        dis = [i for i in items if i.type == "disability"]
        assert len(dis) == 1
        assert dis[0].amount == 270_000

    def test_multiple_dependents(self):
        """複数の扶養親族。"""
        deps = [
            DependentInfo(name="長男", relationship="子", birth_date="2004-05-01"),  # 特定扶養
            DependentInfo(name="次男", relationship="子", birth_date="2008-03-01"),  # 一般扶養
            DependentInfo(name="母", relationship="親", birth_date="1950-06-01"),  # 老人同居
        ]
        items = calc_dependents_deduction(deps, taxpayer_income=5_000_000, fiscal_year=2025)
        dep_items = [i for i in items if i.type == "dependent"]
        total = sum(i.amount for i in dep_items)
        assert total == 630_000 + 380_000 + 580_000

    def test_dependents_via_calc_income_tax(self):
        """calc_income_tax 経由で扶養控除が適用される。"""
        base = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
            )
        )
        with_deps = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                dependents=[
                    # 2025年末時点で17歳 → 一般扶養（38万円）
                    DependentInfo(name="子", relationship="子", birth_date="2008-01-01"),
                ],
            )
        )
        # 扶養控除38万円分、所得控除が増える
        assert with_deps.total_income_deductions == base.total_income_deductions + 380_000
        assert with_deps.total_tax < base.total_tax


# ============================================================
# 住宅ローン控除（詳細版）
# ============================================================


class TestHousingLoanDetailedCredit:
    """住宅区分別の年末残高上限での控除計算テスト。"""

    def test_certified_new_within_limit(self):
        """認定住宅（新築）5,000万円上限内 → balance * 0.7%。"""
        detail = HousingLoanDetail(
            housing_type="new_custom",
            housing_category="certified",
            move_in_date="2024-03-01",
            year_end_balance=40_000_000,
            is_new_construction=True,
        )
        credit = calc_housing_loan_credit(40_000_000, detail=detail)
        assert credit == 280_000  # 4,000万 * 0.7%

    def test_certified_new_over_limit(self):
        """認定住宅（新築）残高が上限5,000万超 → 上限適用。"""
        detail = HousingLoanDetail(
            housing_type="new_custom",
            housing_category="certified",
            move_in_date="2024-03-01",
            year_end_balance=60_000_000,
            is_new_construction=True,
        )
        credit = calc_housing_loan_credit(60_000_000, detail=detail)
        # 上限5,000万 * 0.7% = 350,000
        assert credit == 350_000

    def test_zeh_new(self):
        """ZEH水準省エネ（新築）4,500万円上限。"""
        detail = HousingLoanDetail(
            housing_type="new_subdivision",
            housing_category="zeh",
            move_in_date="2024-06-01",
            year_end_balance=50_000_000,
            is_new_construction=True,
        )
        credit = calc_housing_loan_credit(50_000_000, detail=detail)
        # 上限4,500万 * 0.7% = 315,000
        assert credit == 315_000

    def test_energy_efficient_new(self):
        """省エネ基準適合（新築）4,000万円上限。"""
        detail = HousingLoanDetail(
            housing_type="new_custom",
            housing_category="energy_efficient",
            move_in_date="2024-01-15",
            year_end_balance=45_000_000,
            is_new_construction=True,
        )
        credit = calc_housing_loan_credit(45_000_000, detail=detail)
        # 上限4,000万 * 0.7% = 280,000
        assert credit == 280_000

    def test_general_new(self):
        """一般住宅（新築）3,000万円上限。"""
        detail = HousingLoanDetail(
            housing_type="new_subdivision",
            housing_category="general",
            move_in_date="2024-04-01",
            year_end_balance=35_000_000,
            is_new_construction=True,
        )
        credit = calc_housing_loan_credit(35_000_000, detail=detail)
        # 上限3,000万 * 0.7% = 210,000
        assert credit == 210_000

    def test_used_general(self):
        """一般住宅（中古）2,000万円上限。"""
        detail = HousingLoanDetail(
            housing_type="used",
            housing_category="general",
            move_in_date="2024-08-01",
            year_end_balance=25_000_000,
            is_new_construction=False,
        )
        credit = calc_housing_loan_credit(25_000_000, detail=detail)
        # 上限2,000万 * 0.7% = 140,000
        assert credit == 140_000

    def test_used_certified(self):
        """認定住宅（中古）3,000万円上限。"""
        detail = HousingLoanDetail(
            housing_type="resale",
            housing_category="certified",
            move_in_date="2024-05-01",
            year_end_balance=35_000_000,
            is_new_construction=False,
        )
        credit = calc_housing_loan_credit(35_000_000, detail=detail)
        # 上限3,000万 * 0.7% = 210,000
        assert credit == 210_000

    def test_backward_compat_no_detail(self):
        """detail=None の場合は従来通り balance * 0.7%。"""
        credit = calc_housing_loan_credit(35_000_000, detail=None)
        assert credit == 245_000

    def test_via_calc_income_tax(self):
        """calc_income_tax 経由で詳細住宅ローン控除が適用される。"""
        detail = HousingLoanDetail(
            housing_type="new_custom",
            housing_category="certified",
            move_in_date="2024-03-01",
            year_end_balance=40_000_000,
            is_new_construction=True,
        )
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=8_000_000,
                business_revenue=2_000_000,
                housing_loan_detail=detail,
            )
        )
        # 4,000万 * 0.7% = 280,000 の税額控除
        assert r.total_tax_credits == 280_000


# ============================================================
# 事業所得の源泉徴収（Business Withholding）
# ============================================================


class TestBusinessWithheldTax:
    """事業所得の源泉徴収税額が税額計算に反映される。"""

    def test_business_withheld_reduces_tax_due(self):
        """事業源泉徴収税額が tax_due から差し引かれる。"""
        base = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
            )
        )
        with_bw = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                business_withheld_tax=50_000,
            )
        )
        # total_tax は同じ
        assert with_bw.total_tax == base.total_tax
        # tax_due が事業源泉分だけ減る
        assert with_bw.tax_due == base.tax_due - 50_000
        assert with_bw.business_withheld_tax == 50_000

    def test_business_withheld_zero_backward_compatible(self):
        """事業源泉0（デフォルト） → 従来計算と同じ。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                business_withheld_tax=0,
            )
        )
        assert r.business_withheld_tax == 0
        assert r.tax_due == r.total_tax - r.withheld_tax

    def test_business_withheld_causes_refund(self):
        """事業源泉+給与源泉により還付になるケース。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                business_withheld_tax=400_000,
            )
        )
        # total_tax = 805,400; tax_due = 805,400 - 466,800 - 400,000 = -61,400
        assert r.tax_due < 0

    def test_combined_with_estimated_tax(self):
        """事業源泉+予定納税の両方がある場合。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                withheld_tax=466_800,
                business_withheld_tax=50_000,
                estimated_tax_payment=100_000,
            )
        )
        expected_due = r.total_tax - 466_800 - 50_000 - 100_000
        assert r.tax_due == expected_due

    def test_business_withheld_in_result(self):
        """business_withheld_tax が結果モデルに含まれる。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=1_000_000,
                business_withheld_tax=30_000,
            )
        )
        assert r.business_withheld_tax == 30_000


# ============================================================
# 損失繰越（Loss Carryforward）
# ============================================================


class TestLossCarryforward:
    """繰越損失の適用テスト。"""

    def test_loss_reduces_total_income(self):
        """繰越損失が総所得金額から控除される。"""
        base = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
            )
        )
        with_loss = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
                loss_carryforward_amount=1_000_000,
            )
        )
        # 総所得から繰越損失分が差し引かれる
        assert with_loss.total_income == base.total_income - 1_000_000
        assert with_loss.loss_carryforward_applied == 1_000_000
        assert with_loss.total_tax < base.total_tax

    def test_loss_capped_at_total_income(self):
        """繰越損失が総所得を超える場合、総所得分のみ適用。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=3_000_000,
                business_revenue=500_000,
                loss_carryforward_amount=10_000_000,
            )
        )
        # salary_after = 3,000K - 980K(給与所得控除) = 2,020K
        # business = 500K - 650K = -150K
        # total_income_raw = 2,020K + (-150K) = 1,870K
        assert r.loss_carryforward_applied == 1_870_000
        assert r.total_income == 0
        assert r.total_tax == 0

    def test_loss_zero_backward_compatible(self):
        """繰越損失0（デフォルト） → 従来計算と同じ。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=6_000_000,
                business_revenue=3_000_000,
            )
        )
        assert r.loss_carryforward_applied == 0

    def test_loss_not_applied_when_negative_income(self):
        """損益通算後に所得が0以下の場合、繰越損失は適用されない。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=1_000_000,
                business_revenue=0,
                business_expenses=2_000_000,
                loss_carryforward_amount=500_000,
            )
        )
        # salary_after = 1,000K - 650K = 350K
        # business = 0 - 2,000K - 650K = -2,650K
        # total_income_raw = 350K + (-2,650K) = -2,300K (negative)
        assert r.loss_carryforward_applied == 0
        assert r.total_income == 0

    def test_loss_partial_application(self):
        """繰越損失が一部だけ適用されるケース。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=4_000_000,
                business_revenue=1_000_000,
                loss_carryforward_amount=500_000,
            )
        )
        assert r.loss_carryforward_applied == 500_000
        # total_income は500K分減少
        base = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=4_000_000,
                business_revenue=1_000_000,
            )
        )
        assert r.total_income == base.total_income - 500_000


# ============================================================
# Phase 3: 生命保険料控除（旧制度・3区分対応）
# ============================================================


class TestLifeInsuranceDeductionOld:
    """旧制度の生命保険料控除 (max 50,000)."""

    def test_up_to_25000_full_deduction(self):
        assert calc_life_insurance_deduction_old(25_000) == 25_000

    def test_at_25001(self):
        # 25,001〜50,000: premium // 2 + 12,500
        assert calc_life_insurance_deduction_old(25_001) == 25_001 // 2 + 12_500

    def test_at_50000(self):
        assert calc_life_insurance_deduction_old(50_000) == 50_000 // 2 + 12_500

    def test_at_50001(self):
        # 50,001〜100,000: premium // 4 + 25,000
        assert calc_life_insurance_deduction_old(50_001) == 50_001 // 4 + 25_000

    def test_at_100000(self):
        assert calc_life_insurance_deduction_old(100_000) == 100_000 // 4 + 25_000

    def test_over_100000_capped(self):
        assert calc_life_insurance_deduction_old(200_000) == 50_000

    def test_zero(self):
        assert calc_life_insurance_deduction_old(0) == 0

    def test_returns_int(self):
        assert isinstance(calc_life_insurance_deduction_old(33_333), int)


class TestLifeInsuranceCategory:
    """新旧合算1区分: max(新のみ, 旧のみ, min(新+旧, 40,000))."""

    def test_new_only(self):
        result = calc_life_insurance_category(new_premium=80_000, old_premium=0)
        # 新制度 max 40,000
        assert result == 40_000

    def test_old_only(self):
        result = calc_life_insurance_category(new_premium=0, old_premium=100_000)
        # 旧制度 max 50,000
        assert result == 50_000

    def test_both_combined_capped(self):
        # 新20,000→控除10,000 + 旧30,000→控除27,500 = 37,500 (< 40,000)
        result = calc_life_insurance_category(new_premium=20_000, old_premium=30_000)
        new_ded = calc_life_insurance_deduction(20_000)  # 新制度
        old_ded = calc_life_insurance_deduction_old(30_000)
        expected = min(new_ded + old_ded, 40_000)
        assert result == expected

    def test_both_large_takes_old_only(self):
        # 新80,000→40,000、旧200,000→50,000、合算→min(90,000,40,000)=40,000
        # max(40,000, 50,000, 40,000) = 50,000（旧のみが有利）
        result = calc_life_insurance_category(new_premium=80_000, old_premium=200_000)
        assert result == 50_000

    def test_zero_both(self):
        assert calc_life_insurance_category(0, 0) == 0


class TestLifeInsuranceTotal:
    """3区分合計 max 120,000."""

    def test_all_max(self):
        # 各区分max値で合計120,000上限
        result = calc_life_insurance_total(
            general_new=80_000,
            general_old=200_000,
            medical_care=80_000,
            annuity_new=80_000,
            annuity_old=200_000,
        )
        assert result == 120_000

    def test_single_category(self):
        result = calc_life_insurance_total(
            general_new=30_000,
            general_old=0,
            medical_care=0,
            annuity_new=0,
            annuity_old=0,
        )
        # 新制度 30,000→控除15,000
        assert result == calc_life_insurance_deduction(30_000)
        assert result < 120_000

    def test_all_zero(self):
        assert calc_life_insurance_total(0, 0, 0, 0, 0) == 0

    def test_returns_int(self):
        assert isinstance(calc_life_insurance_total(50_000, 50_000, 50_000, 50_000, 50_000), int)

    def test_via_calc_deductions_detail(self):
        """LifeInsurancePremiumInput を使った場合の calc_deductions 統合テスト。"""
        detail = LifeInsurancePremiumInput(
            general_new=80_000,
            general_old=0,
            medical_care=60_000,
            annuity_new=0,
            annuity_old=80_000,
        )
        r = calc_deductions(total_income=5_000_000, life_insurance_detail=detail)
        li = [d for d in r.income_deductions if d.type == "life_insurance"]
        assert len(li) == 1
        expected = calc_life_insurance_total(80_000, 0, 60_000, 0, 80_000)
        assert li[0].amount == expected


# ============================================================
# Phase 4: 地震保険料控除（旧長期損害保険対応）
# ============================================================


class TestEarthquakeInsuranceDeduction:
    """地震保険料控除 + 旧長期損害保険料。"""

    def test_earthquake_only_under_50000(self):
        assert calc_earthquake_insurance_deduction(30_000) == 30_000

    def test_earthquake_only_at_50000(self):
        assert calc_earthquake_insurance_deduction(50_000) == 50_000

    def test_earthquake_only_over_50000(self):
        assert calc_earthquake_insurance_deduction(80_000) == 50_000

    def test_old_long_term_up_to_5000(self):
        assert calc_earthquake_insurance_deduction(0, 5_000) == 5_000

    def test_old_long_term_at_5001(self):
        # 5,001〜15,000: premium // 2 + 2,500
        assert calc_earthquake_insurance_deduction(0, 5_001) == 5_001 // 2 + 2_500

    def test_old_long_term_at_15000(self):
        assert calc_earthquake_insurance_deduction(0, 15_000) == 15_000 // 2 + 2_500

    def test_old_long_term_over_15000(self):
        assert calc_earthquake_insurance_deduction(0, 20_000) == 15_000

    def test_combined_capped_at_50000(self):
        # 地震40,000 + 旧長期20,000→15,000 = 55,000 → cap 50,000
        assert calc_earthquake_insurance_deduction(40_000, 20_000) == 50_000

    def test_combined_under_cap(self):
        # 地震20,000 + 旧長期5,000→5,000 = 25,000
        assert calc_earthquake_insurance_deduction(20_000, 5_000) == 25_000

    def test_zero_both(self):
        assert calc_earthquake_insurance_deduction(0, 0) == 0

    def test_returns_int(self):
        assert isinstance(calc_earthquake_insurance_deduction(12_345, 7_890), int)

    def test_via_calc_deductions(self):
        """calc_deductions with old_long_term_insurance_premium."""
        r = calc_deductions(
            total_income=5_000_000,
            earthquake_insurance_premium=30_000,
            old_long_term_insurance_premium=10_000,
        )
        eq = [d for d in r.income_deductions if d.type == "earthquake_insurance"]
        assert len(eq) == 1
        expected = calc_earthquake_insurance_deduction(30_000, 10_000)
        assert eq[0].amount == expected


# ============================================================
# Phase 5: 人的控除（寡婦/ひとり親/障害者/勤労学生）
# ============================================================


class TestWidowDeduction:
    """寡婦控除/ひとり親控除。"""

    def test_none_status(self):
        assert calc_widow_deduction("none", 3_000_000) == 0

    def test_widow_under_limit(self):
        # 寡婦: 270,000（所得500万以下）
        assert calc_widow_deduction("widow", 4_000_000) == 270_000

    def test_widow_over_limit(self):
        assert calc_widow_deduction("widow", 5_000_001) == 0

    def test_single_parent_under_limit(self):
        # ひとり親: 350,000（所得500万以下）
        assert calc_widow_deduction("single_parent", 4_000_000) == 350_000

    def test_single_parent_over_limit(self):
        assert calc_widow_deduction("single_parent", 5_000_001) == 0

    def test_at_exact_limit(self):
        assert calc_widow_deduction("widow", 5_000_000) == 270_000
        assert calc_widow_deduction("single_parent", 5_000_000) == 350_000


class TestDisabilityDeductionSelf:
    """障害者控除（本人）。"""

    def test_none(self):
        assert calc_disability_deduction_self("none") == 0

    def test_general(self):
        assert calc_disability_deduction_self("general") == 270_000

    def test_special(self):
        assert calc_disability_deduction_self("special") == 400_000


class TestWorkingStudentDeduction:
    """勤労学生控除。"""

    def test_eligible(self):
        assert calc_working_student_deduction(True, 750_000) == 270_000

    def test_not_student(self):
        assert calc_working_student_deduction(False, 500_000) == 0

    def test_income_over_limit(self):
        # 令和7年改正: 所得制限75万→85万
        assert calc_working_student_deduction(True, 850_001) == 0


class TestPersonalDeductionsIntegration:
    """人的控除の calc_deductions 統合テスト。"""

    def test_widow_in_deductions(self):
        r = calc_deductions(total_income=4_000_000, widow_status="widow")
        widow = [d for d in r.income_deductions if d.type == "widow"]
        assert len(widow) == 1
        assert widow[0].amount == 270_000

    def test_single_parent_in_deductions(self):
        r = calc_deductions(total_income=4_000_000, widow_status="single_parent")
        # ひとり親控除は type="widow" で name="ひとり親控除"
        sp = [d for d in r.income_deductions if d.type == "widow"]
        assert len(sp) == 1
        assert sp[0].amount == 350_000
        assert sp[0].name == "ひとり親控除"

    def test_disability_in_deductions(self):
        r = calc_deductions(total_income=4_000_000, disability_status="special")
        dis = [d for d in r.income_deductions if d.type == "disability_self"]
        assert len(dis) == 1
        assert dis[0].amount == 400_000

    def test_working_student_in_deductions(self):
        r = calc_deductions(total_income=700_000, working_student=True)
        ws = [d for d in r.income_deductions if d.type == "working_student"]
        assert len(ws) == 1
        assert ws[0].amount == 270_000

    def test_all_personal_deductions_combined(self):
        r = calc_deductions(
            total_income=3_000_000,
            widow_status="widow",
            disability_status="general",
        )
        widow = [d for d in r.income_deductions if d.type == "widow"]
        dis = [d for d in r.income_deductions if d.type == "disability_self"]
        assert len(widow) == 1
        assert len(dis) == 1
        assert widow[0].amount == 270_000
        assert dis[0].amount == 270_000


# ============================================================
# Phase 8: セルフメディケーション税制
# ============================================================


class TestSelfMedicationDeduction:
    """OTC購入額 - 12,000（上限88,000）。"""

    def test_basic_calculation(self):
        # 50,000 - 12,000 = 38,000
        assert calc_self_medication_deduction(50_000) == 38_000

    def test_under_threshold(self):
        assert calc_self_medication_deduction(12_000) == 0
        assert calc_self_medication_deduction(11_999) == 0

    def test_at_threshold(self):
        assert calc_self_medication_deduction(12_001) == 1

    def test_max_cap(self):
        # 100,000 + 12,000 = 112,000 → cap 88,000
        assert calc_self_medication_deduction(112_000) == 88_000
        assert calc_self_medication_deduction(200_000) == 88_000

    def test_zero(self):
        assert calc_self_medication_deduction(0) == 0

    def test_via_calc_deductions_preferred_over_medical(self):
        """セルフメディケーションが医療費控除より有利な場合。"""
        # 医療費20万 → 控除=200,000-100,000=100,000
        # セルフメディケーション10万 → 控除=100,000-12,000=88,000
        # 医療費控除が有利なので医療費控除が適用される
        r = calc_deductions(
            total_income=5_000_000,
            medical_expenses=200_000,
            self_medication_eligible=True,
            self_medication_expenses=100_000,
        )
        med = [d for d in r.income_deductions if d.type == "medical"]
        selfmed = [d for d in r.income_deductions if d.type == "self_medication"]
        # 有利な方が選択される（同時に適用されない）
        assert len(med) + len(selfmed) <= 1

    def test_selfmed_chosen_when_more_favorable(self):
        """セルフメディケーションが有利な場合に選択される。"""
        # 医療費11万 → 控除=110,000-100,000=10,000
        # セルフメディケーション5万 → 控除=50,000-12,000=38,000
        r = calc_deductions(
            total_income=5_000_000,
            medical_expenses=110_000,
            self_medication_eligible=True,
            self_medication_expenses=50_000,
        )
        selfmed = [d for d in r.income_deductions if d.type == "self_medication"]
        med = [d for d in r.income_deductions if d.type == "medical"]
        assert len(selfmed) == 1
        assert len(med) == 0
        assert selfmed[0].amount == 38_000


# ============================================================
# Phase 10: 配当控除
# ============================================================


class TestDividendTaxCredit:
    """配当控除: 課税所得1,000万以下→10%、超→5%。"""

    def test_under_10m(self):
        assert calc_dividend_tax_credit(200_000, 5_000_000) == 200_000 * 10 // 100

    def test_over_10m(self):
        assert calc_dividend_tax_credit(200_000, 15_000_000) == 200_000 * 5 // 100

    def test_at_10m(self):
        assert calc_dividend_tax_credit(200_000, 10_000_000) == 200_000 * 10 // 100

    def test_zero_dividend(self):
        assert calc_dividend_tax_credit(0, 5_000_000) == 0


# ============================================================
# Phase 10: その他所得の total_income 統合
# ============================================================


class TestOtherIncomeIntegration:
    """misc/dividend/one_time income の calc_income_tax 統合テスト。"""

    def test_misc_income_adds_to_total(self):
        base = calc_income_tax(
            IncomeTaxInput(fiscal_year=2025, business_revenue=3_000_000)
        )
        with_misc = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=3_000_000,
                misc_income=500_000,
            )
        )
        assert with_misc.total_income == base.total_income + 500_000

    def test_dividend_comprehensive_adds_to_total(self):
        base = calc_income_tax(
            IncomeTaxInput(fiscal_year=2025, business_revenue=3_000_000)
        )
        with_div = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=3_000_000,
                dividend_income_comprehensive=200_000,
            )
        )
        assert with_div.total_income == base.total_income + 200_000

    def test_one_time_income_half_rule(self):
        """一時所得: (収入 - 500,000特別控除) × 1/2 が total_income に加算。"""
        base = calc_income_tax(
            IncomeTaxInput(fiscal_year=2025, business_revenue=3_000_000)
        )
        with_onetime = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=3_000_000,
                one_time_income=1_500_000,
            )
        )
        # 一時所得 = max(0, (1,500,000 - 500,000)) * 1/2 = 500,000
        assert with_onetime.total_income == base.total_income + 500_000

    def test_one_time_income_under_special_deduction(self):
        """一時所得50万以下は特別控除で相殺。"""
        base = calc_income_tax(
            IncomeTaxInput(fiscal_year=2025, business_revenue=3_000_000)
        )
        with_onetime = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=3_000_000,
                one_time_income=400_000,
            )
        )
        assert with_onetime.total_income == base.total_income

    def test_other_income_withheld_reduces_tax_due(self):
        """other_income_withheld_tax が tax_due を減らす。"""
        without = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=5_000_000,
                misc_income=1_000_000,
            )
        )
        with_withheld = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=5_000_000,
                misc_income=1_000_000,
                other_income_withheld_tax=50_000,
            )
        )
        assert with_withheld.tax_due == without.tax_due - 50_000
