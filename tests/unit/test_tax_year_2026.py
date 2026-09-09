"""令和8年度税制改正（令和8年分以後）の年分依存ロジックのテスト。

根拠: 国税庁「令和8年4月 源泉所得税の改正のあらまし」、令和8年度税制改正の大綱（令和7年12月26日閣議決定）。
"""

from __future__ import annotations

import pytest

from shinkoku.models import (
    ConsumptionTaxInput,
    DependentInfo,
    FurusatoLimitInput,
    HousingLoanDetail,
    IncomeTaxInput,
    LifeInsurancePremiumInput,
)
from shinkoku.tools.tax_calc import (
    calc_basic_deduction,
    calc_consumption_tax,
    calc_deductions,
    calc_dependents_deduction,
    calc_furusato_deduction_limit,
    calc_furusato_limit_detailed,
    calc_housing_loan_credit,
    calc_income_tax,
    calc_life_insurance_total,
    calc_salary_deduction,
    calc_spouse_deduction,
    calc_working_student_deduction,
)

# ============================================================
# 基礎控除
# ============================================================


@pytest.mark.parametrize(
    ("total_income", "expected"),
    [
        (1_000_000, 1_040_000),  # ≤489万: 62万+42万
        (4_890_000, 1_040_000),
        (4_890_001, 670_000),  # 489万超〜655万: 62万+5万
        (6_550_000, 670_000),
        (6_550_001, 620_000),  # 655万超〜2,350万: 本則のみ
        (23_500_000, 620_000),
        (23_500_001, 480_000),  # 改正なし
        (25_000_001, 0),
    ],
)
def test_basic_deduction_2026(total_income: int, expected: int) -> None:
    assert calc_basic_deduction(total_income, 2026) == expected
    assert calc_basic_deduction(total_income, 2027) == expected


def test_basic_deduction_2025_unchanged() -> None:
    assert calc_basic_deduction(1_000_000, 2025) == 950_000
    assert calc_basic_deduction(1_000_000) == 950_000  # デフォルトは令和7年分
    assert calc_basic_deduction(5_000_000, 2025) == 630_000


def test_basic_deduction_2028() -> None:
    # 令和10年分以後: 132万以下のみ加算37万、それ以外は本則62万
    assert calc_basic_deduction(1_320_000, 2028) == 990_000
    assert calc_basic_deduction(1_320_001, 2028) == 620_000
    assert calc_basic_deduction(23_500_000, 2028) == 620_000


# ============================================================
# 給与所得控除
# ============================================================


@pytest.mark.parametrize(
    ("salary", "expected_deduction"),
    [
        (1_000_000, 740_000),  # 最低保障74万
        (1_900_000, 740_000),
        (2_190_000, 740_000),  # ≤220万は一律74万
        (2_191_000, 2_191_000 - 1_451_000),  # 給与所得の金額固定: 145万1,000円
        (2_194_000, 2_194_000 - 1_453_000),  # 145万3,000円
        (2_199_999, 2_199_999 - 1_456_000),  # 145万6,000円
        (2_200_000, 740_000),  # 220万ちょうど: 220万×30%+8万=74万
        (3_000_000, 980_000),  # 変更なし: 30%+8万
        (10_000_000, 1_950_000),
    ],
)
def test_salary_deduction_2026(salary: int, expected_deduction: int) -> None:
    assert calc_salary_deduction(salary, 2026) == expected_deduction
    assert calc_salary_deduction(salary, 2027) == expected_deduction


def test_salary_deduction_2025_unchanged() -> None:
    assert calc_salary_deduction(1_800_000, 2025) == 650_000
    assert calc_salary_deduction(1_800_000) == 650_000
    assert calc_salary_deduction(2_000_000, 2025) == 680_000


def test_salary_deduction_2028() -> None:
    # 令和10年分以後: 本則69万。190万超〜220万は 30%+8万（69万未満なら69万）
    assert calc_salary_deduction(1_900_000, 2028) == 690_000
    assert calc_salary_deduction(2_000_000, 2028) == 690_000  # 68万 < 69万
    assert calc_salary_deduction(2_100_000, 2028) == 710_000
    assert calc_salary_deduction(2_200_000, 2028) == 740_000


def test_income_tax_uses_year_specific_salary_deduction() -> None:
    result_2025 = calc_income_tax(IncomeTaxInput(fiscal_year=2025, salary_income=1_780_000))
    result_2026 = calc_income_tax(IncomeTaxInput(fiscal_year=2026, salary_income=1_780_000))
    assert result_2025.salary_income_after_deduction == 1_130_000
    assert result_2026.salary_income_after_deduction == 1_040_000
    # 178万円の壁: 給与所得104万 − 基礎控除104万 = 0 → 所得税0
    assert result_2026.taxable_income == 0


# ============================================================
# 扶養親族等の所得要件（58万→62万）
# ============================================================


def _dep(income: int, birth_date: str = "2000-06-01") -> DependentInfo:
    return DependentInfo(name="x", relationship="子", birth_date=birth_date, income=income)


def test_dependent_income_limit_2026() -> None:
    dep = _dep(600_000, birth_date="1995-01-01")  # 31歳、所得60万
    assert calc_dependents_deduction([dep], 5_000_000, fiscal_year=2025) == []
    items = calc_dependents_deduction([dep], 5_000_000, fiscal_year=2026)
    assert len(items) == 1 and items[0].amount == 380_000


def test_specific_relative_special_lower_bound_2026() -> None:
    dep = _dep(600_000, birth_date="2006-04-01")  # 20歳、所得60万
    items_2025 = calc_dependents_deduction([dep], 5_000_000, fiscal_year=2025)
    assert items_2025[0].type == "specific_relative_special" and items_2025[0].amount == 630_000
    items_2026 = calc_dependents_deduction([dep], 5_000_000, fiscal_year=2026)
    assert items_2026[0].type == "dependent" and items_2026[0].amount == 630_000  # 特定扶養


def test_spouse_deduction_threshold_2026() -> None:
    assert calc_spouse_deduction(5_000_000, 600_000, 2025) == 380_000  # 配偶者特別控除（満額）
    assert calc_spouse_deduction(5_000_000, 600_000, 2026) == 380_000  # 配偶者控除
    assert calc_spouse_deduction(5_000_000, 970_000, 2026) == 360_000
    assert calc_spouse_deduction(5_000_000, 1_330_001, 2026) == 0


def test_working_student_limit_2026() -> None:
    assert calc_working_student_deduction(True, 870_000, 2025) == 0
    assert calc_working_student_deduction(True, 870_000, 2026) == 270_000
    assert calc_working_student_deduction(True, 890_001, 2026) == 0


# ============================================================
# 生命保険料控除の子育て特例（令和8・9年分）
# ============================================================


def test_life_insurance_child_special_table() -> None:
    assert calc_life_insurance_total(general_new=30_000, child_special=True) == 30_000
    assert calc_life_insurance_total(general_new=50_000, child_special=True) == 40_000  # /2+15,000
    assert calc_life_insurance_total(general_new=100_000, child_special=True) == 55_000  # /4+30,000
    assert calc_life_insurance_total(general_new=150_000, child_special=True) == 60_000
    assert calc_life_insurance_total(general_new=150_000) == 40_000
    # 合計上限12万は変わらない
    assert (
        calc_life_insurance_total(
            general_new=150_000, medical_care=100_000, annuity_new=100_000, child_special=True
        )
        == 120_000
    )


def test_calc_deductions_applies_child_special_only_in_2026_2027() -> None:
    child = DependentInfo(name="c", relationship="子", birth_date="2015-01-01")
    detail = LifeInsurancePremiumInput(general_new=150_000)

    def li(fy: int, deps: list[DependentInfo]) -> int:
        d = calc_deductions(
            total_income=5_000_000, life_insurance_detail=detail, dependents=deps, fiscal_year=fy
        )
        return next(i.amount for i in d.income_deductions if i.type == "life_insurance")

    assert li(2025, [child]) == 40_000
    assert li(2026, [child]) == 60_000
    assert li(2027, [child]) == 60_000
    assert li(2028, [child]) == 40_000
    assert li(2026, []) == 40_000
    # 23歳以上の子は対象外
    adult = DependentInfo(name="a", relationship="子", birth_date="2000-01-01")
    assert li(2026, [adult]) == 40_000


# ============================================================
# 住宅ローン控除（令和8〜12年入居）
# ============================================================


def _hl(
    category: str, new: bool, childcare: bool = False, move_in: str = "2026-04-01"
) -> HousingLoanDetail:
    return HousingLoanDetail(
        housing_type="new_custom" if new else "used",
        housing_category=category,
        move_in_date=move_in,
        year_end_balance=60_000_000,
        is_new_construction=new,
        is_childcare_household=childcare,
    )


@pytest.mark.parametrize(
    ("category", "new", "childcare", "expected_limit"),
    [
        ("certified", True, False, 45_000_000),
        ("zeh", True, False, 35_000_000),
        ("energy_efficient", True, False, 20_000_000),
        ("general", True, False, 0),
        ("certified", True, True, 50_000_000),
        ("zeh", True, True, 45_000_000),
        ("energy_efficient", True, True, 30_000_000),
        ("certified", False, False, 35_000_000),
        ("zeh", False, False, 35_000_000),
        ("energy_efficient", False, False, 20_000_000),
        ("general", False, False, 20_000_000),
        ("certified", False, True, 45_000_000),
        ("energy_efficient", False, True, 30_000_000),
        ("general", False, True, 20_000_000),
    ],
)
def test_housing_loan_limits_r8(
    category: str, new: bool, childcare: bool, expected_limit: int
) -> None:
    detail = _hl(category, new, childcare)
    credit = calc_housing_loan_credit(detail.year_end_balance, detail)
    assert credit == expected_limit * 7 // 1000


def test_housing_loan_energy_efficient_new_after_2027() -> None:
    detail = _hl("energy_efficient", True, move_in="2028-03-01")
    assert calc_housing_loan_credit(detail.year_end_balance, detail) == 20_000_000 * 7 // 1000


def test_housing_loan_r7_unchanged() -> None:
    detail = _hl("certified", False, move_in="2025-10-01")
    assert calc_housing_loan_credit(detail.year_end_balance, detail) == 30_000_000 * 7 // 1000


# ============================================================
# 消費税 3割特例
# ============================================================


def test_consumption_tax_special_30pct() -> None:
    result = calc_consumption_tax(
        ConsumptionTaxInput(fiscal_year=2027, method="special_30pct", taxable_sales_10=11_000_000)
    )
    # 課税標準額1,000万 → 国税78万 → 納付は30%=23.4万、地方消費税 23.4万×22/78=6.6万
    assert result.national_tax_on_sales == 780_000
    assert result.tax_on_purchases == 546_000
    assert result.net_tax == 234_000
    assert result.local_tax_due == 66_000
    assert result.total_due == 300_000


# ============================================================
# ふるさと納税上限（住民税側の控除を考慮）
# ============================================================


def test_furusato_limit_detailed_matches_soumu_table() -> None:
    """総務省の目安表（給与収入・独身・社会保険料15%）と一致することを確認する。"""
    expectations = {3_000_000: 28_000, 5_000_000: 61_000, 7_000_000: 108_000, 10_000_000: 176_000}
    for fy in (2025, 2026):
        for salary, expected in expectations.items():
            income = salary - calc_salary_deduction(salary, fy)
            result = calc_furusato_limit_detailed(
                FurusatoLimitInput(
                    fiscal_year=fy, total_income=income, social_insurance=salary * 15 // 100
                )
            )
            assert abs(result.estimated_limit - expected) < 2_000, (fy, salary, result)


def test_furusato_limit_detailed_spouse_and_child() -> None:
    # 総務省目安表: 給与500万・夫婦（配偶者控除あり）+子1人（16歳以上）→ 40,000円
    result = calc_furusato_limit_detailed(
        FurusatoLimitInput(
            fiscal_year=2026,
            total_income=5_000_000 - calc_salary_deduction(5_000_000, 2026),
            social_insurance=750_000,
            spouse_income=0,
            dependents=[DependentInfo(name="c", relationship="子", birth_date="2008-05-01")],
        )
    )
    assert abs(result.estimated_limit - 40_000) < 2_000
    # 人的控除差: 基礎5万 + 配偶者5万 + 一般扶養5万
    assert result.personal_deduction_difference == 150_000
    # 住民税課税所得 172万（≤200万）→ min(人的控除差15万, 課税所得) × 5% = 7,500
    assert result.adjustment_credit == 7_500


def test_furusato_limit_detailed_is_independent_of_income_tax_basic_deduction() -> None:
    """所得税の基礎控除が58万→104万に増えても住民税所得割は変わらないので上限も変わらない。"""
    kwargs = {"total_income": 3_500_000, "social_insurance": 500_000}
    r25 = calc_furusato_limit_detailed(FurusatoLimitInput(fiscal_year=2025, **kwargs))
    r26 = calc_furusato_limit_detailed(FurusatoLimitInput(fiscal_year=2026, **kwargs))
    assert r25.income_tax_deductions_total < r26.income_tax_deductions_total
    assert r25.resident_tax_taxable_income == r26.resident_tax_taxable_income
    assert r25.estimated_limit == r26.estimated_limit


def test_furusato_limit_legacy_signature_still_works() -> None:
    assert calc_furusato_deduction_limit(5_000_000, 1_500_000) > 0
    # 住民税側の控除を渡すと上限が大きくなる（基礎控除差 61万 → 所得割 +6.1万）
    simple = calc_furusato_deduction_limit(5_000_000, 1_500_000)
    detailed = calc_furusato_deduction_limit(
        5_000_000,
        1_500_000,
        resident_tax_income_deductions=890_000,
        personal_deduction_difference=50_000,
    )
    assert detailed > simple


def test_furusato_special_credit_cap_from_2027() -> None:
    # 所得割額 1,500万（課税所得1.5億）→ 特例控除上限 300万 → 2027年以後は193万でキャップ
    r26 = calc_furusato_limit_detailed(
        FurusatoLimitInput(fiscal_year=2026, total_income=150_000_000)
    )
    r27 = calc_furusato_limit_detailed(
        FurusatoLimitInput(fiscal_year=2027, total_income=150_000_000)
    )
    assert not r26.special_credit_cap_applied
    assert r27.special_credit_cap_applied
    assert r27.special_credit_max == 1_930_000
    assert r27.estimated_limit < r26.estimated_limit
