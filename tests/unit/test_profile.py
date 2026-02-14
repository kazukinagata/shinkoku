"""Tests for profile tool — taxpayer profile loading with my_number masking."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from shinkoku.tools.profile import get_taxpayer_profile


def _write_yaml(path: Path, content: str) -> str:
    """Write YAML content to path and return its string path."""
    path.write_text(dedent(content), encoding="utf-8")
    return str(path)


@pytest.fixture
def full_config_path(tmp_path: Path) -> str:
    """Config YAML with all fields populated including my_number."""
    return _write_yaml(
        tmp_path / "full_config.yaml",
        """\
        tax_year: 2025
        db_path: ./shinkoku.db
        output_dir: ./output
        taxpayer:
          last_name: "山田"
          first_name: "太郎"
          last_name_kana: "ヤマダ"
          first_name_kana: "タロウ"
          gender: male
          date_of_birth: "1990-01-15"
          phone: "090-1234-5678"
          my_number: "123456789012"
          widow_status: none
          disability_status: none
          working_student: false
        address:
          postal_code: "100-0001"
          prefecture: "東京都"
          city: "千代田区"
          street: "千代田1-1"
          building: "テストビル101"
        business_address:
          postal_code: "150-0001"
          prefecture: "東京都"
          city: "渋谷区"
          street: "神宮前1-1"
          building: "ワークビル3F"
        business:
          trade_name: "山田開発"
          industry_type: "情報通信業"
          business_description: "ソフトウェア開発"
          establishment_year: 2020
        filing:
          submission_method: e-tax
          return_type: blue
          blue_return_deduction: 650000
          electronic_bookkeeping: true
          tax_office_name: "千代田税務署"
        """,
    )


@pytest.fixture
def config_without_my_number(tmp_path: Path) -> str:
    """Config YAML without my_number field."""
    return _write_yaml(
        tmp_path / "no_mynumber.yaml",
        """\
        tax_year: 2025
        taxpayer:
          last_name: "田中"
          first_name: "花子"
          last_name_kana: "タナカ"
          first_name_kana: "ハナコ"
        """,
    )


class TestGetTaxpayerProfileFullConfig:
    """get_taxpayer_profile with full config — verify all fields returned."""

    def test_returns_all_top_level_keys(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        expected_keys = {
            "taxpayer",
            "address",
            "business_address",
            "business",
            "filing",
            "tax_year",
            "db_path",
            "output_dir",
        }
        assert set(result.keys()) == expected_keys

    def test_taxpayer_fields(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        tp = result["taxpayer"]
        assert tp["last_name"] == "山田"
        assert tp["first_name"] == "太郎"
        assert tp["last_name_kana"] == "ヤマダ"
        assert tp["first_name_kana"] == "タロウ"
        assert tp["gender"] == "male"
        assert tp["date_of_birth"] == "1990-01-15"
        assert tp["phone"] == "090-1234-5678"
        assert tp["widow_status"] == "none"
        assert tp["disability_status"] == "none"
        assert tp["working_student"] is False

    def test_address_fields(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        addr = result["address"]
        assert addr["postal_code"] == "100-0001"
        assert addr["prefecture"] == "東京都"
        assert addr["city"] == "千代田区"
        assert addr["street"] == "千代田1-1"
        assert addr["building"] == "テストビル101"

    def test_business_address_present(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        ba = result["business_address"]
        assert ba is not None
        assert ba["postal_code"] == "150-0001"
        assert ba["prefecture"] == "東京都"
        assert ba["city"] == "渋谷区"

    def test_business_fields(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        biz = result["business"]
        assert biz["trade_name"] == "山田開発"
        assert biz["industry_type"] == "情報通信業"
        assert biz["business_description"] == "ソフトウェア開発"
        assert biz["establishment_year"] == 2020

    def test_filing_fields(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        filing = result["filing"]
        assert filing["submission_method"] == "e-tax"
        assert filing["return_type"] == "blue"
        assert filing["blue_return_deduction"] == 650000
        assert filing["electronic_bookkeeping"] is True
        assert filing["tax_office_name"] == "千代田税務署"

    def test_tax_year(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        assert result["tax_year"] == 2025

    def test_db_path(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        assert result["db_path"] == "./shinkoku.db"

    def test_output_dir(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        assert result["output_dir"] == "./output"


class TestMyNumberMasking:
    """my_number is NOT exposed in output — only has_my_number flag."""

    def test_my_number_not_in_taxpayer(self, full_config_path: str) -> None:
        """my_number must never appear as a key in the result dict."""
        result = get_taxpayer_profile(config_path=full_config_path)
        assert "my_number" not in result["taxpayer"]

    def test_my_number_value_not_in_any_output(self, full_config_path: str) -> None:
        """The actual my_number string must not appear anywhere in the output."""
        result = get_taxpayer_profile(config_path=full_config_path)
        result_str = str(result)
        assert "123456789012" not in result_str

    def test_has_my_number_true_when_present(self, full_config_path: str) -> None:
        """has_my_number=True when 12-digit my_number is provided."""
        result = get_taxpayer_profile(config_path=full_config_path)
        assert result["taxpayer"]["has_my_number"] is True

    def test_has_my_number_false_when_missing(self, config_without_my_number: str) -> None:
        """has_my_number=False when my_number is not provided."""
        result = get_taxpayer_profile(config_path=config_without_my_number)
        assert result["taxpayer"]["has_my_number"] is False

    def test_has_my_number_false_when_wrong_length(self, tmp_path: Path) -> None:
        """has_my_number=False when my_number is not exactly 12 digits."""
        path = _write_yaml(
            tmp_path / "short_mynumber.yaml",
            """\
            taxpayer:
              last_name: "佐藤"
              first_name: "次郎"
              my_number: "12345"
            """,
        )
        result = get_taxpayer_profile(config_path=path)
        assert result["taxpayer"]["has_my_number"] is False


class TestFullNameConcatenation:
    """full_name is correctly concatenated from last_name + first_name."""

    def test_full_name_with_both_names(self, full_config_path: str) -> None:
        result = get_taxpayer_profile(config_path=full_config_path)
        assert result["taxpayer"]["full_name"] == "山田 太郎"

    def test_full_name_last_name_only(self, tmp_path: Path) -> None:
        """full_name with only last_name returns just last_name (stripped)."""
        path = _write_yaml(
            tmp_path / "last_only.yaml",
            """\
            taxpayer:
              last_name: "鈴木"
              first_name: ""
            """,
        )
        result = get_taxpayer_profile(config_path=path)
        assert result["taxpayer"]["full_name"] == "鈴木"

    def test_full_name_first_name_only(self, tmp_path: Path) -> None:
        """full_name with only first_name returns just first_name (stripped)."""
        path = _write_yaml(
            tmp_path / "first_only.yaml",
            """\
            taxpayer:
              last_name: ""
              first_name: "一郎"
            """,
        )
        result = get_taxpayer_profile(config_path=path)
        assert result["taxpayer"]["full_name"] == "一郎"

    def test_full_name_both_empty(self, tmp_path: Path) -> None:
        """full_name is empty string when both names are empty."""
        path = _write_yaml(
            tmp_path / "empty_names.yaml",
            """\
            taxpayer:
              last_name: ""
              first_name: ""
            """,
        )
        result = get_taxpayer_profile(config_path=path)
        assert result["taxpayer"]["full_name"] == ""

    def test_full_name_defaults(self, tmp_path: Path) -> None:
        """full_name is empty string when taxpayer section uses defaults."""
        path = _write_yaml(
            tmp_path / "defaults.yaml",
            """\
            taxpayer: {}
            """,
        )
        result = get_taxpayer_profile(config_path=path)
        assert result["taxpayer"]["full_name"] == ""


class TestBusinessAddressOptional:
    """business_address is None when not configured."""

    def test_business_address_none_when_absent(self, config_without_my_number: str) -> None:
        result = get_taxpayer_profile(config_path=config_without_my_number)
        assert result["business_address"] is None


class TestConfigNotFound:
    """FileNotFoundError when config path does not exist."""

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        nonexistent = str(tmp_path / "does_not_exist.yaml")
        with pytest.raises(FileNotFoundError):
            get_taxpayer_profile(config_path=nonexistent)
