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
    DepreciationAsset,
    DepreciationResult,
    IncomeTaxInput,
    IncomeTaxResult,
    ConsumptionTaxInput,
    ConsumptionTaxResult,
)


# ============================================================
# Basic Deduction (Reiwa 7 stepped table)
# ============================================================

# (upper_limit_inclusive, deduction_amount)
_BASIC_DEDUCTION_TABLE: list[tuple[int, int]] = [
    (1_320_000, 950_000),
    (23_500_000, 880_000),
    (24_000_000, 680_000),
    (24_500_000, 630_000),
    (25_000_000, 580_000),
    (25_450_000, 480_000),
    (25_950_000, 320_000),
    (26_450_000, 160_000),
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

# Spouse special deduction table for taxpayer income <= 9,000,000
# (spouse_income_upper, deduction)
_SPOUSE_SPECIAL_TABLE: list[tuple[int, int]] = [
    (580_000, 380_000),   # This is regular spouse deduction
    (630_000, 360_000),
    (680_000, 310_000),
    (730_000, 260_000),
    (780_000, 210_000),
    (830_000, 160_000),
    (880_000, 110_000),
    (930_000, 60_000),
    (980_000, 30_000),
    (1_330_000, 10_000),
]

_SPOUSE_SPECIAL_TABLE_9M: list[tuple[int, int]] = [
    (580_000, 260_000),
    (630_000, 240_000),
    (680_000, 210_000),
    (730_000, 180_000),
    (780_000, 140_000),
    (830_000, 110_000),
    (880_000, 70_000),
    (930_000, 40_000),
    (980_000, 20_000),
    (1_330_000, 10_000),
]

_SPOUSE_SPECIAL_TABLE_10M: list[tuple[int, int]] = [
    (580_000, 130_000),
    (630_000, 120_000),
    (680_000, 100_000),
    (730_000, 90_000),
    (780_000, 70_000),
    (830_000, 50_000),
    (880_000, 40_000),
    (930_000, 20_000),
    (980_000, 10_000),
    (1_330_000, 10_000),
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
# Furusato Nozei (Hometown Tax Donation) Deduction
# ============================================================

def calc_furusato_deduction(donation: int) -> int:
    """Calculate furusato nozei income deduction = donation - 2,000 yen."""
    if donation <= 2_000:
        return 0
    return donation - 2_000


# ============================================================
# Housing Loan Tax Credit
# ============================================================

def calc_housing_loan_credit(balance: int) -> int:
    """Calculate housing loan tax credit = balance * 0.7% (truncated)."""
    if balance <= 0:
        return 0
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
) -> DeductionsResult:
    """Calculate all applicable deductions and return structured result."""
    income_deductions: list[DeductionItem] = []
    tax_credits: list[DeductionItem] = []

    # 1. Basic deduction (always applied if > 0)
    basic = calc_basic_deduction(total_income)
    if basic > 0:
        income_deductions.append(
            DeductionItem(type="basic", name="基礎控除", amount=basic)
        )

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

    # 5. Medical expenses
    if medical_expenses > 100_000:
        med_deduction = min(medical_expenses - 100_000, 2_000_000)
        income_deductions.append(
            DeductionItem(
                type="medical",
                name="医療費控除",
                amount=med_deduction,
            )
        )

    # 6. Furusato nozei
    if furusato_nozei > 0:
        furusato = calc_furusato_deduction(furusato_nozei)
        if furusato > 0:
            income_deductions.append(
                DeductionItem(
                    type="furusato_nozei",
                    name="寄附金控除",
                    amount=furusato,
                    details="ふるさと納税",
                )
            )

    # 7. Spouse deduction
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

    # Tax credits
    # Housing loan credit
    if housing_loan_balance > 0:
        hl_credit = calc_housing_loan_credit(housing_loan_balance)
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

    # Step 2: Business income
    business_income = max(
        0,
        input_data.business_revenue
        - input_data.business_expenses
        - input_data.blue_return_deduction,
    )

    # Step 3: Total income
    total_income = salary_income_after + business_income

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

    # Step 10: Difference
    tax_due = total_tax - input_data.withheld_tax

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
            input_data.taxable_purchases_10 * 10 // 110
            if input_data.taxable_purchases_10
            else 0
        )
        tax_on_purchases_8 = (
            input_data.taxable_purchases_8 * 8 // 108
            if input_data.taxable_purchases_8
            else 0
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
        withheld_tax: int = 0,
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
            withheld_tax=withheld_tax,
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
