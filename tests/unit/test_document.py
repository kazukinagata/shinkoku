"""Tests for document generation module."""

import os
import pytest
from shinkoku.tools.document import (
    generate_bs_pl_pdf,
    generate_income_tax_pdf,
    generate_consumption_tax_pdf,
    generate_deduction_detail_pdf,
)
from shinkoku.models import (
    PLResult,
    PLItem,
    BSResult,
    BSItem,
    IncomeTaxResult,
    ConsumptionTaxResult,
    DeductionsResult,
    DeductionItem,
)


@pytest.fixture
def sample_pl():
    """Sample P/L result for PDF generation."""
    return PLResult(
        fiscal_year=2025,
        revenues=[
            PLItem(account_code="4001", account_name="売上", amount=5_000_000),
            PLItem(account_code="4110", account_name="雑収入", amount=100_000),
        ],
        expenses=[
            PLItem(account_code="5140", account_name="通信費", amount=120_000),
            PLItem(account_code="5250", account_name="地代家賃", amount=600_000),
            PLItem(account_code="5200", account_name="減価償却費", amount=200_000),
            PLItem(account_code="5190", account_name="消耗品費", amount=80_000),
        ],
        total_revenue=5_100_000,
        total_expense=1_000_000,
        net_income=4_100_000,
    )


@pytest.fixture
def sample_bs():
    """Sample B/S result for PDF generation."""
    return BSResult(
        fiscal_year=2025,
        assets=[
            BSItem(account_code="1001", account_name="現金", amount=500_000),
            BSItem(account_code="1002", account_name="普通預金", amount=3_000_000),
            BSItem(account_code="1010", account_name="売掛金", amount=200_000),
            BSItem(account_code="1130", account_name="工具器具備品", amount=800_000),
        ],
        liabilities=[
            BSItem(account_code="2030", account_name="未払金", amount=100_000),
        ],
        equity=[
            BSItem(account_code="3001", account_name="元入金", amount=300_000),
            BSItem(account_code="3020", account_name="控除前所得金額", amount=4_100_000),
        ],
        total_assets=4_500_000,
        total_liabilities=100_000,
        total_equity=4_400_000,
    )


class TestGenerateBsPl:
    """Test blue return BS/PL PDF generation."""

    def test_generates_pdf_file(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        assert os.path.exists(result)
        assert result == output

    def test_pdf_not_empty(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        size = os.path.getsize(output)
        assert size > 100  # PDF should have some content

    def test_pdf_starts_with_magic(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        with open(output, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_with_taxpayer_name(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
            taxpayer_name="テスト太郎",
        )
        assert os.path.exists(result)

    def test_creates_parent_directories(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "nested" / "dir" / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_pl_only(self, tmp_path, sample_pl):
        output = str(tmp_path / "pl_only.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=None,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_returns_string_path(self, tmp_path, sample_pl, sample_bs):
        output = str(tmp_path / "bs_pl.pdf")
        result = generate_bs_pl_pdf(
            pl_data=sample_pl,
            bs_data=sample_bs,
            output_path=output,
        )
        assert isinstance(result, str)


# ============================================================
# Task 19: Income Tax PDF
# ============================================================


@pytest.fixture
def sample_income_tax():
    """Sample income tax result for PDF generation."""
    return IncomeTaxResult(
        fiscal_year=2025,
        salary_income_after_deduction=4_360_000,
        business_income=2_350_000,
        total_income=6_710_000,
        total_income_deductions=928_000,
        taxable_income=5_782_000,
        income_tax_base=728_900,
        total_tax_credits=0,
        income_tax_after_credits=728_900,
        reconstruction_tax=15_306,
        total_tax=744_200,
        withheld_tax=466_800,
        tax_due=277_400,
        deductions_detail=DeductionsResult(
            income_deductions=[
                DeductionItem(type="basic", name="基礎控除", amount=880_000),
                DeductionItem(type="furusato_nozei", name="寄附金控除", amount=48_000),
            ],
            tax_credits=[],
            total_income_deductions=928_000,
            total_tax_credits=0,
        ),
    )


class TestGenerateIncomeTaxPdf:
    def test_generates_pdf_file(self, tmp_path, sample_income_tax):
        output = str(tmp_path / "income_tax.pdf")
        result = generate_income_tax_pdf(
            tax_result=sample_income_tax,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_pdf_starts_with_magic(self, tmp_path, sample_income_tax):
        output = str(tmp_path / "income_tax.pdf")
        generate_income_tax_pdf(tax_result=sample_income_tax, output_path=output)
        with open(output, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_with_taxpayer_name(self, tmp_path, sample_income_tax):
        output = str(tmp_path / "income_tax.pdf")
        result = generate_income_tax_pdf(
            tax_result=sample_income_tax,
            output_path=output,
            taxpayer_name="確定太郎",
        )
        assert os.path.exists(result)

    def test_not_empty(self, tmp_path, sample_income_tax):
        output = str(tmp_path / "income_tax.pdf")
        generate_income_tax_pdf(tax_result=sample_income_tax, output_path=output)
        assert os.path.getsize(output) > 100


# ============================================================
# Task 19: Consumption Tax PDF
# ============================================================


@pytest.fixture
def sample_consumption_tax():
    return ConsumptionTaxResult(
        fiscal_year=2025,
        method="special_20pct",
        taxable_sales_total=5_500_000,
        tax_on_sales=500_000,
        tax_on_purchases=400_000,
        tax_due=78_000,
        local_tax_due=22_000,
        total_due=100_000,
    )


class TestGenerateConsumptionTaxPdf:
    def test_generates_pdf_file(self, tmp_path, sample_consumption_tax):
        output = str(tmp_path / "consumption_tax.pdf")
        result = generate_consumption_tax_pdf(
            tax_result=sample_consumption_tax,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_pdf_starts_with_magic(self, tmp_path, sample_consumption_tax):
        output = str(tmp_path / "consumption_tax.pdf")
        generate_consumption_tax_pdf(
            tax_result=sample_consumption_tax,
            output_path=output,
        )
        with open(output, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_with_taxpayer_name(self, tmp_path, sample_consumption_tax):
        output = str(tmp_path / "consumption_tax.pdf")
        result = generate_consumption_tax_pdf(
            tax_result=sample_consumption_tax,
            output_path=output,
            taxpayer_name="消費太郎",
        )
        assert os.path.exists(result)


# ============================================================
# Task 19: Deduction Detail PDF
# ============================================================


@pytest.fixture
def sample_deductions():
    return DeductionsResult(
        income_deductions=[
            DeductionItem(type="basic", name="基礎控除", amount=880_000),
            DeductionItem(type="social_insurance", name="社会保険料控除", amount=800_000),
            DeductionItem(type="life_insurance", name="生命保険料控除", amount=40_000),
            DeductionItem(
                type="furusato_nozei", name="寄附金控除", amount=48_000, details="ふるさと納税"
            ),
        ],
        tax_credits=[
            DeductionItem(type="housing_loan", name="住宅ローン控除", amount=245_000),
        ],
        total_income_deductions=1_768_000,
        total_tax_credits=245_000,
    )


class TestGenerateDeductionDetailPdf:
    def test_generates_pdf_file(self, tmp_path, sample_deductions):
        output = str(tmp_path / "deduction_detail.pdf")
        result = generate_deduction_detail_pdf(
            deductions=sample_deductions,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_pdf_starts_with_magic(self, tmp_path, sample_deductions):
        output = str(tmp_path / "deduction_detail.pdf")
        generate_deduction_detail_pdf(
            deductions=sample_deductions,
            fiscal_year=2025,
            output_path=output,
        )
        with open(output, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_with_taxpayer_name(self, tmp_path, sample_deductions):
        output = str(tmp_path / "deduction_detail.pdf")
        result = generate_deduction_detail_pdf(
            deductions=sample_deductions,
            fiscal_year=2025,
            output_path=output,
            taxpayer_name="控除太郎",
        )
        assert os.path.exists(result)

    def test_empty_deductions(self, tmp_path):
        output = str(tmp_path / "deduction_empty.pdf")
        empty = DeductionsResult(
            income_deductions=[],
            tax_credits=[],
            total_income_deductions=0,
            total_tax_credits=0,
        )
        result = generate_deduction_detail_pdf(
            deductions=empty,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_creates_parent_dirs(self, tmp_path, sample_deductions):
        output = str(tmp_path / "a" / "b" / "detail.pdf")
        result = generate_deduction_detail_pdf(
            deductions=sample_deductions,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)


# ============================================================
# Medical Expense Detail PDF
# ============================================================


class TestGenerateMedicalExpenseDetailPdf:
    def test_generates_pdf_file(self, tmp_path):
        from shinkoku.tools.document import generate_medical_expense_detail_pdf

        output = str(tmp_path / "medical.pdf")
        expenses = [
            {
                "medical_institution": "○○病院",
                "patient_name": "太郎",
                "amount": 50_000,
                "insurance_reimbursement": 10_000,
            },
            {
                "medical_institution": "△△歯科",
                "patient_name": "太郎",
                "amount": 30_000,
                "insurance_reimbursement": 0,
            },
        ]
        result = generate_medical_expense_detail_pdf(
            expenses=expenses,
            fiscal_year=2025,
            total_income=5_000_000,
            output_path=output,
            taxpayer_name="テスト太郎",
        )
        assert os.path.exists(result)

    def test_pdf_starts_with_magic(self, tmp_path):
        from shinkoku.tools.document import generate_medical_expense_detail_pdf

        output = str(tmp_path / "medical.pdf")
        result = generate_medical_expense_detail_pdf(
            expenses=[{"medical_institution": "病院", "patient_name": "花子", "amount": 20_000}],
            fiscal_year=2025,
            output_path=output,
        )
        with open(result, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_empty_expenses(self, tmp_path):
        from shinkoku.tools.document import generate_medical_expense_detail_pdf

        output = str(tmp_path / "medical_empty.pdf")
        result = generate_medical_expense_detail_pdf(
            expenses=[],
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_max_15_lines(self, tmp_path):
        from shinkoku.tools.document import generate_medical_expense_detail_pdf

        output = str(tmp_path / "medical_max.pdf")
        expenses = [
            {"medical_institution": f"病院{i}", "patient_name": "太郎", "amount": 10_000 * (i + 1)}
            for i in range(20)
        ]
        result = generate_medical_expense_detail_pdf(
            expenses=expenses,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_low_income_threshold(self, tmp_path):
        """Medical deduction threshold is 5% of income when income < 2M."""
        from shinkoku.tools.document import generate_medical_expense_detail_pdf

        output = str(tmp_path / "medical_low.pdf")
        result = generate_medical_expense_detail_pdf(
            expenses=[{"medical_institution": "病院", "patient_name": "太郎", "amount": 150_000}],
            fiscal_year=2025,
            total_income=1_000_000,
            output_path=output,
        )
        assert os.path.exists(result)


# ============================================================
# Rent Detail PDF
# ============================================================


class TestGenerateRentDetailPdf:
    def test_generates_pdf_file(self, tmp_path):
        from shinkoku.tools.document import generate_rent_detail_pdf

        output = str(tmp_path / "rent.pdf")
        details = [
            {
                "usage": "自宅兼事務所",
                "property_type": "事務所",
                "landlord_name": "○○不動産",
                "landlord_address": "東京都渋谷区1-1-1",
                "monthly_rent": 100_000,
                "annual_rent": 1_200_000,
                "business_ratio": 40,
            },
        ]
        result = generate_rent_detail_pdf(
            rent_details=details,
            fiscal_year=2025,
            output_path=output,
            taxpayer_name="テスト太郎",
        )
        assert os.path.exists(result)

    def test_pdf_starts_with_magic(self, tmp_path):
        from shinkoku.tools.document import generate_rent_detail_pdf

        output = str(tmp_path / "rent.pdf")
        result = generate_rent_detail_pdf(
            rent_details=[{"usage": "事務所", "landlord_name": "A", "monthly_rent": 50_000}],
            fiscal_year=2025,
            output_path=output,
        )
        with open(result, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_empty_details(self, tmp_path):
        from shinkoku.tools.document import generate_rent_detail_pdf

        output = str(tmp_path / "rent_empty.pdf")
        result = generate_rent_detail_pdf(
            rent_details=[],
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_multiple_properties(self, tmp_path):
        from shinkoku.tools.document import generate_rent_detail_pdf

        output = str(tmp_path / "rent_multi.pdf")
        details = [
            {
                "usage": "事務所",
                "property_type": "事務所",
                "landlord_name": f"不動産{i}",
                "monthly_rent": 80_000 + i * 10_000,
                "annual_rent": (80_000 + i * 10_000) * 12,
                "business_ratio": 100,
            }
            for i in range(4)
        ]
        result = generate_rent_detail_pdf(
            rent_details=details,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_max_5_lines(self, tmp_path):
        from shinkoku.tools.document import generate_rent_detail_pdf

        output = str(tmp_path / "rent_max.pdf")
        details = [
            {"usage": f"用途{i}", "landlord_name": f"大家{i}", "monthly_rent": 50_000}
            for i in range(8)
        ]
        result = generate_rent_detail_pdf(
            rent_details=details,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)


# ============================================================
# Housing Loan Detail PDF
# ============================================================


class TestGenerateHousingLoanDetailPdf:
    def test_generates_pdf_new_certified(self, tmp_path):
        from shinkoku.tools.document import generate_housing_loan_detail_pdf

        output = str(tmp_path / "housing.pdf")
        detail = {
            "housing_type": "new_custom",
            "housing_category": "certified",
            "move_in_date": "2025-03-15",
            "year_end_balance": 40_000_000,
            "is_new_construction": True,
        }
        result = generate_housing_loan_detail_pdf(
            housing_detail=detail,
            credit_amount=280_000,
            fiscal_year=2025,
            output_path=output,
            taxpayer_name="住宅太郎",
        )
        assert os.path.exists(result)

    def test_pdf_starts_with_magic(self, tmp_path):
        from shinkoku.tools.document import generate_housing_loan_detail_pdf

        output = str(tmp_path / "housing.pdf")
        result = generate_housing_loan_detail_pdf(
            housing_detail={"housing_type": "resale", "housing_category": "general"},
            credit_amount=100_000,
            fiscal_year=2025,
            output_path=output,
        )
        with open(result, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_used_general(self, tmp_path):
        from shinkoku.tools.document import generate_housing_loan_detail_pdf

        output = str(tmp_path / "housing_used.pdf")
        detail = {
            "housing_type": "used",
            "housing_category": "general",
            "move_in_date": "2025-06-01",
            "year_end_balance": 15_000_000,
            "is_new_construction": False,
        }
        result = generate_housing_loan_detail_pdf(
            housing_detail=detail,
            credit_amount=105_000,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_balance_over_limit(self, tmp_path):
        """Year-end balance exceeding the limit is capped."""
        from shinkoku.tools.document import generate_housing_loan_detail_pdf

        output = str(tmp_path / "housing_over.pdf")
        detail = {
            "housing_type": "new_subdivision",
            "housing_category": "general",
            "year_end_balance": 50_000_000,
            "is_new_construction": True,
        }
        result = generate_housing_loan_detail_pdf(
            housing_detail=detail,
            credit_amount=210_000,  # 30_000_000 * 0.007
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)

    def test_empty_detail(self, tmp_path):
        from shinkoku.tools.document import generate_housing_loan_detail_pdf

        output = str(tmp_path / "housing_empty.pdf")
        result = generate_housing_loan_detail_pdf(
            housing_detail={},
            credit_amount=0,
            fiscal_year=2025,
            output_path=output,
        )
        assert os.path.exists(result)


# ============================================================
# Income Tax PDF with New Fields (business_withheld, estimated, loss_carryforward)
# ============================================================


class TestIncomeTaxPdfWithNewFields:
    def test_with_business_withheld_tax(self, tmp_path):
        output = str(tmp_path / "income_tax_bw.pdf")
        tax_result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=0,
            business_income=5_000_000,
            total_income=5_000_000,
            total_income_deductions=880_000,
            taxable_income=4_120_000,
            income_tax_base=396_500,
            total_tax_credits=0,
            income_tax_after_credits=396_500,
            reconstruction_tax=8_326,
            total_tax=404_800,
            withheld_tax=0,
            tax_due=304_800,
            business_withheld_tax=100_000,
        )
        result = generate_income_tax_pdf(tax_result=tax_result, output_path=output)
        assert os.path.exists(result)

    def test_with_estimated_tax_payment(self, tmp_path):
        output = str(tmp_path / "income_tax_est.pdf")
        tax_result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=0,
            business_income=8_000_000,
            total_income=8_000_000,
            total_income_deductions=880_000,
            taxable_income=7_120_000,
            income_tax_base=1_013_600,
            total_tax_credits=0,
            income_tax_after_credits=1_013_600,
            reconstruction_tax=21_285,
            total_tax=1_034_800,
            withheld_tax=0,
            tax_due=534_800,
            estimated_tax_payment=500_000,
        )
        result = generate_income_tax_pdf(tax_result=tax_result, output_path=output)
        assert os.path.exists(result)

    def test_with_loss_carryforward(self, tmp_path):
        output = str(tmp_path / "income_tax_loss.pdf")
        tax_result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=0,
            business_income=3_000_000,
            total_income=3_000_000,
            total_income_deductions=880_000,
            taxable_income=2_120_000,
            income_tax_base=114_500,
            total_tax_credits=0,
            income_tax_after_credits=114_500,
            reconstruction_tax=2_404,
            total_tax=116_900,
            withheld_tax=0,
            tax_due=116_900,
            loss_carryforward_applied=1_000_000,
        )
        result = generate_income_tax_pdf(tax_result=tax_result, output_path=output)
        assert os.path.exists(result)

    def test_with_all_new_fields(self, tmp_path):
        output = str(tmp_path / "income_tax_all.pdf")
        tax_result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=4_000_000,
            business_income=3_000_000,
            total_income=7_000_000,
            total_income_deductions=1_500_000,
            taxable_income=5_500_000,
            income_tax_base=672_500,
            total_tax_credits=200_000,
            income_tax_after_credits=472_500,
            reconstruction_tax=9_922,
            total_tax=482_400,
            withheld_tax=200_000,
            tax_due=32_400,
            business_withheld_tax=50_000,
            estimated_tax_payment=200_000,
            loss_carryforward_applied=500_000,
        )
        result = generate_income_tax_pdf(
            tax_result=tax_result, output_path=output, taxpayer_name="全フィールド太郎"
        )
        assert os.path.exists(result)
