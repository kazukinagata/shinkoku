"""Tests for xtx BS beginning (期首) field generation."""

from __future__ import annotations

from shinkoku.models import BSItem, BSResult
from shinkoku.xtx.blue_return import build_bs_fields
from shinkoku.xtx.field_codes import (
    BS_CODES_BEGINNING,
    BS_CODES_ENDING,
    BS_FIELD_GROUPS,
    BS_LIABILITIES_BEGINNING,
)


def _make_bs_result(
    *,
    opening_assets: list[BSItem] | None = None,
    opening_liabilities: list[BSItem] | None = None,
    opening_equity: list[BSItem] | None = None,
    opening_total_assets: int | None = None,
    opening_total_liabilities: int | None = None,
    opening_total_equity: int | None = None,
) -> BSResult:
    """テスト用 BSResult を生成するヘルパー。"""
    return BSResult(
        fiscal_year=2025,
        assets=[BSItem(account_code="1001", account_name="現金", amount=500000)],
        liabilities=[BSItem(account_code="2001", account_name="買掛金", amount=100000)],
        equity=[BSItem(account_code="3001", account_name="元入金", amount=400000)],
        total_assets=500000,
        total_liabilities=100000,
        total_equity=400000,
        opening_assets=opening_assets,
        opening_liabilities=opening_liabilities,
        opening_equity=opening_equity,
        opening_total_assets=opening_total_assets,
        opening_total_liabilities=opening_total_liabilities,
        opening_total_equity=opening_total_equity,
    )


def test_build_bs_fields_with_opening():
    """期首データが設定されている場合、期首 AMG コードが出力されること。"""
    bs = _make_bs_result(
        opening_assets=[
            BSItem(account_code="1001", account_name="現金", amount=300000),
            BSItem(account_code="1002", account_name="普通預金", amount=200000),
        ],
        opening_liabilities=[
            BSItem(account_code="2001", account_name="買掛金", amount=80000),
        ],
        opening_equity=[
            BSItem(account_code="3001", account_name="元入金", amount=420000),
        ],
        opening_total_assets=500000,
        opening_total_liabilities=80000,
        opening_total_equity=420000,
    )

    fields = build_bs_fields(bs)

    # 期首資産: 現金 AMG00060, 普通預金=other_deposit AMG00090
    assert fields.get(BS_CODES_BEGINNING["cash"]) == 300000
    assert fields.get(BS_CODES_BEGINNING["other_deposit"]) == 200000
    assert fields.get(BS_CODES_BEGINNING["total_assets"]) == 500000

    # 期首負債: 買掛金
    assert fields.get(BS_LIABILITIES_BEGINNING["accounts_payable"]) == 80000

    # 期首純資産: 元入金
    assert fields.get(BS_LIABILITIES_BEGINNING["capital"]) == 420000

    # 期末もちゃんと出力されていること
    assert fields.get(BS_CODES_ENDING["cash"]) == 500000


def test_build_bs_fields_without_opening():
    """opening_*=None 時に期首コードが出ないこと。"""
    bs = _make_bs_result()

    fields = build_bs_fields(bs)

    # 期首コードが含まれないこと
    for code in BS_CODES_BEGINNING.values():
        assert code not in fields
    for code in BS_LIABILITIES_BEGINNING.values():
        assert code not in fields

    # 期末は出力されていること
    assert fields.get(BS_CODES_ENDING["cash"]) == 500000


def test_bs_field_groups_includes_beginning():
    """BS_FIELD_GROUPS に期首コードが含まれること。"""
    for code in BS_CODES_BEGINNING.values():
        assert code in BS_FIELD_GROUPS, f"期首資産コード {code} が BS_FIELD_GROUPS にない"

    for code in BS_LIABILITIES_BEGINNING.values():
        assert code in BS_FIELD_GROUPS, f"期首負債コード {code} が BS_FIELD_GROUPS にない"
