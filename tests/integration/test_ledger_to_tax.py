"""Integration tests: Ledger -> Trial Balance -> Tax Calculation flow.

Verifies that journal entries registered in the ledger can be
aggregated via trial balance/PL/BS and used as input for income
tax calculation with consistent results.
"""

import pytest

from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journals_batch,
    ledger_trial_balance,
    ledger_pl,
    ledger_bs,
)
from shinkoku.tools.tax_calc import calc_income_tax
from shinkoku.models import (
    JournalEntry,
    JournalLine,
    IncomeTaxInput,
)


def _build_business_ledger(tmp_path):
    """Set up a ledger with realistic freelance business data.

    Revenue: 5,000,000 (売上)
    Expenses:
      - 通信費: 120,000
      - 地代家賃: 600,000
      - 消耗品費: 80,000
      - 減価償却費: 200,000
    Total Expenses: 1,000,000
    Net Income: 4,000,000
    """
    db_path = str(tmp_path / "business.db")
    ledger_init(fiscal_year=2025, db_path=db_path)

    entries = [
        # Revenue: multiple sales invoices
        JournalEntry(
            date="2025-01-31", description="1月売上",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=2_000_000),
                JournalLine(side="credit", account_code="4001", amount=2_000_000),
            ],
        ),
        JournalEntry(
            date="2025-06-30", description="6月売上",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=1_500_000),
                JournalLine(side="credit", account_code="4001", amount=1_500_000),
            ],
        ),
        JournalEntry(
            date="2025-12-31", description="12月売上",
            lines=[
                JournalLine(side="debit", account_code="1002", amount=1_500_000),
                JournalLine(side="credit", account_code="4001", amount=1_500_000),
            ],
        ),
        # Expenses
        JournalEntry(
            date="2025-01-31", description="通信費(年間)",
            lines=[
                JournalLine(side="debit", account_code="5140", amount=120_000),
                JournalLine(side="credit", account_code="1002", amount=120_000),
            ],
        ),
        JournalEntry(
            date="2025-01-31", description="家賃(年間)",
            lines=[
                JournalLine(side="debit", account_code="5250", amount=600_000),
                JournalLine(side="credit", account_code="1002", amount=600_000),
            ],
        ),
        JournalEntry(
            date="2025-03-15", description="消耗品",
            lines=[
                JournalLine(side="debit", account_code="5190", amount=80_000),
                JournalLine(side="credit", account_code="1001", amount=80_000),
            ],
        ),
        JournalEntry(
            date="2025-12-31", description="減価償却費",
            lines=[
                JournalLine(side="debit", account_code="5200", amount=200_000),
                JournalLine(side="credit", account_code="1130", amount=200_000),
            ],
        ),
        # Initial capital
        JournalEntry(
            date="2025-01-01", description="元入金",
            lines=[
                JournalLine(side="debit", account_code="1001", amount=500_000),
                JournalLine(side="credit", account_code="3001", amount=500_000),
            ],
        ),
    ]
    ledger_add_journals_batch(db_path=db_path, fiscal_year=2025, entries=entries)
    return db_path


class TestLedgerToTax:
    """Test ledger -> financial reports -> tax calculation pipeline."""

    def test_trial_balance_consistency(self, tmp_path):
        """Trial balance should have equal debit and credit totals."""
        db_path = _build_business_ledger(tmp_path)
        tb = ledger_trial_balance(db_path=db_path, fiscal_year=2025)

        assert tb["status"] == "ok"
        assert tb["total_debit"] == tb["total_credit"]
        assert tb["total_debit"] > 0

    def test_pl_matches_expected(self, tmp_path):
        """PL totals should match the known journal amounts."""
        db_path = _build_business_ledger(tmp_path)
        pl = ledger_pl(db_path=db_path, fiscal_year=2025)

        assert pl["status"] == "ok"
        assert pl["total_revenue"] == 5_000_000
        assert pl["total_expense"] == 1_000_000
        assert pl["net_income"] == 4_000_000

    def test_bs_equation_holds(self, tmp_path):
        """BS: Assets = Liabilities + Equity (including net income)."""
        db_path = _build_business_ledger(tmp_path)
        bs = ledger_bs(db_path=db_path, fiscal_year=2025)

        assert bs["status"] == "ok"
        assert bs["total_assets"] == (
            bs["total_liabilities"] + bs["total_equity"]
        )

    def test_bs_pl_net_income_match(self, tmp_path):
        """Net income from PL should be embedded in BS equity."""
        db_path = _build_business_ledger(tmp_path)
        pl = ledger_pl(db_path=db_path, fiscal_year=2025)
        bs = ledger_bs(db_path=db_path, fiscal_year=2025)

        assert bs["net_income"] == pl["net_income"]

    def test_pl_to_income_tax_calculation(self, tmp_path):
        """PL net income should flow correctly into income tax calculation.

        Scenario: Salary 6M + business revenue 5M, expenses 1M, blue return.
        Business income = 5,000,000 - 1,000,000 - 650,000 (blue) = 3,350,000
        But from ledger PL, we get net_income = 4,000,000.
        The blue return deduction is applied at the tax calc level.
        So business_income = PL net_income - blue = 4,000,000 - 650,000 = 3,350,000
        """
        db_path = _build_business_ledger(tmp_path)
        pl = ledger_pl(db_path=db_path, fiscal_year=2025)

        # Use PL data as business revenue/expense input
        # In practice, net_income from PL = revenue - expense already computed
        # For tax calc, we pass raw revenue and raw expenses
        tax_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=6_000_000,
            business_revenue=pl["total_revenue"],
            business_expenses=pl["total_expense"],
            withheld_tax=466_800,
        ))

        # Verify business income = 5M - 1M - 650K(blue) = 3,350,000
        assert tax_result.business_income == 3_350_000

        # Salary deduction for 6M = 6M * 20% + 440K = 1,640K
        # Salary income after deduction = 6M - 1,640K = 4,360K
        assert tax_result.salary_income_after_deduction == 4_360_000

        # Total income = 4,360K + 3,350K = 7,710K
        assert tax_result.total_income == 7_710_000

        # All amounts must be int
        assert isinstance(tax_result.taxable_income, int)
        assert isinstance(tax_result.total_tax, int)
        assert isinstance(tax_result.tax_due, int)

    def test_pl_to_income_tax_with_deductions(self, tmp_path):
        """Full flow with deductions: social insurance, furusato, housing loan."""
        db_path = _build_business_ledger(tmp_path)
        pl = ledger_pl(db_path=db_path, fiscal_year=2025)

        tax_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=6_000_000,
            business_revenue=pl["total_revenue"],
            business_expenses=pl["total_expense"],
            social_insurance=800_000,
            furusato_nozei=50_000,
            housing_loan_balance=25_000_000,
            withheld_tax=600_000,
        ))

        # Verify deductions were applied
        assert tax_result.total_income_deductions > 0
        assert tax_result.total_tax_credits > 0  # housing loan credit
        assert tax_result.deductions_detail is not None

        # Total tax should be less than without deductions
        tax_no_deductions = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            salary_income=6_000_000,
            business_revenue=pl["total_revenue"],
            business_expenses=pl["total_expense"],
            withheld_tax=600_000,
        ))
        assert tax_result.total_tax < tax_no_deductions.total_tax

    def test_all_amounts_integer_through_pipeline(self, tmp_path):
        """Verify int constraint across ledger -> PL -> tax pipeline."""
        db_path = _build_business_ledger(tmp_path)

        # Trial balance
        tb = ledger_trial_balance(db_path=db_path, fiscal_year=2025)
        assert isinstance(tb["total_debit"], int)
        assert isinstance(tb["total_credit"], int)
        for acct in tb["accounts"]:
            assert isinstance(acct["debit_total"], int)
            assert isinstance(acct["credit_total"], int)

        # PL
        pl = ledger_pl(db_path=db_path, fiscal_year=2025)
        assert isinstance(pl["total_revenue"], int)
        assert isinstance(pl["total_expense"], int)
        assert isinstance(pl["net_income"], int)

        # BS
        bs = ledger_bs(db_path=db_path, fiscal_year=2025)
        assert isinstance(bs["total_assets"], int)
        assert isinstance(bs["total_liabilities"], int)
        assert isinstance(bs["total_equity"], int)

        # Tax
        tax_result = calc_income_tax(IncomeTaxInput(
            fiscal_year=2025,
            business_revenue=pl["total_revenue"],
            business_expenses=pl["total_expense"],
        ))
        assert isinstance(tax_result.taxable_income, int)
        assert isinstance(tax_result.income_tax_base, int)
        assert isinstance(tax_result.reconstruction_tax, int)
        assert isinstance(tax_result.total_tax, int)
        assert isinstance(tax_result.tax_due, int)
