"""消費税計算の端数処理テスト。

法的根拠:
- 国税通則法 第118条: 課税標準額は1,000円未満切捨
- 国税通則法 第119条: 差引税額は100円未満切捨
- 消費税法 第28条: 課税標準 = 課税資産の譲渡等の対価の額
- 消費税法 第45条: 消費税額の計算
"""

from __future__ import annotations


from shinkoku.models import ConsumptionTaxInput
from shinkoku.tools.tax_calc import calc_consumption_tax


class TestTaxableBaseRounding:
    """課税標準額の1,000円未満切捨テスト（国税通則法118条）。"""

    def test_exact_thousand(self) -> None:
        """税抜金額が1,000の倍数の場合、切捨なし。"""
        # 1,100,000 (税込) → 1,000,000 (税抜) → 1,000,000 (切捨後)
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="standard", taxable_sales_10=1_100_000)
        )
        assert r.taxable_base_10 == 1_000_000

    def test_truncate_below_thousand(self) -> None:
        """税抜金額に1,000未満の端数がある場合、切捨。"""
        # 1,234,567 (税込) → 1,122,333 (税抜=1,234,567*100//110) → 1,122,000 (切捨)
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="standard", taxable_sales_10=1_234_567)
        )
        assert r.taxable_base_10 == 1_122_000

    def test_reduced_rate_base(self) -> None:
        """軽減税率8%の課税標準額。"""
        # 108,000 (税込) → 100,000 (税抜=108,000*100//108) → 100,000 (切捨)
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="standard", taxable_sales_8=108_000)
        )
        assert r.taxable_base_8 == 100_000

    def test_reduced_rate_truncation(self) -> None:
        """軽減税率8%で端数が出るケース。"""
        # 123,456 (税込) → 114,311 (税抜=123,456*100//108) → 114,000 (切捨)
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="standard", taxable_sales_8=123_456)
        )
        assert r.taxable_base_8 == 114_000

    def test_mixed_rates(self) -> None:
        """10%と8%の混在ケース。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=1_100_000,
                taxable_sales_8=108_000,
            )
        )
        assert r.taxable_base_10 == 1_000_000
        assert r.taxable_base_8 == 100_000


class TestSpecial20PctRounding:
    """2割特例の端数処理テスト。"""

    def test_iter2_case(self) -> None:
        """iter2シナリオ: 165,000円(税込10%), 2割特例。

        期待値（freee検証済み）:
        課税標準額: 150,000、消費税額(国税): 11,700
        差引税額: 2,300、地方消費税: 600、合計: 2,900
        """
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="special_20pct", taxable_sales_10=165_000)
        )
        assert r.taxable_base_10 == 150_000
        assert r.national_tax_on_sales == 11_700
        assert r.net_tax == 2_300  # 11,700 * 20% = 2,340 → 100円切捨 = 2,300
        assert r.local_tax_due == 600  # 2,300 * 22/78 = 648 → 100円切捨 = 600
        assert r.total_due == 2_900

    def test_large_sales(self) -> None:
        """大きい売上額での2割特例。"""
        # 5,500,000 (税込) → 5,000,000 (税抜) → 国税: 390,000
        # 差引: 390,000 * 20% = 78,000 (ちょうど100の倍数)
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025, method="special_20pct", taxable_sales_10=5_500_000
            )
        )
        assert r.taxable_base_10 == 5_000_000
        assert r.national_tax_on_sales == 390_000
        assert r.net_tax == 78_000
        assert r.tax_due == 78_000

    def test_tax_on_sales_equals_national(self) -> None:
        """tax_on_sales は後方互換で national_tax_on_sales と同じ。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="special_20pct", taxable_sales_10=165_000)
        )
        assert r.tax_on_sales == r.national_tax_on_sales


class TestSimplifiedRounding:
    """簡易課税の端数処理テスト。"""

    def test_service_business(self) -> None:
        """第5種（サービス業、みなし仕入率50%）。"""
        # 1,100,000 (税込) → 1,000,000 (税抜) → 国税: 78,000
        # 仕入控除: 78,000 * 50% = 39,000
        # 差引: 39,000 → 100円切捨 = 39,000
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="simplified",
                taxable_sales_10=1_100_000,
                simplified_business_type=5,
            )
        )
        assert r.net_tax == 39_000
        assert r.tax_on_purchases == 39_000

    def test_wholesale(self) -> None:
        """第1種（卸売業、みなし仕入率90%）。"""
        # 2,200,000 (税込) → 2,000,000 (税抜) → 国税: 156,000
        # 仕入控除: 156,000 * 90% = 140,400
        # 差引: 15,600 → 100円切捨 = 15,600
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="simplified",
                taxable_sales_10=2_200_000,
                simplified_business_type=1,
            )
        )
        assert r.national_tax_on_sales == 156_000
        assert r.tax_on_purchases == 140_400
        assert r.net_tax == 15_600


class TestStandardRounding:
    """本則課税の端数処理テスト。"""

    def test_plan_verification_case(self) -> None:
        """プランの検証ケース: 売上1,234,567/仕入987,654 → 合計22,300。

        旧コード: 22,400（間違い）→ 新コード: 22,300（正しい）
        """
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=1_234_567,
                taxable_purchases_10=987_654,
            )
        )
        assert r.total_due == 22_300

    def test_purchase_tax_national_rate(self) -> None:
        """仕入税額は国税率(7.8/110)で計算される。"""
        # 1,100,000 (税込仕入) → 7.8/110 * 1,100,000 = 78,000
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=2_200_000,
                taxable_purchases_10=1_100_000,
            )
        )
        assert r.tax_on_purchases == 78_000

    def test_reduced_rate_purchase(self) -> None:
        """軽減税率8%の仕入: 6.24/108。"""
        # 108,000 (税込仕入8%) → 6.24/108 * 108,000 = 6,240
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=1_100_000,
                taxable_purchases_8=108_000,
            )
        )
        assert r.tax_on_purchases == 6_240


class TestRefundCase:
    """還付が発生するケースのテスト。"""

    def test_refund_basic(self) -> None:
        """仕入税額 > 売上税額で還付が発生する。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=500_000,
                taxable_purchases_10=1_500_000,
            )
        )
        assert r.net_tax == 0
        assert r.refund_shortfall > 0
        assert r.tax_due <= 0 or r.net_tax == 0

    def test_refund_not_blocked(self) -> None:
        """旧コードの max(0,...) バグが修正されていること。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=110_000,
                taxable_purchases_10=1_100_000,
            )
        )
        # 売上国税: 100,000 * 78/1000 = 7,800 (base 100,000)
        # 仕入国税: 1,100,000 * 78/1100 = 78,000
        # 差額: 7,800 - 78,000 = -70,200 → refund
        assert r.refund_shortfall == 70_200
        assert r.net_tax == 0

    def test_refund_local_tax_negative(self) -> None:
        """還付時、地方消費税も負（還付額に含む）。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=110_000,
                taxable_purchases_10=1_100_000,
            )
        )
        assert r.local_tax_due < 0
        assert r.total_due < 0


class TestMixedRates:
    """8%軽減税率の混在テスト。"""

    def test_mixed_sales(self) -> None:
        """10%と8%が混在する売上。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="special_20pct",
                taxable_sales_10=1_100_000,
                taxable_sales_8=108_000,
            )
        )
        assert r.taxable_base_10 == 1_000_000
        assert r.taxable_base_8 == 100_000
        # 国税: 78,000 + 6,240 = 84,240
        assert r.national_tax_on_sales == 84_240

    def test_mixed_purchases(self) -> None:
        """10%と8%が混在する仕入（本則課税）。"""
        r = calc_consumption_tax(
            ConsumptionTaxInput(
                fiscal_year=2025,
                method="standard",
                taxable_sales_10=5_500_000,
                taxable_purchases_10=1_100_000,
                taxable_purchases_8=216_000,
            )
        )
        # 仕入国税10%: 1,100,000 * 78/1100 = 78,000
        # 仕入国税8%:  216,000 * 624/10800 = 12,480
        assert r.tax_on_purchases == 78_000 + 12_480


class TestZeroSales:
    """売上0のケース。"""

    def test_zero_sales(self) -> None:
        r = calc_consumption_tax(
            ConsumptionTaxInput(fiscal_year=2025, method="standard", taxable_sales_10=0)
        )
        assert r.taxable_base_10 == 0
        assert r.national_tax_on_sales == 0
        assert r.net_tax == 0
        assert r.total_due == 0
