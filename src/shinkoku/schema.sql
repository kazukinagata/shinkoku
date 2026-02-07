-- shinkoku schema v1
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
    source_file TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_journals_fiscal_year ON journals(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_journals_date ON journals(date);
CREATE INDEX IF NOT EXISTS idx_journals_source ON journals(source);
CREATE INDEX IF NOT EXISTS idx_journal_lines_journal_id ON journal_lines(journal_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_account_code ON journal_lines(account_code);
CREATE INDEX IF NOT EXISTS idx_journal_lines_side ON journal_lines(side);
CREATE INDEX IF NOT EXISTS idx_fixed_assets_fiscal_year ON fixed_assets(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_deductions_fiscal_year ON deductions(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_withholding_slips_fiscal_year ON withholding_slips(fiscal_year);
