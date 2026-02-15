"""Tests for XtxBuilder core XML generation engine."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from shinkoku.xtx.field_codes import NS_GENERAL, NS_SHOHI, NS_SHOTOKU
from shinkoku.xtx.generator import XtxBuilder, sanitize_text

# ET.fromstring() で名前空間付きタグを検索するためのヘルパー
_NS_INCOME = {"": NS_SHOTOKU, "gen": NS_GENERAL}
_NS_CONSUMPTION = {"": NS_SHOHI, "gen": NS_GENERAL}


def _find(root: ET.Element, path: str, ns: dict[str, str] = _NS_INCOME) -> ET.Element | None:
    """名前空間を考慮した find() ヘルパー。"""
    # ET の find() でデフォルト名前空間を使うにはプレフィックスが必要
    # path 内の各要素に名前空間プレフィックスを付与する
    parts = path.split("/")
    ns_path = "/".join(f"ns:{p}" if not p.startswith(".") else p for p in parts)
    ns_map = {"ns": ns[""]}
    return root.find(ns_path, ns_map)


def _findall(root: ET.Element, path: str, ns: dict[str, str] = _NS_INCOME) -> list[ET.Element]:
    """名前空間を考慮した findall() ヘルパー。"""
    parts = path.split("/")
    ns_path = "/".join(f"ns:{p}" if not p.startswith(".") else p for p in parts)
    ns_map = {"ns": ns[""]}
    return root.findall(ns_path, ns_map)


class TestXtxBuilderInit:
    """XtxBuilder の初期化テスト。"""

    def test_init_income_tax(self) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        assert builder.tax_type == "income"
        assert builder.fiscal_year == 2025

    def test_init_consumption_tax(self) -> None:
        builder = XtxBuilder(tax_type="consumption", fiscal_year=2025)
        assert builder.tax_type == "consumption"
        assert builder.fiscal_year == 2025

    def test_init_invalid_tax_type(self) -> None:
        with pytest.raises(ValueError, match="tax_type"):
            XtxBuilder(tax_type="invalid", fiscal_year=2025)

    def test_init_stores_metadata(self) -> None:
        builder = XtxBuilder(
            tax_type="income",
            fiscal_year=2025,
            software_name="shinkoku",
            creator_name="山田太郎",
        )
        assert builder.software_name == "shinkoku"
        assert builder.creator_name == "山田太郎"


class TestXtxBuilderSetIT:
    """IT部（共通ヘッダ）の設定テスト。"""

    def test_set_taxpayer_info(self) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.set_taxpayer_info(
            name="山田太郎",
            name_kana="ﾔﾏﾀﾞ ﾀﾛｳ",
            address="東京都千代田区千代田1-1",
            address_code="13101",
            zip_code="1000001",
            tax_office_code="01234",
            tax_office_name="麹町",
            taxpayer_id="1234567890123456",
            my_number="123456789012",
        )
        assert builder.taxpayer_info["name"] == "山田太郎"
        assert builder.taxpayer_info["zip_code"] == "1000001"


class TestXtxBuilderAddForm:
    """add_form() テスト。"""

    def test_add_form_creates_section(self) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000, "ABB00080": 8_000_000},
        )
        assert len(builder.forms) == 1
        assert builder.forms[0]["form_code"] == "KOA020"
        assert builder.forms[0]["fields"]["ABB00030"] == 5_000_000

    def test_add_multiple_forms(self) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        builder.add_form(
            form_code="KOA210",
            version="11.0",
            fields={"AMF00100": 5_000_000},
        )
        assert len(builder.forms) == 2

    def test_add_form_with_sub_sections(self) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
            sub_sections={
                "KOA020-1": {"ABB00030": 5_000_000},
                "KOA020-2": {"ABD00020": "給与"},
            },
        )
        assert "KOA020-1" in builder.forms[0]["sub_sections"]

    def test_add_form_skips_zero_and_none(self) -> None:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000, "ABB00040": 0, "ABB00050": None},
        )
        fields = builder.forms[0]["fields"]
        assert "ABB00030" in fields
        # 0 と None はスキップされる
        assert "ABB00040" not in fields
        assert "ABB00050" not in fields


class TestXtxBuilderBuild:
    """build() テスト — XML 文字列の生成。"""

    def _minimal_builder(self) -> XtxBuilder:
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        return builder

    def test_build_returns_xml_string(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        assert isinstance(xml_str, str)
        assert xml_str.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_build_has_data_root(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        # 名前空間付きタグ
        assert root.tag == f"{{{NS_SHOTOKU}}}DATA"

    def test_build_has_xmlns_attributes(self) -> None:
        """xmlns 名前空間宣言が正しく設定される。"""
        builder = self._minimal_builder()
        xml_str = builder.build()
        assert f'xmlns="{NS_SHOTOKU}"' in xml_str
        assert f'xmlns:gen="{NS_GENERAL}"' in xml_str

    def test_build_consumption_has_shohi_xmlns(self) -> None:
        """消費税の場合は shohi 名前空間が使われる。"""
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
        builder.add_form(
            form_code="SHA010",
            version="10.0",
            fields={"AAJ00010": 5_000_000},
        )
        xml_str = builder.build()
        assert f'xmlns="{NS_SHOHI}"' in xml_str

    def test_build_has_procedure_element(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        # 所得税の場合 RKO0010
        rko = _find(root, "RKO0010")
        assert rko is not None
        assert rko.get("VR") == "25.0.0"

    def test_build_has_catalog_and_contents(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        rko = _find(root, "RKO0010")
        assert _find(rko, "CATALOG") is not None
        assert _find(rko, "CONTENTS") is not None

    def test_build_has_it_section(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        contents = _find(root, "RKO0010/CONTENTS")
        it = _find(contents, "IT")
        assert it is not None

    def test_build_it_has_taxpayer_name(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        nm = _find(it, "NOZEISHA_NM")
        assert nm is not None
        assert nm.text == "山田太郎"

    def test_build_it_has_zip_code(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        zip_el = _find(it, "NOZEISHA_ZIP")
        assert zip_el is not None
        assert _find(zip_el, "zip1").text == "100"
        assert _find(zip_el, "zip2").text == "0001"

    def test_build_it_has_tax_office(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        zeimusho = _find(it, "ZEIMUSHO")
        assert zeimusho is not None
        assert _find(zeimusho, "zeimusho_CD").text == "01234"
        assert _find(zeimusho, "zeimusho_NM").text == "麹町"

    def test_build_has_form_element(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        contents = _find(root, "RKO0010/CONTENTS")
        koa020 = _find(contents, "KOA020")
        assert koa020 is not None
        assert koa020.get("VR") == "23.0"
        assert koa020.get("softNM") == "shinkoku"

    def test_build_form_has_field_value(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        koa020 = _find(root, "RKO0010/CONTENTS/KOA020")
        # .// prefix needs special handling for namespace
        ns_map = {"ns": NS_SHOTOKU}
        abb = koa020.find(".//ns:ABB00030", ns_map)
        assert abb is not None
        assert abb.text == "5000000"

    def test_build_consumption_tax(self) -> None:
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
        builder.add_form(
            form_code="SHA010",
            version="10.0",
            fields={"AAJ00010": 5_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        # 消費税の場合 RSH0010
        rsh = _find(root, "RSH0010", _NS_CONSUMPTION)
        assert rsh is not None
        assert rsh.get("VR") == "23.2.0"

    def test_build_utf8_encoding(self) -> None:
        builder = self._minimal_builder()
        xml_str = builder.build()
        # エンコーディング宣言の確認
        assert 'encoding="UTF-8"' in xml_str
        # 日本語が含まれている
        assert "山田太郎" in xml_str

    def test_build_nenbun_element(self) -> None:
        """NENBUN（年分）が正しく設定される。"""
        builder = self._minimal_builder()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        nenbun = _find(it, "NENBUN")
        assert nenbun is not None
        # 2025年 = 令和7年
        assert _find(nenbun, "era").text == "5"
        assert _find(nenbun, "yy").text == "7"


class TestXtxBuilderSave:
    """save() テスト。"""

    def test_save_writes_file(self, tmp_path: Path) -> None:
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        output = tmp_path / "test.xtx"
        builder.save(output)
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "山田太郎" in content

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        output = tmp_path / "subdir" / "test.xtx"
        builder.save(output)
        assert output.exists()


class TestSanitizeText:
    """機種依存文字のサニタイズテスト。"""

    def test_circled_numbers(self) -> None:
        """丸囲み数字 ①〜⑳ → (1)〜(20)。"""
        assert sanitize_text("①②③") == "(1)(2)(3)"
        assert sanitize_text("⑩⑳") == "(10)(20)"

    def test_roman_numerals(self) -> None:
        """ローマ数字 Ⅰ〜Ⅹ → I〜X。"""
        assert sanitize_text("Ⅰ") == "I"
        assert sanitize_text("Ⅱ") == "II"
        assert sanitize_text("Ⅲ") == "III"

    def test_no_change_for_normal_text(self) -> None:
        assert sanitize_text("山田太郎") == "山田太郎"
        assert sanitize_text("abc123") == "abc123"

    def test_empty_string(self) -> None:
        assert sanitize_text("") == ""

    def test_fullwidth_to_halfwidth_numbers(self) -> None:
        """全角数字 → 半角数字。"""
        assert sanitize_text("１２３") == "123"


class TestXtxBuilderIDREF:
    """IDREF 参照メカニズムのテスト。"""

    def test_add_form_with_idref(self) -> None:
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
            idrefs={"ABA00010": "NENBUN", "ABA00030": "ZEIMUSHO"},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        koa020 = _find(root, "RKO0010/CONTENTS/KOA020")
        ns_map = {"ns": NS_SHOTOKU}
        aba00010 = koa020.find(".//ns:ABA00010", ns_map)
        assert aba00010 is not None
        assert aba00010.get("IDREF") == "NENBUN"


class TestXtxBuilderRepeatingGroups:
    """繰り返しグループ（所得の内訳等）のテスト。"""

    def test_add_repeating_group(self) -> None:
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={},
            repeating_groups={
                "ABD00010": [
                    {"ABD00020": "給与", "ABD00040": "株式会社ABC", "ABD00050": 8_000_000},
                    {"ABD00020": "営業", "ABD00040": "フリーランス", "ABD00050": 5_000_000},
                ],
            },
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        koa020 = _find(root, "RKO0010/CONTENTS/KOA020")
        ns_map = {"ns": NS_SHOTOKU}
        groups = koa020.findall(".//ns:ABD00010", ns_map)
        assert len(groups) == 2
        assert groups[0].find(f"{{{NS_SHOTOKU}}}ABD00020").text == "給与"
        assert groups[1].find(f"{{{NS_SHOTOKU}}}ABD00020").text == "営業"


class TestXtxBuilderNesting:
    """仕様準拠の XML ネスト構造テスト。"""

    def _taxpayer_builder(self, tax_type: str = "income") -> XtxBuilder:
        builder = XtxBuilder(tax_type=tax_type, fiscal_year=2025)
        builder.set_taxpayer_info(
            name="山田太郎",
            name_kana="ﾔﾏﾀﾞ ﾀﾛｳ",
            address="東京都千代田区千代田1-1",
            address_code="13101",
            zip_code="1000001",
            tax_office_code="01234",
            tax_office_name="麹町",
        )
        return builder

    def test_p1_nesting_creates_koa020_1(self) -> None:
        """nesting_key="KOA020-1" で KOA020 > KOA020-1 構造が生成される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00030": 5_000_000, "ABB00300": 3_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        koa020 = root.find(".//ns:KOA020", ns)
        assert koa020 is not None
        koa020_1 = koa020.find("ns:KOA020-1", ns)
        assert koa020_1 is not None

    def test_p1_fields_in_abb00000(self) -> None:
        """第一表フィールドは ABB00000 グループ要素の下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00030": 5_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        abb00000 = root.find(".//ns:KOA020-1/ns:ABB00000", ns)
        assert abb00000 is not None

    def test_p1_revenue_in_abb00010(self) -> None:
        """収入金額フィールドは ABB00000 > ABB00010 グループの下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00030": 5_000_000, "ABB00080": 8_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        abb00010 = root.find(".//ns:ABB00000/ns:ABB00010", ns)
        assert abb00010 is not None
        assert abb00010.find("ns:ABB00030", ns).text == "5000000"
        assert abb00010.find("ns:ABB00080", ns).text == "8000000"

    def test_p1_income_in_abb00270(self) -> None:
        """所得金額フィールドは ABB00000 > ABB00270 グループの下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00300": 3_000_000, "ABB00370": 6_100_000, "ABB00410": 9_100_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        abb00270 = root.find(".//ns:ABB00000/ns:ABB00270", ns)
        assert abb00270 is not None
        assert abb00270.find("ns:ABB00300", ns).text == "3000000"
        assert abb00270.find("ns:ABB00370", ns).text == "6100000"
        assert abb00270.find("ns:ABB00410", ns).text == "9100000"

    def test_p1_deductions_in_abb00420(self) -> None:
        """控除フィールドは ABB00000 > ABB00420 グループの下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00450": 1_200_000, "ABB00550": 480_000, "ABB00560": 1_680_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        abb00420 = root.find(".//ns:ABB00000/ns:ABB00420", ns)
        assert abb00420 is not None
        assert abb00420.find("ns:ABB00450", ns).text == "1200000"

    def test_p1_tax_calc_in_abb00570(self) -> None:
        """税金計算フィールドは ABB00000 > ABB00570 グループの下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00580": 7_420_000, "ABB00590": 982_500, "ABB00750": 203_100},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        abb00570 = root.find(".//ns:ABB00000/ns:ABB00570", ns)
        assert abb00570 is not None
        assert abb00570.find("ns:ABB00580", ns).text == "7420000"
        assert abb00570.find("ns:ABB00750", ns).text == "203100"

    def test_p1_other_direct_under_abb00000(self) -> None:
        """その他フィールド（ABB00800等）は ABB00000 直下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00800": 650_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        abb00000 = root.find(".//ns:KOA020-1/ns:ABB00000", ns)
        assert abb00000 is not None
        assert abb00000.find("ns:ABB00800", ns).text == "650000"
        # ABB00570 グループは作成されないことを確認
        assert abb00000.find("ns:ABB00570", ns) is None

    def test_merged_koa020_with_p1_and_p2(self) -> None:
        """同じ form_code の P1 と P2 が1つの KOA020 要素にマージされる。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-1",
            fields={"ABB00030": 5_000_000},
        )
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            nesting_key="KOA020-2",
            fields={"ABD00070": 800_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        # KOA020 要素は1つだけ
        koa020_list = root.findall(".//ns:KOA020", ns)
        assert len(koa020_list) == 1

        koa020 = koa020_list[0]
        assert koa020.find("ns:KOA020-1", ns) is not None
        assert koa020.find("ns:KOA020-2", ns) is not None

    def test_pl_nesting_amf00000(self) -> None:
        """青色申告決算書フィールドは AMF00000 グループの下に配置される。"""
        builder = self._taxpayer_builder()
        builder.add_form(
            form_code="KOA210",
            version="11.0",
            fields={"AMF00100": 5_000_000, "AMF00290": 300_000, "AMF00530": 3_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOTOKU}

        koa210 = root.find(".//ns:KOA210", ns)
        assert koa210 is not None
        amf00000 = koa210.find("ns:AMF00000", ns)
        assert amf00000 is not None
        # 売上は AMF00000 直下
        assert amf00000.find("ns:AMF00100", ns).text == "5000000"
        # 経費は AMF00000 > AMF00180 の下
        amf00180 = amf00000.find("ns:AMF00180", ns)
        assert amf00180 is not None
        assert amf00180.find("ns:AMF00290", ns).text == "300000"
        # 所得は AMF00000 直下
        assert amf00000.find("ns:AMF00530", ns).text == "3000000"

    def test_consumption_tax_nesting(self) -> None:
        """消費税フィールドは AAJ00000/AAK00000 グループの下に配置される。"""
        builder = self._taxpayer_builder(tax_type="consumption")
        builder.add_form(
            form_code="SHA010",
            version="10.0",
            fields={
                "AAJ00010": 5_000_000,
                "AAJ00020": 390_000,
                "AAK00040": 47_200,
                "AAK00130": 237_200,
            },
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        ns = {"ns": NS_SHOHI}

        sha010 = root.find(".//ns:SHA010", ns)
        assert sha010 is not None
        aaj00000 = sha010.find("ns:AAJ00000", ns)
        assert aaj00000 is not None
        assert aaj00000.find("ns:AAJ00010", ns).text == "5000000"
        aak00000 = sha010.find("ns:AAK00000", ns)
        assert aak00000 is not None
        assert aak00000.find("ns:AAK00130", ns).text == "237200"


class TestXtxBuilderW2W5Fields:
    """W2-W5 IT部フィールドのテスト。"""

    def _builder_with_w2w5(self) -> XtxBuilder:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.set_taxpayer_info(
            name="山田太郎",
            name_kana="ﾔﾏﾀﾞ ﾀﾛｳ",
            address="東京都千代田区千代田1-1",
            address_code="13101",
            zip_code="1000001",
            tax_office_code="01234",
            tax_office_name="麹町",
            address_kana="ﾄｳｷｮｳﾄ ﾁﾖﾀﾞｸ ﾁﾖﾀﾞ1-1",
            seiribango="12345678",
            refund_bank_name="みずほ銀行",
            refund_bank_type="1",
            refund_branch_name="丸の内支店",
            refund_branch_type="2",
            refund_deposit_type="1",
            refund_account_number="1234567",
        )
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        return builder

    def test_w5_nozeisha_adr_kn(self) -> None:
        """W5: NOZEISHA_ADR_KN（住所フリガナ）が IT部に出力される。"""
        builder = self._builder_with_w2w5()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        adr_kn = _find(it, "NOZEISHA_ADR_KN")
        assert adr_kn is not None
        assert adr_kn.text == "ﾄｳｷｮｳﾄ ﾁﾖﾀﾞｸ ﾁﾖﾀﾞ1-1"

    def test_w4_seiribango(self) -> None:
        """W4: SEIRIBANGO（整理番号）が IT部に出力される。"""
        builder = self._builder_with_w2w5()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        seiribango = _find(it, "SEIRIBANGO")
        assert seiribango is not None
        assert seiribango.text == "12345678"

    def test_w3_keisansho_kbn(self) -> None:
        """W3: KEISANSHO_KBN（計算書区分）が IT部に出力される。"""
        builder = self._builder_with_w2w5()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        keisansho = _find(it, "KEISANSHO_KBN")
        assert keisansho is not None
        kbn = _find(keisansho, "kubun_CD")
        assert kbn is not None
        assert kbn.text == "1"

    def test_w2_kanpu_kinyukikan(self) -> None:
        """W2: KANPU_KINYUKIKAN（還付金融機関）が IT部に出力される。"""
        builder = self._builder_with_w2w5()
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        kanpu = _find(it, "KANPU_KINYUKIKAN")
        assert kanpu is not None

        kinyukikan_nm = _find(kanpu, "kinyukikan_NM")
        assert kinyukikan_nm is not None
        assert kinyukikan_nm.text == "みずほ銀行"
        assert kinyukikan_nm.get("kinyukikan_KB") == "1"

        shiten_nm = _find(kanpu, "shiten_NM")
        assert shiten_nm is not None
        assert shiten_nm.text == "丸の内支店"
        assert shiten_nm.get("shiten_KB") == "2"

        yokin = _find(kanpu, "yokin")
        assert yokin is not None
        assert yokin.text == "1"

        koza = _find(kanpu, "koza")
        assert koza is not None
        assert koza.text == "1234567"

    def test_w2_kanpu_omitted_when_empty(self) -> None:
        """還付金融機関は銀行名が空なら出力しない。"""
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        kanpu = _find(it, "KANPU_KINYUKIKAN")
        assert kanpu is None

    def test_w5_adr_kn_omitted_when_empty(self) -> None:
        """住所フリガナは空なら出力しない。"""
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        adr_kn = _find(it, "NOZEISHA_ADR_KN")
        assert adr_kn is None

    def test_w4_seiribango_omitted_when_empty(self) -> None:
        """整理番号は空なら出力しない。"""
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
        builder.add_form(
            form_code="KOA020",
            version="23.0",
            fields={"ABB00030": 5_000_000},
        )
        xml_str = builder.build()
        root = ET.fromstring(xml_str)
        it = _find(root, "RKO0010/CONTENTS/IT")
        seiribango = _find(it, "SEIRIBANGO")
        assert seiribango is None
