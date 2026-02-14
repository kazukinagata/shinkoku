"""Tests for separate_tax module (分離課税: 株式・FX)."""

from __future__ import annotations

from shinkoku.models import SeparateTaxInput
from shinkoku.tools.separate_tax import calc_separate_tax


FISCAL_YEAR = 2025


class TestBasicStockGain:
    """Basic stock gain: 20.315% = income 15% + residential 5% + reconstruction 0.315%."""

    def test_stock_gain_1m(self):
        inp = SeparateTaxInput(fiscal_year=FISCAL_YEAR, stock_gains=1_000_000)
        result = calc_separate_tax(inp)

        # 所得税 15%
        assert result.stock_income_tax == 1_000_000 * 15 // 100  # 150,000
        # 住民税 5%
        assert result.stock_residential_tax == 1_000_000 * 5 // 100  # 50,000
        # 復興特別所得税 = 所得税 * 2.1% (整数演算)
        assert result.stock_reconstruction_tax == 150_000 * 21 // 1000  # 3,150
        # 合計
        assert result.stock_total_tax == 150_000 + 50_000 + 3_150  # 203,150
        assert result.stock_taxable_income == 1_000_000
        assert result.stock_net_gain == 1_000_000

    def test_all_amounts_are_int(self):
        inp = SeparateTaxInput(fiscal_year=FISCAL_YEAR, stock_gains=1_000_000)
        result = calc_separate_tax(inp)

        assert isinstance(result.stock_income_tax, int)
        assert isinstance(result.stock_residential_tax, int)
        assert isinstance(result.stock_reconstruction_tax, int)
        assert isinstance(result.stock_total_tax, int)


class TestStockLossOffsetsDividend:
    """損益通算: 株式譲渡損と分離課税配当を相殺。"""

    def test_loss_fully_offsets_dividend(self):
        """損失500,000 > 配当300,000 -> 配当課税0、オフセット300,000。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=0,
            stock_losses=500_000,
            stock_dividend_separate=300_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_net_gain == -500_000
        assert result.stock_dividend_offset == 300_000
        # 配当300,000 - オフセット300,000 = 課税0
        assert result.stock_taxable_income == 0
        assert result.stock_total_tax == 0

    def test_loss_partially_offsets_dividend(self):
        """損失200,000 < 配当300,000 -> 配当課税100,000。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=0,
            stock_losses=200_000,
            stock_dividend_separate=300_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_dividend_offset == 200_000
        assert result.stock_taxable_income == 100_000
        expected_income_tax = 100_000 * 15 // 100  # 15,000
        assert result.stock_income_tax == expected_income_tax

    def test_gain_and_dividend_combined(self):
        """譲渡益あり: 譲渡益 + 配当が課税ベース。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=500_000,
            stock_losses=0,
            stock_dividend_separate=200_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_net_gain == 500_000
        assert result.stock_dividend_offset == 0
        assert result.stock_taxable_income == 700_000


class TestStockLossCarryforward:
    """繰越損失の適用（3年繰越）。"""

    def test_carryforward_reduces_taxable(self):
        """gains=1,000,000, carryforward=400,000 -> taxable=600,000。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=1_000_000,
            stock_loss_carryforward=400_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_taxable_income == 600_000
        assert result.stock_loss_carryforward_used == 400_000
        assert result.stock_income_tax == 600_000 * 15 // 100  # 90,000
        assert result.stock_residential_tax == 600_000 * 5 // 100  # 30,000
        assert result.stock_reconstruction_tax == 90_000 * 21 // 1000  # 1,890

    def test_carryforward_exceeds_gain(self):
        """繰越損失 > 譲渡益: 課税所得0。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=300_000,
            stock_loss_carryforward=500_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_taxable_income == 0
        assert result.stock_loss_carryforward_used == 300_000
        assert result.stock_total_tax == 0


class TestStockWithheldTaxDeduction:
    """源泉徴収済み税額の差引。"""

    def test_withheld_deducted_from_total(self):
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=1_000_000,
            stock_withheld_income_tax=150_000,
            stock_withheld_residential_tax=50_000,
        )
        result = calc_separate_tax(inp)

        expected_total = 150_000 + 50_000 + (150_000 * 21 // 1000)  # 203,150
        assert result.stock_total_tax == expected_total
        assert result.stock_withheld_total == 200_000
        # due = total - withheld
        assert result.stock_tax_due == expected_total - 200_000  # 3,150

    def test_withheld_exceeds_tax_results_in_negative_due(self):
        """源泉徴収 > 税額: due < 0（還付）。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=100_000,
            stock_withheld_income_tax=100_000,
            stock_withheld_residential_tax=50_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_withheld_total == 150_000
        assert result.stock_tax_due < 0  # 還付


class TestBasicFxGain:
    """FX gains: 同率20.315%、源泉徴収なし。"""

    def test_fx_gain_500k(self):
        inp = SeparateTaxInput(fiscal_year=FISCAL_YEAR, fx_gains=500_000)
        result = calc_separate_tax(inp)

        expected_income = 500_000 * 15 // 100  # 75,000
        expected_residential = 500_000 * 5 // 100  # 25,000
        expected_reconstruction = expected_income * 21 // 1000  # 1,575

        assert result.fx_taxable_income == 500_000
        assert result.fx_income_tax == expected_income
        assert result.fx_residential_tax == expected_residential
        assert result.fx_reconstruction_tax == expected_reconstruction
        assert result.fx_total_tax == expected_income + expected_residential + expected_reconstruction
        # FX は源泉徴収なし → due = total
        assert result.fx_tax_due == result.fx_total_tax

    def test_fx_net_income_reflects_expenses(self):
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            fx_gains=500_000,
            fx_expenses=100_000,
        )
        result = calc_separate_tax(inp)

        assert result.fx_net_income == 400_000
        assert result.fx_taxable_income == 400_000


class TestFxLossCarryforward:
    """FX繰越損失の適用。"""

    def test_carryforward_reduces_taxable(self):
        """fx_gains=500,000, carryforward=200,000 -> taxable=300,000。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            fx_gains=500_000,
            fx_loss_carryforward=200_000,
        )
        result = calc_separate_tax(inp)

        assert result.fx_taxable_income == 300_000
        assert result.fx_loss_carryforward_used == 200_000
        assert result.fx_income_tax == 300_000 * 15 // 100  # 45,000

    def test_carryforward_exceeds_gain(self):
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            fx_gains=200_000,
            fx_loss_carryforward=500_000,
        )
        result = calc_separate_tax(inp)

        assert result.fx_taxable_income == 0
        assert result.fx_loss_carryforward_used == 200_000
        assert result.fx_total_tax == 0


class TestCombinedStockAndFx:
    """Stock + FX: separate pools, no cross-offset."""

    def test_separate_pools(self):
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=1_000_000,
            fx_gains=500_000,
        )
        result = calc_separate_tax(inp)

        # Stock tax
        stock_income = 1_000_000 * 15 // 100
        stock_residential = 1_000_000 * 5 // 100
        stock_reconstruction = stock_income * 21 // 1000
        stock_total = stock_income + stock_residential + stock_reconstruction

        # FX tax
        fx_income = 500_000 * 15 // 100
        fx_residential = 500_000 * 5 // 100
        fx_reconstruction = fx_income * 21 // 1000
        fx_total = fx_income + fx_residential + fx_reconstruction

        assert result.stock_total_tax == stock_total
        assert result.fx_total_tax == fx_total
        assert result.total_separate_tax == stock_total + fx_total

    def test_stock_loss_does_not_offset_fx(self):
        """株式損失がFX利益を相殺しないことを確認。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=0,
            stock_losses=1_000_000,
            fx_gains=500_000,
        )
        result = calc_separate_tax(inp)

        # FX is unaffected by stock loss
        assert result.fx_taxable_income == 500_000
        assert result.fx_total_tax > 0
        # Stock has no taxable income
        assert result.stock_taxable_income == 0
        assert result.stock_total_tax == 0


class TestZeroGains:
    """Zero gains -> zero tax."""

    def test_all_zero(self):
        inp = SeparateTaxInput(fiscal_year=FISCAL_YEAR)
        result = calc_separate_tax(inp)

        assert result.stock_taxable_income == 0
        assert result.stock_total_tax == 0
        assert result.stock_tax_due == 0
        assert result.fx_taxable_income == 0
        assert result.fx_total_tax == 0
        assert result.fx_tax_due == 0
        assert result.total_separate_tax == 0

    def test_zero_gains_with_carryforward(self):
        """繰越損失があっても利益0なら税額0。"""
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_loss_carryforward=500_000,
            fx_loss_carryforward=300_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_taxable_income == 0
        assert result.stock_loss_carryforward_used == 0
        assert result.fx_taxable_income == 0
        assert result.fx_loss_carryforward_used == 0
        assert result.total_separate_tax == 0


class TestNetLoss:
    """Net loss -> zero taxable income."""

    def test_stock_net_loss(self):
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            stock_gains=200_000,
            stock_losses=500_000,
        )
        result = calc_separate_tax(inp)

        assert result.stock_net_gain == -300_000
        assert result.stock_taxable_income == 0
        assert result.stock_total_tax == 0

    def test_fx_net_loss(self):
        inp = SeparateTaxInput(
            fiscal_year=FISCAL_YEAR,
            fx_gains=100_000,
            fx_expenses=400_000,
        )
        result = calc_separate_tax(inp)

        assert result.fx_net_income == -300_000
        assert result.fx_taxable_income == 0
        assert result.fx_total_tax == 0
