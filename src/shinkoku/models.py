"""Pydantic models for MCP tool input/output types."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- 帳簿管理 (ledger) ---


class JournalLine(BaseModel):
    """仕訳明細（借方または貸方の1行）。"""

    side: str = Field(pattern=r"^(debit|credit)$")
    account_code: str
    amount: int = Field(gt=0, description="円単位の整数")
    tax_category: str | None = None
    tax_amount: int = 0


class JournalEntry(BaseModel):
    """仕訳1件の入力データ。"""

    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    description: str | None = None
    lines: list[JournalLine] = Field(min_length=2)
    source: str | None = None
    source_file: str | None = None
    is_adjustment: bool = False


class JournalSearchParams(BaseModel):
    """仕訳検索の条件。"""

    fiscal_year: int
    date_from: str | None = None
    date_to: str | None = None
    account_code: str | None = None
    description_contains: str | None = None
    source: str | None = None
    limit: int = 100
    offset: int = 0


class JournalRecord(BaseModel):
    """DB上の仕訳レコード。"""

    id: int
    fiscal_year: int
    date: str
    description: str | None
    source: str | None
    source_file: str | None
    is_adjustment: bool
    lines: list[JournalLineRecord]


class JournalLineRecord(BaseModel):
    """DB上の仕訳明細レコード。"""

    id: int
    side: str
    account_code: str
    amount: int
    tax_category: str | None
    tax_amount: int


class JournalSearchResult(BaseModel):
    """仕訳検索の結果。"""

    journals: list[JournalRecord]
    total_count: int


# --- 財務諸表 ---


class TrialBalanceAccount(BaseModel):
    """残高試算表の1行。"""

    account_code: str
    account_name: str
    category: str
    debit_total: int = 0
    credit_total: int = 0
    balance: int = 0


class TrialBalanceResult(BaseModel):
    """残高試算表。"""

    fiscal_year: int
    accounts: list[TrialBalanceAccount]
    total_debit: int
    total_credit: int


class PLItem(BaseModel):
    """損益計算書の1行。"""

    account_code: str
    account_name: str
    amount: int


class PLResult(BaseModel):
    """損益計算書。"""

    fiscal_year: int
    revenues: list[PLItem]
    expenses: list[PLItem]
    total_revenue: int
    total_expense: int
    net_income: int


class BSItem(BaseModel):
    """貸借対照表の1行。"""

    account_code: str
    account_name: str
    amount: int


class BSResult(BaseModel):
    """貸借対照表。"""

    fiscal_year: int
    assets: list[BSItem]
    liabilities: list[BSItem]
    equity: list[BSItem]
    total_assets: int
    total_liabilities: int
    total_equity: int


# --- データ取り込み (import) ---


class CSVImportCandidate(BaseModel):
    """CSV取り込み候補の1行。"""

    row_number: int
    date: str
    description: str
    amount: int
    original_data: dict


class CSVImportResult(BaseModel):
    """CSV取り込み結果。"""

    file_path: str
    encoding: str
    total_rows: int
    candidates: list[CSVImportCandidate]
    skipped_rows: list[int] = []
    errors: list[str] = []


class ReceiptData(BaseModel):
    """レシート読み取りテンプレート。"""

    file_path: str
    date: str | None = None
    vendor: str | None = None
    total_amount: int | None = None
    items: list[dict] = []
    tax_included: bool = True


class InvoiceData(BaseModel):
    """請求書読み取り結果。"""

    file_path: str
    extracted_text: str
    vendor: str | None = None
    invoice_number: str | None = None
    date: str | None = None
    total_amount: int | None = None
    tax_amount: int | None = None


class WithholdingSlipData(BaseModel):
    """源泉徴収票の構造化データ。"""

    file_path: str
    extracted_text: str
    payer_name: str | None = None
    payment_amount: int = 0
    withheld_tax: int = 0
    social_insurance: int = 0
    life_insurance_deduction: int = 0
    earthquake_insurance_deduction: int = 0
    housing_loan_deduction: int = 0


# --- 税額計算 (tax) ---


class DeductionItem(BaseModel):
    """控除1項目。"""

    type: str
    name: str
    amount: int
    details: str | None = None


class DeductionsResult(BaseModel):
    """控除計算結果。"""

    income_deductions: list[DeductionItem] = Field(
        default_factory=list, description="所得控除"
    )
    tax_credits: list[DeductionItem] = Field(
        default_factory=list, description="税額控除"
    )
    total_income_deductions: int = 0
    total_tax_credits: int = 0


class DepreciationAsset(BaseModel):
    """減価償却計算結果の1資産。"""

    asset_id: int
    name: str
    acquisition_cost: int
    method: str
    useful_life: int
    business_use_ratio: int
    current_year_amount: int
    accumulated: int


class DepreciationResult(BaseModel):
    """減価償却費計算結果。"""

    fiscal_year: int
    assets: list[DepreciationAsset]
    total_depreciation: int


class IncomeTaxInput(BaseModel):
    """所得税計算の入力。"""

    fiscal_year: int
    salary_income: int = 0
    business_revenue: int = 0
    business_expenses: int = 0
    blue_return_deduction: int = 650000
    social_insurance: int = 0
    life_insurance_premium: int = 0
    earthquake_insurance_premium: int = 0
    medical_expenses: int = 0
    furusato_nozei: int = 0
    housing_loan_balance: int = 0
    housing_loan_year: int | None = None
    spouse_income: int | None = None
    withheld_tax: int = 0


class IncomeTaxResult(BaseModel):
    """所得税計算結果。"""

    fiscal_year: int
    # 所得
    salary_income_after_deduction: int = 0
    business_income: int = 0
    total_income: int = 0
    # 所得控除
    total_income_deductions: int = 0
    taxable_income: int = 0
    # 税額
    income_tax_base: int = 0
    total_tax_credits: int = 0
    income_tax_after_credits: int = 0
    reconstruction_tax: int = 0
    total_tax: int = 0
    withheld_tax: int = 0
    tax_due: int = Field(description="正:納付、負:還付")
    # 内訳
    deductions_detail: DeductionsResult | None = None


class ConsumptionTaxInput(BaseModel):
    """消費税計算の入力。"""

    fiscal_year: int
    method: str = Field(
        pattern=r"^(standard|simplified|special_20pct)$",
        description="standard=本則, simplified=簡易, special_20pct=2割特例",
    )
    taxable_sales_10: int = 0
    taxable_sales_8: int = 0
    taxable_purchases_10: int = 0
    taxable_purchases_8: int = 0
    simplified_business_type: int | None = Field(
        default=None, ge=1, le=6, description="簡易課税の事業区分(1-6)"
    )


class ConsumptionTaxResult(BaseModel):
    """消費税計算結果。"""

    fiscal_year: int
    method: str
    taxable_sales_total: int = 0
    tax_on_sales: int = 0
    tax_on_purchases: int = 0
    tax_due: int = 0
    local_tax_due: int = 0
    total_due: int = 0
