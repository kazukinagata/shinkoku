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
    assert "donation" in deduction_types


def _donation_record(amount: int, donation_type: str) -> dict:
    """DonationRecordRecord に必要な全フィールドを含むヘルパー."""
    return {
        "id": 1,
        "fiscal_year": 2025,
        "donation_type": donation_type,
        "recipient_name": "テスト寄附先",
        "amount": amount,
        "date": "2025-06-01",
        "receipt_number": "R-001",
        "source_file": "test.pdf",
    }


def test_calc_deductions_donation_combined(tmp_path: Path) -> None:
    """T4: ふるさと納税+その他寄附金を合算して40%上限・2,000円足切りを1回だけ適用."""
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 5_000_000,
            "social_insurance": 700_000,
            "furusato_nozei": 30_000,
            "donations": [_donation_record(20_000, "political")],
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # 合算=50,000, 40%上限=2,000,000, deduction = 50,000 - 2,000 = 48,000
    donation_items = [d for d in output["income_deductions"] if d["type"] == "donation"]
    assert len(donation_items) == 1
    assert donation_items[0]["amount"] == 48_000


def test_calc_deductions_donation_income_limit(tmp_path: Path) -> None:
    """T4: 40%上限に到達するケース."""
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 100_000,
            "social_insurance": 0,
            "furusato_nozei": 30_000,
            "donations": [_donation_record(20_000, "npo")],
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # 合算=50,000, 40%上限=40,000, deduction = 40,000 - 2,000 = 38,000
    donation_items = [d for d in output["income_deductions"] if d["type"] == "donation"]
    assert len(donation_items) == 1
    assert donation_items[0]["amount"] == 38_000


def _get_tax_credit(output: dict, credit_type: str) -> int:
    """deductions_detail.tax_credits から指定タイプの控除額を取得."""
    detail = output.get("deductions_detail") or {}
    for tc in detail.get("tax_credits", []):
        if tc["type"] == credit_type:
            return tc["amount"]
    return 0


def test_calc_income_donation_credit_cap(tmp_path: Path) -> None:
    """T3: 政治献金の税額控除に所得税額の25%キャップが適用される.

    salary 600万（限界税率20% < 30%）で税額控除が有利 → 自動選択で税額控除採用。
    political 30万のcreditは (300,000 - 2,000) * 30% = 89,400 → 25%キャップで制限。
    """
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 6_000_000,
            "social_insurance": 840_000,
            "donations": [_donation_record(300_000, "political")],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # 税額控除が25%キャップで制限されていることを確認
    income_tax_base = output["income_tax_base"]
    cap = income_tax_base * 25 // 100
    political_credit = _get_tax_credit(output, "political_donation")
    assert political_credit > 0  # 税額控除が選択されている
    assert political_credit <= cap
    assert political_credit == cap  # キャップに到達しているはず


def test_calc_income_donation_credit_no_cap(tmp_path: Path) -> None:
    """T3: 十分な所得がある場合、キャップが適用されない."""
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 10_000_000,
            "social_insurance": 1_000_000,
            "donations": [_donation_record(10_000, "political")],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # (10,000 - 2,000) * 30% = 2,400 — キャップに到達しない
    political_credit = _get_tax_credit(output, "political_donation")
    assert political_credit == 2_400


def test_calc_income_high_income_prefers_income_deduction(tmp_path: Path) -> None:
    """高所得（限界税率40%）で所得控除が有利 → 税額控除が選択されない."""
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 20_000_000,
            "social_insurance": 2_000_000,
            "donations": [_donation_record(100_000, "political")],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # 限界税率40% > 30%（税額控除率） → 所得控除が有利
    political_credit = _get_tax_credit(output, "political_donation")
    assert political_credit == 0  # 税額控除は選択されていない
    # 所得控除に donation が含まれている
    donation_items = [
        d for d in output["deductions_detail"]["income_deductions"] if d["type"] == "donation"
    ]
    assert len(donation_items) == 1


def test_calc_income_low_income_prefers_tax_credit(tmp_path: Path) -> None:
    """低所得（限界税率10%）で税額控除が有利 → 税額控除が選択される."""
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 4_000_000,
            "social_insurance": 500_000,
            "donations": [_donation_record(50_000, "political")],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # 限界税率10% < 30%（税額控除率） → 税額控除が有利
    political_credit = _get_tax_credit(output, "political_donation")
    assert political_credit > 0  # 税額控除が選択されている
    # 所得控除の donation に political 分が含まれない（ふるさと納税もないので donation なし）
    donation_items = [
        d for d in output["deductions_detail"]["income_deductions"] if d["type"] == "donation"
    ]
    assert len(donation_items) == 0


def test_calc_income_mixed_other_and_selectable(tmp_path: Path) -> None:
    """other は常に所得控除、political は自動選択."""
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 5_000_000,
            "social_insurance": 700_000,
            "donations": [
                _donation_record(30_000, "political"),
                _donation_record(20_000, "other"),
            ],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # other は常に所得控除に含まれる
    donation_items = [
        d for d in output["deductions_detail"]["income_deductions"] if d["type"] == "donation"
    ]
    assert len(donation_items) == 1
    # political は限界税率20% < 30% なので税額控除が有利
    political_credit = _get_tax_credit(output, "political_donation")
    assert political_credit > 0


def test_calc_income_group_independent_selection(tmp_path: Path) -> None:
    """political と npo が独立に選択される.

    salary 2000万（限界税率33%）: political 30% < 33% → 所得控除が有利、
    npo 40% > 33% → 税額控除が有利。グループ独立に最適選択されることを確認。
    """
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 20_000_000,
            "social_insurance": 2_000_000,
            "donations": [
                _donation_record(100_000, "political"),
                _donation_record(100_000, "npo"),
            ],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # political: 30% < 33%（限界税率） → 所得控除が有利
    political_credit = _get_tax_credit(output, "political_donation")
    assert political_credit == 0
    # npo: 40% > 33%（限界税率） → 税額控除が有利
    npo_credit = _get_tax_credit(output, "npo_donation")
    assert npo_credit > 0
    # 所得控除にも donation がある（political 分 + ふるさと納税なし → political のみ）
    donation_items = [
        d for d in output["deductions_detail"]["income_deductions"] if d["type"] == "donation"
    ]
    assert len(donation_items) == 1


def test_calc_income_npo_credit_income_cap(tmp_path: Path) -> None:
    """NPO税額控除の40%所得上限が適用される（calc-deductions で直接確認）."""
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 200_000,
            "social_insurance": 0,
            "donations": [_donation_record(500_000, "npo")],
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # total_income = 200,000, 40% = 80,000
    # npo_total = 500,000 > 80,000 → capped to 80,000
    # credit = (80,000 - 2,000) * 40% = 31,200
    npo_credits = [c for c in output["tax_credits"] if c["type"] == "npo_donation"]
    assert len(npo_credits) == 1
    assert npo_credits[0]["amount"] == 31_200


def test_calc_income_political_credit_income_cap(tmp_path: Path) -> None:
    """政治献金税額控除の40%所得上限が適用される（租特法41条の18第1項）."""
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 200_000,
            "social_insurance": 0,
            "donations": [_donation_record(500_000, "political")],
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    # total_income = 200,000, 40% = 80,000
    # political_total = 500,000 > 80,000 → capped to 80,000
    # credit = (80,000 - 2,000) * 30% = 23,400
    political_credits = [c for c in output["tax_credits"] if c["type"] == "political_donation"]
    assert len(political_credits) == 1
    assert political_credits[0]["amount"] == 23_400


def test_calc_deductions_with_political_and_npo_donations(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "total_income": 5_000_000,
            "social_insurance": 700_000,
            "donations": [
                {
                    "id": 1,
                    "fiscal_year": 2025,
                    "donation_type": "political",
                    "recipient_name": "政党A",
                    "amount": 30_000,
                    "date": "2025-05-01",
                    "receipt_number": None,
                    "source_file": None,
                },
                {
                    "id": 2,
                    "fiscal_year": 2025,
                    "donation_type": "npo",
                    "recipient_name": "NPO B",
                    "amount": 20_000,
                    "date": "2025-06-01",
                    "receipt_number": None,
                    "source_file": None,
                },
            ],
        },
    )
    result = run_cli("tax", "calc-deductions", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    deduction_types = [d["type"] for d in output["income_deductions"]]
    assert "donation" in deduction_types

    credit_types = [d["type"] for d in output["tax_credits"]]
    assert "political_donation" in credit_types
    assert "npo_donation" in credit_types


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


def test_calc_income_with_political_and_npo_donation_optimization(tmp_path: Path) -> None:
    input_file = _write_input(
        tmp_path,
        {
            "fiscal_year": 2025,
            "salary_income": 5_000_000,
            "social_insurance": 700_000,
            "donations": [
                {
                    "id": 1,
                    "fiscal_year": 2025,
                    "donation_type": "political",
                    "recipient_name": "政党A",
                    "amount": 30_000,
                    "date": "2025-05-01",
                    "receipt_number": None,
                    "source_file": None,
                },
                {
                    "id": 2,
                    "fiscal_year": 2025,
                    "donation_type": "npo",
                    "recipient_name": "NPO B",
                    "amount": 20_000,
                    "date": "2025-06-01",
                    "receipt_number": None,
                    "source_file": None,
                },
            ],
        },
    )
    result = run_cli("tax", "calc-income", "--input", str(input_file))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert "deductions_detail" in output

    # salary 500万（限界税率20%）→ political 30%、npo 40% なので税額控除が有利
    # 自動選択により tax_credits に political_donation, npo_donation が残る
    credit_types = [d["type"] for d in output["deductions_detail"]["tax_credits"]]
    assert "political_donation" in credit_types
    assert "npo_donation" in credit_types

    # 所得控除の donation には selectable な寄付が除外されている
    # （ふるさと納税がないので donation 自体がないはず）
    donation_items = [
        d for d in output["deductions_detail"]["income_deductions"] if d["type"] == "donation"
    ]
    assert len(donation_items) == 0


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
