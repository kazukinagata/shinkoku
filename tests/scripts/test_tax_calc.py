"""Tests for tax_calc CLI."""

from __future__ import annotations

import json
from pathlib import Path

from .conftest import run_cli


# ============================================================
# Helper
# ============================================================


def _write_input(tmp_path: Path, data: dict) -> Path:
    f = tmp_path / "input.json"
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return f


# ============================================================
# calc-deductions
# ============================================================


def test_calc_deductions_basic(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 5_000_000,
            "social_insurance": 700_000,
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "total_income_deductions" in output
    assert isinstance(output["total_income_deductions"], int)
    assert output["total_income_deductions"] > 0


def test_calc_deductions_with_furusato(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 5_000_000,
            "social_insurance": 700_000,
            "furusato_nozei": 50_000,
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # ふるさと納税控除が含まれている
    deduction_types = [d["type"] for d in output["income_deductions"]]
    assert "furusato_nozei" in deduction_types


# ============================================================
# calc-income
# ============================================================


def test_calc_income_salary_only(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 5_000_000,
            "social_insurance": 700_000,
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "taxable_income" in output
    assert isinstance(output["taxable_income"], int)
    assert output["fiscal_year"] == 2025


def test_calc_income_with_business(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 5_000_000,
            "business_revenue": 3_000_000,
            "business_expenses": 1_000_000,
            "blue_return_deduction": 650_000,
            "social_insurance": 700_000,
            "withheld_tax": 100_000,
            "business_withheld_tax": 30_000,
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["business_income"] == 3_000_000 - 1_000_000 - 650_000
    assert "tax_due" in output


# ============================================================
# calc-depreciation
# ============================================================


def test_calc_depreciation_straight_line(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "method": "straight_line",
            "acquisition_cost": 300_000,
            "useful_life": 4,
            "business_use_ratio": 100,
            "months": 12,
        },
    )
    result = run_cli("tax", "calc-depreciation", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["method"] == "straight_line"
    assert output["depreciation_amount"] == 300_000 // 4


def test_calc_depreciation_declining_balance(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "method": "declining_balance",
            "book_value": 200_000,
            "declining_rate": 500,
            "business_use_ratio": 100,
            "months": 12,
            "acquisition_cost": 300_000,
            "useful_life": 4,
        },
    )
    result = run_cli("tax", "calc-depreciation", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["method"] == "declining_balance"
    # 200,000 * 500/1000 * 100/100 * 12/12 = 100,000
    assert output["depreciation_amount"] == 100_000


def test_calc_depreciation_declining_missing_params(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "method": "declining_balance",
            "acquisition_cost": 300_000,
            "useful_life": 4,
        },
    )
    result = run_cli("tax", "calc-depreciation", "--input", str(input_file))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


# ============================================================
# calc-consumption
# ============================================================


def test_calc_consumption_special(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "method": "special_20pct",
            "taxable_sales_10": 5_500_000,
        },
    )
    result = run_cli("tax", "calc-consumption", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["method"] == "special_20pct"
    assert output["total_due"] > 0


def test_calc_consumption_simplified(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "method": "simplified",
            "taxable_sales_10": 5_500_000,
            "simplified_business_type": 5,
        },
    )
    result = run_cli("tax", "calc-consumption", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["method"] == "simplified"


# ============================================================
# calc-furusato-limit
# ============================================================


def test_calc_furusato_limit(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 5_000_000,
            "total_income_deductions": 1_500_000,
        },
    )
    result = run_cli("tax", "calc-furusato-limit", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "estimated_limit" in output
    assert isinstance(output["estimated_limit"], int)
    assert output["estimated_limit"] > 0


# ============================================================
# calc-pension
# ============================================================


def test_calc_pension_over_65(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "pension_income": 2_000_000,
            "is_over_65": True,
            "other_income": 0,
        },
    )
    result = run_cli("tax", "calc-pension", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["is_over_65"] is True
    assert output["deduction_amount"] > 0
    assert output["taxable_pension_income"] < output["pension_income"]


def test_calc_pension_under_65(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "pension_income": 1_000_000,
            "is_over_65": False,
        },
    )
    result = run_cli("tax", "calc-pension", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["is_over_65"] is False


# ============================================================
# calc-retirement
# ============================================================


def test_calc_retirement_normal(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "severance_pay": 10_000_000,
            "years_of_service": 20,
        },
    )
    result = run_cli("tax", "calc-retirement", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["severance_pay"] == 10_000_000
    assert output["years_of_service"] == 20
    # 20年 × 40万 = 800万 → 控除後200万 → 1/2 = 100万
    assert output["retirement_income_deduction"] == 8_000_000
    assert output["taxable_retirement_income"] == 1_000_000
    assert output["half_taxation_applied"] is True


def test_calc_retirement_officer(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "severance_pay": 5_000_000,
            "years_of_service": 3,
            "is_officer": True,
        },
    )
    result = run_cli("tax", "calc-retirement", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["is_officer"] is True
    # 役員等短期: 1/2なし
    assert output["half_taxation_applied"] is False


# ============================================================
# sanity-check
# ============================================================


def test_sanity_check_pass(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "input": {
                "fiscal_year": 2025,
                "business_revenue": 3_000_000,
                "business_expenses": 1_000_000,
                "blue_return_deduction": 650_000,
                "salary_income": 5_000_000,
                "withheld_tax": 100_000,
            },
            "result": {
                "fiscal_year": 2025,
                "salary_income_after_deduction": 3_560_000,
                "business_income": 1_350_000,
                "effective_blue_return_deduction": 650_000,
                "total_income": 4_910_000,
                "taxable_income": 3_000_000,
                "income_tax_base": 202_500,
                "total_tax_credits": 0,
                "income_tax_after_credits": 202_500,
                "reconstruction_tax": 4_252,
                "total_tax": 206_752,
                "withheld_tax": 100_000,
                "tax_due": 106_700,
            },
        },
    )
    result = run_cli("tax", "sanity-check", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["passed"] is True
    assert output["error_count"] == 0


def test_sanity_check_detects_error(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "input": {
                "fiscal_year": 2025,
                "business_revenue": 100_000,
                "business_expenses": 200_000,
            },
            "result": {
                "fiscal_year": 2025,
                "effective_blue_return_deduction": 50_000,
                "taxable_income": 0,
                "income_tax_base": 0,
                "income_tax_after_credits": 0,
                "reconstruction_tax": 0,
                "total_tax": 0,
                "tax_due": 0,
            },
        },
    )
    result = run_cli("tax", "sanity-check", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["passed"] is False
    assert output["error_count"] > 0
    codes = [item["code"] for item in output["items"]]
    assert "BLUE_DEDUCTION_ON_LOSS" in codes


def test_sanity_check_missing_keys(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {"fiscal_year": 2025},  # missing 'input' and 'result'
    )
    result = run_cli("tax", "sanity-check", "--input", str(input_file))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


# ============================================================
# Error handling
# ============================================================


def test_missing_input_file(tmp_path: Path) -> None:
    result = run_cli("tax", "calc-income", "--input", str(tmp_path / "nonexistent.json"))
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


def test_no_command() -> None:
    result = run_cli("tax")
    assert result.returncode == 1
