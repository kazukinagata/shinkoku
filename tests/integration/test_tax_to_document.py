"""Integration tests: Tax Calculation -> PDF Generation flow.

Verifies that tax calculation results (IncomeTaxResult, ConsumptionTaxResult)
can be passed directly to document generation functions to produce valid PDFs.
"""

import os

import pytest

from shinkoku.tools.tax_calc import calc_income_tax, calc_consumption_tax
from shinkoku.tools.document import (
    generate_income_tax_pdf,
    generate_consumption_tax_pdf,
    generate_bs_pl_pdf,
    generate_deduction_detail_pdf,
)
from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journals_batch,
    ledger_pl,
    ledger_bs,
)
from shinkoku.models import (
    IncomeTaxInput,
    ConsumptionTaxInput,
    JournalEntry,
    JournalLine,
    PLResult,
    PLItem,
    BSResult,
    BSItem,
)


class TestIncomeTaxToPdf:
    """Test income tax calculation -> PDF generation."""

    def test_income_tax_result_to_pdf(self, tmp_path):
        """calc_income_tax result directly feeds into generate_income_tax_pdf."""
        tax_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=6_000_000,
            business_revenue=3_000_000,
            business_expenses=0,
            furusato_nozei=50_000,
            withheld_tax=466_800,
        ))

        output = str(tmp_path / "income_tax.pdf")
        path = generate_income_tax_pdf(
            tax_result=tax_result,
            output_path=output,
            taxpayer_name="テスト太郎",
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

        # Verify PDF header
        with open(path, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_income_tax_with_all_deductions_to_pdf(self, tmp_path):
        """Full deductions scenario generates valid PDF."""
        tax_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=8_000_000,
            business_revenue=2_000_000,
            business_expenses=0,
            social_insurance=800_000,
            life_insurance_premium=100_000,
            furusato_nozei=100_000,
            housing_loan_balance=35_000_000,
            spouse_income=0,
            withheld_tax=720_200,
        ))

        output = str(tmp_path / "income_tax_full.pdf")
        path = generate_income_tax_pdf(
            tax_result=tax_result,
            output_path=output,
            taxpayer_name="控除太郎",
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    def test_income_tax_deduction_detail_pdf(self, tmp_path):
        """Deduction details from tax calc -> deduction detail PDF."""
        tax_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=6_000_000,
            business_revenue=3_000_000,
            social_insurance=500_000,
            life_insurance_premium=80_000,
            furusato_nozei=50_000,
            housing_loan_balance=25_000_000,
        ))

        assert tax_result.deductions_detail is not None

        output = str(tmp_path / "deduction_detail.pdf")
        path = generate_deduction_detail_pdf(
            deductions=tax_result.deductions_detail,
            fiscal_year=2025,
            output_path=output,
            taxpayer_name="控除太郎",
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100


class TestConsumptionTaxToPdf:
    """Test consumption tax calculation -> PDF generation."""

    def test_special_20pct_to_pdf(self, tmp_path):
        """2-wari special consumption tax result -> PDF."""
        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="special_20pct",
            taxable_sales_10=5_500_000,
        ))

        output = str(tmp_path / "consumption_tax_special.pdf")
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output,
            taxpayer_name="消費太郎",
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

        with open(path, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_simplified_to_pdf(self, tmp_path):
        """Simplified consumption tax result -> PDF."""
        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="simplified",
            taxable_sales_10=11_000_000,
            simplified_business_type=5,
        ))

        output = str(tmp_path / "consumption_tax_simplified.pdf")
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output,
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    def test_standard_to_pdf(self, tmp_path):
        """Standard consumption tax result -> PDF."""
        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="standard",
            taxable_sales_10=5_500_000,
            taxable_purchases_10=2_200_000,
        ))

        output = str(tmp_path / "consumption_tax_standard.pdf")
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output,
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100


class TestLedgerToPdf:
    """Test ledger PL/BS -> PDF generation."""

    def _setup_ledger(self, tmp_path):
        """Create a ledger with data and return db_path."""
        db_path = str(tmp_path / "ledger.db")
        ledger_init(fiscal_year=2025, db_path=db_path)

        entries = [
            JournalEntry(
                date="2025-01-31", description="売上",
                lines=[
                    JournalLine(side="debit", account_code="1002", amount=5_000_000),
                    JournalLine(side="credit", account_code="4001", amount=5_000_000),
                ],
            ),
            JournalEntry(
                date="2025-06-30", description="雑収入",
                lines=[
                    JournalLine(side="debit", account_code="1002", amount=100_000),
                    JournalLine(side="credit", account_code="4110", amount=100_000),
                ],
            ),
            JournalEntry(
                date="2025-02-28", description="通信費",
                lines=[
                    JournalLine(side="debit", account_code="5140", amount=120_000),
                    JournalLine(side="credit", account_code="1002", amount=120_000),
                ],
            ),
            JournalEntry(
                date="2025-03-31", description="家賃",
                lines=[
                    JournalLine(side="debit", account_code="5250", amount=600_000),
                    JournalLine(side="credit", account_code="1002", amount=600_000),
                ],
            ),
            JournalEntry(
                date="2025-01-01", description="元入金",
                lines=[
                    JournalLine(side="debit", account_code="1001", amount=300_000),
                    JournalLine(side="credit", account_code="3001", amount=300_000),
                ],
            ),
        ]
        ledger_add_journals_batch(db_path=db_path, fiscal_year=2025, entries=entries)
        return db_path

    def test_ledger_pl_to_pdf(self, tmp_path):
        """PL data from ledger -> BS/PL PDF."""
        db_path = self._setup_ledger(tmp_path)
        pl_data = ledger_pl(db_path=db_path, fiscal_year=2025)

        # Convert ledger PL dict to PLResult model
        pl_result = PLResult(
            fiscal_year=2025,
            revenues=[
                PLItem(
                    account_code=r["account_code"],
                    account_name=r["account_name"],
                    amount=r["amount"],
                )
                for r in pl_data["revenues"]
            ],
            expenses=[
                PLItem(
                    account_code=e["account_code"],
                    account_name=e["account_name"],
                    amount=e["amount"],
                )
                for e in pl_data["expenses"]
            ],
            total_revenue=pl_data["total_revenue"],
            total_expense=pl_data["total_expense"],
            net_income=pl_data["net_income"],
        )

        output = str(tmp_path / "pl_only.pdf")
        path = generate_bs_pl_pdf(
            pl_data=pl_result,
            bs_data=None,
            output_path=output,
            taxpayer_name="帳簿太郎",
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    def test_ledger_bs_pl_to_pdf(self, tmp_path):
        """Both PL and BS from ledger -> multi-page PDF."""
        db_path = self._setup_ledger(tmp_path)
        pl_data = ledger_pl(db_path=db_path, fiscal_year=2025)
        bs_data = ledger_bs(db_path=db_path, fiscal_year=2025)

        pl_result = PLResult(
            fiscal_year=2025,
            revenues=[
                PLItem(
                    account_code=r["account_code"],
                    account_name=r["account_name"],
                    amount=r["amount"],
                )
                for r in pl_data["revenues"]
            ],
            expenses=[
                PLItem(
                    account_code=e["account_code"],
                    account_name=e["account_name"],
                    amount=e["amount"],
                )
                for e in pl_data["expenses"]
            ],
            total_revenue=pl_data["total_revenue"],
            total_expense=pl_data["total_expense"],
            net_income=pl_data["net_income"],
        )

        bs_result = BSResult(
            fiscal_year=2025,
            assets=[
                BSItem(
                    account_code=a["account_code"],
                    account_name=a["account_name"],
                    amount=a["amount"],
                )
                for a in bs_data["assets"]
            ],
            liabilities=[
                BSItem(
                    account_code=l["account_code"],
                    account_name=l["account_name"],
                    amount=l["amount"],
                )
                for l in bs_data["liabilities"]
            ],
            equity=[
                BSItem(
                    account_code=e["account_code"],
                    account_name=e["account_name"],
                    amount=e["amount"],
                )
                for e in bs_data["equity"]
            ],
            total_assets=bs_data["total_assets"],
            total_liabilities=bs_data["total_liabilities"],
            total_equity=bs_data["total_equity"],
        )

        output = str(tmp_path / "bs_pl.pdf")
        path = generate_bs_pl_pdf(
            pl_data=pl_result,
            bs_data=bs_result,
            output_path=output,
            taxpayer_name="帳簿太郎",
        )

        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

        with open(path, "rb") as f:
            assert f.read(5) == b"%PDF-"


class TestFullTaxDocumentSet:
    """Test generating a complete set of tax documents from calculation results."""

    def test_generate_all_documents(self, tmp_path):
        """Generate income tax, consumption tax, BS/PL, and deduction PDFs."""
        # Income tax
        income_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=6_000_000,
            business_revenue=3_000_000,
            social_insurance=500_000,
            furusato_nozei=50_000,
            withheld_tax=466_800,
        ))

        # Consumption tax
        consumption_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="special_20pct",
            taxable_sales_10=3_300_000,
        ))

        # Generate all PDFs
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        paths = []

        p1 = generate_income_tax_pdf(
            tax_result=income_result,
            output_path=str(output_dir / "income_tax.pdf"),
            taxpayer_name="テスト太郎",
        )
        paths.append(p1)

        p2 = generate_consumption_tax_pdf(
            tax_result=consumption_result,
            output_path=str(output_dir / "consumption_tax.pdf"),
            taxpayer_name="テスト太郎",
        )
        paths.append(p2)

        if income_result.deductions_detail:
            p3 = generate_deduction_detail_pdf(
                deductions=income_result.deductions_detail,
                fiscal_year=2025,
                output_path=str(output_dir / "deduction_detail.pdf"),
                taxpayer_name="テスト太郎",
            )
            paths.append(p3)

        # Verify all PDFs exist and are non-empty
        for path in paths:
            assert os.path.exists(path), f"PDF not found: {path}"
            assert os.path.getsize(path) > 100, f"PDF too small: {path}"

        # Verify at least income tax + consumption tax + deduction detail
        assert len(paths) == 3
