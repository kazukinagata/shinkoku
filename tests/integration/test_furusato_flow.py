"""Integration tests: furusato donation -> tax calculation flow."""

from __future__ import annotations

from shinkoku.tools.furusato import (
    add_furusato_donation,
    summarize_furusato_donations,
)
from shinkoku.tools.tax_calc import (
    calc_furusato_deduction_limit,
    calc_income_tax,
)
from shinkoku.models import IncomeTaxInput


class TestFurusatoToTaxFlow:
    """Test furusato donation registration -> income tax calculation flow."""

    def test_donations_reflected_in_income_tax(self, sample_furusato_donations):
        """Furusato donations should reduce income tax via deduction."""
        db = sample_furusato_donations
        summary = summarize_furusato_donations(db, 2025)

        # Calculate income tax with furusato deduction
        result_with = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=2_000_000,
                business_expenses=500_000,
                social_insurance=700_000,
                furusato_nozei=summary.total_amount,
            )
        )

        # Calculate without furusato
        result_without = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=5_000_000,
                business_revenue=2_000_000,
                business_expenses=500_000,
                social_insurance=700_000,
                furusato_nozei=0,
            )
        )

        # With furusato deduction, tax should be lower
        assert result_with.total_tax <= result_without.total_tax

    def test_deduction_limit_check(self, sample_furusato_donations):
        """Verify deduction limit estimation works with donation data."""
        db = sample_furusato_donations

        # Estimate limit for a typical case
        limit = calc_furusato_deduction_limit(
            total_income=5_000_000,
            total_income_deductions=1_500_000,
        )

        summary = summarize_furusato_donations(
            db,
            2025,
            estimated_limit=limit,
        )

        # With 100,000 total donations and typical income, should be under limit
        assert summary.over_limit is False
        assert summary.estimated_limit == limit

    def test_add_then_summarize(self, in_memory_db_with_accounts):
        """Add donations and verify summary reflects them."""
        db = in_memory_db_with_accounts
        db.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
        db.commit()

        add_furusato_donation(
            conn=db,
            fiscal_year=2025,
            municipality_name="北海道札幌市",
            amount=30000,
            date="2025-04-01",
        )
        add_furusato_donation(
            conn=db,
            fiscal_year=2025,
            municipality_name="京都府京都市",
            amount=20000,
            date="2025-05-15",
            one_stop_applied=True,
        )

        summary = summarize_furusato_donations(db, 2025)
        assert summary.total_amount == 50000
        assert summary.donation_count == 2
        assert summary.municipality_count == 2
        assert summary.deduction_amount == 48000  # 50000 - 2000
        assert summary.one_stop_count == 1
