-- shinkoku schema v4
-- 確定申告自動化のための複式簿記データベース

-- スキーマバージョン管理
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 年度管理
CREATE TABLE IF NOT EXISTS fiscal_years (
    year INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 勘定科目マスタ
CREATE TABLE IF NOT EXISTS accounts (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    sub_category TEXT,
    tax_category TEXT CHECK (tax_category IN ('taxable', 'non_taxable', 'exempt', 'out_of_scope') OR tax_category IS NULL),
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- 仕訳ヘッダ
CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    date TEXT NOT NULL,
    description TEXT,
    content_hash TEXT,
    source TEXT CHECK (source IN ('csv_import', 'receipt_ocr', 'invoice_ocr', 'manual', 'adjustment')),
    source_file TEXT,
    is_adjustment INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 仕訳明細（借方・貸方）
CREATE TABLE IF NOT EXISTS journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,
    side TEXT NOT NULL CHECK (side IN ('debit', 'credit')),
    account_code TEXT NOT NULL REFERENCES accounts(code),
    amount INTEGER NOT NULL CHECK (amount > 0),
    tax_category TEXT CHECK (tax_category IN (
        'taxable_10', 'taxable_8', 'taxable_8_reduced',
        'non_taxable', 'exempt', 'out_of_scope'
    ) OR tax_category IS NULL),
    tax_amount INTEGER DEFAULT 0
);

-- 固定資産台帳
CREATE TABLE IF NOT EXISTS fixed_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    acquisition_date TEXT NOT NULL,
    acquisition_cost INTEGER NOT NULL,
    useful_life INTEGER NOT NULL,
    method TEXT NOT NULL DEFAULT 'straight_line' CHECK (method IN ('straight_line', 'declining_balance')),
    business_use_ratio INTEGER NOT NULL DEFAULT 100 CHECK (business_use_ratio BETWEEN 1 AND 100),
    accumulated_depreciation INTEGER NOT NULL DEFAULT 0,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    memo TEXT
);

-- 控除情報
CREATE TABLE IF NOT EXISTS deductions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    type TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount >= 0),
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 源泉徴収票データ
CREATE TABLE IF NOT EXISTS withholding_slips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    payer_name TEXT,
    payment_amount INTEGER NOT NULL DEFAULT 0,
    withheld_tax INTEGER NOT NULL DEFAULT 0,
    social_insurance INTEGER NOT NULL DEFAULT 0,
    life_insurance_deduction INTEGER NOT NULL DEFAULT 0,
    earthquake_insurance_deduction INTEGER NOT NULL DEFAULT 0,
    housing_loan_deduction INTEGER NOT NULL DEFAULT 0,
    spouse_deduction INTEGER NOT NULL DEFAULT 0,
    dependent_deduction INTEGER NOT NULL DEFAULT 0,
    basic_deduction INTEGER NOT NULL DEFAULT 0,
    life_insurance_general_new INTEGER NOT NULL DEFAULT 0,
    life_insurance_general_old INTEGER NOT NULL DEFAULT 0,
    life_insurance_medical_care INTEGER NOT NULL DEFAULT 0,
    life_insurance_annuity_new INTEGER NOT NULL DEFAULT 0,
    life_insurance_annuity_old INTEGER NOT NULL DEFAULT 0,
    national_pension_premium INTEGER NOT NULL DEFAULT 0,
    old_long_term_insurance_premium INTEGER NOT NULL DEFAULT 0,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- インポート元ファイル管理（CSV再インポート防止）
CREATE TABLE IF NOT EXISTS import_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    file_hash TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT,
    row_count INTEGER NOT NULL DEFAULT 0,
    imported_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 事業所得の源泉徴収（取引先別）
CREATE TABLE IF NOT EXISTS business_withholding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    client_name TEXT NOT NULL,
    gross_amount INTEGER NOT NULL CHECK (gross_amount > 0),
    withholding_tax INTEGER NOT NULL CHECK (withholding_tax >= 0),
    UNIQUE(fiscal_year, client_name)
);

-- 損失繰越
CREATE TABLE IF NOT EXISTS loss_carryforward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    loss_year INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    used_amount INTEGER NOT NULL DEFAULT 0
);

-- 医療費明細
CREATE TABLE IF NOT EXISTS medical_expense_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    date TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    medical_institution TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    insurance_reimbursement INTEGER DEFAULT 0,
    description TEXT
);

-- 地代家賃の内訳
CREATE TABLE IF NOT EXISTS rent_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    property_type TEXT NOT NULL,
    usage TEXT NOT NULL,
    landlord_name TEXT NOT NULL,
    landlord_address TEXT NOT NULL,
    monthly_rent INTEGER NOT NULL CHECK (monthly_rent > 0),
    annual_rent INTEGER NOT NULL CHECK (annual_rent > 0),
    deposit INTEGER DEFAULT 0,
    business_ratio INTEGER DEFAULT 100 CHECK (business_ratio BETWEEN 1 AND 100),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 住宅ローン控除詳細
CREATE TABLE IF NOT EXISTS housing_loan_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    housing_type TEXT NOT NULL CHECK (housing_type IN (
        'new_custom', 'new_subdivision', 'resale', 'used', 'renovation'
    )),
    housing_category TEXT NOT NULL CHECK (housing_category IN (
        'general', 'certified', 'zeh', 'energy_efficient'
    )),
    move_in_date TEXT NOT NULL,
    year_end_balance INTEGER NOT NULL CHECK (year_end_balance >= 0),
    is_new_construction INTEGER NOT NULL DEFAULT 1,
    is_childcare_household INTEGER NOT NULL DEFAULT 0,
    has_pre_r6_building_permit INTEGER NOT NULL DEFAULT 0,
    purchase_date TEXT,
    purchase_price INTEGER NOT NULL DEFAULT 0,
    total_floor_area INTEGER NOT NULL DEFAULT 0,
    residential_floor_area INTEGER NOT NULL DEFAULT 0,
    property_number TEXT,
    application_submitted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ふるさと納税寄附データ
CREATE TABLE IF NOT EXISTS furusato_donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    municipality_name TEXT NOT NULL,
    municipality_prefecture TEXT,
    amount INTEGER NOT NULL CHECK (amount > 0),
    date TEXT NOT NULL,
    receipt_number TEXT,
    one_stop_applied INTEGER NOT NULL DEFAULT 0,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 配偶者情報
CREATE TABLE IF NOT EXISTS spouse_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    income INTEGER NOT NULL DEFAULT 0,
    disability TEXT CHECK (disability IN ('general','special','special_cohabiting') OR disability IS NULL),
    cohabiting INTEGER NOT NULL DEFAULT 1,
    other_taxpayer_dependent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(fiscal_year)
);

-- 扶養親族
CREATE TABLE IF NOT EXISTS dependents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    income INTEGER NOT NULL DEFAULT 0,
    disability TEXT CHECK (disability IN ('general','special','special_cohabiting') OR disability IS NULL),
    cohabiting INTEGER NOT NULL DEFAULT 1,
    other_taxpayer_dependent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- その他所得（雑所得/配当所得/一時所得）
CREATE TABLE IF NOT EXISTS other_income_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    income_type TEXT NOT NULL CHECK (income_type IN (
        'miscellaneous', 'dividend_comprehensive', 'one_time'
    )),
    description TEXT NOT NULL,
    revenue INTEGER NOT NULL CHECK (revenue >= 0),
    expenses INTEGER NOT NULL DEFAULT 0,
    withheld_tax INTEGER NOT NULL DEFAULT 0,
    payer_name TEXT,
    payer_address TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 仮想通貨取引
CREATE TABLE IF NOT EXISTS crypto_income_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    exchange_name TEXT NOT NULL,
    gains INTEGER NOT NULL DEFAULT 0,
    expenses INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(fiscal_year, exchange_name)
);

-- 在庫棚卸
CREATE TABLE IF NOT EXISTS inventory_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    period TEXT NOT NULL CHECK (period IN ('beginning', 'ending')),
    amount INTEGER NOT NULL CHECK (amount >= 0),
    method TEXT NOT NULL DEFAULT 'cost',
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(fiscal_year, period)
);

-- 税理士等報酬
CREATE TABLE IF NOT EXISTS professional_fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    payer_address TEXT NOT NULL,
    payer_name TEXT NOT NULL,
    fee_amount INTEGER NOT NULL CHECK (fee_amount > 0),
    expense_deduction INTEGER NOT NULL DEFAULT 0,
    withheld_tax INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 株式取引口座
CREATE TABLE IF NOT EXISTS stock_trading_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    account_type TEXT NOT NULL CHECK (account_type IN (
        'tokutei_withholding', 'tokutei_no_withholding',
        'ippan_listed', 'ippan_unlisted'
    )),
    broker_name TEXT NOT NULL,
    gains INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    withheld_income_tax INTEGER NOT NULL DEFAULT 0,
    withheld_residential_tax INTEGER NOT NULL DEFAULT 0,
    dividend_income INTEGER NOT NULL DEFAULT 0,
    dividend_withheld_tax INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(fiscal_year, account_type, broker_name)
);

-- 株式譲渡損失の繰越
CREATE TABLE IF NOT EXISTS stock_loss_carryforward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    loss_year INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    used_amount INTEGER NOT NULL DEFAULT 0
);

-- FX取引
CREATE TABLE IF NOT EXISTS fx_trading_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    broker_name TEXT NOT NULL,
    realized_gains INTEGER NOT NULL DEFAULT 0,
    swap_income INTEGER NOT NULL DEFAULT 0,
    expenses INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(fiscal_year, broker_name)
);

-- FX損失の繰越
CREATE TABLE IF NOT EXISTS fx_loss_carryforward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    loss_year INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    used_amount INTEGER NOT NULL DEFAULT 0
);

-- 社会保険料の種別別内訳
CREATE TABLE IF NOT EXISTS social_insurance_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    insurance_type TEXT NOT NULL CHECK (insurance_type IN (
        'national_health', 'national_pension', 'national_pension_fund',
        'nursing_care', 'labor_insurance', 'other'
    )),
    name TEXT,
    amount INTEGER NOT NULL CHECK (amount > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 生命保険/地震保険の保険会社名
CREATE TABLE IF NOT EXISTS insurance_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    policy_type TEXT NOT NULL CHECK (policy_type IN (
        'life_general_new', 'life_general_old', 'life_medical_care',
        'life_annuity_new', 'life_annuity_old', 'earthquake', 'old_long_term'
    )),
    company_name TEXT NOT NULL,
    premium INTEGER NOT NULL CHECK (premium > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ふるさと納税以外の寄附金
CREATE TABLE IF NOT EXISTS donation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    donation_type TEXT NOT NULL CHECK (donation_type IN (
        'political', 'npo', 'public_interest', 'specified', 'other'
    )),
    recipient_name TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    date TEXT NOT NULL,
    receipt_number TEXT,
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_journals_fiscal_year ON journals(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_journals_date ON journals(date);
CREATE INDEX IF NOT EXISTS idx_journals_source ON journals(source);
CREATE UNIQUE INDEX IF NOT EXISTS idx_journals_content_hash ON journals(fiscal_year, content_hash) WHERE content_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_journal_lines_journal_id ON journal_lines(journal_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_account_code ON journal_lines(account_code);
CREATE INDEX IF NOT EXISTS idx_journal_lines_side ON journal_lines(side);
CREATE INDEX IF NOT EXISTS idx_fixed_assets_fiscal_year ON fixed_assets(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_deductions_fiscal_year ON deductions(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_withholding_slips_fiscal_year ON withholding_slips(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_import_sources_fiscal_year ON import_sources(fiscal_year);
CREATE UNIQUE INDEX IF NOT EXISTS idx_import_sources_file_hash ON import_sources(fiscal_year, file_hash);
CREATE INDEX IF NOT EXISTS idx_business_withholding_fiscal_year ON business_withholding(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_loss_carryforward_fiscal_year ON loss_carryforward(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_medical_expense_details_fiscal_year ON medical_expense_details(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_rent_details_fiscal_year ON rent_details(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_housing_loan_details_fiscal_year ON housing_loan_details(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_furusato_donations_fiscal_year ON furusato_donations(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_spouse_info_fiscal_year ON spouse_info(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_dependents_fiscal_year ON dependents(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_other_income_items_fiscal_year ON other_income_items(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_crypto_income_records_fiscal_year ON crypto_income_records(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_inventory_records_fiscal_year ON inventory_records(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_professional_fees_fiscal_year ON professional_fees(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_stock_trading_accounts_fiscal_year ON stock_trading_accounts(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_stock_loss_carryforward_fiscal_year ON stock_loss_carryforward(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_fx_trading_records_fiscal_year ON fx_trading_records(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_fx_loss_carryforward_fiscal_year ON fx_loss_carryforward(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_social_insurance_items_fiscal_year ON social_insurance_items(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_insurance_policies_fiscal_year ON insurance_policies(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_donation_records_fiscal_year ON donation_records(fiscal_year);
