"""Tests for consumption tax xtx builder (消費税申告書)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from shinkoku.models import ConsumptionTaxResult
from shinkoku.xtx.consumption_tax import build_consumption_tax_fields
from shinkoku.xtx.field_codes import NS_SHOHI
from shinkoku.xtx.generator import XtxBuilder

# ET.fromstring() で名前空間付きタグを検索するためのヘルパー
_NS = {"ns": NS_SHOHI}


def _find_descendant(root: ET.Element, tag: str) -> ET.Element | None:
    """名前空間を考慮した子孫検索ヘルパー (.//tag)。"""
    return root.find(f".//ns:{tag}", _NS)


@pytest.fixture()
def sample_consumption_tax() -> ConsumptionTaxResult:
    return ConsumptionTaxResult(
        fiscal_year=2025,
        method="standard",
        taxable_sales_total=5_000_000,
        tax_on_sales=390_000,
        tax_on_purchases=200_000,
        tax_due=190_000,
        local_tax_due=47_200,
        total_due=237_200,
    )


class TestBuildConsumptionTaxFields:
    """build_consumption_tax_fields() テスト。"""

    def test_returns_dict(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert isinstance(fields, dict)

    def test_has_taxable_base(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAJ00010"] == 5_000_000

    def test_has_consumption_tax(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAJ00020"] == 390_000

    def test_has_deductible_purchase_tax(
        self, sample_consumption_tax: ConsumptionTaxResult
    ) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAJ00050"] == 200_000

    def test_has_net_tax(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAJ00100"] == 190_000

    def test_has_tax_due(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAJ00120"] == 190_000

    def test_has_local_tax(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAK00040"] == 47_200

    def test_has_total_due(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        fields = build_consumption_tax_fields(sample_consumption_tax)
        assert fields["AAK00130"] == 237_200

    def test_skips_zero_values(self) -> None:
        result = ConsumptionTaxResult(
            fiscal_year=2025,
            method="standard",
            taxable_sales_total=1_000_000,
            tax_on_sales=78_000,
            tax_on_purchases=0,
            tax_due=78_000,
            local_tax_due=19_400,
            total_due=97_400,
        )
        fields = build_consumption_tax_fields(result)
        assert "AAJ00050" not in fields  # 仕入税額が 0 → スキップ


class TestConsumptionTaxXtxGeneration:
    """消費税 xtx ファイル統合テスト。"""

    def test_full_consumption_tax_xtx(self, sample_consumption_tax: ConsumptionTaxResult) -> None:
        builder = XtxBuilder(tax_type="consumption", fiscal_year=2025)
        builder.set_taxpayer_info(
            name="山田太郎",
            name_kana="ﾔﾏﾀﾞ ﾀﾛｳ",
            address="東京都千代田区千代田1-1",
            address_code="13101",
            zip_code="1000001",
            tax_office_code="01234",
            tax_office_name="麹町",
        )

        fields = build_consumption_tax_fields(sample_consumption_tax)
        builder.add_form("SHA010", "10.0", fields)

        xml_str = builder.build()
        root = ET.fromstring(xml_str)

        # 消費税パッケージ（名前空間付きタグ）
        rsh = root.find("ns:RSH0010", _NS)
        assert rsh is not None
        assert rsh.get("VR") == "23.2.0"

        # 帳票（ネスト構造: SHA010 > AAJ00000 > AAJフィールド）
        sha010 = rsh.find("ns:CONTENTS/ns:SHA010", _NS)
        assert sha010 is not None
        aaj00000 = sha010.find("ns:AAJ00000", _NS)
        assert aaj00000 is not None
        assert aaj00000.find("ns:AAJ00010", _NS).text == "5000000"

        aak00000 = sha010.find("ns:AAK00000", _NS)
        assert aak00000 is not None
        assert aak00000.find("ns:AAK00130", _NS).text == "237200"
