"""Configuration loader for shinkoku.

Loads taxpayer profile, address, business, and filing settings from YAML.
All fields have defaults for backward compatibility with older config files.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


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


def determine_blue_return_deduction(
    submission_method: str,
    return_type: str,
    electronic_bookkeeping: bool,
    simple_bookkeeping: bool = False,
) -> int:
    """青色申告特別控除額を自動判定する。

    判定ロジック（国税庁 No.2072、租税特別措置法第25条の2）:
    - 65万円: 複式簿記 + (e-Tax提出 又は 電子帳簿保存) + 期限内申告
    - 55万円: 複式簿記 + 書面提出 + 期限内申告
    - 10万円: 簡易帳簿 又は 期限後申告
    """
    if return_type != "blue":
        return 0
    if simple_bookkeeping:
        return 100_000
    # 複式簿記: e-Tax提出 又は 電子帳簿保存 → 65万円
    if submission_method == "e-tax" or electronic_bookkeeping:
        return 650_000
    # 複式簿記 + 書面提出 + 電子帳簿保存なし → 55万円
    return 550_000


class FilingConfig(BaseModel):
    """申告方法。"""

    submission_method: str = "e-tax"  # e-tax / mail / in-person
    return_type: str = "blue"  # blue / white
    blue_return_deduction: int = 650_000
    simple_bookkeeping: bool = False  # 簡易帳簿かどうか
    electronic_bookkeeping: bool = False
    tax_office_name: str = ""
    seiribango: str = ""  # 整理番号（8桁）

    @model_validator(mode="after")
    def validate_blue_return_deduction(self) -> FilingConfig:
        """submission_method・electronic_bookkeeping から控除額の整合性を検証する。"""
        expected = determine_blue_return_deduction(
            submission_method=self.submission_method,
            return_type=self.return_type,
            electronic_bookkeeping=self.electronic_bookkeeping,
            simple_bookkeeping=self.simple_bookkeeping,
        )
        # return_type が white の場合は控除額 0 だが、設定ファイルの既存値を尊重する
        if self.return_type == "blue" and self.blue_return_deduction != expected:
            self.blue_return_deduction = expected
        return self


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
