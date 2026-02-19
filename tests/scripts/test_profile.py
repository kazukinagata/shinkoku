"""Tests for profile CLI."""

from __future__ import annotations

import json
from pathlib import Path

from .conftest import run_cli


def run_profile(*args: str):
    return run_cli("profile", *args)


def test_get_profile(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(
        """\
tax_year: 2025
db_path: test.db
output_dir: output
taxpayer:
  last_name: 山田
  first_name: 太郎
  last_name_kana: ヤマダ
  first_name_kana: タロウ
  gender: male
  date_of_birth: "1990-01-01"
  phone: "090-1234-5678"
address:
  postal_code: "100-0001"
  prefecture: 東京都
  city: 千代田区
  street: 丸の内1-1-1
  building: ""
filing:
  return_type: blue
""",
        encoding="utf-8",
    )
    result = run_profile("--config", str(config))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["taxpayer"]["last_name"] == "山田"
    assert output["taxpayer"]["first_name"] == "太郎"
    assert output["taxpayer"]["full_name"] == "山田 太郎"
    assert output["address"]["prefecture"] == "東京都"
    assert output["tax_year"] == 2025


def test_get_profile_minimal(tmp_path: Path):
    """最小設定でもデフォルト値で動作する。"""
    config = tmp_path / "minimal.yaml"
    config.write_text("tax_year: 2025\n", encoding="utf-8")
    result = run_profile("--config", str(config))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["tax_year"] == 2025
    assert output["taxpayer"]["last_name"] == ""


def test_get_profile_with_my_number(tmp_path: Path):
    """my_number が has_my_number フラグに変換される。"""
    config = tmp_path / "config.yaml"
    config.write_text(
        """\
tax_year: 2025
taxpayer:
  last_name: 田中
  first_name: 花子
  my_number: "123456789012"
""",
        encoding="utf-8",
    )
    result = run_profile("--config", str(config))
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["taxpayer"]["has_my_number"] is True
    # my_number 自体は出力されない
    assert "my_number" not in output["taxpayer"]


def test_get_profile_config_not_found(tmp_path: Path):
    result = run_profile("--config", str(tmp_path / "nonexistent.yaml"))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


def test_no_args():
    result = run_profile()
    assert result.returncode != 0
