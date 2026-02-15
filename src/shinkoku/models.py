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

    income_deductions: list[DeductionItem] = Field(default_factory=list, description="所得控除")
    tax_credits: list[DeductionItem] = Field(default_factory=list, description="税額控除")
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


class DependentInfo(BaseModel):
    """扶養親族の情報。"""

    name: str
    relationship: str  # 配偶者/子/親 等
    birth_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    income: int = 0  # 年間所得
    disability: str | None = Field(default=None, pattern=r"^(general|special|special_cohabiting)$")
    cohabiting: bool = True  # 同居
    other_taxpayer_dependent: bool = False  # 他の納税者の扶養親族に該当する


class HousingLoanDetail(BaseModel):
    """住宅ローン控除の詳細情報。"""

    housing_type: str = Field(
        pattern=r"^(new_custom|new_subdivision|resale|used|renovation)$",
        description="住宅区分: new_custom=注文新築, new_subdivision=分譲新築, "
        "resale=中古, used=既存, renovation=増改築",
    )
    housing_category: str = Field(
        pattern=r"^(general|certified|zeh|energy_efficient)$",
        description="住宅性能区分: general=一般, certified=認定住宅, "
        "zeh=ZEH水準省エネ, energy_efficient=省エネ基準適合",
    )
    move_in_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    year_end_balance: int  # 年末残高
    is_new_construction: bool = True  # 新築=True, 中古=False
    is_childcare_household: bool = False  # 子育て世帯・若者夫婦世帯
    has_pre_r6_building_permit: bool = False  # R5以前の建築確認済み（一般住宅のみ関連）


class HousingLoanDetailInput(BaseModel):
    """住宅ローン控除詳細の登録入力。"""

    housing_type: str = Field(
        pattern=r"^(new_custom|new_subdivision|resale|used|renovation)$",
    )
    housing_category: str = Field(
        pattern=r"^(general|certified|zeh|energy_efficient)$",
    )
    move_in_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    year_end_balance: int = Field(ge=0, description="年末残高（円）")
    is_new_construction: bool = True
    is_childcare_household: bool = False
    has_pre_r6_building_permit: bool = False
    purchase_date: str | None = None  # 住宅購入日
    purchase_price: int = 0  # 住宅の価格（円）
    total_floor_area: int = 0  # 総床面積（平方メートル×100: 10063=100.63㎡）
    residential_floor_area: int = 0  # 居住用部分の面積（同上）
    property_number: str | None = None  # 不動産番号
    application_submitted: bool = False  # 適用申請書提出有無


class HousingLoanDetailRecord(BaseModel):
    """住宅ローン控除詳細のDBレコード。"""

    id: int
    fiscal_year: int
    housing_type: str
    housing_category: str
    move_in_date: str
    year_end_balance: int
    is_new_construction: bool
    is_childcare_household: bool = False
    has_pre_r6_building_permit: bool = False
    purchase_date: str | None = None
    purchase_price: int = 0
    total_floor_area: int = 0
    residential_floor_area: int = 0
    property_number: str | None = None
    application_submitted: bool = False


class LifeInsurancePremiumInput(BaseModel):
    """生命保険料控除の3区分入力（新旧制度対応）。"""

    general_new: int = 0  # 一般生命保険料（新制度）
    general_old: int = 0  # 一般生命保険料（旧制度）
    medical_care: int = 0  # 介護医療保険料（新制度のみ）
    annuity_new: int = 0  # 個人年金保険料（新制度）
    annuity_old: int = 0  # 個人年金保険料（旧制度）


class SmallBusinessMutualAidInput(BaseModel):
    """小規模企業共済等掛金控除のサブタイプ。"""

    small_business_mutual_aid: int = 0  # 小規模企業共済
    ideco: int = 0  # iDeCo（個人型確定拠出年金）
    disability_mutual_aid: int = 0  # 心身障害者扶養共済

    @property
    def total(self) -> int:
        return self.small_business_mutual_aid + self.ideco + self.disability_mutual_aid


class IncomeTaxInput(BaseModel):
    """所得税計算の入力。"""

    fiscal_year: int
    salary_income: int = 0
    business_revenue: int = 0
    business_expenses: int = 0
    blue_return_deduction: int = 650_000
    social_insurance: int = 0
    life_insurance_premium: int = 0
    life_insurance_detail: LifeInsurancePremiumInput | None = None  # 3区分詳細（Phase 3）
    earthquake_insurance_premium: int = 0
    old_long_term_insurance_premium: int = 0  # 旧長期損害保険料（Phase 4）
    medical_expenses: int = 0
    self_medication_expenses: int = 0  # セルフメディケーション税制（Phase 8）
    self_medication_eligible: bool = False  # 特定健康診査等を受けているか
    furusato_nozei: int = 0
    housing_loan_balance: int = 0
    housing_loan_year: int | None = None
    housing_loan_detail: HousingLoanDetail | None = None
    spouse_income: int | None = None
    dependents: list[DependentInfo] = Field(default_factory=list)
    ideco_contribution: int = 0  # iDeCo掛金（小規模企業共済等掛金控除）
    small_business_mutual_aid: SmallBusinessMutualAidInput | None = None  # Phase 7
    widow_status: str = "none"  # none / widow / single_parent（Phase 5）
    disability_status: str = "none"  # none / general / special（Phase 5）
    working_student: bool = False  # 勤労学生（Phase 5）
    withheld_tax: int = 0  # 給与の源泉徴収税額
    business_withheld_tax: int = 0  # 事業所得の源泉徴収税額（取引先別合計）
    loss_carryforward_amount: int = 0  # 繰越損失額
    estimated_tax_payment: int = 0  # 予定納税額（第1期+第2期）
    # Phase 10: その他所得（総合課税）
    misc_income: int = 0  # 雑所得
    dividend_income_comprehensive: int = 0  # 配当所得（総合課税）
    one_time_income: int = 0  # 一時所得（1/2適用前の金額）
    other_income_withheld_tax: int = 0  # その他所得の源泉徴収税額


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
    dividend_credit: int = 0  # 配当控除（税額控除）
    housing_loan_credit: int = 0  # 住宅ローン控除（税額控除）
    total_tax_credits: int = 0
    income_tax_after_credits: int = 0
    reconstruction_tax: int = 0
    total_tax: int = 0
    withheld_tax: int = 0
    business_withheld_tax: int = 0  # 事業所得の源泉徴収税額
    estimated_tax_payment: int = 0  # 予定納税額
    loss_carryforward_applied: int = 0  # 適用した繰越損失額
    tax_due: int = Field(
        description="正:納付、負:還付 = total_tax - withheld_tax - "
        "business_withheld_tax - estimated_tax_payment"
    )
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


# --- ふるさと納税 (furusato nozei) ---


class FurusatoReceiptData(BaseModel):
    """ふるさと納税受領証明書テンプレート。"""

    file_path: str
    municipality_name: str | None = None
    municipality_prefecture: str | None = None
    address: str | None = None
    amount: int | None = None
    date: str | None = None
    receipt_number: str | None = None


class FurusatoDonationRecord(BaseModel):
    """ふるさと納税寄附データ（DBレコード）。"""

    id: int
    fiscal_year: int
    municipality_name: str
    municipality_prefecture: str | None
    amount: int
    date: str
    receipt_number: str | None
    one_stop_applied: bool
    source_file: str | None


class FurusatoDonationSummary(BaseModel):
    """ふるさと納税集計結果。"""

    fiscal_year: int
    total_amount: int
    donation_count: int
    municipality_count: int
    deduction_amount: int = Field(description="所得控除額 = 合計 - 2,000円")
    estimated_limit: int | None = Field(
        default=None, description="推定控除上限額（所得情報が必要）"
    )
    over_limit: bool = False
    one_stop_count: int = 0
    needs_tax_return: bool = Field(
        default=True,
        description="確定申告が必要か（副業ユーザーは常にTrue）",
    )
    donations: list[FurusatoDonationRecord] = Field(default_factory=list)


# --- 事業所得の源泉徴収 (business withholding) ---


class BusinessWithholdingInput(BaseModel):
    """取引先別の源泉徴収入力。"""

    client_name: str
    gross_amount: int = Field(gt=0, description="支払金額（円）")
    withholding_tax: int = Field(ge=0, description="源泉徴収税額（円）")


class BusinessWithholdingRecord(BaseModel):
    """取引先別の源泉徴収DBレコード。"""

    id: int
    fiscal_year: int
    client_name: str
    gross_amount: int
    withholding_tax: int


# --- 損失繰越 (loss carryforward) ---


class LossCarryforwardInput(BaseModel):
    """損失繰越の入力。"""

    loss_year: int  # 損失が発生した年
    amount: int = Field(gt=0, description="繰越損失額（円）")


class LossCarryforwardRecord(BaseModel):
    """損失繰越のDBレコード。"""

    id: int
    fiscal_year: int
    loss_year: int
    amount: int
    used_amount: int


# --- 医療費明細 (medical expense details) ---


class MedicalExpenseInput(BaseModel):
    """医療費明細の入力。"""

    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    patient_name: str
    medical_institution: str
    amount: int = Field(gt=0, description="医療費（円）")
    insurance_reimbursement: int = 0  # 保険補填額
    description: str | None = None


class MedicalExpenseRecord(BaseModel):
    """医療費明細のDBレコード。"""

    id: int
    fiscal_year: int
    date: str
    patient_name: str
    medical_institution: str
    amount: int
    insurance_reimbursement: int
    description: str | None


# --- 地代家賃の内訳 (rent details) ---


class RentDetailInput(BaseModel):
    """地代家賃の内訳入力。"""

    property_type: str  # 事務所/自宅兼事務所/駐車場
    usage: str  # 事務所/自宅兼事務所
    landlord_name: str
    landlord_address: str
    monthly_rent: int = Field(gt=0, description="月額賃料（円）")
    annual_rent: int = Field(gt=0, description="年間賃料（円）")
    deposit: int = 0  # 権利金等
    business_ratio: int = Field(default=100, ge=1, le=100, description="事業割合（%）")


class RentDetailRecord(BaseModel):
    """地代家賃の内訳DBレコード。"""

    id: int
    fiscal_year: int
    property_type: str
    usage: str
    landlord_name: str
    landlord_address: str
    monthly_rent: int
    annual_rent: int
    deposit: int
    business_ratio: int


# --- 重複検出 (duplicate detection) ---


class DuplicateWarning(BaseModel):
    """登録時の重複警告。"""

    match_type: str = Field(pattern=r"^(exact|similar)$")
    score: int = Field(ge=0, le=100)
    existing_journal_id: int
    reason: str


class DuplicatePair(BaseModel):
    """重複ペア（申告前チェック用）。"""

    journal_id_a: int
    journal_id_b: int
    score: int = Field(ge=0, le=100)
    reason: str


class DuplicateCheckResult(BaseModel):
    """重複チェック結果。"""

    pairs: list[DuplicatePair] = Field(default_factory=list)
    exact_count: int = 0
    suspected_count: int = 0


# --- 配偶者情報 (spouse info) ---


class SpouseInput(BaseModel):
    """配偶者情報の入力。"""

    name: str
    date_of_birth: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    income: int = 0
    disability: str | None = Field(default=None, pattern=r"^(general|special|special_cohabiting)$")
    cohabiting: bool = True
    other_taxpayer_dependent: bool = False


class SpouseRecord(BaseModel):
    """配偶者情報のDBレコード。"""

    id: int
    fiscal_year: int
    name: str
    date_of_birth: str
    income: int
    disability: str | None
    cohabiting: bool
    other_taxpayer_dependent: bool


# --- 扶養親族 (dependents) DB永続化 ---


class DependentInput(BaseModel):
    """扶養親族の登録入力。"""

    name: str
    relationship: str
    date_of_birth: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    income: int = 0
    disability: str | None = Field(default=None, pattern=r"^(general|special|special_cohabiting)$")
    cohabiting: bool = True
    other_taxpayer_dependent: bool = False  # 他の納税者の扶養親族に該当する


class DependentRecord(BaseModel):
    """扶養親族のDBレコード。"""

    id: int
    fiscal_year: int
    name: str
    relationship: str
    date_of_birth: str
    income: int
    disability: str | None
    cohabiting: bool
    other_taxpayer_dependent: bool = False


# --- 源泉徴収票 (withholding slip) 拡張 ---


class WithholdingSlipInput(BaseModel):
    """源泉徴収票の登録入力。"""

    payer_name: str | None = None
    payment_amount: int = 0
    withheld_tax: int = 0
    social_insurance: int = 0
    life_insurance_deduction: int = 0
    earthquake_insurance_deduction: int = 0
    housing_loan_deduction: int = 0
    spouse_deduction: int = 0
    dependent_deduction: int = 0
    basic_deduction: int = 0
    # 拡張フィールド（Phase 6）
    life_insurance_general_new: int = 0
    life_insurance_general_old: int = 0
    life_insurance_medical_care: int = 0
    life_insurance_annuity_new: int = 0
    life_insurance_annuity_old: int = 0
    national_pension_premium: int = 0
    old_long_term_insurance_premium: int = 0
    source_file: str | None = None


class WithholdingSlipRecord(BaseModel):
    """源泉徴収票のDBレコード。"""

    id: int
    fiscal_year: int
    payer_name: str | None
    payment_amount: int
    withheld_tax: int
    social_insurance: int
    life_insurance_deduction: int
    earthquake_insurance_deduction: int
    housing_loan_deduction: int
    spouse_deduction: int
    dependent_deduction: int
    basic_deduction: int
    life_insurance_general_new: int = 0
    life_insurance_general_old: int = 0
    life_insurance_medical_care: int = 0
    life_insurance_annuity_new: int = 0
    life_insurance_annuity_old: int = 0
    national_pension_premium: int = 0
    old_long_term_insurance_premium: int = 0
    source_file: str | None = None


# --- その他所得 (other income) ---


class OtherIncomeInput(BaseModel):
    """その他所得（雑/配当/一時）の入力。"""

    income_type: str = Field(
        pattern=r"^(miscellaneous|dividend_comprehensive|one_time)$",
        description="miscellaneous=雑所得, dividend_comprehensive=配当所得(総合課税), one_time=一時所得",
    )
    description: str
    revenue: int = Field(ge=0, description="収入（円）")
    expenses: int = 0
    withheld_tax: int = 0
    payer_name: str | None = None
    payer_address: str | None = None


class OtherIncomeRecord(BaseModel):
    """その他所得のDBレコード。"""

    id: int
    fiscal_year: int
    income_type: str
    description: str
    revenue: int
    expenses: int
    withheld_tax: int
    payer_name: str | None
    payer_address: str | None


# --- 仮想通貨 (crypto) ---


class CryptoIncomeInput(BaseModel):
    """仮想通貨取引の入力。"""

    exchange_name: str
    gains: int = 0
    expenses: int = 0


class CryptoIncomeRecord(BaseModel):
    """仮想通貨取引のDBレコード。"""

    id: int
    fiscal_year: int
    exchange_name: str
    gains: int
    expenses: int


# --- 在庫棚卸 (inventory) ---


class InventoryInput(BaseModel):
    """在庫棚卸の入力。"""

    period: str = Field(
        pattern=r"^(beginning|ending)$",
        description="beginning=期首棚卸, ending=期末棚卸",
    )
    amount: int = Field(ge=0, description="棚卸高（円）")
    method: str = "cost"  # cost / retail / etc.
    details: str | None = None


class InventoryRecord(BaseModel):
    """在庫棚卸のDBレコード。"""

    id: int
    fiscal_year: int
    period: str
    amount: int
    method: str
    details: str | None


# --- 税理士等報酬 (professional fees) ---


class ProfessionalFeeInput(BaseModel):
    """税理士等報酬の入力。"""

    payer_address: str
    payer_name: str
    fee_amount: int = Field(gt=0, description="報酬金額（円）")
    expense_deduction: int = 0  # 必要経費
    withheld_tax: int = 0


class ProfessionalFeeRecord(BaseModel):
    """税理士等報酬のDBレコード。"""

    id: int
    fiscal_year: int
    payer_address: str
    payer_name: str
    fee_amount: int
    expense_deduction: int
    withheld_tax: int


# --- 株式取引 (stock trading) ---


class StockTradingAccountInput(BaseModel):
    """株式取引口座の入力。"""

    account_type: str = Field(
        pattern=r"^(tokutei_withholding|tokutei_no_withholding|ippan_listed|ippan_unlisted)$",
        description="tokutei_withholding=特定口座(源泉あり), tokutei_no_withholding=特定口座(源泉なし), "
        "ippan_listed=一般口座(上場), ippan_unlisted=一般口座(非上場)",
    )
    broker_name: str
    gains: int = 0
    losses: int = 0
    withheld_income_tax: int = 0
    withheld_residential_tax: int = 0
    dividend_income: int = 0
    dividend_withheld_tax: int = 0


class StockTradingAccountRecord(BaseModel):
    """株式取引口座のDBレコード。"""

    id: int
    fiscal_year: int
    account_type: str
    broker_name: str
    gains: int
    losses: int
    withheld_income_tax: int
    withheld_residential_tax: int
    dividend_income: int
    dividend_withheld_tax: int


class StockLossCarryforwardInput(BaseModel):
    """株式譲渡損失繰越の入力。"""

    loss_year: int
    amount: int = Field(gt=0, description="繰越損失額（円）")


class StockLossCarryforwardRecord(BaseModel):
    """株式譲渡損失繰越のDBレコード。"""

    id: int
    fiscal_year: int
    loss_year: int
    amount: int
    used_amount: int


# --- FX取引 (FX trading) ---


class FXTradingInput(BaseModel):
    """FX取引の入力。"""

    broker_name: str
    realized_gains: int = 0
    swap_income: int = 0
    expenses: int = 0


class FXTradingRecord(BaseModel):
    """FX取引のDBレコード。"""

    id: int
    fiscal_year: int
    broker_name: str
    realized_gains: int
    swap_income: int
    expenses: int


class FXLossCarryforwardInput(BaseModel):
    """FX損失繰越の入力。"""

    loss_year: int
    amount: int = Field(gt=0, description="繰越損失額（円）")


class FXLossCarryforwardRecord(BaseModel):
    """FX損失繰越のDBレコード。"""

    id: int
    fiscal_year: int
    loss_year: int
    amount: int
    used_amount: int


# --- 分離課税 (separate taxation) ---


class SeparateTaxInput(BaseModel):
    """分離課税計算の入力。"""

    fiscal_year: int
    # 株式
    stock_gains: int = 0
    stock_losses: int = 0
    stock_dividend_separate: int = 0  # 分離課税選択の配当
    stock_withheld_income_tax: int = 0
    stock_withheld_residential_tax: int = 0
    stock_loss_carryforward: int = 0  # 株式繰越損失額
    # FX
    fx_gains: int = 0  # realized_gains + swap_income
    fx_expenses: int = 0
    fx_loss_carryforward: int = 0  # FX繰越損失額


class SeparateTaxResult(BaseModel):
    """分離課税計算結果。"""

    fiscal_year: int
    # 株式
    stock_net_gain: int = 0  # 譲渡益 - 譲渡損
    stock_dividend_offset: int = 0  # 配当との損益通算額
    stock_taxable_income: int = 0  # 課税所得（繰越損失適用後）
    stock_loss_carryforward_used: int = 0
    stock_income_tax: int = 0  # 所得税15%
    stock_residential_tax: int = 0  # 住民税5%
    stock_reconstruction_tax: int = 0  # 復興特別所得税0.315%
    stock_total_tax: int = 0
    stock_withheld_total: int = 0
    stock_tax_due: int = 0
    # FX
    fx_net_income: int = 0
    fx_taxable_income: int = 0
    fx_loss_carryforward_used: int = 0
    fx_income_tax: int = 0
    fx_residential_tax: int = 0
    fx_reconstruction_tax: int = 0
    fx_total_tax: int = 0
    fx_tax_due: int = 0
    # 合計
    total_separate_tax: int = 0


# --- 社会保険料の種別別内訳 (social insurance items) ---


class SocialInsuranceItemInput(BaseModel):
    """社会保険料の種別入力。"""

    insurance_type: str = Field(
        description="種別: national_health / national_pension / national_pension_fund"
        " / nursing_care / labor_insurance / other"
    )
    name: str | None = None  # 保険者名等
    amount: int = Field(gt=0, description="円単位の整数")


class SocialInsuranceItemRecord(BaseModel):
    """社会保険料の種別DBレコード。"""

    id: int
    fiscal_year: int
    insurance_type: str
    name: str | None
    amount: int


# --- 保険契約（生命保険・地震保険の保険会社名） ---


class InsurancePolicyInput(BaseModel):
    """保険契約の入力。"""

    policy_type: str = Field(
        description="種別: life_general_new / life_general_old / life_medical_care"
        " / life_annuity_new / life_annuity_old / earthquake / old_long_term"
    )
    company_name: str  # 保険会社名
    premium: int = Field(gt=0, description="円単位の整数")


class InsurancePolicyRecord(BaseModel):
    """保険契約のDBレコード。"""

    id: int
    fiscal_year: int
    policy_type: str
    company_name: str
    premium: int


# --- 寄附金（ふるさと納税以外） ---


class DonationRecordInput(BaseModel):
    """ふるさと納税以外の寄附金入力。"""

    donation_type: str = Field(
        description="種別: political / npo / public_interest / specified / other"
    )
    recipient_name: str  # 寄附先名
    amount: int = Field(gt=0, description="円単位の整数")
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    receipt_number: str | None = None
    source_file: str | None = None


class DonationRecordRecord(BaseModel):
    """寄附金のDBレコード。"""

    id: int
    fiscal_year: int
    donation_type: str
    recipient_name: str
    amount: int
    date: str
    receipt_number: str | None
    source_file: str | None


# --- 公的年金等控除 (pension deduction) ---


class PensionDeductionInput(BaseModel):
    """公的年金等控除の入力。"""

    pension_income: int = Field(ge=0, description="公的年金等の収入金額（円）")
    is_over_65: bool = Field(description="65歳以上かどうか（年度末時点）")
    other_income: int = 0  # 公的年金等以外の合計所得金額


class PensionDeductionResult(BaseModel):
    """公的年金等控除の計算結果。"""

    pension_income: int  # 入力の年金収入
    deduction_amount: int  # 控除額
    taxable_pension_income: int  # 雑所得（年金） = pension_income - deduction_amount
    is_over_65: bool
    other_income_adjustment: int = 0  # 所得調整額（0, 100000, 200000）


# --- 退職所得 (retirement income) ---


class RetirementIncomeInput(BaseModel):
    """退職所得の入力。"""

    severance_pay: int = Field(ge=0, description="退職手当等の収入金額（円）")
    years_of_service: int = Field(gt=0, description="勤続年数（1年未満切上げ）")
    is_officer: bool = False  # 役員等かどうか（5年以下特例）
    is_disability_retirement: bool = False  # 障害退職かどうか（+100万加算）


class RetirementIncomeResult(BaseModel):
    """退職所得の計算結果。"""

    severance_pay: int
    retirement_income_deduction: int  # 退職所得控除額
    taxable_retirement_income: int  # 退職所得（1/2適用後）
    years_of_service: int
    is_officer: bool
    half_taxation_applied: bool  # 1/2課税が適用されたか
