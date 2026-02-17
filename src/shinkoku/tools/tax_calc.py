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
    DonationRecordRecord,
    HousingLoanDetail,
    IncomeTaxInput,
    IncomeTaxResult,
    LifeInsurancePremiumInput,
    ConsumptionTaxInput,
    ConsumptionTaxResult,
    PensionDeductionInput,
    PensionDeductionResult,
    RetirementIncomeInput,
    RetirementIncomeResult,
    TaxSanityCheckItem,
    TaxSanityCheckResult,
)
from shinkoku.tax_constants import (
    BASIC_DEDUCTION_TABLE,
    DEPENDENT_ELDERLY,
    DEPENDENT_ELDERLY_COHABITING,
    DEPENDENT_GENERAL,
    DEPENDENT_AGE_SPECIFIC_MAX,
    DEPENDENT_AGE_SPECIFIC_MIN,
    DEPENDENT_INCOME_LIMIT,
    DONATION_INCOME_DEDUCTION_RATIO,
    DONATION_SELF_BURDEN,
    NPO_DONATION_CREDIT_CAP_RATIO,
    NPO_DONATION_CREDIT_RATE,
    NPO_DONATION_CREDIT_RATE_DENOM,
    PENSION_DEDUCTION_OVER_65,
    PENSION_DEDUCTION_OVER_65_MAX,
    PENSION_DEDUCTION_UNDER_65,
    PENSION_DEDUCTION_UNDER_65_MAX,
    PENSION_OTHER_INCOME_ADJUSTMENT_1,
    PENSION_OTHER_INCOME_ADJUSTMENT_2,
    PENSION_OTHER_INCOME_BRACKET_1,
    PENSION_OTHER_INCOME_BRACKET_2,
    POLITICAL_DONATION_CREDIT_CAP_RATIO,
    POLITICAL_DONATION_CREDIT_RATE,
    POLITICAL_DONATION_CREDIT_RATE_DENOM,
    DEPENDENT_SPECIFIC,
    DISABILITY_GENERAL,
    DISABILITY_SPECIAL,
    DISABILITY_SPECIAL_COHABITING,
    DIVIDEND_CREDIT_RATE_HIGH,
    DIVIDEND_CREDIT_RATE_LOW,
    DIVIDEND_CREDIT_THRESHOLD,
    EARTHQUAKE_INSURANCE_MAX,
    FURUSATO_INCOME_RATIO,
    FURUSATO_RESIDENTIAL_TAX_RATIO,
    FURUSATO_SELF_BURDEN,
    HOUSING_LOAN_DEFAULT_LIMIT,
    HOUSING_LOAN_GENERAL_R5_CONFIRMED,
    HOUSING_LOAN_LIMITS_R4_R5,
    HOUSING_LOAN_LIMITS_R6_R7,
    HOUSING_LOAN_LIMITS_R6_R7_CHILDCARE,
    HOUSING_LOAN_RATE,
    HOUSING_LOAN_RATE_DENOMINATOR,
    INCOME_TAX_TABLE,
    INCOME_TAX_TOP_DEDUCTION,
    INCOME_TAX_TOP_RATE,
    LOCAL_TAX_RATIO,
    LIFE_INSURANCE_COMBINED_MAX,
    LIFE_INSURANCE_NEW_MAX,
    LIFE_INSURANCE_OLD_MAX,
    LIFE_INSURANCE_TOTAL_MAX,
    NATIONAL_TAX_RATIO,
    MEDICAL_EXPENSE_INCOME_RATIO,
    MEDICAL_EXPENSE_MAX,
    MEDICAL_EXPENSE_THRESHOLD,
    OLD_LONG_TERM_MAX,
    ONE_TIME_INCOME_SPECIAL_DEDUCTION,
    PERSONAL_DEDUCTION_INCOME_LIMIT,
    RECONSTRUCTION_TAX_DENOMINATOR,
    RECONSTRUCTION_TAX_RATE,
    RETIREMENT_DEDUCTION_BASE_20,
    RETIREMENT_DEDUCTION_DISABILITY_ADD,
    RETIREMENT_DEDUCTION_MIN,
    RETIREMENT_DEDUCTION_PER_YEAR_OVER_20,
    RETIREMENT_DEDUCTION_PER_YEAR_UNDER_20,
    RETIREMENT_OFFICER_SHORT_SERVICE_YEARS,
    RETIREMENT_SHORT_SERVICE_HALF_LIMIT,
    SALARY_DEDUCTION_MAX,
    SALARY_DEDUCTION_MIN,
    SELF_MEDICATION_MAX,
    SELF_MEDICATION_THRESHOLD,
    SIMPLIFIED_DEEMED_RATIOS,
    SIMPLIFIED_DEFAULT_RATIO,
    SINGLE_PARENT_DEDUCTION,
    SPECIAL_20PCT_RATE,
    SPECIFIC_RELATIVE_SPECIAL_DEDUCTION_TABLE,
    SPECIFIC_RELATIVE_SPECIAL_INCOME_MAX,
    SPOUSE_DEDUCTION_TABLE,
    SPOUSE_DEDUCTION_TABLE_9M,
    SPOUSE_DEDUCTION_TABLE_10M,
    SPOUSE_TAXPAYER_BRACKET_1,
    SPOUSE_TAXPAYER_BRACKET_2,
    SPOUSE_TAXPAYER_INCOME_LIMIT,
    TAX_AMOUNT_ROUNDING,
    TAXABLE_INCOME_ROUNDING,
    WIDOW_DEDUCTION,
    WORKING_STUDENT_DEDUCTION,
    WORKING_STUDENT_INCOME_LIMIT,
)


def calc_basic_deduction(total_income: int) -> int:
    """Calculate basic deduction based on total income (Reiwa 7)."""
    for upper, deduction in BASIC_DEDUCTION_TABLE:
        if total_income <= upper:
            return deduction
    return 0


# ============================================================
# Salary Income Deduction (Reiwa 7)
# ============================================================


def calc_salary_deduction(salary_income: int) -> int:
    """Calculate salary income deduction (Reiwa 7 revision).

    令和7年改正: 最低保障額65万、≤190万で一律65万に変更。
    Returns the deduction amount (not the net salary income).
    """
    if salary_income <= 0:
        return 0
    # 令和7年改正: ≤190万は一律65万（旧: ≤162.5万で55万、162.5万超〜180万は40%-10万）
    if salary_income <= 1_900_000:
        return SALARY_DEDUCTION_MIN
    if salary_income <= 3_600_000:
        return int(salary_income * 30 // 100) + 80_000
    if salary_income <= 6_600_000:
        return int(salary_income * 20 // 100) + 440_000
    if salary_income <= 8_500_000:
        return int(salary_income * 10 // 100) + 1_100_000
    return SALARY_DEDUCTION_MAX


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
    return LIFE_INSURANCE_NEW_MAX


# ============================================================
# Life Insurance Deduction - Old System (Phase 3)
# ============================================================


def calc_life_insurance_deduction_old(premium: int) -> int:
    """旧制度の生命保険料控除（1区分あたり、上限50,000円）。"""
    if premium <= 0:
        return 0
    if premium <= 25_000:
        return premium
    if premium <= 50_000:
        return premium // 2 + 12_500
    if premium <= 100_000:
        return premium // 4 + 25_000
    return LIFE_INSURANCE_OLD_MAX


def calc_life_insurance_category(new_premium: int, old_premium: int) -> int:
    """新旧合算で1区分の控除額を計算（上限40,000円）。

    max(新のみ, 旧のみ, min(新+旧合算, 40,000))
    """
    new_only = calc_life_insurance_deduction(new_premium) if new_premium > 0 else 0
    old_only = calc_life_insurance_deduction_old(old_premium) if old_premium > 0 else 0

    if new_premium > 0 and old_premium > 0:
        combined = min(new_only + old_only, LIFE_INSURANCE_COMBINED_MAX)
        return max(new_only, old_only, combined)
    if new_premium > 0:
        return new_only
    return old_only


def calc_life_insurance_total(
    general_new: int = 0,
    general_old: int = 0,
    medical_care: int = 0,
    annuity_new: int = 0,
    annuity_old: int = 0,
) -> int:
    """生命保険料控除の3区分合計（上限120,000円）。

    一般: 新旧合算
    介護医療: 新制度のみ（上限40,000）
    個人年金: 新旧合算
    合計: min(各区分合計, 120,000)
    """
    general = calc_life_insurance_category(general_new, general_old)
    medical = calc_life_insurance_deduction(medical_care)  # 新制度のみ
    annuity = calc_life_insurance_category(annuity_new, annuity_old)
    return min(general + medical + annuity, LIFE_INSURANCE_TOTAL_MAX)


# ============================================================
# Earthquake Insurance Deduction - Old Long-term (Phase 4)
# ============================================================


def calc_earthquake_insurance_deduction(
    earthquake_premium: int = 0,
    old_long_term_premium: int = 0,
) -> int:
    """地震保険料控除（旧長期損害保険対応）。

    地震保険: min(premium, 50,000)
    旧長期: ≤5,000→全額, ≤15,000→premium//2+2,500, >15,000→15,000
    合算: min(地震 + 旧長期, 50,000)
    """
    eq = min(earthquake_premium, EARTHQUAKE_INSURANCE_MAX) if earthquake_premium > 0 else 0

    old = 0
    if old_long_term_premium > 0:
        if old_long_term_premium <= 5_000:
            old = old_long_term_premium
        elif old_long_term_premium <= 15_000:
            old = old_long_term_premium // 2 + 2_500
        else:
            old = OLD_LONG_TERM_MAX

    return min(eq + old, EARTHQUAKE_INSURANCE_MAX)


# ============================================================
# Personal Deductions (Phase 5): widow, single_parent, disability, working student
# ============================================================


def calc_widow_deduction(status: str, total_income: int) -> int:
    """寡婦/ひとり親控除。

    ひとり親: 350,000（所得500万以下）
    寡婦: 270,000（所得500万以下）
    """
    if total_income > PERSONAL_DEDUCTION_INCOME_LIMIT:
        return 0
    if status == "single_parent":
        return SINGLE_PARENT_DEDUCTION
    if status == "widow":
        return WIDOW_DEDUCTION
    return 0


def calc_disability_deduction_self(status: str) -> int:
    """本人の障害者控除。

    一般: 270,000
    特別: 400,000
    """
    if status == "special":
        return DISABILITY_SPECIAL
    if status == "general":
        return DISABILITY_GENERAL
    return 0


def calc_working_student_deduction(flag: bool, total_income: int) -> int:
    """勤労学生控除: 270,000（合計所得75万以下）。"""
    if flag and total_income <= WORKING_STUDENT_INCOME_LIMIT:
        return WORKING_STUDENT_DEDUCTION
    return 0


# ============================================================
# Self-Medication Tax System (Phase 8)
# ============================================================


def calc_self_medication_deduction(expenses: int) -> int:
    """セルフメディケーション税制の控除額。

    控除額 = OTC購入額 - 12,000（上限 88,000）
    医療費控除とは選択適用（併用不可）。
    """
    if expenses <= SELF_MEDICATION_THRESHOLD:
        return 0
    return min(expenses - SELF_MEDICATION_THRESHOLD, SELF_MEDICATION_MAX)


# ============================================================
# Dividend Tax Credit (Phase 10: 配当控除)
# ============================================================


def calc_dividend_tax_credit(dividend_income: int, taxable_income: int) -> int:
    """配当控除（税額控除）。

    課税所得1,000万以下: 配当の10%
    課税所得1,000万超: 超過部分は5%
    """
    if dividend_income <= 0:
        return 0
    if taxable_income <= DIVIDEND_CREDIT_THRESHOLD:
        return dividend_income * DIVIDEND_CREDIT_RATE_LOW // 100
    # 1,000万超の場合: 1,000万以下部分=10%, 超過部分=5%
    under_10m = max(0, DIVIDEND_CREDIT_THRESHOLD - (taxable_income - dividend_income))
    if under_10m >= dividend_income:
        return dividend_income * DIVIDEND_CREDIT_RATE_LOW // 100
    over_10m = dividend_income - under_10m
    return under_10m * DIVIDEND_CREDIT_RATE_LOW // 100 + over_10m * DIVIDEND_CREDIT_RATE_HIGH // 100


# ============================================================
# Spouse Deduction
# ============================================================


def calc_spouse_deduction(taxpayer_income: int, spouse_income: int | None) -> int:
    """Calculate spouse deduction / special spouse deduction."""
    if spouse_income is None:
        return 0
    if taxpayer_income > SPOUSE_TAXPAYER_INCOME_LIMIT:
        return 0

    # Select the appropriate table based on taxpayer income
    if taxpayer_income <= SPOUSE_TAXPAYER_BRACKET_1:
        table = SPOUSE_DEDUCTION_TABLE
    elif taxpayer_income <= SPOUSE_TAXPAYER_BRACKET_2:
        table = SPOUSE_DEDUCTION_TABLE_9M
    else:  # <= 10_000_000
        table = SPOUSE_DEDUCTION_TABLE_10M

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
    """Calculate deductions for dependents (扶養控除 + 特定親族特別控除 + 障害者控除).

    扶養控除（配偶者以外の親族で所得58万以下）:
    - 一般扶養: 38万円（16歳以上）
    - 特定扶養: 63万円（19歳以上23歳未満）
    - 老人扶養（同居）: 58万円（70歳以上、同居）
    - 老人扶養（別居）: 48万円（70歳以上、別居）
    - 16歳未満: 扶養控除なし（児童手当対象）

    特定親族特別控除（令和7年新設、19〜22歳で所得58万超〜123万以下）:
    - 所得金額に応じて63万〜3万の段階的控除

    障害者控除:
    - 一般障害者: 27万円
    - 特別障害者: 40万円
    - 同居特別障害者: 75万円
    """
    items: list[DeductionItem] = []
    fiscal_year_end = f"{fiscal_year}-12-31"

    for dep in dependents:
        # 他の納税者の扶養親族 → 二重控除防止のため除外
        if dep.other_taxpayer_dependent:
            continue

        # 配偶者は配偶者控除で処理するため除外
        if dep.relationship == "配偶者":
            continue

        age = _calc_age(dep.birth_date, fiscal_year_end)
        is_specific_age = DEPENDENT_AGE_SPECIFIC_MIN <= age < DEPENDENT_AGE_SPECIFIC_MAX

        # 所得要件: 19〜22歳は123万まで許容（特定親族特別控除）、それ以外は58万
        if is_specific_age:
            if dep.income > SPECIFIC_RELATIVE_SPECIAL_INCOME_MAX:
                continue
        else:
            if dep.income > DEPENDENT_INCOME_LIMIT:
                continue

        # 扶養控除（16歳以上のみ）
        if age >= 70:
            # 老人扶養親族
            if dep.cohabiting:
                deduction = DEPENDENT_ELDERLY_COHABITING  # 同居老親等
                detail = f"{dep.name}（老人扶養・同居）"
            else:
                deduction = DEPENDENT_ELDERLY  # 別居
                detail = f"{dep.name}（老人扶養・別居）"
            items.append(
                DeductionItem(
                    type="dependent",
                    name="扶養控除",
                    amount=deduction,
                    details=detail,
                )
            )
        elif is_specific_age:
            if dep.income <= DEPENDENT_INCOME_LIMIT:
                # 所得58万以下: 通常の特定扶養控除
                items.append(
                    DeductionItem(
                        type="dependent",
                        name="扶養控除",
                        amount=DEPENDENT_SPECIFIC,
                        details=f"{dep.name}（特定扶養）",
                    )
                )
            else:
                # 所得58万超〜123万: 特定親族特別控除（段階的逓減）
                special_amount = 0
                for threshold, amount in SPECIFIC_RELATIVE_SPECIAL_DEDUCTION_TABLE:
                    if dep.income <= threshold:
                        special_amount = amount
                        break
                if special_amount > 0:
                    items.append(
                        DeductionItem(
                            type="specific_relative_special",
                            name="特定親族特別控除",
                            amount=special_amount,
                            details=f"{dep.name}（所得{dep.income}円）",
                        )
                    )
        elif age >= 16:
            # 一般扶養親族
            items.append(
                DeductionItem(
                    type="dependent",
                    name="扶養控除",
                    amount=DEPENDENT_GENERAL,
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
                    amount=DISABILITY_SPECIAL_COHABITING,
                    details=f"{dep.name}（同居特別障害者）",
                )
            )
        elif dep.disability == "special":
            items.append(
                DeductionItem(
                    type="disability",
                    name="障害者控除",
                    amount=DISABILITY_SPECIAL,
                    details=f"{dep.name}（特別障害者）",
                )
            )
        elif dep.disability == "general":
            items.append(
                DeductionItem(
                    type="disability",
                    name="障害者控除",
                    amount=DISABILITY_GENERAL,
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
    if donation <= FURUSATO_SELF_BURDEN:
        return 0
    capped = donation
    if total_income is not None:
        capped = min(donation, total_income * FURUSATO_INCOME_RATIO // 100)
    if capped <= FURUSATO_SELF_BURDEN:
        return 0
    return capped - FURUSATO_SELF_BURDEN


# ============================================================
# Housing Loan Tax Credit
# ============================================================


def calc_housing_loan_credit(
    balance: int,
    detail: HousingLoanDetail | None = None,
) -> int:
    """Calculate housing loan tax credit.

    控除率: 0.7%（令和4年以降入居）
    控除期間: 新築13年、中古10年（ここでは年単位の判定は呼び出し側で行う）
    年末残高上限: 住宅区分・入居年・世帯区分別に異なる

    入居年による上限テーブル選択:
    - R4-R5（〜2023年）: 従来の上限額
    - R6-R7（2024年〜）一般世帯: 引下げ後の上限額
    - R6-R7（2024年〜）子育て世帯: 従来水準維持

    detail が None の場合は従来のシンプル計算（balance * 0.7%）を行う。
    """
    if balance <= 0:
        return 0

    if detail is not None:
        move_in_year = int(detail.move_in_date[:4])
        key = (detail.housing_category, detail.is_new_construction)

        # 入居年に応じたテーブル選択
        if move_in_year <= 2023:
            limits = HOUSING_LOAN_LIMITS_R4_R5
        elif detail.is_childcare_household:
            limits = HOUSING_LOAN_LIMITS_R6_R7_CHILDCARE
        else:
            limits = HOUSING_LOAN_LIMITS_R6_R7

        limit = limits.get(key, HOUSING_LOAN_DEFAULT_LIMIT)

        # 一般住宅新築 R6-R7: R5確認済みなら特例上限（2,000万/控除期間10年）
        if (
            limit == 0
            and detail.housing_category == "general"
            and detail.is_new_construction
            and detail.has_pre_r6_building_permit
        ):
            limit = HOUSING_LOAN_GENERAL_R5_CONFIRMED

        capped = min(detail.year_end_balance, limit)
        return int(capped * HOUSING_LOAN_RATE // HOUSING_LOAN_RATE_DENOMINATOR)

    return int(balance * HOUSING_LOAN_RATE // HOUSING_LOAN_RATE_DENOMINATOR)


# ============================================================
# Aggregated Deductions Calculator
# ============================================================


def calc_deductions(
    total_income: int,
    social_insurance: int = 0,
    life_insurance_premium: int = 0,
    life_insurance_detail: LifeInsurancePremiumInput | None = None,
    earthquake_insurance_premium: int = 0,
    old_long_term_insurance_premium: int = 0,
    medical_expenses: int = 0,
    self_medication_expenses: int = 0,
    self_medication_eligible: bool = False,
    furusato_nozei: int = 0,
    housing_loan_balance: int = 0,
    spouse_income: int | None = None,
    ideco_contribution: int = 0,
    small_business_mutual_aid: int = 0,
    dependents: list[DependentInfo] | None = None,
    fiscal_year: int = 2025,
    housing_loan_detail: HousingLoanDetail | None = None,
    widow_status: str = "none",
    disability_status: str = "none",
    working_student: bool = False,
    dividend_income_comprehensive: int = 0,
    taxable_income_for_dividend_credit: int = 0,
    donations: list[DonationRecordRecord] | None = None,
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

    # 3. Life insurance（3区分対応: Phase 3）
    if life_insurance_detail is not None:
        li_deduction = calc_life_insurance_total(
            general_new=life_insurance_detail.general_new,
            general_old=life_insurance_detail.general_old,
            medical_care=life_insurance_detail.medical_care,
            annuity_new=life_insurance_detail.annuity_new,
            annuity_old=life_insurance_detail.annuity_old,
        )
        if li_deduction > 0:
            income_deductions.append(
                DeductionItem(
                    type="life_insurance",
                    name="生命保険料控除",
                    amount=li_deduction,
                    details="3区分詳細",
                )
            )
    elif life_insurance_premium > 0:
        li_deduction = calc_life_insurance_deduction(life_insurance_premium)
        if li_deduction > 0:
            income_deductions.append(
                DeductionItem(
                    type="life_insurance",
                    name="生命保険料控除",
                    amount=li_deduction,
                )
            )

    # 4. Earthquake insurance（旧長期損害保険対応: Phase 4）
    if earthquake_insurance_premium > 0 or old_long_term_insurance_premium > 0:
        eq_deduction = calc_earthquake_insurance_deduction(
            earthquake_premium=earthquake_insurance_premium,
            old_long_term_premium=old_long_term_insurance_premium,
        )
        if eq_deduction > 0:
            income_deductions.append(
                DeductionItem(
                    type="earthquake_insurance",
                    name="地震保険料控除",
                    amount=eq_deduction,
                )
            )

    # 5. 小規模企業共済等掛金控除（Phase 7: サブタイプ対応）
    mutual_aid_total = ideco_contribution + small_business_mutual_aid
    if mutual_aid_total > 0:
        # details: サブタイプの内訳を示す
        if ideco_contribution > 0 and small_business_mutual_aid == 0:
            mutual_aid_details = "iDeCo"
        elif ideco_contribution == 0 and small_business_mutual_aid > 0:
            mutual_aid_details = "小規模企業共済"
        elif ideco_contribution > 0 and small_business_mutual_aid > 0:
            mutual_aid_details = f"iDeCo: {ideco_contribution}, 共済: {small_business_mutual_aid}"
        else:
            mutual_aid_details = None
        income_deductions.append(
            DeductionItem(
                type="small_business_mutual_aid",
                name="小規模企業共済等掛金控除",
                amount=mutual_aid_total,
                details=mutual_aid_details,
            )
        )

    # 6. Medical expenses / Self-medication（選択適用: Phase 8）
    if self_medication_eligible and self_medication_expenses > 0:
        # セルフメディケーション税制（医療費控除と併用不可）
        selfmed = calc_self_medication_deduction(self_medication_expenses)
        # 通常の医療費控除と比較して有利な方を適用
        medical_threshold = min(
            MEDICAL_EXPENSE_THRESHOLD, total_income * MEDICAL_EXPENSE_INCOME_RATIO // 100
        )
        med_normal = (
            min(medical_expenses - medical_threshold, MEDICAL_EXPENSE_MAX)
            if medical_expenses > medical_threshold
            else 0
        )
        if selfmed > med_normal and selfmed > 0:
            income_deductions.append(
                DeductionItem(
                    type="self_medication",
                    name="セルフメディケーション税制",
                    amount=selfmed,
                )
            )
        elif med_normal > 0:
            income_deductions.append(
                DeductionItem(type="medical", name="医療費控除", amount=med_normal)
            )
    else:
        medical_threshold = min(
            MEDICAL_EXPENSE_THRESHOLD, total_income * MEDICAL_EXPENSE_INCOME_RATIO // 100
        )
        if medical_expenses > medical_threshold:
            med_deduction = min(medical_expenses - medical_threshold, MEDICAL_EXPENSE_MAX)
            income_deductions.append(
                DeductionItem(type="medical", name="医療費控除", amount=med_deduction)
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

    # 7b. その他の寄附金控除（政治活動/認定NPO/公益法人等）
    if donations:
        # 所得控除対象（所得税法第78条）: 全寄附金 - 2,000円（総所得金額×40%上限）
        donation_total = sum(d.amount for d in donations)
        if donation_total > DONATION_SELF_BURDEN:
            income_limit = total_income * DONATION_INCOME_DEDUCTION_RATIO // 100
            donation_deduction = max(0, min(donation_total, income_limit) - DONATION_SELF_BURDEN)
            if donation_deduction > 0:
                income_deductions.append(
                    DeductionItem(
                        type="donation",
                        name="寄附金控除（その他）",
                        amount=donation_deduction,
                        details=f"寄附金合計: {donation_total}",
                    )
                )

        # 税額控除対象: 政治活動寄附金（租税特別措置法第41条の18）
        political_total = sum(d.amount for d in donations if d.donation_type == "political")
        if political_total > DONATION_SELF_BURDEN:
            political_credit = (
                (political_total - DONATION_SELF_BURDEN)
                * POLITICAL_DONATION_CREDIT_RATE
                // POLITICAL_DONATION_CREDIT_RATE_DENOM
            )
            if political_credit > 0:
                tax_credits.append(
                    DeductionItem(
                        type="political_donation",
                        name="政治活動寄附金控除",
                        amount=political_credit,
                        details=f"所得税額の{POLITICAL_DONATION_CREDIT_CAP_RATIO}%上限あり",
                    )
                )

        # 税額控除対象: 認定NPO/公益法人等（租税特別措置法第41条の18の2/3）
        npo_total = sum(
            d.amount for d in donations if d.donation_type in ("npo", "public_interest")
        )
        if npo_total > DONATION_SELF_BURDEN:
            npo_credit = (
                (npo_total - DONATION_SELF_BURDEN)
                * NPO_DONATION_CREDIT_RATE
                // NPO_DONATION_CREDIT_RATE_DENOM
            )
            if npo_credit > 0:
                tax_credits.append(
                    DeductionItem(
                        type="npo_donation",
                        name="認定NPO等寄附金控除",
                        amount=npo_credit,
                        details=f"所得税額の{NPO_DONATION_CREDIT_CAP_RATIO}%上限あり",
                    )
                )

    # 8. Spouse deduction
    if spouse_income is not None:
        spouse = calc_spouse_deduction(total_income, spouse_income)
        if spouse > 0:
            income_deductions.append(DeductionItem(type="spouse", name="配偶者控除", amount=spouse))

    # 9. Dependent deductions (扶養控除 + 障害者控除)
    if dependents:
        dep_items = calc_dependents_deduction(
            dependents=dependents,
            taxpayer_income=total_income,
            fiscal_year=fiscal_year,
        )
        income_deductions.extend(dep_items)

    # 10. 寡婦/ひとり親控除（Phase 5）
    if widow_status != "none":
        widow = calc_widow_deduction(widow_status, total_income)
        if widow > 0:
            name = "ひとり親控除" if widow_status == "single_parent" else "寡婦控除"
            income_deductions.append(DeductionItem(type="widow", name=name, amount=widow))

    # 11. 本人の障害者控除（Phase 5）
    if disability_status != "none":
        disability = calc_disability_deduction_self(disability_status)
        if disability > 0:
            income_deductions.append(
                DeductionItem(type="disability_self", name="障害者控除（本人）", amount=disability)
            )

    # 12. 勤労学生控除（Phase 5）
    if working_student:
        ws = calc_working_student_deduction(True, total_income)
        if ws > 0:
            income_deductions.append(
                DeductionItem(type="working_student", name="勤労学生控除", amount=ws)
            )

    # Tax credits
    # Housing loan credit
    hl_balance = housing_loan_balance
    if housing_loan_detail is not None:
        hl_balance = housing_loan_detail.year_end_balance
    if hl_balance > 0:
        hl_credit = calc_housing_loan_credit(hl_balance, detail=housing_loan_detail)
        if hl_credit > 0:
            tax_credits.append(
                DeductionItem(type="housing_loan", name="住宅ローン控除", amount=hl_credit)
            )

    # 配当控除（Phase 10）
    if dividend_income_comprehensive > 0 and taxable_income_for_dividend_credit > 0:
        div_credit = calc_dividend_tax_credit(
            dividend_income_comprehensive, taxable_income_for_dividend_credit
        )
        if div_credit > 0:
            tax_credits.append(DeductionItem(type="dividend", name="配当控除", amount=div_credit))

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


def _calc_income_tax_from_table(taxable_income: int) -> int:
    """Apply the income tax quick calculation table. All int arithmetic."""
    if taxable_income <= 0:
        return 0
    for upper, rate, deduction in INCOME_TAX_TABLE:
        if taxable_income <= upper:
            return taxable_income * rate // 100 - deduction
    # Over 40,000,000
    return taxable_income * INCOME_TAX_TOP_RATE // 100 - INCOME_TAX_TOP_DEDUCTION


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
    # 青色申告特別控除は事業所得（収入−経費）を上限とする（租特法25条の2）
    warnings: list[str] = []
    business_profit_before_deduction = input_data.business_revenue - input_data.business_expenses
    effective_blue_deduction = min(
        input_data.blue_return_deduction,
        max(0, business_profit_before_deduction),
    )
    if effective_blue_deduction < input_data.blue_return_deduction:
        warnings.append(
            f"青色申告特別控除を自動調整しました: "
            f"{input_data.blue_return_deduction:,}円 → {effective_blue_deduction:,}円"
            f"（事業利益 {business_profit_before_deduction:,}円が上限）"
        )
    business_income = business_profit_before_deduction - effective_blue_deduction

    # Step 3: Total income（損益通算後 + その他所得）
    total_income_raw = salary_income_after + business_income

    # Phase 10: その他所得の加算
    # 雑所得 = 収入 - 経費（既に所得金額）
    misc_income = input_data.misc_income
    # 配当所得（総合課税）= そのまま加算
    dividend_comprehensive = input_data.dividend_income_comprehensive
    # 一時所得 = max(0, (収入 - 経費 - 特別控除50万)) × 1/2
    one_time_income = max(0, input_data.one_time_income - ONE_TIME_INCOME_SPECIAL_DEDUCTION) // 2

    total_income_raw += misc_income + dividend_comprehensive + one_time_income

    # Step 3.5: 繰越損失の適用（青色申告の場合、3年繰越）
    loss_applied = 0
    if input_data.loss_carryforward_amount > 0 and total_income_raw > 0:
        loss_applied = min(input_data.loss_carryforward_amount, total_income_raw)
        total_income_raw -= loss_applied

    total_income = max(0, total_income_raw)

    # 小規模企業共済等掛金控除（Phase 7）
    mutual_aid_total = input_data.ideco_contribution
    if input_data.small_business_mutual_aid is not None:
        mutual_aid_total = input_data.small_business_mutual_aid.total

    # Step 4: Income deductions
    deductions = calc_deductions(
        total_income=total_income,
        social_insurance=input_data.social_insurance,
        life_insurance_premium=input_data.life_insurance_premium,
        life_insurance_detail=input_data.life_insurance_detail,
        earthquake_insurance_premium=input_data.earthquake_insurance_premium,
        old_long_term_insurance_premium=input_data.old_long_term_insurance_premium,
        medical_expenses=input_data.medical_expenses,
        self_medication_expenses=input_data.self_medication_expenses,
        self_medication_eligible=input_data.self_medication_eligible,
        furusato_nozei=input_data.furusato_nozei,
        housing_loan_balance=input_data.housing_loan_balance,
        spouse_income=input_data.spouse_income,
        ideco_contribution=input_data.ideco_contribution,
        small_business_mutual_aid=(
            mutual_aid_total - input_data.ideco_contribution
            if input_data.small_business_mutual_aid is not None
            else 0
        ),
        dependents=input_data.dependents or None,
        fiscal_year=input_data.fiscal_year,
        housing_loan_detail=input_data.housing_loan_detail,
        widow_status=input_data.widow_status,
        disability_status=input_data.disability_status,
        working_student=input_data.working_student,
    )

    total_income_deductions = deductions.total_income_deductions

    # Step 5: Taxable income (truncate to 1,000 yen, min 0)
    taxable_income_raw = max(0, total_income - total_income_deductions)
    taxable_income = (taxable_income_raw // TAXABLE_INCOME_ROUNDING) * TAXABLE_INCOME_ROUNDING

    # Step 6: Tax from table
    income_tax_base = _calc_income_tax_from_table(taxable_income)

    # Step 6.5: 配当控除の計算（Phase 10）
    if dividend_comprehensive > 0:
        div_credit = calc_dividend_tax_credit(dividend_comprehensive, taxable_income)
        if div_credit > 0:
            deductions.tax_credits.append(
                DeductionItem(type="dividend", name="配当控除", amount=div_credit)
            )
            deductions.total_tax_credits += div_credit

    # Step 7: Tax credits
    total_tax_credits = deductions.total_tax_credits
    income_tax_after_credits = max(0, income_tax_base - total_tax_credits)

    # Step 8: Reconstruction tax = 2.1% (truncate to 1 yen)
    reconstruction_tax = int(
        income_tax_after_credits * RECONSTRUCTION_TAX_RATE // RECONSTRUCTION_TAX_DENOMINATOR
    )

    # Step 9: 所得税及び復興特別所得税の額（㊺）— 端数処理なし
    total_tax = income_tax_after_credits + reconstruction_tax

    # Step 10: Difference（給与源泉+事業源泉+その他源泉+予定納税を差し引く）
    total_withheld = (
        input_data.withheld_tax
        + input_data.business_withheld_tax
        + input_data.other_income_withheld_tax
        + input_data.estimated_tax_payment
    )
    tax_due_raw = total_tax - total_withheld

    # 国税通則法 第119条: 納付すべき確定金額は100円未満切捨て
    # 国税通則法 第120条: 還付金は1円単位（1円未満切捨て）
    if tax_due_raw > 0:
        tax_due = (tax_due_raw // TAX_AMOUNT_ROUNDING) * TAX_AMOUNT_ROUNDING
    else:
        tax_due = tax_due_raw

    # 個別の税額控除額を抽出
    _dividend_credit = 0
    _housing_loan_credit = 0
    for tc in deductions.tax_credits:
        if tc.type == "dividend":
            _dividend_credit += tc.amount
        elif tc.type == "housing_loan":
            _housing_loan_credit += tc.amount

    return IncomeTaxResult(
        fiscal_year=input_data.fiscal_year,
        salary_income_after_deduction=salary_income_after,
        business_income=business_income,
        total_income=total_income,
        effective_blue_return_deduction=effective_blue_deduction,
        total_income_deductions=total_income_deductions,
        taxable_income=taxable_income,
        income_tax_base=income_tax_base,
        dividend_credit=_dividend_credit,
        housing_loan_credit=_housing_loan_credit,
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
        warnings=warnings,
    )


# ============================================================
# Consumption Tax Calculation (Task 16)
# ============================================================


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
        tax_due_raw = total_tax_on_sales * SPECIAL_20PCT_RATE // 100
        tax_on_purchases = total_tax_on_sales - tax_due_raw  # deemed 80% credit

    elif input_data.method == "simplified":
        btype = input_data.simplified_business_type or 5  # default: service
        ratio = SIMPLIFIED_DEEMED_RATIOS.get(btype, SIMPLIFIED_DEFAULT_RATIO)
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
    national_tax = max(0, tax_due_raw * NATIONAL_TAX_RATIO // 100)
    national_tax = (national_tax // TAX_AMOUNT_ROUNDING) * TAX_AMOUNT_ROUNDING

    # Local tax = national * 22/78, truncated to 100 yen
    local_tax = national_tax * LOCAL_TAX_RATIO // NATIONAL_TAX_RATIO
    local_tax = (local_tax // TAX_AMOUNT_ROUNDING) * TAX_AMOUNT_ROUNDING

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
    for upper, rate, _ in INCOME_TAX_TABLE:
        if taxable_income <= upper:
            return rate
    return INCOME_TAX_TOP_RATE  # Over 40,000,000


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
    taxable_income = (taxable_income_raw // TAXABLE_INCOME_ROUNDING) * TAXABLE_INCOME_ROUNDING

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
        return juuminzei_shotokuwari * FURUSATO_RESIDENTIAL_TAX_RATIO // 100 + FURUSATO_SELF_BURDEN

    # 上限 = 住民税所得割額 × 20% ÷ (分母/100%) + 2,000
    limit = juuminzei_shotokuwari * 200 // denominator_permille + FURUSATO_SELF_BURDEN

    return limit


# ============================================================
# Pension Deduction (公的年金等控除)
# ============================================================


def calc_pension_deduction(input_data: PensionDeductionInput) -> PensionDeductionResult:
    """公的年金等控除額を計算する（所得税法第35条、令和7年改正）。"""
    pension = input_data.pension_income
    if pension <= 0:
        return PensionDeductionResult(
            pension_income=0,
            deduction_amount=0,
            taxable_pension_income=0,
            is_over_65=input_data.is_over_65,
        )

    # テーブル選択
    table = PENSION_DEDUCTION_OVER_65 if input_data.is_over_65 else PENSION_DEDUCTION_UNDER_65
    max_deduction = (
        PENSION_DEDUCTION_OVER_65_MAX if input_data.is_over_65 else PENSION_DEDUCTION_UNDER_65_MAX
    )

    # 速算表から控除額を計算
    deduction = max_deduction  # デフォルト: 上限（1000万超）
    for upper_limit, rate, fixed in table:
        if pension <= upper_limit:
            if rate == 100:
                deduction = pension  # 全額控除
            elif rate == 0:
                deduction = fixed  # 固定額
            else:
                deduction = pension * rate // 100 + fixed
            break

    # 所得金額調整（公的年金等以外の所得が1,000万超）
    other_income_adj = 0
    if input_data.other_income > PENSION_OTHER_INCOME_BRACKET_2:
        other_income_adj = PENSION_OTHER_INCOME_ADJUSTMENT_2
    elif input_data.other_income > PENSION_OTHER_INCOME_BRACKET_1:
        other_income_adj = PENSION_OTHER_INCOME_ADJUSTMENT_1

    deduction = max(0, deduction - other_income_adj)
    taxable = max(0, pension - deduction)

    return PensionDeductionResult(
        pension_income=pension,
        deduction_amount=deduction,
        taxable_pension_income=taxable,
        is_over_65=input_data.is_over_65,
        other_income_adjustment=other_income_adj,
    )


# ============================================================
# Retirement Income (退職所得)
# ============================================================


def calc_retirement_income(input_data: RetirementIncomeInput) -> RetirementIncomeResult:
    """退職所得を計算する（所得税法第30条）。"""
    years = input_data.years_of_service
    pay = input_data.severance_pay

    # 退職所得控除額の計算
    if years <= 20:
        deduction = max(
            RETIREMENT_DEDUCTION_PER_YEAR_UNDER_20 * years,
            RETIREMENT_DEDUCTION_MIN,
        )
    else:
        deduction = RETIREMENT_DEDUCTION_BASE_20 + RETIREMENT_DEDUCTION_PER_YEAR_OVER_20 * (
            years - 20
        )

    # 障害退職の加算
    if input_data.is_disability_retirement:
        deduction += RETIREMENT_DEDUCTION_DISABILITY_ADD

    # 退職所得の計算
    excess = max(0, pay - deduction)
    half_applied = True

    if input_data.is_officer and years <= RETIREMENT_OFFICER_SHORT_SERVICE_YEARS:
        # 役員等の短期退職: 1/2適用なし
        taxable = excess
        half_applied = False
    elif not input_data.is_officer and years <= RETIREMENT_OFFICER_SHORT_SERVICE_YEARS:
        # 一般の短期退職（令和4年改正）: 300万以下は1/2、300万超はそのまま
        if excess <= RETIREMENT_SHORT_SERVICE_HALF_LIMIT:
            taxable = excess // 2
        else:
            taxable = RETIREMENT_SHORT_SERVICE_HALF_LIMIT // 2 + (
                excess - RETIREMENT_SHORT_SERVICE_HALF_LIMIT
            )
            half_applied = False  # 部分的な1/2適用
    else:
        # 通常: 1/2適用
        taxable = excess // 2

    return RetirementIncomeResult(
        severance_pay=pay,
        retirement_income_deduction=deduction,
        taxable_retirement_income=taxable,
        years_of_service=years,
        is_officer=input_data.is_officer,
        half_taxation_applied=half_applied,
    )


# ============================================================
# Sanity Check (申告前サニティチェック)
# ============================================================


def sanity_check_income_tax(
    input_data: IncomeTaxInput,
    result: IncomeTaxResult,
) -> TaxSanityCheckResult:
    """所得税計算結果のサニティチェック。

    入力と出力の整合性を検証し、明らかな異常を検出する。
    """
    items: list[TaxSanityCheckItem] = []

    business_profit = input_data.business_revenue - input_data.business_expenses

    # 1. BLUE_DEDUCTION_ON_LOSS — 赤字なのに控除適用（Part A 修正後は防御的チェック）
    if business_profit < 0 and result.effective_blue_return_deduction > 0:
        items.append(
            TaxSanityCheckItem(
                severity="error",
                code="BLUE_DEDUCTION_ON_LOSS",
                message=f"事業が赤字（{business_profit:,}円）にもかかわらず"
                f"青色申告特別控除{result.effective_blue_return_deduction:,}円が適用されています",
            )
        )

    # 2. BLUE_DEDUCTION_EXCEEDS_PROFIT — 控除が利益超過
    if business_profit > 0 and result.effective_blue_return_deduction > business_profit:
        items.append(
            TaxSanityCheckItem(
                severity="error",
                code="BLUE_DEDUCTION_EXCEEDS_PROFIT",
                message=f"青色申告特別控除（{result.effective_blue_return_deduction:,}円）が"
                f"事業利益（{business_profit:,}円）を超過しています",
            )
        )

    # 3. LARGE_BUSINESS_LOSS — 事業損失が1,000万円超
    if result.business_income < -10_000_000:
        items.append(
            TaxSanityCheckItem(
                severity="warning",
                code="LARGE_BUSINESS_LOSS",
                message=f"事業損失が{result.business_income:,}円と大きい値です。入力を確認してください",
            )
        )

    # 4. TAX_ON_ZERO_INCOME — 課税所得0なのに税額発生
    if result.taxable_income == 0 and result.income_tax_base > 0:
        items.append(
            TaxSanityCheckItem(
                severity="error",
                code="TAX_ON_ZERO_INCOME",
                message="課税所得が0円ですが算出税額が発生しています",
            )
        )

    # 5. NEGATIVE_TOTAL_INCOME — 合計所得が負（損益通算後もマイナスの場合）
    total_raw = result.salary_income_after_deduction + result.business_income
    if total_raw < 0:
        items.append(
            TaxSanityCheckItem(
                severity="info",
                code="NEGATIVE_TOTAL_INCOME",
                message=f"損益通算後の合計所得が負（{total_raw:,}円）です。"
                "純損失の繰越控除の適用を検討してください",
            )
        )

    # 6. TAXABLE_INCOME_ROUNDING — 1,000円未満切捨て漏れ
    if result.taxable_income % TAXABLE_INCOME_ROUNDING != 0 and result.taxable_income > 0:
        items.append(
            TaxSanityCheckItem(
                severity="error",
                code="TAXABLE_INCOME_ROUNDING",
                message=f"課税所得（{result.taxable_income:,}円）が1,000円単位になっていません",
            )
        )

    # 7. RECONSTRUCTION_TAX_MISMATCH — 復興特別所得税の計算不一致
    expected_reconstruction = int(
        result.income_tax_after_credits * RECONSTRUCTION_TAX_RATE // RECONSTRUCTION_TAX_DENOMINATOR
    )
    if result.reconstruction_tax != expected_reconstruction:
        items.append(
            TaxSanityCheckItem(
                severity="error",
                code="RECONSTRUCTION_TAX_MISMATCH",
                message=f"復興特別所得税の計算が不一致です"
                f"（実際: {result.reconstruction_tax:,}円、"
                f"期待: {expected_reconstruction:,}円）",
            )
        )

    # 8. CREDITS_EXCEED_TAX — 税額控除が算出税額超過
    if result.total_tax_credits > result.income_tax_base and result.income_tax_base > 0:
        items.append(
            TaxSanityCheckItem(
                severity="warning",
                code="CREDITS_EXCEED_TAX",
                message=f"税額控除（{result.total_tax_credits:,}円）が"
                f"算出税額（{result.income_tax_base:,}円）を超過しています",
            )
        )

    # 9. NO_WITHHOLDING_ON_SALARY — 給与ありなのに源泉徴収0
    if input_data.salary_income > 0 and input_data.withheld_tax == 0:
        items.append(
            TaxSanityCheckItem(
                severity="warning",
                code="NO_WITHHOLDING_ON_SALARY",
                message=f"給与収入（{input_data.salary_income:,}円）がありますが"
                "源泉徴収税額が0円です。源泉徴収票を確認してください",
            )
        )

    # 10. REFUND_EXCEEDS_WITHHELD — 還付額が源泉徴収+予定納税の合計超過
    total_prepaid = (
        input_data.withheld_tax
        + input_data.business_withheld_tax
        + input_data.other_income_withheld_tax
        + input_data.estimated_tax_payment
    )
    if result.tax_due < 0 and abs(result.tax_due) > total_prepaid:
        items.append(
            TaxSanityCheckItem(
                severity="error",
                code="REFUND_EXCEEDS_WITHHELD",
                message=f"還付額（{abs(result.tax_due):,}円）が"
                f"源泉徴収+予定納税の合計（{total_prepaid:,}円）を超過しています",
            )
        )

    error_count = sum(1 for item in items if item.severity == "error")
    warning_count = sum(1 for item in items if item.severity == "warning")

    return TaxSanityCheckResult(
        passed=error_count == 0,
        items=items,
        error_count=error_count,
        warning_count=warning_count,
    )
