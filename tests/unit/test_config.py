"""Tests for shinkoku.config — YAML config loader."""

from __future__ import annotations

import pytest

from shinkoku.config import (
    AddressConfig,
    BusinessConfig,
    FilingConfig,
    ShinkokuConfig,
    TaxpayerConfig,
    load_config,
)


@pytest.fixture
def minimal_config_yaml(tmp_path):
    """Minimal config YAML with only tax_year and db_path."""
    config_file = tmp_path / "shinkoku.config.yaml"
    config_file.write_text(
        "tax_year: 2025\ndb_path: ./test.db\n",
        encoding="utf-8",
    )
    return config_file


@pytest.fixture
def full_config_yaml(tmp_path):
    """Full config YAML with all sections populated."""
    content = """\
tax_year: 2025
db_path: ./test.db
output_dir: ./output
taxpayer:
  last_name: 山田
  first_name: 太郎
  last_name_kana: ヤマダ
  first_name_kana: タロウ
  gender: male
  date_of_birth: "1990-01-15"
  phone: "03-1234-5678"
  my_number: "123456789012"
  widow_status: none
  disability_status: none
  working_student: false
address:
  postal_code: "100-0001"
  prefecture: 東京都
  city: 千代田区
  street: 丸の内1-1-1
  building: テストビル3F
business:
  trade_name: テスト屋
  industry_type: 情報通信業
  business_description: ソフトウェア開発
  establishment_year: 2020
filing:
  submission_method: e-tax
  return_type: blue
  blue_return_deduction: 650000
  electronic_bookkeeping: true
  tax_office_name: 麹町税務署
"""
    config_file = tmp_path / "shinkoku.config.yaml"
    config_file.write_text(content, encoding="utf-8")
    return config_file


class TestLoadMinimalConfig:
    """後方互換: tax_year と db_path のみの最小構成で読み込めることを確認。"""

    def test_loads_tax_year(self, minimal_config_yaml):
        cfg = load_config(str(minimal_config_yaml))
        assert cfg.tax_year == 2025

    def test_loads_db_path(self, minimal_config_yaml):
        cfg = load_config(str(minimal_config_yaml))
        assert cfg.db_path == "./test.db"

    def test_returns_shinkoku_config_instance(self, minimal_config_yaml):
        cfg = load_config(str(minimal_config_yaml))
        assert isinstance(cfg, ShinkokuConfig)

    def test_sub_configs_are_defaults(self, minimal_config_yaml):
        cfg = load_config(str(minimal_config_yaml))
        assert isinstance(cfg.taxpayer, TaxpayerConfig)
        assert isinstance(cfg.address, AddressConfig)
        assert isinstance(cfg.business, BusinessConfig)
        assert isinstance(cfg.filing, FilingConfig)


class TestLoadFullConfig:
    """全セクションが記載されたフル構成を正しく読み込むことを確認。"""

    def test_taxpayer_name(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.taxpayer.last_name == "山田"
        assert cfg.taxpayer.first_name == "太郎"

    def test_taxpayer_kana(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.taxpayer.last_name_kana == "ヤマダ"
        assert cfg.taxpayer.first_name_kana == "タロウ"

    def test_taxpayer_personal_info(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.taxpayer.gender == "male"
        assert cfg.taxpayer.date_of_birth == "1990-01-15"
        assert cfg.taxpayer.phone == "03-1234-5678"

    def test_address_fields(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.address.postal_code == "100-0001"
        assert cfg.address.prefecture == "東京都"
        assert cfg.address.city == "千代田区"
        assert cfg.address.street == "丸の内1-1-1"
        assert cfg.address.building == "テストビル3F"

    def test_business_fields(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.business.trade_name == "テスト屋"
        assert cfg.business.industry_type == "情報通信業"
        assert cfg.business.business_description == "ソフトウェア開発"
        assert cfg.business.establishment_year == 2020

    def test_filing_fields(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.filing.submission_method == "e-tax"
        assert cfg.filing.return_type == "blue"
        assert cfg.filing.blue_return_deduction == 650_000
        assert cfg.filing.electronic_bookkeeping is True
        assert cfg.filing.tax_office_name == "麹町税務署"

    def test_output_dir(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.output_dir == "./output"


class TestMissingConfigFile:
    """存在しないファイルパスで FileNotFoundError が発生することを確認。"""

    def test_raises_file_not_found(self, tmp_path):
        missing_path = str(tmp_path / "nonexistent.yaml")
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config(missing_path)

    def test_error_message_includes_path(self, tmp_path):
        missing_path = str(tmp_path / "nonexistent.yaml")
        with pytest.raises(FileNotFoundError, match="nonexistent.yaml"):
            load_config(missing_path)


class TestDefaultValues:
    """セクションが省略された場合にデフォルト値が適用されることを確認。"""

    def test_default_tax_year(self):
        cfg = ShinkokuConfig()
        assert cfg.tax_year == 2025

    def test_default_db_path(self):
        cfg = ShinkokuConfig()
        assert cfg.db_path == "./shinkoku.db"

    def test_default_output_dir(self):
        cfg = ShinkokuConfig()
        assert cfg.output_dir == "./output"

    def test_default_taxpayer_empty_strings(self):
        cfg = ShinkokuConfig()
        assert cfg.taxpayer.last_name == ""
        assert cfg.taxpayer.first_name == ""
        assert cfg.taxpayer.last_name_kana == ""
        assert cfg.taxpayer.first_name_kana == ""
        assert cfg.taxpayer.phone == ""

    def test_default_taxpayer_none_fields(self):
        cfg = ShinkokuConfig()
        assert cfg.taxpayer.my_number is None
        assert cfg.taxpayer.gender is None
        assert cfg.taxpayer.date_of_birth is None

    def test_default_taxpayer_status_fields(self):
        cfg = ShinkokuConfig()
        assert cfg.taxpayer.widow_status == "none"
        assert cfg.taxpayer.disability_status == "none"
        assert cfg.taxpayer.working_student is False

    def test_default_address_empty(self):
        cfg = ShinkokuConfig()
        assert cfg.address.postal_code == ""
        assert cfg.address.prefecture == ""
        assert cfg.address.city == ""
        assert cfg.address.street == ""
        assert cfg.address.building == ""
        assert cfg.address.jan1_address is None

    def test_default_business_address_none(self):
        cfg = ShinkokuConfig()
        assert cfg.business_address is None

    def test_default_business_empty(self):
        cfg = ShinkokuConfig()
        assert cfg.business.trade_name == ""
        assert cfg.business.industry_type == ""
        assert cfg.business.business_description == ""
        assert cfg.business.establishment_year is None

    def test_default_filing(self):
        cfg = ShinkokuConfig()
        assert cfg.filing.submission_method == "e-tax"
        assert cfg.filing.return_type == "blue"
        assert cfg.filing.blue_return_deduction == 650_000
        assert cfg.filing.electronic_bookkeeping is False
        assert cfg.filing.tax_office_name == ""

    def test_default_directory_fields_none(self):
        cfg = ShinkokuConfig()
        assert cfg.invoice_registration_number is None
        assert cfg.invoices_dir is None
        assert cfg.withholding_slips_dir is None
        assert cfg.past_returns_dir is None
        assert cfg.deductions_dir is None
        assert cfg.receipts_dir is None
        assert cfg.bank_statements_dir is None
        assert cfg.credit_card_statements_dir is None
        assert cfg.furusato_receipts_dir is None

    def test_partial_config_uses_defaults(self, tmp_path):
        """一部セクションのみ記載した場合、省略セクションはデフォルトになる。"""
        config_file = tmp_path / "partial.yaml"
        config_file.write_text(
            "tax_year: 2024\ntaxpayer:\n  last_name: 佐藤\n",
            encoding="utf-8",
        )
        cfg = load_config(str(config_file))
        assert cfg.tax_year == 2024
        assert cfg.taxpayer.last_name == "佐藤"
        assert cfg.taxpayer.first_name == ""  # デフォルト
        assert cfg.address.prefecture == ""  # address セクション省略 -> デフォルト
        assert cfg.business.trade_name == ""  # business セクション省略 -> デフォルト
        assert cfg.filing.return_type == "blue"  # filing セクション省略 -> デフォルト


class TestMyNumber:
    """マイナンバーフィールドが正しく読み込まれることを確認。"""

    def test_my_number_loaded(self, full_config_yaml):
        cfg = load_config(str(full_config_yaml))
        assert cfg.taxpayer.my_number == "123456789012"

    def test_my_number_is_string(self, full_config_yaml):
        """マイナンバーは文字列型で保持される（先頭ゼロ対応）。"""
        cfg = load_config(str(full_config_yaml))
        assert isinstance(cfg.taxpayer.my_number, str)

    def test_my_number_none_when_omitted(self, minimal_config_yaml):
        cfg = load_config(str(minimal_config_yaml))
        assert cfg.taxpayer.my_number is None

    def test_my_number_with_leading_zero(self, tmp_path):
        """先頭ゼロのマイナンバーが文字列として正しく保持される。"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            'tax_year: 2025\ndb_path: ./test.db\ntaxpayer:\n  my_number: "012345678901"\n',
            encoding="utf-8",
        )
        cfg = load_config(str(config_file))
        assert cfg.taxpayer.my_number == "012345678901"
        assert cfg.taxpayer.my_number.startswith("0")


class TestEmptyConfigFile:
    """空の YAML ファイルでもデフォルト値で読み込めることを確認。"""

    def test_empty_yaml_loads_defaults(self, tmp_path):
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("", encoding="utf-8")
        cfg = load_config(str(config_file))
        assert isinstance(cfg, ShinkokuConfig)
        assert cfg.tax_year == 2025
        assert cfg.db_path == "./shinkoku.db"
