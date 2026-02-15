"""Tests for income tax xtx builders (申告書B + 青色申告決算書)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from shinkoku.models import (
    BSItem,
    BSResult,
    DeductionItem,
    DeductionsResult,
    IncomeTaxResult,
    PLItem,
    PLResult,
    SeparateTaxResult,
)
from shinkoku.xtx.field_codes import NS_SHOTOKU
from shinkoku.xtx.generator import XtxBuilder
from shinkoku.xtx.income_tax import (
    build_income_tax_p1_fields,
    build_income_tax_p2_fields,
)
from shinkoku.xtx.blue_return import (
    build_pl_fields,
    build_bs_fields,
)
from shinkoku.xtx.schedules import (
    build_schedule3_fields,
)

# ET.fromstring() で名前空間付きタグを検索するためのヘルパー
_NS = {"ns": NS_SHOTOKU}


def _find(root: ET.Element, path: str) -> ET.Element | None:
    """名前空間を考慮した find() ヘルパー。"""
    parts = path.split("/")
    ns_path = "/".join(
        f".//ns:{p}"
        if p.startswith(".//") is False and not p.startswith(".")
        else p.replace(".//", ".//ns:")
        for p in parts
    )
    return root.find(ns_path, _NS)


def _find_descendant(root: ET.Element, tag: str) -> ET.Element | None:
    """名前空間を考慮した子孫検索ヘルパー (.//tag)。"""
    return root.find(f".//ns:{tag}", _NS)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture()
def sample_income_tax_result() -> IncomeTaxResult:
    return IncomeTaxResult(
        fiscal_year=2025,
        salary_income_after_deduction=6_100_000,
        business_income=3_000_000,
        total_income=9_100_000,
        total_income_deductions=1_680_000,
        taxable_income=7_420_000,
        income_tax_base=982_500,
        dividend_credit=0,
        housing_loan_credit=0,
        total_tax_credits=0,
        income_tax_after_credits=982_500,
        reconstruction_tax=20_632,
        total_tax=1_003_132,
        withheld_tax=800_000,
        business_withheld_tax=0,
        estimated_tax_payment=0,
        loss_carryforward_applied=0,
        tax_due=203_100,
        deductions_detail=DeductionsResult(
            income_deductions=[
                DeductionItem(type="social_insurance", name="社会保険料控除", amount=1_200_000),
                DeductionItem(type="basic", name="基礎控除", amount=480_000),
            ],
            total_income_deductions=1_680_000,
        ),
    )


@pytest.fixture()
def sample_deductions() -> DeductionsResult:
    return DeductionsResult(
        income_deductions=[
            DeductionItem(type="social_insurance", name="社会保険料控除", amount=1_200_000),
            DeductionItem(type="basic", name="基礎控除", amount=480_000),
        ],
        total_income_deductions=1_680_000,
    )


@pytest.fixture()
def sample_pl() -> PLResult:
    return PLResult(
        fiscal_year=2025,
        revenues=[PLItem(account_code="4100", account_name="売上高", amount=5_000_000)],
        expenses=[
            PLItem(account_code="5310", account_name="地代家賃", amount=600_000),
            PLItem(account_code="5200", account_name="通信費", amount=120_000),
            PLItem(account_code="5400", account_name="減価償却費", amount=300_000),
            PLItem(account_code="5600", account_name="消耗品費", amount=80_000),
            PLItem(account_code="5900", account_name="雑費", amount=50_000),
        ],
        total_revenue=5_000_000,
        total_expense=1_150_000,
        net_income=3_850_000,
    )


@pytest.fixture()
def sample_bs() -> BSResult:
    return BSResult(
        fiscal_year=2025,
        assets=[
            BSItem(account_code="1010", account_name="現金", amount=200_000),
            BSItem(account_code="1020", account_name="普通預金", amount=3_000_000),
            BSItem(account_code="1100", account_name="売掛金", amount=500_000),
        ],
        liabilities=[
            BSItem(account_code="2100", account_name="買掛金", amount=100_000),
            BSItem(account_code="2200", account_name="未払金", amount=200_000),
        ],
        equity=[
            BSItem(account_code="3010", account_name="元入金", amount=3_400_000),
        ],
        total_assets=3_700_000,
        total_liabilities=300_000,
        total_equity=3_400_000,
    )


@pytest.fixture()
def sample_separate_tax() -> SeparateTaxResult:
    return SeparateTaxResult(
        fiscal_year=2025,
        stock_net_gain=1_000_000,
        stock_dividend_offset=0,
        stock_taxable_income=1_000_000,
        stock_loss_carryforward_used=0,
        stock_income_tax=150_000,
        stock_residential_tax=50_000,
        stock_reconstruction_tax=3_150,
        stock_total_tax=203_150,
        stock_withheld_total=200_000,
        stock_tax_due=3_150,
        fx_net_income=500_000,
        fx_taxable_income=500_000,
        fx_loss_carryforward_used=0,
        fx_income_tax=75_000,
        fx_residential_tax=25_000,
        fx_reconstruction_tax=1_575,
        fx_total_tax=101_575,
        fx_tax_due=101_575,
        total_separate_tax=304_725,
    )


# ============================================================
# 第一表 xtx フィールド生成テスト
# ============================================================


class TestBuildIncomeTaxP1Fields:
    """build_income_tax_p1_fields() テスト。"""

    def test_returns_dict(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert isinstance(fields, dict)

    def test_has_salary_revenue(self, sample_income_tax_result: IncomeTaxResult) -> None:
        # IncomeTaxInput has salary_income, but the result is salary_income_after_deduction
        # The revenue (給与収入) is not directly in the result — we map what we can
        fields = build_income_tax_p1_fields(sample_income_tax_result, salary_revenue=8_000_000)
        assert fields.get("ABB00080") == 8_000_000

    def test_has_business_income(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00300"] == 3_000_000

    def test_has_salary_income(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00370"] == 6_100_000

    def test_has_total_income(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00410"] == 9_100_000

    def test_has_deductions(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00560"] == 1_680_000

    def test_has_taxable_income(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00580"] == 7_420_000

    def test_has_income_tax_base(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00590"] == 982_500

    def test_has_reconstruction_tax(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB01020"] == 20_632

    def test_has_total_tax(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB01030"] == 1_003_132

    def test_has_withheld_tax(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        assert fields["ABB00710"] == 800_000

    def test_has_tax_due(self, sample_income_tax_result: IncomeTaxResult) -> None:
        fields = build_income_tax_p1_fields(sample_income_tax_result)
        # tax_due > 0 → 納める税金
        assert fields["ABB00750"] == 203_100

    def test_refund_case(self) -> None:
        result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=3_000_000,
            business_income=0,
            total_income=3_000_000,
            total_income_deductions=1_000_000,
            taxable_income=2_000_000,
            income_tax_base=102_500,
            income_tax_after_credits=102_500,
            reconstruction_tax=2_152,
            total_tax=104_652,
            withheld_tax=200_000,
            tax_due=-95_300,
        )
        fields = build_income_tax_p1_fields(result)
        # 還付の場合
        assert fields.get("ABB00760") == 95_300
        assert "ABB00750" not in fields

    def test_skips_zero_values(self) -> None:
        result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=0,
            business_income=0,
            total_income=0,
            total_income_deductions=0,
            taxable_income=0,
            income_tax_base=0,
            income_tax_after_credits=0,
            reconstruction_tax=0,
            total_tax=0,
            withheld_tax=0,
            tax_due=0,
        )
        fields = build_income_tax_p1_fields(result)
        # 0 の値は含まれない
        assert "ABB00300" not in fields
        assert "ABB00370" not in fields

    def test_deduction_detail_mapping(self) -> None:
        result = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=3_000_000,
            business_income=0,
            total_income=3_000_000,
            total_income_deductions=1_680_000,
            taxable_income=1_320_000,
            income_tax_base=66_000,
            income_tax_after_credits=66_000,
            reconstruction_tax=1_386,
            total_tax=67_386,
            withheld_tax=100_000,
            tax_due=-32_600,
            deductions_detail=DeductionsResult(
                income_deductions=[
                    DeductionItem(type="social_insurance", name="社会保険料控除", amount=1_200_000),
                    DeductionItem(type="basic", name="基礎控除", amount=480_000),
                ],
                total_income_deductions=1_680_000,
            ),
        )
        fields = build_income_tax_p1_fields(result)
        assert fields.get("ABB00450") == 1_200_000  # 社会保険料控除
        assert fields.get("ABB00550") == 480_000  # 基礎控除


# ============================================================
# 第二表 xtx フィールド生成テスト
# ============================================================


class TestBuildIncomeTaxP2Fields:
    """build_income_tax_p2_fields() テスト。"""

    def test_income_detail_items(self) -> None:
        income_details = [
            {
                "income_type": "給与",
                "category": "給料",
                "payer_name": "株式会社ABC",
                "revenue": 8_000_000,
                "withheld_tax": 600_000,
            },
            {
                "income_type": "営業",
                "category": "ソフトウェア開発",
                "payer_name": "フリーランス収入",
                "revenue": 5_000_000,
                "withheld_tax": 200_000,
            },
        ]
        result = build_income_tax_p2_fields(income_details=income_details)
        assert isinstance(result, dict)
        # 繰り返しグループが含まれる
        groups = result.get("repeating_groups", {})
        assert "ABD00010" in groups
        assert len(groups["ABD00010"]) == 2
        assert groups["ABD00010"][0]["ABD00020"] == "給与"

    def test_withheld_tax_total(self) -> None:
        income_details = [
            {
                "income_type": "給与",
                "category": "給料",
                "payer_name": "株式会社ABC",
                "revenue": 8_000_000,
                "withheld_tax": 600_000,
            },
        ]
        result = build_income_tax_p2_fields(
            income_details=income_details,
            withheld_tax_total=800_000,
        )
        fields = result.get("fields", {})
        assert fields.get("ABD00070") == 800_000

    def test_social_insurance_detail(self) -> None:
        social_insurance = [
            {"insurance_type": "国民健康保険", "amount": 400_000},
            {"insurance_type": "国民年金", "amount": 200_000},
        ]
        result = build_income_tax_p2_fields(social_insurance_details=social_insurance)
        groups = result.get("repeating_groups", {})
        assert "ABH00120" in groups
        assert len(groups["ABH00120"]) == 2

    def test_empty_input(self) -> None:
        result = build_income_tax_p2_fields()
        assert isinstance(result, dict)


# ============================================================
# 青色申告決算書 PL テスト
# ============================================================


class TestBuildPLFields:
    """build_pl_fields() テスト。"""

    def test_returns_dict(self, sample_pl: PLResult) -> None:
        fields = build_pl_fields(sample_pl)
        assert isinstance(fields, dict)

    def test_has_revenue(self, sample_pl: PLResult) -> None:
        fields = build_pl_fields(sample_pl)
        assert fields["AMF00100"] == 5_000_000

    def test_has_expense_items(self, sample_pl: PLResult) -> None:
        fields = build_pl_fields(sample_pl)
        # 地代家賃
        assert fields.get("AMF00340") == 600_000
        # 通信費
        assert fields.get("AMF00230") == 120_000
        # 減価償却費
        assert fields.get("AMF00290") == 300_000

    def test_has_total_expense(self, sample_pl: PLResult) -> None:
        fields = build_pl_fields(sample_pl)
        assert fields["AMF00380"] == 1_150_000

    def test_has_net_income(self, sample_pl: PLResult) -> None:
        fields = build_pl_fields(sample_pl)
        assert fields["AMF00530"] == 3_850_000

    def test_skips_zero_amounts(self) -> None:
        pl = PLResult(
            fiscal_year=2025,
            revenues=[PLItem(account_code="4100", account_name="売上高", amount=1_000_000)],
            expenses=[],
            total_revenue=1_000_000,
            total_expense=0,
            net_income=1_000_000,
        )
        fields = build_pl_fields(pl)
        assert "AMF00380" not in fields  # 経費が0ならスキップ

    def test_blue_return_deduction(self, sample_pl: PLResult) -> None:
        fields = build_pl_fields(sample_pl, blue_return_deduction=650_000)
        assert fields["AMF00510"] == 650_000


# ============================================================
# 青色申告決算書 BS テスト
# ============================================================


class TestBuildBSFields:
    """build_bs_fields() テスト。"""

    def test_returns_dict(self, sample_bs: BSResult) -> None:
        fields = build_bs_fields(sample_bs)
        assert isinstance(fields, dict)

    def test_has_total_assets(self, sample_bs: BSResult) -> None:
        fields = build_bs_fields(sample_bs)
        # 期末資産合計
        assert fields.get("AMG00440") == 3_700_000

    def test_has_total_liabilities(self, sample_bs: BSResult) -> None:
        fields = build_bs_fields(sample_bs)
        assert fields.get("AMG00760") == 300_000


# ============================================================
# 第三表 xtx フィールド生成テスト
# ============================================================


class TestBuildSchedule3Fields:
    """build_schedule3_fields() テスト。"""

    def test_returns_dict(self, sample_separate_tax: SeparateTaxResult) -> None:
        fields = build_schedule3_fields(sample_separate_tax)
        assert isinstance(fields, dict)

    def test_has_stock_income(self, sample_separate_tax: SeparateTaxResult) -> None:
        fields = build_schedule3_fields(sample_separate_tax)
        # 上場株式等の譲渡所得
        assert fields.get("ABL00310") == 1_000_000

    def test_has_futures_income(self, sample_separate_tax: SeparateTaxResult) -> None:
        fields = build_schedule3_fields(sample_separate_tax)
        # 先物取引
        assert fields.get("ABL00330") == 500_000

    def test_has_stock_tax(self, sample_separate_tax: SeparateTaxResult) -> None:
        fields = build_schedule3_fields(sample_separate_tax)
        assert fields.get("ABL00500") == 1_000_000  # 課税所得 (72)(73)対応分

    def test_has_futures_tax(self, sample_separate_tax: SeparateTaxResult) -> None:
        fields = build_schedule3_fields(sample_separate_tax)
        assert fields.get("ABL00510") == 500_000  # 課税所得 (75)対応分


# ============================================================
# 統合テスト: xtx ファイル全体の生成
# ============================================================


class TestFullXtxGeneration:
    """XtxBuilder を使った統合テスト。"""

    def test_income_tax_with_blue_return(
        self,
        sample_income_tax_result: IncomeTaxResult,
        sample_pl: PLResult,
    ) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.set_taxpayer_info(
            name="山田太郎",
            name_kana="ﾔﾏﾀﾞ ﾀﾛｳ",
            address="東京都千代田区千代田1-1",
            address_code="13101",
            zip_code="1000001",
            tax_office_code="01234",
            tax_office_name="麹町",
        )

        # 第一表（nesting_key でネスト構造を有効化）
        p1_fields = build_income_tax_p1_fields(
            sample_income_tax_result,
            salary_revenue=8_000_000,
            business_revenue=5_000_000,
        )
        builder.add_form("KOA020", "23.0", p1_fields, nesting_key="KOA020-1")

        # 青色申告決算書（KOA210 は FORM_NESTING に定義済み）
        pl_fields = build_pl_fields(sample_pl, blue_return_deduction=650_000)
        builder.add_form("KOA210", "11.0", pl_fields)

        xml_str = builder.build()
        root = ET.fromstring(xml_str)

        # 構造検証（名前空間付きタグ）
        assert root.tag == f"{{{NS_SHOTOKU}}}DATA"
        rko = root.find("ns:RKO0010", _NS)
        assert rko is not None
        contents = rko.find("ns:CONTENTS", _NS)
        assert contents.find("ns:IT", _NS) is not None
        assert contents.find("ns:KOA020", _NS) is not None
        assert contents.find("ns:KOA210", _NS) is not None

        # 第一表: KOA020 > KOA020-1 > ABB00000 > ABB00010 > ABB00030
        koa020 = contents.find("ns:KOA020", _NS)
        koa020_1 = koa020.find("ns:KOA020-1", _NS)
        assert koa020_1 is not None
        abb00000 = koa020_1.find("ns:ABB00000", _NS)
        assert abb00000 is not None
        # 収入金額は ABB00010 グループの下
        abb00010 = abb00000.find("ns:ABB00010", _NS)
        assert abb00010 is not None
        assert abb00010.find("ns:ABB00030", _NS).text == "5000000"
        assert abb00010.find("ns:ABB00080", _NS).text == "8000000"

        # 青色申告決算書: KOA210 > AMF00000 > AMF00100
        koa210 = contents.find("ns:KOA210", _NS)
        amf00000 = koa210.find("ns:AMF00000", _NS)
        assert amf00000 is not None
        assert amf00000.find("ns:AMF00100", _NS).text == "5000000"

    def test_income_tax_with_schedule3(
        self,
        sample_income_tax_result: IncomeTaxResult,
        sample_separate_tax: SeparateTaxResult,
    ) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.set_taxpayer_info(
            name="山田太郎",
            name_kana="ﾔﾏﾀﾞ ﾀﾛｳ",
            address="東京都千代田区千代田1-1",
            address_code="13101",
            zip_code="1000001",
            tax_office_code="01234",
            tax_office_name="麹町",
        )

        # P1 と Schedule3 は同じ KOA020 にマージされる
        p1_fields = build_income_tax_p1_fields(sample_income_tax_result)
        builder.add_form("KOA020", "23.0", p1_fields, nesting_key="KOA020-1")

        s3_fields = build_schedule3_fields(sample_separate_tax)
        builder.add_form("KOA020", "23.0", s3_fields)

        xml_str = builder.build()
        root = ET.fromstring(xml_str)

        # KOA020 は1つだけ生成される
        koa020_list = root.findall(".//ns:KOA020", _NS)
        assert len(koa020_list) == 1

        # ABL コードも含まれる
        assert _find_descendant(root, "ABL00310") is not None
