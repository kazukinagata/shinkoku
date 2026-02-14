"""E2E test: Full income tax filing flow.

Simulates the complete flow a user would follow via the MCP server:
  1. Load scenario from YAML fixture
  2. Initialize DB (ledger_init)
  3. Register journal entries (ledger_add_journals_batch)
  4. Generate reports (trial balance, PL, BS)
  5. Calculate income tax
  6. Generate PDFs
  7. Verify final tax_due matches expected value from scenario
"""

import os

from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journals_batch,
    ledger_trial_balance,
    ledger_pl,
    ledger_bs,
)
from shinkoku.tools.tax_calc import calc_income_tax
from shinkoku.tools.document import (
    generate_income_tax_pdf,
    generate_bs_pl_pdf,
    generate_deduction_detail_pdf,
)
from shinkoku.models import (
    JournalEntry,
    JournalLine,
    IncomeTaxInput,
    PLResult,
    PLItem,
    BSResult,
    BSItem,
)


class TestIncomeTaxFullFlow:
    """End-to-end income tax filing flow."""

    def test_full_income_tax_flow(self, tmp_path, scenario):
        """Complete flow: scenario -> DB -> journals -> PL/BS -> tax -> PDFs."""
        fiscal_year = scenario["scenario"]["fiscal_year"]
        taxpayer_name = scenario["scenario"]["taxpayer_name"]

        # ==============================
        # Step 1: Initialize DB
        # ==============================
        db_path = str(tmp_path / "shinkoku.db")
        init_result = ledger_init(fiscal_year=fiscal_year, db_path=db_path)
        assert init_result["status"] == "ok"
        assert init_result["accounts_loaded"] > 40

        # ==============================
        # Step 2: Register journal entries from scenario
        # ==============================
        entries = []

        # Revenue entries (debit: 普通預金, credit: 売上)
        for rev in scenario["business"]["revenues"]:
            entries.append(
                JournalEntry(
                    date=rev["date"],
                    description=rev["description"],
                    source="manual",
                    lines=[
                        JournalLine(side="debit", account_code="1002", amount=rev["amount"]),
                        JournalLine(side="credit", account_code="4001", amount=rev["amount"]),
                    ],
                )
            )

        # Expense entries (debit: expense account, credit: 普通預金)
        for exp in scenario["business"]["expenses"]:
            entries.append(
                JournalEntry(
                    date=exp["date"],
                    description=exp["description"],
                    source="manual",
                    lines=[
                        JournalLine(
                            side="debit", account_code=exp["account_code"], amount=exp["amount"]
                        ),
                        JournalLine(side="credit", account_code="1002", amount=exp["amount"]),
                    ],
                )
            )

        batch_result = ledger_add_journals_batch(
            db_path=db_path,
            fiscal_year=fiscal_year,
            entries=entries,
        )
        assert batch_result["status"] == "ok"
        total_entries = len(scenario["business"]["revenues"]) + len(
            scenario["business"]["expenses"]
        )
        assert batch_result["count"] == total_entries

        # ==============================
        # Step 3: Generate financial reports
        # ==============================
        # Trial balance
        tb = ledger_trial_balance(db_path=db_path, fiscal_year=fiscal_year)
        assert tb["status"] == "ok"
        assert tb["total_debit"] == tb["total_credit"]

        # P/L
        pl = ledger_pl(db_path=db_path, fiscal_year=fiscal_year)
        assert pl["status"] == "ok"
        assert pl["total_revenue"] == scenario["business"]["total_revenue"]
        assert pl["total_expense"] == scenario["business"]["total_expense"]
        expected_net = scenario["business"]["total_revenue"] - scenario["business"]["total_expense"]
        assert pl["net_income"] == expected_net

        # B/S
        bs = ledger_bs(db_path=db_path, fiscal_year=fiscal_year)
        assert bs["status"] == "ok"
        assert bs["total_assets"] == bs["total_liabilities"] + bs["total_equity"]

        # ==============================
        # Step 4: Calculate income tax
        # ==============================
        tax_result = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=fiscal_year,
                salary_income=scenario["salary"]["income"],
                business_revenue=pl["total_revenue"],
                business_expenses=pl["total_expense"],
                blue_return_deduction=scenario["business"]["blue_return_deduction"],
                furusato_nozei=scenario["deductions"]["furusato_nozei"],
                withheld_tax=scenario["salary"]["withheld_tax"],
            )
        )

        # Verify against expected values from scenario
        expected = scenario["expected"]["income_tax"]
        assert tax_result.salary_income_after_deduction == expected["salary_income_after_deduction"]
        assert tax_result.business_income == expected["business_income"]
        assert tax_result.total_income == expected["total_income"]
        assert tax_result.total_income_deductions == expected["total_income_deductions"]
        assert tax_result.taxable_income == expected["taxable_income"]
        assert tax_result.income_tax_base == expected["income_tax_base"]
        assert tax_result.total_tax_credits == expected["total_tax_credits"]
        assert tax_result.income_tax_after_credits == expected["income_tax_after_credits"]
        assert tax_result.reconstruction_tax == expected["reconstruction_tax"]
        assert tax_result.total_tax == expected["total_tax"]
        assert tax_result.tax_due == expected["tax_due"]

        # ==============================
        # Step 5: Generate PDFs
        # ==============================
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Income tax PDF
        income_tax_path = generate_income_tax_pdf(
            tax_result=tax_result,
            output_path=str(output_dir / "income_tax.pdf"),
            taxpayer_name=taxpayer_name,
        )
        assert os.path.exists(income_tax_path)
        assert os.path.getsize(income_tax_path) > 100

        # BS/PL PDF
        pl_result = PLResult(
            fiscal_year=fiscal_year,
            revenues=[
                PLItem(
                    account_code=r["account_code"],
                    account_name=r["account_name"],
                    amount=r["amount"],
                )
                for r in pl["revenues"]
            ],
            expenses=[
                PLItem(
                    account_code=e["account_code"],
                    account_name=e["account_name"],
                    amount=e["amount"],
                )
                for e in pl["expenses"]
            ],
            total_revenue=pl["total_revenue"],
            total_expense=pl["total_expense"],
            net_income=pl["net_income"],
        )

        bs_result = BSResult(
            fiscal_year=fiscal_year,
            assets=[
                BSItem(
                    account_code=a["account_code"],
                    account_name=a["account_name"],
                    amount=a["amount"],
                )
                for a in bs["assets"]
            ],
            liabilities=[
                BSItem(
                    account_code=li["account_code"],
                    account_name=li["account_name"],
                    amount=li["amount"],
                )
                for li in bs["liabilities"]
            ],
            equity=[
                BSItem(
                    account_code=e["account_code"],
                    account_name=e["account_name"],
                    amount=e["amount"],
                )
                for e in bs["equity"]
            ],
            total_assets=bs["total_assets"],
            total_liabilities=bs["total_liabilities"],
            total_equity=bs["total_equity"],
        )

        bs_pl_path = generate_bs_pl_pdf(
            pl_data=pl_result,
            bs_data=bs_result,
            output_path=str(output_dir / "bs_pl.pdf"),
            taxpayer_name=taxpayer_name,
        )
        assert os.path.exists(bs_pl_path)
        assert os.path.getsize(bs_pl_path) > 100

        # Deduction detail PDF
        if tax_result.deductions_detail:
            deduction_path = generate_deduction_detail_pdf(
                deductions=tax_result.deductions_detail,
                fiscal_year=fiscal_year,
                output_path=str(output_dir / "deduction_detail.pdf"),
                taxpayer_name=taxpayer_name,
            )
            assert os.path.exists(deduction_path)

        # Verify all PDFs have valid headers
        for pdf_name in ["income_tax.pdf", "bs_pl.pdf"]:
            pdf_path = output_dir / pdf_name
            with open(pdf_path, "rb") as f:
                assert f.read(5) == b"%PDF-"

    def test_tax_due_positive_means_payment(self, tmp_path, scenario):
        """Verify positive tax_due means the taxpayer owes money."""
        fiscal_year = scenario["scenario"]["fiscal_year"]

        tax_result = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=fiscal_year,
                salary_income=scenario["salary"]["income"],
                business_revenue=scenario["business"]["total_revenue"],
                business_expenses=scenario["business"]["total_expense"],
                blue_return_deduction=scenario["business"]["blue_return_deduction"],
                furusato_nozei=scenario["deductions"]["furusato_nozei"],
                withheld_tax=scenario["salary"]["withheld_tax"],
            )
        )

        # In this scenario, tax_due should be positive (payment required)
        expected_tax_due = scenario["expected"]["income_tax"]["tax_due"]
        assert tax_result.tax_due == expected_tax_due
        assert tax_result.tax_due > 0, "This scenario expects a payment (not refund)"

    def test_refund_scenario(self, tmp_path):
        """Verify negative tax_due means a refund."""
        tax_result = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=1_000_000,
                business_expenses=0,
                furusato_nozei=30_000,
                housing_loan_balance=25_000_000,
                withheld_tax=128_200,
            )
        )

        # This matches test scenario 5 from unit tests
        # total_income=3,910,000 → basic=680,000 (336万超〜489万)
        # taxable=3,202,000, tax=222,700, credits=175,000, after=47,700
        # reconstruction=1,001, total=48,700, due=48,700-128,200=-79,500
        assert tax_result.tax_due == -79_500
        assert tax_result.tax_due < 0, "This scenario expects a refund"

    def test_all_integer_amounts_in_flow(self, tmp_path, scenario):
        """Verify all amounts remain int throughout the E2E flow."""
        fiscal_year = scenario["scenario"]["fiscal_year"]
        db_path = str(tmp_path / "int_check.db")
        ledger_init(fiscal_year=fiscal_year, db_path=db_path)

        entries = []
        for rev in scenario["business"]["revenues"]:
            entries.append(
                JournalEntry(
                    date=rev["date"],
                    description=rev["description"],
                    lines=[
                        JournalLine(side="debit", account_code="1002", amount=rev["amount"]),
                        JournalLine(side="credit", account_code="4001", amount=rev["amount"]),
                    ],
                )
            )
        for exp in scenario["business"]["expenses"]:
            entries.append(
                JournalEntry(
                    date=exp["date"],
                    description=exp["description"],
                    lines=[
                        JournalLine(
                            side="debit", account_code=exp["account_code"], amount=exp["amount"]
                        ),
                        JournalLine(side="credit", account_code="1002", amount=exp["amount"]),
                    ],
                )
            )

        ledger_add_journals_batch(db_path=db_path, fiscal_year=fiscal_year, entries=entries)

        pl = ledger_pl(db_path=db_path, fiscal_year=fiscal_year)
        assert isinstance(pl["total_revenue"], int)
        assert isinstance(pl["total_expense"], int)
        assert isinstance(pl["net_income"], int)

        tax_result = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=fiscal_year,
                salary_income=scenario["salary"]["income"],
                business_revenue=pl["total_revenue"],
                business_expenses=pl["total_expense"],
                withheld_tax=scenario["salary"]["withheld_tax"],
            )
        )

        for field_name in [
            "salary_income_after_deduction",
            "business_income",
            "total_income",
            "total_income_deductions",
            "taxable_income",
            "income_tax_base",
            "total_tax_credits",
            "income_tax_after_credits",
            "reconstruction_tax",
            "total_tax",
            "withheld_tax",
            "tax_due",
        ]:
            value = getattr(tax_result, field_name)
            assert isinstance(value, int), f"{field_name} is {type(value).__name__}, expected int"
