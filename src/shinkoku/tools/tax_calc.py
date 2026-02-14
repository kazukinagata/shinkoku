"""Tax calculation tools for income tax, deductions, depreciation, and consumption tax.

All monetary values are int (yen). No floats allowed.
Rounding rules:
  - Taxable income: truncate to 1,000 yen
  - Income tax (filing amount): truncate to 100 yen
  - Reconstruction tax: truncate to 1 yen
  - Consumption tax (national): truncate to 100 yen
"""

from __future__ import annotations

from shinkoku.models import (
    DeductionItem,
    DeductionsResult,
    DependentInfo,
    HousingLoanDetail,
    IncomeTaxInput,
    IncomeTaxResult,
    ConsumptionTaxInput,
    ConsumptionTaxResult,
)


# ============================================================
# Basic Deduction (Reiwa 7 stepped table)
# ============================================================

# (upper_limit_inclusive, deduction_amount)
# Reiwa 7-8 only: 本則改正(48万→58万) + 租税特別措置法第41条の16の2 加算特例
# R9以降は132万以下=95万のみ維持、それ以外は一律58万に戻る（時限措置）
_BASIC_DEDUCTION_TABLE: list[tuple[int, int]] = [
    (1_320_000, 950_000),  # ≤132万: 95万 (本則58万+加算37万)
    (3_360_000, 880_000),  # 132万超〜336万: 88万 (本則58万+加算30万)
    (4_890_000, 680_000),  # 336万超〜489万: 68万 (本則58万+加算10万)
    (6_550_000, 630_000),  # 489万超〜655万: 63万 (本則58万+加算5万)
    (23_500_000, 580_000),  # 655万超〜2,350万: 58万 (本則のみ)
    (24_000_000, 480_000),  # 2,350万超〜2,400万: 48万
    (24_500_000, 320_000),  # 2,400万超〜2,450万: 32万
    (25_000_000, 160_000),  # 2,450万超〜2,500万: 16万
]


def calc_basic_deduction(total_income: int) -> int:
    """Calculate basic deduction based on total income (Reiwa 7)."""
    for upper, deduction in _BASIC_DEDUCTION_TABLE:
        if total_income <= upper:
            return deduction
    return 0


# ============================================================
# Salary Income Deduction (Reiwa 7)
# ============================================================


def calc_salary_deduction(salary_income: int) -> int:
    """Calculate salary income deduction (Reiwa 7 revision).

    Returns the deduction amount (not the net salary income).
    """
    if salary_income <= 0:
        return 0
    if salary_income <= 1_625_000:
        return 650_000
    if salary_income <= 1_800_000:
        return int(salary_income * 40 // 100) - 100_000
    if salary_income <= 3_600_000:
        return int(salary_income * 30 // 100) + 80_000
    if salary_income <= 6_600_000:
        return int(salary_income * 20 // 100) + 440_000
    if salary_income <= 8_500_000:
        return int(salary_income * 10 // 100) + 1_100_000
    return 1_950_000


# ============================================================
# Life Insurance Deduction (new system, per-category)
# ============================================================


def calc_life_insurance_deduction(premium: int) -> int:
    """Calculate life insurance deduction for one category (new system).

    New system: max 40,000 per category, max 120,000 total for 3 categories.
    This function calculates for a single category.
    """
    if premium <= 0:
        return 0
    if premium <= 20_000:
        return premium
    if premium <= 40_000:
        return premium // 2 + 10_000
    if premium <= 80_000:
        return premium // 4 + 20_000
    return 40_000


# ============================================================
# Spouse Deduction
# ============================================================

# Spouse deduction tables (Reiwa 7~)
# 配偶者控除: 配偶者所得≤58万 → 38万/26万/13万 (taxpayer income bracket)
# 配偶者特別控除: 配偶者所得58万超〜133万 → 段階的控除
# Based on NTA No.1195 (https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1195.htm)
#
# (spouse_income_upper, deduction) for taxpayer income <= 9,000,000
_SPOUSE_SPECIAL_TABLE: list[tuple[int, int]] = [
    (580_000, 380_000),  # ≤58万: 配偶者控除 38万
    (950_000, 380_000),  # 58万超〜95万: 配偶者特別控除 38万（満額）
    (1_000_000, 360_000),  # 95万超〜100万: 36万
    (1_050_000, 310_000),  # 100万超〜105万: 31万
    (1_100_000, 260_000),  # 105万超〜110万: 26万
    (1_150_000, 210_000),  # 110万超〜115万: 21万
    (1_200_000, 160_000),  # 115万超〜120万: 16万
    (1_250_000, 110_000),  # 120万超〜125万: 11万
    (1_300_000, 60_000),  # 125万超〜130万: 6万
    (1_330_000, 30_000),  # 130万超〜133万: 3万
]

# taxpayer income 900万超〜950万
_SPOUSE_SPECIAL_TABLE_9M: list[tuple[int, int]] = [
    (580_000, 260_000),  # ≤58万: 配偶者控除 26万
    (950_000, 260_000),  # 58万超〜95万: 26万
    (1_000_000, 240_000),  # 95万超〜100万: 24万
    (1_050_000, 210_000),  # 100万超〜105万: 21万
    (1_100_000, 180_000),  # 105万超〜110万: 18万
    (1_150_000, 140_000),  # 110万超〜115万: 14万
    (1_200_000, 110_000),  # 115万超〜120万: 11万
    (1_250_000, 80_000),  # 120万超〜125万: 8万
    (1_300_000, 40_000),  # 125万超〜130万: 4万
    (1_330_000, 20_000),  # 130万超〜133万: 2万
]

# taxpayer income 950万超〜1,000万
_SPOUSE_SPECIAL_TABLE_10M: list[tuple[int, int]] = [
    (580_000, 130_000),  # ≤58万: 配偶者控除 13万
    (950_000, 130_000),  # 58万超〜95万: 13万
    (1_000_000, 120_000),  # 95万超〜100万: 12万
    (1_050_000, 100_000),  # 100万超〜105万: 10万
    (1_100_000, 90_000),  # 105万超〜110万: 9万
    (1_150_000, 70_000),  # 110万超〜115万: 7万
    (1_200_000, 50_000),  # 115万超〜120万: 5万
    (1_250_000, 40_000),  # 120万超〜125万: 4万
    (1_300_000, 20_000),  # 125万超〜130万: 2万
    (1_330_000, 10_000),  # 130万超〜133万: 1万
]


def calc_spouse_deduction(taxpayer_income: int, spouse_income: int | None) -> int:
    """Calculate spouse deduction / special spouse deduction."""
    if spouse_income is None:
        return 0
    if taxpayer_income > 10_000_000:
        return 0

    # Select the appropriate table based on taxpayer income
    if taxpayer_income <= 9_000_000:
        table = _SPOUSE_SPECIAL_TABLE
    elif taxpayer_income <= 9_500_000:
        table = _SPOUSE_SPECIAL_TABLE_9M
    else:  # <= 10_000_000
        table = _SPOUSE_SPECIAL_TABLE_10M

    for upper, deduction in table:
        if spouse_income <= upper:
            return deduction
    return 0


# ============================================================
# Dependent Deduction (扶養控除)
# ============================================================


def _calc_age(birth_date: str, fiscal_year_end: str = "2025-12-31") -> int:
    """Calculate age at end of fiscal year from birth_date (YYYY-MM-DD)."""
    by, bm, bd = (int(x) for x in birth_date.split("-"))
    ey, em, ed = (int(x) for x in fiscal_year_end.split("-"))
    age = ey - by
    if (em, ed) < (bm, bd):
        age -= 1
    return age


def calc_dependents_deduction(
    dependents: list[DependentInfo],
    taxpayer_income: int,
    fiscal_year: int = 2025,
) -> list[DeductionItem]:
    """Calculate deductions for dependents (扶養控除 + 障害者控除).

    扶養控除（配偶者以外の親族で所得48万以下）:
    - 一般扶養: 38万円（16歳以上）
    - 特定扶養: 63万円（19歳以上23歳未満）
    - 老人扶養（同居）: 58万円（70歳以上、同居）
    - 老人扶養（別居）: 48万円（70歳以上、別居）
    - 16歳未満: 扶養控除なし（児童手当対象）

    障害者控除:
    - 一般障害者: 27万円
    - 特別障害者: 40万円
    - 同居特別障害者: 75万円
    """
    items: list[DeductionItem] = []
    fiscal_year_end = f"{fiscal_year}-12-31"

    for dep in dependents:
        # 配偶者は配偶者控除で処理するため除外
        if dep.relationship == "配偶者":
            continue

        # 所得要件: 48万円以下
        if dep.income > 480_000:
            continue

        age = _calc_age(dep.birth_date, fiscal_year_end)

        # 扶養控除（16歳以上のみ）
        if age >= 70:
            # 老人扶養親族
            if dep.cohabiting:
                deduction = 580_000  # 同居老親等
                detail = f"{dep.name}（老人扶養・同居）"
            else:
                deduction = 480_000  # 別居
                detail = f"{dep.name}（老人扶養・別居）"
            items.append(
                DeductionItem(
                    type="dependent",
                    name="扶養控除",
                    amount=deduction,
                    details=detail,
                )
            )
        elif age >= 19 and age < 23:
            # 特定扶養親族（19歳以上23歳未満）
            items.append(
                DeductionItem(
                    type="dependent",
                    name="扶養控除",
                    amount=630_000,
                    details=f"{dep.name}（特定扶養）",
                )
            )
        elif age >= 16:
            # 一般扶養親族
            items.append(
                DeductionItem(
                    type="dependent",
                    name="扶養控除",
                    amount=380_000,
                    details=f"{dep.name}（一般扶養）",
                )
            )
        # 16歳未満: 扶養控除なし

        # 障害者控除（年齢制限なし）
        if dep.disability == "special_cohabiting":
            items.append(
                DeductionItem(
                    type="disability",
                    name="障害者控除",
                    amount=750_000,
                    details=f"{dep.name}（同居特別障害者）",
                )
            )
        elif dep.disability == "special":
            items.append(
                DeductionItem(
                    type="disability",
                    name="障害者控除",
                    amount=400_000,
                    details=f"{dep.name}（特別障害者）",
                )
            )
        elif dep.disability == "general":
            items.append(
                DeductionItem(
                    type="disability",
                    name="障害者控除",
                    amount=270_000,
                    details=f"{dep.name}（一般障害者）",
                )
            )

    return items


# ============================================================
# Furusato Nozei (Hometown Tax Donation) Deduction
# ============================================================


def calc_furusato_deduction(donation: int, total_income: int | None = None) -> int:
    """Calculate furusato nozei income deduction.

    所得税法第78条: 控除額 = MIN(寄附金合計, 総所得金額等×40%) - 2,000円
    total_income が指定されない場合は40%上限を適用しない（集計表示用）。
    """
    if donation <= 2_000:
        return 0
    capped = donation
    if total_income is not None:
        capped = min(donation, total_income * 40 // 100)
    if capped <= 2_000:
        return 0
    return capped - 2_000


# ============================================================
# Housing Loan Tax Credit
# ============================================================

# 住宅区分別の年末残高上限額（令和4年〜7年入居）
# (housing_category, is_new_construction) -> balance_limit
_HOUSING_LOAN_LIMITS: dict[tuple[str, bool], int] = {
    # 新築
    ("certified", True): 50_000_000,  # 認定住宅（長期優良/低炭素）
    ("zeh", True): 45_000_000,  # ZEH水準省エネ住宅
    ("energy_efficient", True): 40_000_000,  # 省エネ基準適合住宅
    ("general", True): 30_000_000,  # 一般住宅
    # 中古
    ("certified", False): 30_000_000,  # 認定住宅（中古）
    ("zeh", False): 30_000_000,  # ZEH水準省エネ住宅（中古）
    ("energy_efficient", False): 30_000_000,  # 省エネ基準適合住宅（中古）
    ("general", False): 20_000_000,  # 一般住宅（中古）
}


def calc_housing_loan_credit(
    balance: int,
    detail: HousingLoanDetail | None = None,
) -> int:
    """Calculate housing loan tax credit.

    控除率: 0.7%（令和4年以降入居）
    控除期間: 新築13年、中古10年（ここでは年単位の判定は呼び出し側で行う）
    年末残高上限: 住宅区分別に異なる

    detail が None の場合は従来のシンプル計算（balance * 0.7%）を行う。
    """
    if balance <= 0:
        return 0

    if detail is not None:
        key = (detail.housing_category, detail.is_new_construction)
        limit = _HOUSING_LOAN_LIMITS.get(key, 30_000_000)
        capped = min(detail.year_end_balance, limit)
        return int(capped * 7 // 1000)

    return int(balance * 7 // 1000)


# ============================================================
# Aggregated Deductions Calculator
# ============================================================


def calc_deductions(
    total_income: int,
    social_insurance: int = 0,
    life_insurance_premium: int = 0,
    earthquake_insurance_premium: int = 0,
    medical_expenses: int = 0,
    furusato_nozei: int = 0,
    housing_loan_balance: int = 0,
    spouse_income: int | None = None,
    ideco_contribution: int = 0,
    dependents: list[DependentInfo] | None = None,
    fiscal_year: int = 2025,
    housing_loan_detail: HousingLoanDetail | None = None,
) -> DeductionsResult:
    """Calculate all applicable deductions and return structured result."""
    income_deductions: list[DeductionItem] = []
    tax_credits: list[DeductionItem] = []

    # 1. Basic deduction (always applied if > 0)
    basic = calc_basic_deduction(total_income)
    if basic > 0:
        income_deductions.append(DeductionItem(type="basic", name="基礎控除", amount=basic))

    # 2. Social insurance (full amount)
    if social_insurance > 0:
        income_deductions.append(
            DeductionItem(
                type="social_insurance",
                name="社会保険料控除",
                amount=social_insurance,
            )
        )

    # 3. Life insurance (new system - treat as single category for simplicity)
    if life_insurance_premium > 0:
        li_deduction = calc_life_insurance_deduction(life_insurance_premium)
        if li_deduction > 0:
            income_deductions.append(
                DeductionItem(
                    type="life_insurance",
                    name="生命保険料控除",
                    amount=li_deduction,
                )
            )

    # 4. Earthquake insurance
    if earthquake_insurance_premium > 0:
        eq_deduction = min(earthquake_insurance_premium, 50_000)
        income_deductions.append(
            DeductionItem(
                type="earthquake_insurance",
                name="地震保険料控除",
                amount=eq_deduction,
            )
        )

    # 5. iDeCo / 小規模企業共済等掛金控除（全額所得控除）
    if ideco_contribution > 0:
        income_deductions.append(
            DeductionItem(
                type="small_business_mutual_aid",
                name="小規模企業共済等掛金控除",
                amount=ideco_contribution,
                details="iDeCo",
            )
        )

    # 6. Medical expenses (所得税法第73条)
    # Threshold: min(100,000, total_income * 5%)
    medical_threshold = min(100_000, total_income * 5 // 100)
    if medical_expenses > medical_threshold:
        med_deduction = min(medical_expenses - medical_threshold, 2_000_000)
        income_deductions.append(
            DeductionItem(
                type="medical",
                name="医療費控除",
                amount=med_deduction,
            )
        )

    # 7. Furusato nozei（所得税法第78条: 総所得金額×40%上限）
    if furusato_nozei > 0:
        furusato = calc_furusato_deduction(furusato_nozei, total_income=total_income)
        if furusato > 0:
            income_deductions.append(
                DeductionItem(
                    type="furusato_nozei",
                    name="寄附金控除",
                    amount=furusato,
                    details="ふるさと納税",
                )
            )

    # 8. Spouse deduction
    if spouse_income is not None:
        spouse = calc_spouse_deduction(total_income, spouse_income)
        if spouse > 0:
            income_deductions.append(
                DeductionItem(
                    type="spouse",
                    name="配偶者控除",
                    amount=spouse,
                )
            )

    # 9. Dependent deductions (扶養控除 + 障害者控除)
    if dependents:
        dep_items = calc_dependents_deduction(
            dependents=dependents,
            taxpayer_income=total_income,
            fiscal_year=fiscal_year,
        )
        income_deductions.extend(dep_items)

    # Tax credits
    # Housing loan credit
    hl_balance = housing_loan_balance
    if housing_loan_detail is not None:
        hl_balance = housing_loan_detail.year_end_balance
    if hl_balance > 0:
        hl_credit = calc_housing_loan_credit(hl_balance, detail=housing_loan_detail)
        if hl_credit > 0:
            tax_credits.append(
                DeductionItem(
                    type="housing_loan",
                    name="住宅ローン控除",
                    amount=hl_credit,
                )
            )

    total_income_deductions = sum(d.amount for d in income_deductions)
    total_tax_credits = sum(d.amount for d in tax_credits)

    return DeductionsResult(
        income_deductions=income_deductions,
        tax_credits=tax_credits,
        total_income_deductions=total_income_deductions,
        total_tax_credits=total_tax_credits,
    )


# ============================================================
# Depreciation (Task 14)
# ============================================================


def calc_depreciation_straight_line(
    acquisition_cost: int,
    useful_life: int,
    business_use_ratio: int,
    months: int = 12,
) -> int:
    """Straight-line depreciation.

    amount = acquisition_cost * (1/useful_life) * (business_use_ratio/100) * (months/12)
    """
    if useful_life <= 0 or months <= 0:
        return 0
    annual = acquisition_cost // useful_life
    amount = annual * business_use_ratio * months // (100 * 12)
    return amount


def calc_depreciation_declining_balance(
    book_value: int,
    declining_rate: int,
    business_use_ratio: int,
    months: int = 12,
) -> int:
    """Declining balance depreciation.

    amount = book_value * (declining_rate/1000) * (business_use_ratio/100) * (months/12)
    declining_rate is expressed in per-mille (e.g., 500 means 0.500).
    """
    if book_value <= 0 or months <= 0:
        return 0
    amount = book_value * declining_rate * business_use_ratio * months // (1000 * 100 * 12)
    return amount


# ============================================================
# Income Tax Calculation (Task 15)
# ============================================================

# (upper_limit, rate_percent, deduction)
_INCOME_TAX_TABLE: list[tuple[int, int, int]] = [
    (1_950_000, 5, 0),
    (3_300_000, 10, 97_500),
    (6_950_000, 20, 427_500),
    (9_000_000, 23, 636_000),
    (18_000_000, 33, 1_536_000),
    (40_000_000, 40, 2_796_000),
]


def _calc_income_tax_from_table(taxable_income: int) -> int:
    """Apply the income tax quick calculation table. All int arithmetic."""
    if taxable_income <= 0:
        return 0
    for upper, rate, deduction in _INCOME_TAX_TABLE:
        if taxable_income <= upper:
            return taxable_income * rate // 100 - deduction
    # Over 40,000,000
    return taxable_income * 45 // 100 - 4_796_000


def calc_income_tax(input_data: IncomeTaxInput) -> IncomeTaxResult:
    """Full income tax calculation flow (Reiwa 7).

    Steps:
    1. Salary income after deduction
    2. Business income = revenue - expenses - blue return deduction
    3. Total income
    4. Income deductions (call calc_deductions)
    5. Taxable income (truncate to 1,000 yen, min 0)
    6. Tax from table
    7. Tax credits (housing loan)
    8. Reconstruction tax = tax * 2.1% (truncate to 1 yen)
    9. Filing tax amount (truncate to 100 yen)
    10. Difference = filing amount - withheld tax
    """
    # Step 1: Salary income after deduction
    salary_deduction = calc_salary_deduction(input_data.salary_income)
    salary_income_after = max(0, input_data.salary_income - salary_deduction)

    # Step 2: Business income（赤字の場合は負値 → 給与所得と損益通算）
    business_income = (
        input_data.business_revenue
        - input_data.business_expenses
        - input_data.blue_return_deduction
    )

    # Step 3: Total income（損益通算後、0円未満にはならない）
    total_income_raw = salary_income_after + business_income

    # Step 3.5: 繰越損失の適用（青色申告の場合、3年繰越）
    loss_applied = 0
    if input_data.loss_carryforward_amount > 0 and total_income_raw > 0:
        loss_applied = min(input_data.loss_carryforward_amount, total_income_raw)
        total_income_raw -= loss_applied

    total_income = max(0, total_income_raw)

    # Step 4: Income deductions
    deductions = calc_deductions(
        total_income=total_income,
        social_insurance=input_data.social_insurance,
        life_insurance_premium=input_data.life_insurance_premium,
        earthquake_insurance_premium=input_data.earthquake_insurance_premium,
        medical_expenses=input_data.medical_expenses,
        furusato_nozei=input_data.furusato_nozei,
        housing_loan_balance=input_data.housing_loan_balance,
        spouse_income=input_data.spouse_income,
        ideco_contribution=input_data.ideco_contribution,
        dependents=input_data.dependents or None,
        fiscal_year=input_data.fiscal_year,
        housing_loan_detail=input_data.housing_loan_detail,
    )

    total_income_deductions = deductions.total_income_deductions

    # Step 5: Taxable income (truncate to 1,000 yen, min 0)
    taxable_income_raw = max(0, total_income - total_income_deductions)
    taxable_income = (taxable_income_raw // 1_000) * 1_000

    # Step 6: Tax from table
    income_tax_base = _calc_income_tax_from_table(taxable_income)

    # Step 7: Tax credits
    total_tax_credits = deductions.total_tax_credits
    income_tax_after_credits = max(0, income_tax_base - total_tax_credits)

    # Step 8: Reconstruction tax = 2.1% (truncate to 1 yen)
    reconstruction_tax = int(income_tax_after_credits * 21 // 1000)

    # Step 9: Total tax and filing amount (truncate to 100 yen)
    total_tax_raw = income_tax_after_credits + reconstruction_tax
    total_tax = (total_tax_raw // 100) * 100

    # Step 10: Difference（給与源泉+事業源泉+予定納税を差し引く）
    total_withheld = (
        input_data.withheld_tax
        + input_data.business_withheld_tax
        + input_data.estimated_tax_payment
    )
    tax_due = total_tax - total_withheld

    return IncomeTaxResult(
        fiscal_year=input_data.fiscal_year,
        salary_income_after_deduction=salary_income_after,
        business_income=business_income,
        total_income=total_income,
        total_income_deductions=total_income_deductions,
        taxable_income=taxable_income,
        income_tax_base=income_tax_base,
        total_tax_credits=total_tax_credits,
        income_tax_after_credits=income_tax_after_credits,
        reconstruction_tax=reconstruction_tax,
        total_tax=total_tax,
        withheld_tax=input_data.withheld_tax,
        business_withheld_tax=input_data.business_withheld_tax,
        estimated_tax_payment=input_data.estimated_tax_payment,
        loss_carryforward_applied=loss_applied,
        tax_due=tax_due,
        deductions_detail=deductions,
    )


# ============================================================
# Consumption Tax Calculation (Task 16)
# ============================================================

# Simplified taxation deemed purchase ratios by business type (percent)
_SIMPLIFIED_RATIOS: dict[int, int] = {
    1: 90,  # Wholesale
    2: 80,  # Retail
    3: 70,  # Manufacturing
    4: 60,  # Other
    5: 50,  # Service
    6: 40,  # Real estate
}


def calc_consumption_tax(input_data: ConsumptionTaxInput) -> ConsumptionTaxResult:
    """Calculate consumption tax (Reiwa 7).

    Methods:
    - special_20pct: Invoice 2-wari special = sales tax * 20%
    - simplified: Simplified taxation = tax * (1 - deemed ratio)
    - standard: Standard taxation = sales tax - purchase tax

    National tax rate = 7.8/10 of total 10% rate
    Local consumption tax = national * 22/78
    All truncated to 100 yen.
    """
    # Calculate tax on sales
    # For 10% rate items: tax_included_amount * 10/110 or tax_excluded * 10/100
    # We assume inputs are tax-excluded amounts
    tax_on_sales_10 = input_data.taxable_sales_10 * 10 // 110 if input_data.taxable_sales_10 else 0
    tax_on_sales_8 = input_data.taxable_sales_8 * 8 // 108 if input_data.taxable_sales_8 else 0

    # Actually, let's treat inputs as tax-included amounts for sales
    # and compute the consumption tax portion
    total_tax_on_sales = tax_on_sales_10 + tax_on_sales_8
    taxable_sales_total = input_data.taxable_sales_10 + input_data.taxable_sales_8

    if input_data.method == "special_20pct":
        # 2-wari special: tax due = sales tax * 20%
        tax_due_raw = total_tax_on_sales * 20 // 100
        tax_on_purchases = total_tax_on_sales - tax_due_raw  # deemed 80% credit

    elif input_data.method == "simplified":
        btype = input_data.simplified_business_type or 5  # default: service
        ratio = _SIMPLIFIED_RATIOS.get(btype, 50)
        tax_on_purchases = total_tax_on_sales * ratio // 100
        tax_due_raw = total_tax_on_sales - tax_on_purchases

    else:  # standard
        tax_on_purchases_10 = (
            input_data.taxable_purchases_10 * 10 // 110 if input_data.taxable_purchases_10 else 0
        )
        tax_on_purchases_8 = (
            input_data.taxable_purchases_8 * 8 // 108 if input_data.taxable_purchases_8 else 0
        )
        tax_on_purchases = tax_on_purchases_10 + tax_on_purchases_8
        tax_due_raw = total_tax_on_sales - tax_on_purchases

    # Split into national (7.8/10) and local (2.2/10)
    # National tax = tax_due * 78/100, truncated to 100 yen
    national_tax = max(0, tax_due_raw * 78 // 100)
    national_tax = (national_tax // 100) * 100

    # Local tax = national * 22/78, truncated to 100 yen
    local_tax = national_tax * 22 // 78
    local_tax = (local_tax // 100) * 100

    total_due = national_tax + local_tax

    return ConsumptionTaxResult(
        fiscal_year=input_data.fiscal_year,
        method=input_data.method,
        taxable_sales_total=taxable_sales_total,
        tax_on_sales=total_tax_on_sales,
        tax_on_purchases=tax_on_purchases,
        tax_due=national_tax,
        local_tax_due=local_tax,
        total_due=total_due,
    )


# ============================================================
# Furusato Nozei Deduction Limit Estimation
# ============================================================


def _get_marginal_tax_rate(taxable_income: int) -> int:
    """Get marginal income tax rate (percent) for the given taxable income.

    Uses the same bracket table as income tax calculation.
    """
    if taxable_income <= 0:
        return 0
    for upper, rate, _ in _INCOME_TAX_TABLE:
        if taxable_income <= upper:
            return rate
    return 45  # Over 40,000,000


def calc_furusato_deduction_limit(
    total_income: int,
    total_income_deductions: int,
    income_tax_rate_percent: int | None = None,
) -> int:
    """Estimate furusato nozei deduction limit.

    推定上限額の計算式（住民税所得割額の20%ベース）:
    上限 ≈ 住民税所得割額 × 20% ÷ (100% - 所得税率 × 1.021 - 10%) + 2,000

    住民税所得割額 = (総所得 - 所得控除) × 10%

    Note: この計算は推定値。調整控除等は考慮していない。
    """
    taxable_income_raw = max(0, total_income - total_income_deductions)
    # 課税所得を1,000円未満切捨て
    taxable_income = (taxable_income_raw // 1_000) * 1_000

    if taxable_income <= 0:
        return 0

    # 所得税率を自動計算（指定がなければ）
    if income_tax_rate_percent is None:
        income_tax_rate_percent = _get_marginal_tax_rate(taxable_income)

    # 住民税所得割額 = 課税所得 × 10%
    juuminzei_shotokuwari = taxable_income * 10 // 100

    if juuminzei_shotokuwari <= 0:
        return 0

    # 分母: 100% - (所得税率 × 1.021) - 10%(住民税基本分)
    # パーセント整数演算のため1000倍して計算
    denominator_permille = 1000 - income_tax_rate_percent * 1021 // 100 - 100

    if denominator_permille <= 0:
        # 所得税率が非常に高い場合の安全策
        return juuminzei_shotokuwari * 20 // 100 + 2_000

    # 上限 = 住民税所得割額 × 20% ÷ (分母/100%) + 2,000
    limit = juuminzei_shotokuwari * 200 // denominator_permille + 2_000

    return limit


# ============================================================
# MCP Tool Registration
# ============================================================


def register(mcp) -> None:
    """Register tax calculation tools with the MCP server."""

    @mcp.tool()
    def tax_calc_deductions(
        total_income: int,
        social_insurance: int = 0,
        life_insurance_premium: int = 0,
        earthquake_insurance_premium: int = 0,
        medical_expenses: int = 0,
        furusato_nozei: int = 0,
        housing_loan_balance: int = 0,
        spouse_income: int | None = None,
        ideco_contribution: int = 0,
    ) -> dict:
        """Calculate applicable deductions for income tax filing."""
        result = calc_deductions(
            total_income=total_income,
            social_insurance=social_insurance,
            life_insurance_premium=life_insurance_premium,
            earthquake_insurance_premium=earthquake_insurance_premium,
            medical_expenses=medical_expenses,
            furusato_nozei=furusato_nozei,
            housing_loan_balance=housing_loan_balance,
            spouse_income=spouse_income,
            ideco_contribution=ideco_contribution,
        )
        return result.model_dump()

    @mcp.tool()
    def tax_calc_income(
        fiscal_year: int,
        salary_income: int = 0,
        business_revenue: int = 0,
        business_expenses: int = 0,
        blue_return_deduction: int = 650_000,
        social_insurance: int = 0,
        life_insurance_premium: int = 0,
        earthquake_insurance_premium: int = 0,
        medical_expenses: int = 0,
        furusato_nozei: int = 0,
        housing_loan_balance: int = 0,
        housing_loan_year: int | None = None,
        spouse_income: int | None = None,
        ideco_contribution: int = 0,
        withheld_tax: int = 0,
        business_withheld_tax: int = 0,
        loss_carryforward_amount: int = 0,
        estimated_tax_payment: int = 0,
    ) -> dict:
        """Calculate income tax for the fiscal year."""
        input_data = IncomeTaxInput(
            fiscal_year=fiscal_year,
            salary_income=salary_income,
            business_revenue=business_revenue,
            business_expenses=business_expenses,
            blue_return_deduction=blue_return_deduction,
            social_insurance=social_insurance,
            life_insurance_premium=life_insurance_premium,
            earthquake_insurance_premium=earthquake_insurance_premium,
            medical_expenses=medical_expenses,
            furusato_nozei=furusato_nozei,
            housing_loan_balance=housing_loan_balance,
            housing_loan_year=housing_loan_year,
            spouse_income=spouse_income,
            ideco_contribution=ideco_contribution,
            withheld_tax=withheld_tax,
            business_withheld_tax=business_withheld_tax,
            loss_carryforward_amount=loss_carryforward_amount,
            estimated_tax_payment=estimated_tax_payment,
        )
        result = calc_income_tax(input_data)
        return result.model_dump()

    @mcp.tool()
    def tax_calc_depreciation(
        acquisition_cost: int,
        useful_life: int,
        business_use_ratio: int = 100,
        months: int = 12,
        method: str = "straight_line",
        book_value: int | None = None,
        declining_rate: int | None = None,
    ) -> dict:
        """Calculate depreciation for a fixed asset."""
        if method == "declining_balance":
            if book_value is None or declining_rate is None:
                return {"error": "book_value and declining_rate required for declining balance"}
            amount = calc_depreciation_declining_balance(
                book_value=book_value,
                declining_rate=declining_rate,
                business_use_ratio=business_use_ratio,
                months=months,
            )
        else:
            amount = calc_depreciation_straight_line(
                acquisition_cost=acquisition_cost,
                useful_life=useful_life,
                business_use_ratio=business_use_ratio,
                months=months,
            )
        return {
            "method": method,
            "depreciation_amount": amount,
            "acquisition_cost": acquisition_cost,
            "useful_life": useful_life,
            "business_use_ratio": business_use_ratio,
            "months": months,
        }

    @mcp.tool()
    def tax_calc_consumption(
        fiscal_year: int,
        method: str = "special_20pct",
        taxable_sales_10: int = 0,
        taxable_sales_8: int = 0,
        taxable_purchases_10: int = 0,
        taxable_purchases_8: int = 0,
        simplified_business_type: int | None = None,
    ) -> dict:
        """Calculate consumption tax for the fiscal year."""
        input_data = ConsumptionTaxInput(
            fiscal_year=fiscal_year,
            method=method,
            taxable_sales_10=taxable_sales_10,
            taxable_sales_8=taxable_sales_8,
            taxable_purchases_10=taxable_purchases_10,
            taxable_purchases_8=taxable_purchases_8,
            simplified_business_type=simplified_business_type,
        )
        result = calc_consumption_tax(input_data)
        return result.model_dump()

    @mcp.tool()
    def tax_calc_furusato_limit(
        total_income: int,
        total_income_deductions: int,
        income_tax_rate_percent: int | None = None,
    ) -> dict:
        """Estimate furusato nozei deduction limit."""
        limit = calc_furusato_deduction_limit(
            total_income=total_income,
            total_income_deductions=total_income_deductions,
            income_tax_rate_percent=income_tax_rate_percent,
        )
        return {"estimated_limit": limit}
