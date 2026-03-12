"""住宅ローン控除 重複適用（中古購入＋リフォーム同時）のテスト。"""

from __future__ import annotations

import pytest

from shinkoku.models import HousingLoanDetail
from shinkoku.tools.tax_calc import (
    calc_housing_loan_credit,
    calc_housing_loan_credit_dual,
    calc_deductions,
)


def _make_detail(
    housing_type: str = "used",
    housing_category: str = "general",
    year_end_balance: int = 15_151_931,
    dual_application_group: str | None = "loan-01",
    cost_for_proration: int = 0,
    is_new_construction: bool = False,
) -> HousingLoanDetail:
    """テスト用の HousingLoanDetail を作成するヘルパー。"""
    return HousingLoanDetail(
        housing_type=housing_type,
        housing_category=housing_category,
        move_in_date="2025-04-01",
        year_end_balance=year_end_balance,
        is_new_construction=is_new_construction,
        dual_application_group=dual_application_group,
        cost_for_proration=cost_for_proration,
    )


class TestCalcHousingLoanCreditDual:
    """calc_housing_loan_credit_dual() のテスト。"""

    def test_basic_proration(self):
        """計画の計算例と一致すること。

        購入価格: 42,800,000円、リフォーム費用: 5,000,000円
        年末残高: 15,151,931円、住宅性能: 一般住宅
        """
        purchase = _make_detail(
            housing_type="used",
            cost_for_proration=42_800_000,
        )
        renovation = _make_detail(
            housing_type="renovation",
            cost_for_proration=5_000_000,
        )

        total_credit, entries = calc_housing_loan_credit_dual([purchase, renovation])

        # 按分後残高の検証
        assert entries[0].prorated_balance == 15_151_931 * 42_800_000 // 47_800_000
        # 端数調整: リフォーム分 = 年末残高 - 購入分
        assert entries[1].prorated_balance == 15_151_931 - entries[0].prorated_balance
        # 合計が元の年末残高と一致
        assert entries[0].prorated_balance + entries[1].prorated_balance == 15_151_931

        # 限度額は一般中古住宅で2,000万 → 按分後残高はそれ以下なので制限なし
        assert entries[0].capped_balance == entries[0].prorated_balance
        assert entries[1].capped_balance == entries[1].prorated_balance

        # 控除額の検証（100円未満切捨）
        expected_purchase_credit = entries[0].capped_balance * 7 // 1000 // 100 * 100
        expected_renovation_credit = entries[1].capped_balance * 7 // 1000 // 100 * 100
        assert entries[0].credit == expected_purchase_credit
        assert entries[1].credit == expected_renovation_credit

        # 合計控除額
        assert total_credit == expected_purchase_credit + expected_renovation_credit

        # 整数演算による按分結果の照合
        # 15,151,931 × 42,800,000 // 47,800,000 = 13,567,000
        # 15,151,931 - 13,567,000 = 1,584,931
        assert entries[0].prorated_balance == 13_567_000
        assert entries[1].prorated_balance == 1_584_931
        assert entries[0].credit == 94_900
        assert entries[1].credit == 11_000
        assert total_credit == 105_900

    def test_balance_exceeds_limit(self):
        """按分後残高が借入限度額を超える場合、限度額でキャップされること。"""
        # 認定住宅(中古)の限度額は3,000万
        # 按分後に3,000万を超えるケース
        purchase = _make_detail(
            housing_type="used",
            housing_category="certified",
            year_end_balance=50_000_000,
            cost_for_proration=45_000_000,
        )
        renovation = _make_detail(
            housing_type="renovation",
            housing_category="certified",
            year_end_balance=50_000_000,
            cost_for_proration=5_000_000,
        )

        total_credit, entries = calc_housing_loan_credit_dual([purchase, renovation])

        # 購入分: 50,000,000 * 45,000,000 / 50,000,000 = 45,000,000
        # → 限度額 30,000,000 でキャップ
        assert entries[0].prorated_balance == 45_000_000
        assert entries[0].balance_limit == 30_000_000
        assert entries[0].capped_balance == 30_000_000

        # リフォーム分: 50,000,000 - 45,000,000 = 5,000,000
        # → 限度額 30,000,000 以下なのでそのまま
        assert entries[1].prorated_balance == 5_000_000
        assert entries[1].capped_balance == 5_000_000

        # ㉓欄キャップ: 各控除限度額の最大 = 30,000,000 × 0.7% = 210,000
        # 購入分 credit: 30,000,000 × 7 // 1000 = 210,000 → 210,000
        # リフォーム分 credit: 5,000,000 × 7 // 1000 = 35,000 → 35,000
        # 合計 245,000 → min(245,000, 210,000) = 210,000
        assert total_credit == 210_000

    def test_rounding_sum_matches_original(self):
        """按分合計が元の年末残高と一致すること（端数調整の検証）。"""
        # 3で割り切れない年末残高
        purchase = _make_detail(
            year_end_balance=10_000_001,
            cost_for_proration=30_000_000,
        )
        renovation = _make_detail(
            housing_type="renovation",
            year_end_balance=10_000_001,
            cost_for_proration=20_000_000,
        )

        _total, entries = calc_housing_loan_credit_dual([purchase, renovation])

        assert entries[0].prorated_balance + entries[1].prorated_balance == 10_000_001

    def test_cost_for_proration_zero_raises(self):
        """cost_for_proration が 0 の場合 ValueError を送出すること。"""
        purchase = _make_detail(cost_for_proration=42_800_000)
        renovation = _make_detail(
            housing_type="renovation",
            cost_for_proration=0,
        )

        with pytest.raises(ValueError, match="cost_for_proration は正の整数が必要です"):
            calc_housing_loan_credit_dual([purchase, renovation])

    def test_single_detail_raises(self):
        """明細が1件の場合 ValueError を送出すること。"""
        single = _make_detail(cost_for_proration=42_800_000)

        with pytest.raises(ValueError, match="2件以上の明細が必要です"):
            calc_housing_loan_credit_dual([single])

    def test_total_credit_capped_by_max_annual_limit(self):
        """合計控除額が㉓欄の上限（各控除限度額の最大）でキャップされること。

        一般中古住宅: 借入限度額 2,000万、控除限度額 = 2,000万 × 0.7% = 140,000円
        年末残高 50,000,000円（購入43,000,000 + リフォーム7,000,000）
        購入分 credit: min(43,000,000, 20,000,000) × 0.7% = 140,000
        リフォーム分 credit: min(7,000,000, 20,000,000) × 0.7% = 48,900 (100円未満切捨)
        合計 188,900 → ㉓上限 140,000 でキャップ → 140,000
        """
        purchase = _make_detail(
            housing_type="used",
            housing_category="general",
            year_end_balance=50_000_000,
            cost_for_proration=43_000_000,
        )
        renovation = _make_detail(
            housing_type="renovation",
            housing_category="general",
            year_end_balance=50_000_000,
            cost_for_proration=7_000_000,
        )

        total_credit, entries = calc_housing_loan_credit_dual([purchase, renovation])

        # 按分後残高: 購入分 = 50,000,000 × 43,000,000 // 50,000,000 = 43,000,000
        assert entries[0].prorated_balance == 43_000_000
        # → 限度額 20,000,000 でキャップ
        assert entries[0].capped_balance == 20_000_000
        assert entries[0].credit == 140_000

        # リフォーム分: 50,000,000 - 43,000,000 = 7,000,000
        assert entries[1].prorated_balance == 7_000_000
        assert entries[1].capped_balance == 7_000_000
        # 7,000,000 × 7 // 1000 = 49,000 → 48,900 ではなく 49,000
        assert entries[1].credit == 49_000

        # 合計 189,000 → ㉓上限 140,000 でキャップ
        assert total_credit == 140_000

    def test_total_credit_under_cap_no_change(self):
        """合計が㉓上限以下の場合、キャップの影響がないこと。"""
        purchase = _make_detail(
            housing_type="used",
            housing_category="general",
            year_end_balance=15_151_931,
            cost_for_proration=42_800_000,
        )
        renovation = _make_detail(
            housing_type="renovation",
            housing_category="general",
            year_end_balance=15_151_931,
            cost_for_proration=5_000_000,
        )

        total_credit, entries = calc_housing_loan_credit_dual([purchase, renovation])

        # 個々のクレジット合計
        raw_sum = sum(e.credit for e in entries)
        # ㉓上限: 一般中古住宅の限度額 20,000,000 × 0.7% = 140,000
        # raw_sum = 105,900 < 140,000 なのでキャップなし
        assert total_credit == raw_sum
        assert total_credit == 105_900

    def test_proration_ratio_pct(self):
        """万分率の按分比率が正しいこと。"""
        purchase = _make_detail(cost_for_proration=42_800_000)
        renovation = _make_detail(
            housing_type="renovation",
            cost_for_proration=5_000_000,
        )

        _total, entries = calc_housing_loan_credit_dual([purchase, renovation])

        # 42,800,000 / 47,800,000 * 10000 = 8953 (切捨)
        assert entries[0].proration_ratio_pct == 42_800_000 * 10000 // 47_800_000
        assert entries[1].proration_ratio_pct == 5_000_000 * 10000 // 47_800_000


class TestCalcDeductionsDualApplication:
    """calc_deductions() の重複適用統合テスト。"""

    def test_dual_application_via_housing_loan_details(self):
        """housing_loan_details から重複適用が正しく計算されること。"""
        purchase = _make_detail(cost_for_proration=42_800_000)
        renovation = _make_detail(
            housing_type="renovation",
            cost_for_proration=5_000_000,
        )

        result = calc_deductions(
            total_income=5_000_000,
            housing_loan_details=[purchase, renovation],
        )

        hl_credits = [tc for tc in result.tax_credits if tc.type == "housing_loan"]
        assert len(hl_credits) == 1
        assert hl_credits[0].amount == 105_900

    def test_single_detail_backward_compat(self):
        """単独明細は housing_loan_detail パスと同じ結果になること。"""
        detail = HousingLoanDetail(
            housing_type="used",
            housing_category="general",
            move_in_date="2025-04-01",
            year_end_balance=15_000_000,
            is_new_construction=False,
        )

        # 従来パス
        result_old = calc_deductions(
            total_income=5_000_000,
            housing_loan_detail=detail,
        )

        # 新パス（dual_application_group なしの単独）
        detail_single = HousingLoanDetail(
            housing_type="used",
            housing_category="general",
            move_in_date="2025-04-01",
            year_end_balance=15_000_000,
            is_new_construction=False,
            dual_application_group=None,
        )
        result_new = calc_deductions(
            total_income=5_000_000,
            housing_loan_details=[detail_single],
        )

        old_hl = [tc for tc in result_old.tax_credits if tc.type == "housing_loan"]
        new_hl = [tc for tc in result_new.tax_credits if tc.type == "housing_loan"]
        assert len(old_hl) == 1
        assert len(new_hl) == 1
        assert old_hl[0].amount == new_hl[0].amount

    def test_mixed_grouped_and_single(self):
        """グループ化された明細と単独明細が混在する場合。"""
        # グループ: 購入 + リフォーム
        purchase = _make_detail(
            year_end_balance=10_000_000,
            cost_for_proration=8_000_000,
        )
        renovation = _make_detail(
            housing_type="renovation",
            year_end_balance=10_000_000,
            cost_for_proration=2_000_000,
        )
        # 単独: 別の住宅ローン（dual_application_group なし）
        standalone = HousingLoanDetail(
            housing_type="used",
            housing_category="general",
            move_in_date="2025-04-01",
            year_end_balance=5_000_000,
            is_new_construction=False,
            dual_application_group=None,
        )

        result = calc_deductions(
            total_income=5_000_000,
            housing_loan_details=[purchase, renovation, standalone],
        )

        hl_credits = [tc for tc in result.tax_credits if tc.type == "housing_loan"]
        assert len(hl_credits) == 1

        # 個別計算で検証
        dual_credit, _ = calc_housing_loan_credit_dual([purchase, renovation])
        single_credit = calc_housing_loan_credit(5_000_000, detail=standalone)
        assert hl_credits[0].amount == dual_credit + single_credit
