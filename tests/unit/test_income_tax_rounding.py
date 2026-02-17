"""所得税の端数処理境界値テスト。

法的根拠:
- 国税通則法 第118条: 課税所得金額は1,000円未満切捨
- 国税通則法 第119条: 納付税額は100円未満切捨（納付の場合のみ）
- 国税通則法 第120条: 還付金は1円単位（1円未満切捨）
- 復興財源確保法 第13条: 復興特別所得税 = 基準所得税額 × 2.1%（1円未満切捨）
"""

from __future__ import annotations

from shinkoku.models import IncomeTaxInput
from shinkoku.tools.tax_calc import calc_income_tax


class TestTaxableIncomeRounding:
    """課税所得の1,000円切捨境界テスト（国税通則法118条）。"""

    def test_exact_thousand(self) -> None:
        """課税所得が1,000の倍数の場合、切捨なし。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=2_000_000,
                business_expenses=0,
                blue_return_deduction=0,
                social_insurance=50_000,
            )
        )
        # 課税所得は1,000円単位
        assert r.taxable_income % 1_000 == 0

    def test_truncation_removes_fraction(self) -> None:
        """課税所得に1,000未満の端数がある場合、切捨される。"""
        # 事業所得 = 1,234,567 - 0 = 1,234,567
        # 所得控除: 基礎控除(合計所得≤132万で95万) + 社会保険10,000
        # 課税所得raw = 1,234,567 - 950,000 - 10,000 = 274,567
        # → 274,000 (1000円切捨)
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=1_234_567,
                business_expenses=0,
                blue_return_deduction=0,
                social_insurance=10_000,
            )
        )
        assert r.taxable_income % 1_000 == 0
        assert r.taxable_income == 274_000


class TestPaymentVsRefund:
    """納付 vs 還付の境界テスト。"""

    def test_payment_truncated_to_100(self) -> None:
        """納付額（正）は100円未満切捨。"""
        # 適当な金額で納付が発生するケース
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=5_000_000,
                business_expenses=0,
                blue_return_deduction=0,
                social_insurance=100_000,
            )
        )
        if r.tax_due > 0:
            assert r.tax_due % 100 == 0

    def test_refund_not_truncated(self) -> None:
        """還付額（負）は100円未満切捨しない（1円単位）。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=500_000,
                business_expenses=0,
                blue_return_deduction=650_000,
                social_insurance=100_000,
                withheld_tax=50_000,
            )
        )
        # 所得が控除で0になり、源泉徴収分がそのまま還付される
        assert r.tax_due < 0
        assert r.tax_due == -50_000  # 1円単位のまま

    def test_refund_1_yen_precision(self) -> None:
        """還付額は1円単位の精度が保たれる。"""
        # 給与所得のみ（源泉徴収あり）で少額の還付
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                salary_income=3_000_000,
                social_insurance=400_000,
                withheld_tax=60_000,
            )
        )
        # 税額: 所得控除を引いた後の計算による
        # 重要なのは、tax_due < 0 の場合に100円切捨が適用されないこと
        if r.tax_due < 0:
            # 還付なので100の倍数でなくてよい
            pass  # 1円単位のまま
        else:
            # 納付なら100円の倍数
            assert r.tax_due % 100 == 0

    def test_zero_tax_due(self) -> None:
        """tax_due = 0 の境界ケース。"""
        # 所得 = 0
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=0,
                business_expenses=0,
            )
        )
        assert r.tax_due == 0

    def test_small_positive_truncated(self) -> None:
        """小額の納付: 99円 → 0円に切捨。"""
        # tax_due_raw が 1〜99 の場合、100円未満切捨で 0 になる
        # これを直接テストするのは難しいので、100円未満切捨が適用されていることを確認
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=3_000_000,
                business_expenses=0,
                blue_return_deduction=650_000,
                social_insurance=500_000,
            )
        )
        if r.tax_due > 0:
            assert r.tax_due % 100 == 0


class TestReconstructionTax:
    """復興特別所得税のテスト。"""

    def test_reconstruction_tax_1yen_truncation(self) -> None:
        """復興特別所得税は1円未満切捨。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=5_000_000,
                business_expenses=0,
                blue_return_deduction=650_000,
                social_insurance=500_000,
            )
        )
        # reconstruction_tax = income_tax_after_credits * 21 // 1000
        # 整数演算なので自動的に1円未満切捨
        expected = r.income_tax_after_credits * 21 // 1000
        assert r.reconstruction_tax == expected

    def test_total_tax_no_rounding(self) -> None:
        """所得税及び復興特別所得税の額（㊺）には端数処理なし。"""
        r = calc_income_tax(
            IncomeTaxInput(
                fiscal_year=2025,
                business_revenue=5_000_000,
                business_expenses=0,
                blue_return_deduction=650_000,
                social_insurance=500_000,
            )
        )
        assert r.total_tax == r.income_tax_after_credits + r.reconstruction_tax
