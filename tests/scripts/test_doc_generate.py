"""Tests for doc_generate.py CLI script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = PROJECT_ROOT / "skills" / "document" / "scripts" / "doc_generate.py"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=60,
    )


# ============================================================
# Helper
# ============================================================


def _write_input(tmp_path: Path, data: dict) -> Path:
    f = tmp_path / "input.json"
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return f


def _assert_pdf_output(result, output_path: str) -> dict:
    """共通アサーション: 終了コード0、output_path が存在。"""
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "output_path" in output
    assert Path(output["output_path"]).exists(), f"PDF not found: {output['output_path']}"
    return output


# ============================================================
# bs-pl
# ============================================================


def test_bs_pl_pl_only(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "bs_pl.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "pl_revenues": [
                {"account_code": "4100", "account_name": "売上高", "amount": 3_000_000}
            ],
            "pl_expenses": [
                {"account_code": "5100", "account_name": "通信費", "amount": 120_000},
                {"account_code": "5200", "account_name": "地代家賃", "amount": 600_000},
            ],
        },
    )
    result = _run(
        SCRIPT,
        "bs-pl",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    output = _assert_pdf_output(result, output_pdf)
    assert output["pages"] == 1


def test_bs_pl_with_bs(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "bs_pl.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "pl_revenues": [
                {"account_code": "4100", "account_name": "売上高", "amount": 3_000_000}
            ],
            "pl_expenses": [{"account_code": "5100", "account_name": "通信費", "amount": 120_000}],
            "bs_assets": [{"account_code": "1100", "account_name": "現金", "amount": 500_000}],
            "bs_liabilities": [],
            "bs_equity": [{"account_code": "3100", "account_name": "元入金", "amount": 500_000}],
        },
    )
    result = _run(
        SCRIPT,
        "bs-pl",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    output = _assert_pdf_output(result, output_pdf)
    assert output["pages"] == 2


# ============================================================
# income-tax
# ============================================================


def test_income_tax(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "income_tax.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income_after_deduction": 3_500_000,
            "business_income": 1_350_000,
            "total_income": 4_850_000,
            "total_income_deductions": 1_500_000,
            "taxable_income": 3_350_000,
            "income_tax_base": 237_500,
            "total_tax_credits": 0,
            "income_tax_after_credits": 237_500,
            "reconstruction_tax": 4_987,
            "total_tax": 242_400,
            "withheld_tax": 100_000,
            "tax_due": 142_400,
        },
    )
    result = _run(
        SCRIPT,
        "income-tax",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# consumption-tax
# ============================================================


def test_consumption_tax(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "consumption_tax.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "method": "special_20pct",
            "taxable_sales_total": 5_500_000,
            "tax_on_sales": 500_000,
            "tax_on_purchases": 400_000,
            "tax_due": 78_000,
            "local_tax_due": 22_000,
            "total_due": 100_000,
        },
    )
    result = _run(
        SCRIPT,
        "consumption-tax",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# medical-expense
# ============================================================


def test_medical_expense(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "medical_expense.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "expenses": [
                {
                    "medical_institution": "ABC病院",
                    "patient_name": "山田太郎",
                    "amount": 150_000,
                    "insurance_reimbursement": 0,
                },
            ],
            "total_income": 5_000_000,
        },
    )
    result = _run(
        SCRIPT,
        "medical-expense",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# housing-loan
# ============================================================


def test_housing_loan(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "housing_loan.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "housing_detail": {
                "housing_type": "new_custom",
                "housing_category": "certified",
                "move_in_date": "2024-03-15",
                "year_end_balance": 30_000_000,
                "is_new_construction": True,
            },
            "credit_amount": 210_000,
        },
    )
    result = _run(
        SCRIPT,
        "housing-loan",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# schedule-3
# ============================================================


def test_schedule_3(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "schedule_3.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "stock_net_gain": 800_000,
            "stock_dividend_offset": 0,
            "stock_taxable_income": 800_000,
            "stock_loss_carryforward_used": 0,
            "stock_income_tax": 120_000,
            "stock_residential_tax": 40_000,
            "stock_reconstruction_tax": 2_520,
            "stock_total_tax": 162_520,
            "stock_withheld_total": 0,
            "stock_tax_due": 162_520,
            "fx_net_income": 0,
            "fx_taxable_income": 0,
            "fx_loss_carryforward_used": 0,
            "fx_income_tax": 0,
            "fx_residential_tax": 0,
            "fx_reconstruction_tax": 0,
            "fx_total_tax": 0,
            "fx_tax_due": 0,
            "total_separate_tax": 162_520,
        },
    )
    result = _run(
        SCRIPT,
        "schedule-3",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# schedule-4
# ============================================================


def test_schedule_4(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "schedule_4.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "losses": [
                {
                    "loss_type": "business",
                    "loss_year": 2023,
                    "amount": 500_000,
                    "used_amount": 200_000,
                },
            ],
        },
    )
    result = _run(
        SCRIPT,
        "schedule-4",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# income-expense
# ============================================================


@pytest.mark.xfail(
    reason="generate_income_expense_statement_pdf has pre-existing bug: "
    "accesses 'x' key on digit_cells coordinates that use 'x_start'",
    strict=True,
)
def test_income_expense(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "income_expense.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "pl_revenues": [
                {"account_code": "4100", "account_name": "売上高", "amount": 2_000_000}
            ],
            "pl_expenses": [{"account_code": "5100", "account_name": "通信費", "amount": 60_000}],
        },
    )
    result = _run(
        SCRIPT,
        "income-expense",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# income-tax-p2
# ============================================================


def test_income_tax_p2(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "income_tax_p2.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "income_details": [
                {
                    "type": "給与",
                    "payer": "株式会社テスト",
                    "revenue": 5_000_000,
                    "withheld": 100_000,
                },
            ],
            "social_insurance_details": [
                {"type": "健康保険", "payer": "", "amount": 300_000},
                {"type": "厚生年金", "payer": "", "amount": 400_000},
            ],
        },
    )
    result = _run(
        SCRIPT,
        "income-tax-p2",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    _assert_pdf_output(result, output_pdf)


# ============================================================
# full-set
# ============================================================


def test_full_set_minimal(tmp_path: Path) -> None:
    output_pdf = str(tmp_path / "full_set.pdf")
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income_after_deduction": 3_500_000,
            "business_income": 1_350_000,
            "total_income": 4_850_000,
            "total_income_deductions": 1_500_000,
            "taxable_income": 3_350_000,
            "income_tax_base": 237_500,
            "total_tax_credits": 0,
            "income_tax_after_credits": 237_500,
            "reconstruction_tax": 4_987,
            "total_tax": 242_400,
            "withheld_tax": 100_000,
            "tax_due": 142_400,
            "pl_revenues": [
                {"account_code": "4100", "account_name": "売上高", "amount": 3_000_000}
            ],
            "pl_expenses": [{"account_code": "5100", "account_name": "通信費", "amount": 120_000}],
        },
    )
    result = _run(
        SCRIPT,
        "full-set",
        "--input",
        str(input_file),
        "--output-path",
        output_pdf,
    )
    output = _assert_pdf_output(result, output_pdf)
    assert output["pages"] == 3  # P1 + P2 + PL


# ============================================================
# Error handling
# ============================================================


def test_missing_input_file(tmp_path: Path) -> None:
    result = _run(
        SCRIPT,
        "income-tax",
        "--input",
        str(tmp_path / "nonexistent.json"),
        "--output-path",
        str(tmp_path / "out.pdf"),
    )
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "error"


def test_no_command() -> None:
    result = _run(SCRIPT)
    assert result.returncode == 1
