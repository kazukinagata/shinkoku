"""Configuration loader for shinkoku.

Loads taxpayer profile, address, business, and filing settings from YAML.
All fields have defaults for backward compatibility with older config files.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class TaxpayerConfig(BaseModel):
    """納税者基本情報。"""

    last_name: str = ""
    first_name: str = ""
    last_name_kana: str = ""
    first_name_kana: str = ""
    gender: str | None = None  # male / female
    date_of_birth: str | None = None  # YYYY-MM-DD
    phone: str = ""
    my_number: str | None = None  # マイナンバー12桁
    widow_status: str = "none"  # none / widow / single_parent
    disability_status: str = "none"  # none / general / special
    working_student: bool = False
    relationship_to_head: str | None = None


class AddressConfig(BaseModel):
    """住所情報。"""

    postal_code: str = ""
    prefecture: str = ""
    city: str = ""
    street: str = ""
    building: str = ""
    jan1_address: str | None = None  # 1/1時点の住所（異なる場合のみ）
    address_kana: str = ""  # 住所フリガナ（半角カナ）


class BusinessConfig(BaseModel):
    """事業情報。"""

    trade_name: str = ""  # 屋号
    industry_type: str = ""  # 業種
    business_description: str = ""  # 事業内容
    establishment_year: int | None = None  # 開業年


class FilingConfig(BaseModel):
    """申告方法。"""

    submission_method: str = "e-tax"  # e-tax / mail / in-person
    return_type: str = "blue"  # blue / white
    blue_return_deduction: int = 650_000
    electronic_bookkeeping: bool = False
    tax_office_name: str = ""
    seiribango: str = ""  # 整理番号（8桁）


class RefundAccountConfig(BaseModel):
    """還付金の受入先口座。"""

    bank_name: str = ""
    branch_name: str = ""
    account_type: str = ""  # 普通 / 当座
    account_number: str = ""
    account_holder: str = ""  # 口座名義（カナ）


class ShinkokuConfig(BaseModel):
    """shinkoku 設定ファイル全体。"""

    tax_year: int = 2025
    db_path: str = "./shinkoku.db"
    output_dir: str = "./output"
    invoice_registration_number: str | None = None

    # 書類ディレクトリ
    invoices_dir: str | None = None
    withholding_slips_dir: str | None = None
    past_returns_dir: str | None = None
    deductions_dir: str | None = None
    receipts_dir: str | None = None
    bank_statements_dir: str | None = None
    credit_card_statements_dir: str | None = None
    furusato_receipts_dir: str | None = None

    # 新規追加セクション
    taxpayer: TaxpayerConfig = Field(default_factory=TaxpayerConfig)
    address: AddressConfig = Field(default_factory=AddressConfig)
    business_address: AddressConfig | None = None
    business: BusinessConfig = Field(default_factory=BusinessConfig)
    filing: FilingConfig = Field(default_factory=FilingConfig)
    refund_account: RefundAccountConfig = Field(default_factory=RefundAccountConfig)


def load_config(config_path: str) -> ShinkokuConfig:
    """Load config from YAML file.

    Backward compatible: missing sections use defaults.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return ShinkokuConfig(**raw)
