"""Tests for 特定親族特別控除 (specific relative special deduction, R7 新設)."""

import pytest

from shinkoku.models import DependentInfo
from shinkoku.tax_constants import (
    DEPENDENT_SPECIFIC,
    SPECIFIC_RELATIVE_SPECIAL_DEDUCTION_TABLE,
)
from shinkoku.tools.tax_calc import calc_dependents_deduction


def _make_dep(
    name: str = "太郎",
    birth_date: str = "2005-06-01",
    income: int = 0,
    disability: str | None = None,
) -> DependentInfo:
    """Helper: create a dependent (default: 20 years old in 2025)."""
    return DependentInfo(
        name=name,
        relationship="子",
        birth_date=birth_date,
        income=income,
        disability=disability,
    )


TAXPAYER_INCOME = 5_000_000
FISCAL_YEAR = 2025


class TestSpecificRelativeSpecialDeduction:
    """特定親族特別控除: 19〜22歳で所得58万超〜123万以下に段階的控除。"""

    def test_income_at_580000_normal_specific(self):
        """所得58万以下 → 通常の特定扶養控除63万。"""
        deps = [_make_dep(income=580_000)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 1
        assert dep_items[0].amount == DEPENDENT_SPECIFIC
        assert "特定扶養" in (dep_items[0].details or "")

    def test_income_zero_normal_specific(self):
        """所得0 → 通常の特定扶養控除63万。"""
        deps = [_make_dep(income=0)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        dep_items = [i for i in items if i.type == "dependent"]
        assert len(dep_items) == 1
        assert dep_items[0].amount == DEPENDENT_SPECIFIC

    @pytest.mark.parametrize(
        "income, expected_amount",
        [
            # 各段階の境界値テスト
            (580_001, 630_000),  # 58万超の最小値 → 63万
            (850_000, 630_000),  # 85万ちょうど → 63万
            (850_001, 610_000),  # 85万超 → 61万
            (900_000, 610_000),  # 90万ちょうど → 61万
            (900_001, 510_000),  # 90万超 → 51万
            (950_000, 510_000),  # 95万ちょうど → 51万
            (950_001, 410_000),  # 95万超 → 41万
            (1_000_000, 410_000),  # 100万ちょうど → 41万
            (1_000_001, 310_000),  # 100万超 → 31万
            (1_050_000, 310_000),  # 105万ちょうど → 31万
            (1_050_001, 210_000),  # 105万超 → 21万
            (1_100_000, 210_000),  # 110万ちょうど → 21万
            (1_100_001, 110_000),  # 110万超 → 11万
            (1_150_000, 110_000),  # 115万ちょうど → 11万
            (1_150_001, 60_000),  # 115万超 → 6万
            (1_200_000, 60_000),  # 120万ちょうど → 6万
            (1_200_001, 30_000),  # 120万超 → 3万
            (1_230_000, 30_000),  # 123万ちょうど → 3万
        ],
        ids=lambda v: f"{v}",
    )
    def test_stepped_deduction(self, income: int, expected_amount: int):
        """所得58万超〜123万: 段階的控除額。"""
        deps = [_make_dep(income=income)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        special_items = [i for i in items if i.type == "specific_relative_special"]
        assert len(special_items) == 1
        assert special_items[0].amount == expected_amount
        assert special_items[0].name == "特定親族特別控除"

    def test_income_over_1230000_no_deduction(self):
        """所得123万超 → 控除なし。"""
        deps = [_make_dep(income=1_230_001)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        assert len(items) == 0

    def test_age_18_not_eligible(self):
        """18歳（19歳未満）は特定親族特別控除の対象外。"""
        # 2025年末で18歳
        deps = [_make_dep(birth_date="2007-06-01", income=700_000)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        # 所得58万超かつ特定年齢外 → 控除なし
        assert len(items) == 0

    def test_age_23_not_eligible(self):
        """23歳以上は特定親族特別控除の対象外。"""
        # 2025年末で23歳
        deps = [_make_dep(birth_date="2002-06-01", income=700_000)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        # 所得58万超かつ特定年齢外 → 控除なし
        assert len(items) == 0

    def test_age_19_boundary(self):
        """19歳（特定年齢下限）は特定親族特別控除の対象。"""
        # 2025年末で19歳
        deps = [_make_dep(birth_date="2006-06-01", income=700_000)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        special_items = [i for i in items if i.type == "specific_relative_special"]
        assert len(special_items) == 1
        assert special_items[0].amount == 630_000  # 所得70万 ≤ 85万 → 63万

    def test_age_22_boundary(self):
        """22歳（特定年齢上限-1）は特定親族特別控除の対象。"""
        # 2025年末で22歳
        deps = [_make_dep(birth_date="2003-06-01", income=700_000)]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        special_items = [i for i in items if i.type == "specific_relative_special"]
        assert len(special_items) == 1
        assert special_items[0].amount == 630_000

    def test_disability_with_special_deduction(self):
        """障害者控除との併用: 特定親族特別控除 + 障害者控除が独立して適用される。"""
        deps = [_make_dep(income=700_000, disability="general")]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        special_items = [i for i in items if i.type == "specific_relative_special"]
        disability_items = [i for i in items if i.type == "disability"]
        assert len(special_items) == 1
        assert special_items[0].amount == 630_000
        assert len(disability_items) == 1
        assert disability_items[0].amount == 270_000

    def test_disability_special_cohabiting_with_special_deduction(self):
        """同居特別障害者控除との併用。"""
        deps = [_make_dep(income=900_000, disability="special_cohabiting")]
        items = calc_dependents_deduction(deps, TAXPAYER_INCOME, FISCAL_YEAR)
        special_items = [i for i in items if i.type == "specific_relative_special"]
        disability_items = [i for i in items if i.type == "disability"]
        assert len(special_items) == 1
        assert special_items[0].amount == 610_000  # 所得90万 → 61万
        assert len(disability_items) == 1
        assert disability_items[0].amount == 750_000

    def test_table_consistency(self):
        """テーブルの閾値が昇順であることを確認。"""
        thresholds = [t for t, _ in SPECIFIC_RELATIVE_SPECIAL_DEDUCTION_TABLE]
        assert thresholds == sorted(thresholds)
        # 控除額は逓減
        amounts = [a for _, a in SPECIFIC_RELATIVE_SPECIAL_DEDUCTION_TABLE]
        assert amounts == sorted(amounts, reverse=True)
