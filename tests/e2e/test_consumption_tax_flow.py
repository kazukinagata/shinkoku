"""E2E test: Full consumption tax filing flow.

Simulates the complete consumption tax filing flow:
  1. Load scenario from YAML fixture
  2. Initialize DB and register sales journals
  3. Calculate consumption tax (all 3 methods)
  4. Generate PDFs
  5. Verify tax amounts match expected values
"""

import os

from shinkoku.tools.ledger import (
    ledger_init,
    ledger_add_journals_batch,
)
from shinkoku.tools.tax_calc import calc_consumption_tax
from shinkoku.tools.document import generate_consumption_tax_pdf
from shinkoku.models import (
    JournalEntry,
    JournalLine,
    ConsumptionTaxInput,
)


class TestConsumptionTaxSpecial20pctFlow:
    """E2E flow for 2-wari special (invoice special provision)."""

    def test_full_special_20pct_flow(self, tmp_path, scenario):
        """Complete flow: scenario -> DB -> tax calc -> PDF for special_20pct."""
        fiscal_year = scenario["scenario"]["fiscal_year"]
        taxpayer_name = scenario["scenario"]["taxpayer_name"]
        ct_expected = scenario["expected"]["consumption_tax"]

        # ==============================
        # Step 1: Initialize DB and register sales
        # ==============================
        db_path = str(tmp_path / "consumption.db")
        ledger_init(fiscal_year=fiscal_year, db_path=db_path)

        entries = []
        for rev in scenario["business"]["revenues"]:
            entries.append(JournalEntry(
                date=rev["date"],
                description=rev["description"],
                source="manual",
                lines=[
                    JournalLine(side="debit", account_code="1002", amount=rev["amount"]),
                    JournalLine(side="credit", account_code="4001", amount=rev["amount"]),
                ],
            ))
        ledger_add_journals_batch(
            db_path=db_path, fiscal_year=fiscal_year, entries=entries,
        )

        # ==============================
        # Step 2: Calculate consumption tax (special_20pct)
        # ==============================
        taxable_sales = ct_expected["taxable_sales_10"]
        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=fiscal_year,
            method="special_20pct",
            taxable_sales_10=taxable_sales,
        ))

        # Verify against expected values
        sp = ct_expected["special_20pct"]
        assert tax_result.tax_on_sales == sp["tax_on_sales"]
        assert tax_result.tax_due == sp["tax_due"]
        assert tax_result.local_tax_due == sp["local_tax_due"]
        assert tax_result.total_due == sp["total_due"]

        # ==============================
        # Step 3: Generate PDF
        # ==============================
        output = str(tmp_path / "consumption_tax_special.pdf")
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output,
            taxpayer_name=taxpayer_name,
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

        with open(path, "rb") as f:
            assert f.read(5) == b"%PDF-"


class TestConsumptionTaxSimplifiedFlow:
    """E2E flow for simplified taxation."""

    def test_simplified_service_type5(self, tmp_path):
        """Simplified taxation with service business type (50% deemed ratio)."""
        # Service type freelance: 5,500,000 (tax-included)
        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="simplified",
            taxable_sales_10=5_500_000,
            simplified_business_type=5,
        ))

        # tax_on_sales = 5,500,000 * 10/110 = 500,000
        assert tax_result.tax_on_sales == 500_000
        # deemed purchase = 500,000 * 50% = 250,000
        # tax_due_raw = 500,000 - 250,000 = 250,000
        # national = 250,000 * 78/100 = 195,000
        assert tax_result.tax_due == 195_000
        # local = 195,000 * 22/78 = 55,000
        assert tax_result.local_tax_due == 55_000
        assert tax_result.total_due == 250_000

        # Generate PDF
        output = str(tmp_path / "consumption_tax_simplified.pdf")
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output,
            taxpayer_name="簡易太郎",
        )
        assert os.path.exists(path)

    def test_simplified_all_business_types(self, tmp_path):
        """Verify all 6 business types produce valid results."""
        sales = 11_000_000  # tax-included
        expected_ratios = {1: 90, 2: 80, 3: 70, 4: 60, 5: 50, 6: 40}

        for btype, ratio in expected_ratios.items():
            result = calc_consumption_tax(ConsumptionTaxInput(
                fiscal_year=2025,
                method="simplified",
                taxable_sales_10=sales,
                simplified_business_type=btype,
            ))

            # tax_on_sales = 11,000,000 * 10/110 = 1,000,000
            assert result.tax_on_sales == 1_000_000
            # tax_on_purchases = 1,000,000 * ratio/100
            expected_purchases = 1_000_000 * ratio // 100
            assert result.tax_on_purchases == expected_purchases
            # total_due should be positive
            assert result.total_due > 0
            # All amounts int
            assert isinstance(result.total_due, int)


class TestConsumptionTaxStandardFlow:
    """E2E flow for standard taxation."""

    def test_standard_with_purchases(self, tmp_path):
        """Standard method: sales tax - purchase tax."""
        # Initialize ledger with both sales and purchase journals
        db_path = str(tmp_path / "standard.db")
        ledger_init(fiscal_year=2025, db_path=db_path)

        entries = [
            # Sales
            JournalEntry(
                date="2025-06-30", description="コンサル売上",
                lines=[
                    JournalLine(side="debit", account_code="1002", amount=5_000_000),
                    JournalLine(side="credit", account_code="4001", amount=5_000_000),
                ],
            ),
            # Purchases (taxable)
            JournalEntry(
                date="2025-03-15", description="外注費",
                lines=[
                    JournalLine(side="debit", account_code="5230", amount=2_000_000),
                    JournalLine(side="credit", account_code="1002", amount=2_000_000),
                ],
            ),
        ]
        ledger_add_journals_batch(
            db_path=db_path, fiscal_year=2025, entries=entries,
        )

        # Tax-included amounts for consumption tax calculation
        taxable_sales_10 = 5_500_000    # 5M + 10% tax
        taxable_purchases_10 = 2_200_000  # 2M + 10% tax

        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="standard",
            taxable_sales_10=taxable_sales_10,
            taxable_purchases_10=taxable_purchases_10,
        ))

        # tax_on_sales = 5,500,000 * 10/110 = 500,000
        assert tax_result.tax_on_sales == 500_000
        # tax_on_purchases = 2,200,000 * 10/110 = 200,000
        assert tax_result.tax_on_purchases == 200_000
        # tax_due_raw = 300,000
        # national = 300,000 * 78/100 = 234,000
        assert tax_result.tax_due == 234_000
        # local = 234,000 * 22/78 = 66,000
        assert tax_result.local_tax_due == 66_000
        assert tax_result.total_due == 300_000

        # Generate PDF
        output = str(tmp_path / "consumption_tax_standard.pdf")
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output,
            taxpayer_name="本則太郎",
        )
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

    def test_standard_mixed_rates(self, tmp_path):
        """Standard method with both 10% and 8% items."""
        tax_result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="standard",
            taxable_sales_10=5_500_000,
            taxable_sales_8=1_080_000,
            taxable_purchases_10=1_100_000,
            taxable_purchases_8=540_000,
        ))

        # 10% sales tax = 5,500,000 * 10/110 = 500,000
        # 8% sales tax = 1,080,000 * 8/108 = 80,000
        assert tax_result.tax_on_sales == 580_000

        # 10% purchases tax = 1,100,000 * 10/110 = 100,000
        # 8% purchases tax = 540,000 * 8/108 = 40,000
        assert tax_result.tax_on_purchases == 140_000

        assert tax_result.total_due > 0
        assert isinstance(tax_result.total_due, int)


class TestConsumptionTaxMethodComparison:
    """Compare all 3 methods for the same sales data."""

    def test_three_methods_comparison(self, tmp_path):
        """Compare special_20pct, simplified, and standard for same sales."""
        sales_10 = 5_500_000
        purchases_10 = 2_200_000

        # Method 1: special_20pct
        r1 = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="special_20pct",
            taxable_sales_10=sales_10,
        ))

        # Method 2: simplified (type 5 = service)
        r2 = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="simplified",
            taxable_sales_10=sales_10,
            simplified_business_type=5,
        ))

        # Method 3: standard
        r3 = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="standard",
            taxable_sales_10=sales_10,
            taxable_purchases_10=purchases_10,
        ))

        # All should have the same tax_on_sales
        assert r1.tax_on_sales == r2.tax_on_sales == r3.tax_on_sales

        # special_20pct should have the lowest tax_due (20% of sales tax)
        # For service type simplified: 50% of sales tax
        # Standard depends on actual purchases
        assert r1.total_due < r2.total_due

        # All amounts should be int and positive
        for r in [r1, r2, r3]:
            assert isinstance(r.total_due, int)
            assert r.total_due > 0
            assert r.method in ("special_20pct", "simplified", "standard")

        # Generate all 3 PDFs
        output_dir = tmp_path / "comparison"
        output_dir.mkdir()

        for result, method_name in [
            (r1, "special_20pct"),
            (r2, "simplified"),
            (r3, "standard"),
        ]:
            path = generate_consumption_tax_pdf(
                tax_result=result,
                output_path=str(output_dir / f"consumption_tax_{method_name}.pdf"),
                taxpayer_name="比較太郎",
            )
            assert os.path.exists(path)

    def test_truncation_rules_applied(self, tmp_path):
        """Verify national tax truncated to 100 yen, local tax truncated to 100 yen."""
        result = calc_consumption_tax(ConsumptionTaxInput(
            fiscal_year=2025,
            method="standard",
            taxable_sales_10=5_500_000,
            taxable_purchases_10=2_200_000,
        ))

        # National tax should be truncated to 100 yen
        assert result.tax_due % 100 == 0
        # Local tax should be truncated to 100 yen
        assert result.local_tax_due % 100 == 0
        # Both should be non-negative
        assert result.tax_due >= 0
        assert result.local_tax_due >= 0
