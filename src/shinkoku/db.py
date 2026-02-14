"""Database initialization and connection management."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
CURRENT_SCHEMA_VERSION = 4

# v1 → v2: 配偶者/扶養/その他所得/仮想通貨/在庫/税理士報酬/株式/FX テーブル追加
# + 源泉徴収票に生命保険5区分・国民年金・旧長期損害保険列追加
_V2_MIGRATION_TABLES = """
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
CREATE TABLE IF NOT EXISTS dependents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    income INTEGER NOT NULL DEFAULT 0,
    disability TEXT CHECK (disability IN ('general','special','special_cohabiting') OR disability IS NULL),
    cohabiting INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
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
CREATE TABLE IF NOT EXISTS crypto_income_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    exchange_name TEXT NOT NULL,
    gains INTEGER NOT NULL DEFAULT 0,
    expenses INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(fiscal_year, exchange_name)
);
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
CREATE TABLE IF NOT EXISTS stock_loss_carryforward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    loss_year INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    used_amount INTEGER NOT NULL DEFAULT 0
);
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
CREATE TABLE IF NOT EXISTS fx_loss_carryforward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL REFERENCES fiscal_years(year),
    loss_year INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    used_amount INTEGER NOT NULL DEFAULT 0
);
"""

# 源泉徴収票の拡張列（Phase 6）
_V2_WITHHOLDING_SLIP_COLUMNS = [
    ("life_insurance_general_new", "INTEGER NOT NULL DEFAULT 0"),
    ("life_insurance_general_old", "INTEGER NOT NULL DEFAULT 0"),
    ("life_insurance_medical_care", "INTEGER NOT NULL DEFAULT 0"),
    ("life_insurance_annuity_new", "INTEGER NOT NULL DEFAULT 0"),
    ("life_insurance_annuity_old", "INTEGER NOT NULL DEFAULT 0"),
    ("national_pension_premium", "INTEGER NOT NULL DEFAULT 0"),
    ("old_long_term_insurance_premium", "INTEGER NOT NULL DEFAULT 0"),
]

_V2_INDEXES = """
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
"""


# v2 → v3: 住宅ローン控除に子育て世帯・R5確認済みフラグ追加
_V3_HOUSING_LOAN_COLUMNS = [
    ("is_childcare_household", "INTEGER NOT NULL DEFAULT 0"),
    ("has_pre_r6_building_permit", "INTEGER NOT NULL DEFAULT 0"),
]


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create a connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _has_schema_version_table(conn: sqlite3.Connection) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    return cursor.fetchone() is not None


def _get_current_version(conn: sqlite3.Connection) -> int:
    if not _has_schema_version_table(conn):
        return 0
    row = conn.execute(
        "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else 0


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table})")  # noqa: S608
    return any(row[1] == column for row in cursor.fetchall())


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Apply v1 → v2 migration: new tables + withholding_slips columns."""
    conn.executescript(_V2_MIGRATION_TABLES)

    # 源泉徴収票に列追加（既存列があればスキップ）
    for col_name, col_def in _V2_WITHHOLDING_SLIP_COLUMNS:
        if not _has_column(conn, "withholding_slips", col_name):
            conn.execute(f"ALTER TABLE withholding_slips ADD COLUMN {col_name} {col_def}")

    conn.executescript(_V2_INDEXES)
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (2,),
    )
    conn.commit()


def _migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """Apply v2 → v3 migration: housing_loan_details に子育て世帯・R5確認済みフラグ追加。"""
    for col_name, col_def in _V3_HOUSING_LOAN_COLUMNS:
        if not _has_column(conn, "housing_loan_details", col_name):
            conn.execute(f"ALTER TABLE housing_loan_details ADD COLUMN {col_name} {col_def}")
    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (3,),
    )
    conn.commit()


# v3 → v4: 扶養親族に他の納税者フラグ追加、住宅ローン明細拡張、
# 社会保険料種別内訳/保険会社名/寄附金テーブル追加
_V4_DEPENDENTS_COLUMNS = [
    ("other_taxpayer_dependent", "INTEGER NOT NULL DEFAULT 0"),
]

_V4_HOUSING_LOAN_COLUMNS = [
    ("purchase_date", "TEXT"),
    ("purchase_price", "INTEGER NOT NULL DEFAULT 0"),
    ("total_floor_area", "INTEGER NOT NULL DEFAULT 0"),
    ("residential_floor_area", "INTEGER NOT NULL DEFAULT 0"),
    ("property_number", "TEXT"),
    ("application_submitted", "INTEGER NOT NULL DEFAULT 0"),
]

_V4_NEW_TABLES = """
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
"""

_V4_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_social_insurance_items_fiscal_year ON social_insurance_items(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_insurance_policies_fiscal_year ON insurance_policies(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_donation_records_fiscal_year ON donation_records(fiscal_year);
"""


def _migrate_v3_to_v4(conn: sqlite3.Connection) -> None:
    """Apply v3 → v4 migration."""
    # 扶養親族に other_taxpayer_dependent 列追加
    for col_name, col_def in _V4_DEPENDENTS_COLUMNS:
        if not _has_column(conn, "dependents", col_name):
            conn.execute(f"ALTER TABLE dependents ADD COLUMN {col_name} {col_def}")

    # 住宅ローン詳細に明細フィールド追加
    for col_name, col_def in _V4_HOUSING_LOAN_COLUMNS:
        if not _has_column(conn, "housing_loan_details", col_name):
            conn.execute(f"ALTER TABLE housing_loan_details ADD COLUMN {col_name} {col_def}")

    # 新テーブル作成
    conn.executescript(_V4_NEW_TABLES)
    conn.executescript(_V4_INDEXES)

    conn.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (4,),
    )
    conn.commit()


def migrate(conn: sqlite3.Connection) -> int:
    """Apply schema migrations. Returns the current schema version."""
    current = _get_current_version(conn)

    if current >= CURRENT_SCHEMA_VERSION:
        return current

    if current == 0:
        # Fresh database: apply full schema
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
            (CURRENT_SCHEMA_VERSION,),
        )
        conn.commit()
        return CURRENT_SCHEMA_VERSION

    # Incremental migrations
    if current < 2:
        _migrate_v1_to_v2(conn)
    if current < 3:
        _migrate_v2_to_v3(conn)
    if current < 4:
        _migrate_v3_to_v4(conn)

    return CURRENT_SCHEMA_VERSION


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the database: create file, apply schema, return connection."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    migrate(conn)
    return conn
