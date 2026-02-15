"""Core XML generation engine for e-Tax xtx files.

XtxBuilder を使って e-Tax の xtx XML ファイルを生成する。
xml.etree.ElementTree を使用した軽量実装。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any

from shinkoku.xtx.field_codes import (
    CONSUMPTION_TAX_PROCEDURE,
    CONSUMPTION_TAX_PROCEDURE_VR,
    ERA_CODES,
    FORM_NESTING,
    INCOME_TAX_PROCEDURE,
    INCOME_TAX_PROCEDURE_VR,
    NS_GENERAL,
    NS_SHOHI,
    NS_SHOTOKU,
    REIWA_BASE_YEAR,
    to_reiwa_year,
)

# 機種依存文字変換テーブル
_CIRCLED_NUMBERS: dict[str, str] = {
    chr(0x2460 + i): f"({i + 1})"
    for i in range(20)  # ①〜⑳
}

_ROMAN_NUMERALS: dict[str, str] = {
    "Ⅰ": "I",
    "Ⅱ": "II",
    "Ⅲ": "III",
    "Ⅳ": "IV",
    "Ⅴ": "V",
    "Ⅵ": "VI",
    "Ⅶ": "VII",
    "Ⅷ": "VIII",
    "Ⅸ": "IX",
    "Ⅹ": "X",
}

# 全角数字→半角数字
_FULLWIDTH_DIGITS: dict[str, str] = {
    chr(0xFF10 + i): str(i)
    for i in range(10)  # ０〜９
}


def sanitize_text(text: str) -> str:
    """機種依存文字をサニタイズする。

    - 丸囲み数字 ①〜⑳ → (1)〜(20)
    - ローマ数字 Ⅰ〜Ⅹ → I〜X
    - 全角数字 ０〜９ → 0〜9
    """
    for old, new in _CIRCLED_NUMBERS.items():
        text = text.replace(old, new)
    for old, new in _ROMAN_NUMERALS.items():
        text = text.replace(old, new)
    for old, new in _FULLWIDTH_DIGITS.items():
        text = text.replace(old, new)
    return text


class XtxBuilder:
    """e-Tax xtx XML ビルダー。

    使い方:
        builder = XtxBuilder(tax_type="income", fiscal_year=2025)
        builder.set_taxpayer_info(name="山田太郎", ...)
        builder.add_form("KOA020", "23.0", {"ABB00030": 5_000_000})
        xml_str = builder.build()
        builder.save(Path("output/income_tax.xtx"))
    """

    VALID_TAX_TYPES = ("income", "consumption", "consumption_simplified")

    def __init__(
        self,
        tax_type: str,
        fiscal_year: int,
        *,
        software_name: str = "shinkoku",
        creator_name: str = "",
        creation_date: date | None = None,
    ) -> None:
        if tax_type not in self.VALID_TAX_TYPES:
            msg = f"tax_type must be one of {self.VALID_TAX_TYPES}, got '{tax_type}'"
            raise ValueError(msg)

        self.tax_type = tax_type
        self.fiscal_year = fiscal_year
        self.software_name = software_name
        self.creator_name = creator_name
        self.creation_date = creation_date or date.today()
        self.taxpayer_info: dict[str, str] = {}
        self.forms: list[dict[str, Any]] = []

    def set_taxpayer_info(
        self,
        *,
        name: str,
        name_kana: str,
        address: str,
        address_code: str,
        zip_code: str,
        tax_office_code: str,
        tax_office_name: str,
        taxpayer_id: str = "",
        my_number: str = "",
        jan1_address: str = "",
        jan1_address_code: str = "",
        trade_name: str = "",
        phone: str = "",
        gender: str = "",
        birthday: str = "",
        household_head: str = "",
        household_relation: str = "",
        occupation: str = "",
        business_description: str = "",
        # W2-W5 追加フィールド
        address_kana: str = "",
        seiribango: str = "",
        refund_bank_name: str = "",
        refund_bank_type: str = "1",
        refund_branch_name: str = "",
        refund_branch_type: str = "2",
        refund_deposit_type: str = "",
        refund_account_number: str = "",
    ) -> None:
        """IT部（共通ヘッダ）に格納する納税者情報を設定する。"""
        self.taxpayer_info = {
            "name": name,
            "name_kana": name_kana,
            "address": address,
            "address_code": address_code,
            "zip_code": zip_code,
            "tax_office_code": tax_office_code,
            "tax_office_name": tax_office_name,
            "taxpayer_id": taxpayer_id,
            "my_number": my_number,
            "jan1_address": jan1_address or address,
            "jan1_address_code": jan1_address_code or address_code,
            "trade_name": trade_name,
            "phone": phone,
            "gender": gender,
            "birthday": birthday,
            "household_head": household_head,
            "household_relation": household_relation,
            "occupation": occupation,
            "business_description": business_description,
            "address_kana": address_kana,
            "seiribango": seiribango,
            "refund_bank_name": refund_bank_name,
            "refund_bank_type": refund_bank_type,
            "refund_branch_name": refund_branch_name,
            "refund_branch_type": refund_branch_type,
            "refund_deposit_type": refund_deposit_type,
            "refund_account_number": refund_account_number,
        }

    def add_form(
        self,
        form_code: str,
        version: str,
        fields: dict[str, Any],
        *,
        nesting_key: str = "",
        sub_sections: dict[str, dict[str, Any]] | None = None,
        idrefs: dict[str, str] | None = None,
        repeating_groups: dict[str, list[dict[str, Any]]] | None = None,
        page: int = 1,
    ) -> None:
        """帳票セクションを追加する。

        Args:
            form_code: 帳票コード (例: "KOA020")
            version: バージョン (例: "23.0")
            fields: フィールド辞書 {ABBコード: 値}。0 と None はスキップ。
            nesting_key: ネスト構造キー (例: "KOA020-1")。
                         FORM_NESTING に定義がある場合、フィールドを階層構造に配置する。
                         空文字列の場合は form_code をキーとして検索する。
            sub_sections: サブセクション辞書 {セクション名: {ABBコード: 値}}
            idrefs: IDREF 参照 {ABBコード: IT部のID}
            repeating_groups: 繰り返しグループ {親コード: [{子コード: 値}, ...]}
            page: ページ番号
        """
        # 0 と None をフィルタリング
        filtered_fields = {k: v for k, v in fields.items() if v is not None and v != 0}

        form_entry: dict[str, Any] = {
            "form_code": form_code,
            "version": version,
            "fields": filtered_fields,
            "page": page,
            "nesting_key": nesting_key or form_code,
        }
        if sub_sections is not None:
            form_entry["sub_sections"] = sub_sections
        if idrefs is not None:
            form_entry["idrefs"] = idrefs
        if repeating_groups is not None:
            form_entry["repeating_groups"] = repeating_groups

        self.forms.append(form_entry)

    def build(self) -> str:
        """XML 文字列を生成する。

        同じ form_code を持つフォームは1つの帳票要素にマージされる。
        例: KOA020 に P1(KOA020-1) と P2(KOA020-2) を add_form した場合、
        出力は <KOA020><KOA020-1>...</KOA020-1><KOA020-2>...</KOA020-2></KOA020>
        """
        # e-Tax スキーマバリデーションではデフォルト名前空間が必須
        default_ns = self._get_default_namespace()

        root = ET.Element("DATA", id="data0")
        root.set("xmlns", default_ns)
        root.set("xmlns:gen", NS_GENERAL)

        procedure_code, procedure_vr = self._get_procedure_info()
        procedure_el = ET.SubElement(root, procedure_code, id=procedure_code, VR=procedure_vr)

        ET.SubElement(procedure_el, "CATALOG", id="catalog0")
        contents = ET.SubElement(procedure_el, "CONTENTS", id="contents0")

        # IT部（共通ヘッダ）
        self._build_it_section(contents, procedure_code)

        # 同じ form_code のフォームをマージして出力
        form_elements: dict[str, ET.Element] = {}
        for form in self.forms:
            form_code = form["form_code"]
            if form_code not in form_elements:
                form_elements[form_code] = self._create_form_element(contents, form)
            self._populate_form_element(form_elements[form_code], form)

        # XML文字列化
        xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def save(self, path: Path) -> Path:
        """xtx ファイルを書き出す。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        xml_str = self.build()
        path.write_text(xml_str, encoding="utf-8")
        return path

    # ---- private ----

    def _get_default_namespace(self) -> str:
        """税区分に対応するデフォルト名前空間 URI を返す。"""
        if self.tax_type == "income":
            return NS_SHOTOKU
        return NS_SHOHI  # consumption / consumption_simplified

    def _get_procedure_info(self) -> tuple[str, str]:
        """手続コードとバージョンを返す。"""
        if self.tax_type == "income":
            return INCOME_TAX_PROCEDURE, INCOME_TAX_PROCEDURE_VR
        elif self.tax_type == "consumption":
            return CONSUMPTION_TAX_PROCEDURE, CONSUMPTION_TAX_PROCEDURE_VR
        else:
            # consumption_simplified
            return "RSH0030", CONSUMPTION_TAX_PROCEDURE_VR

    def _build_it_section(self, parent: ET.Element, procedure_code: str) -> None:
        """IT部（共通ヘッダ）を構築する。"""
        it = ET.SubElement(parent, "IT")
        info = self.taxpayer_info

        # 税務署
        zeimusho = ET.SubElement(it, "ZEIMUSHO", ID="ZEIMUSHO")
        _set_text(ET.SubElement(zeimusho, "zeimusho_CD"), info.get("tax_office_code", ""))
        _set_text(ET.SubElement(zeimusho, "zeimusho_NM"), info.get("tax_office_name", ""))

        # 提出年月日
        teisyutsu = ET.SubElement(it, "TEISYUTSU_DAY", ID="TEISYUTSU_DAY")
        _set_text(ET.SubElement(teisyutsu, "era"), str(ERA_CODES["reiwa"]))
        reiwa_year = self.creation_date.year - REIWA_BASE_YEAR + 1
        _set_text(ET.SubElement(teisyutsu, "yy"), str(reiwa_year))
        _set_text(ET.SubElement(teisyutsu, "mm"), str(self.creation_date.month))
        _set_text(ET.SubElement(teisyutsu, "dd"), str(self.creation_date.day))

        # 利用者識別番号
        if info.get("taxpayer_id"):
            _set_text(
                ET.SubElement(it, "NOZEISHA_ID", ID="NOZEISHA_ID"),
                info["taxpayer_id"],
            )

        # 個人番号
        if info.get("my_number"):
            bango = ET.SubElement(it, "NOZEISHA_BANGO", ID="NOZEISHA_BANGO")
            _set_text(ET.SubElement(bango, "kojinbango"), info["my_number"])

        # W4: 整理番号
        if info.get("seiribango"):
            _set_text(
                ET.SubElement(it, "SEIRIBANGO", ID="SEIRIBANGO"),
                info["seiribango"],
            )

        # 氏名フリガナ
        _set_text(
            ET.SubElement(it, "NOZEISHA_NM_KN", ID="NOZEISHA_NM_KN"),
            info.get("name_kana", ""),
        )

        # 氏名
        _set_text(
            ET.SubElement(it, "NOZEISHA_NM", ID="NOZEISHA_NM"),
            info.get("name", ""),
        )

        # 郵便番号
        zip_code = info.get("zip_code", "")
        if zip_code and len(zip_code) >= 7:
            zip_el = ET.SubElement(it, "NOZEISHA_ZIP", ID="NOZEISHA_ZIP")
            _set_text(ET.SubElement(zip_el, "zip1"), zip_code[:3])
            _set_text(ET.SubElement(zip_el, "zip2"), zip_code[3:7])

        # W5: 住所フリガナ
        if info.get("address_kana"):
            _set_text(
                ET.SubElement(it, "NOZEISHA_ADR_KN", ID="NOZEISHA_ADR_KN"),
                info["address_kana"],
            )

        # 住所
        _set_text(
            ET.SubElement(it, "NOZEISHA_ADR", ID="NOZEISHA_ADR"),
            info.get("address", ""),
        )

        # 地方自治体コード
        if info.get("address_code"):
            _set_text(
                ET.SubElement(it, "NOZEISHA_ADR_CODE", ID="NOZEISHA_ADR_CODE"),
                info["address_code"],
            )

        # 1月1日住所
        if info.get("jan1_address"):
            _set_text(
                ET.SubElement(it, "ICHIGATSUIPPI_ADR", ID="ICHIGATSUIPPI_ADR"),
                info["jan1_address"],
            )
        if info.get("jan1_address_code"):
            _set_text(
                ET.SubElement(it, "ICHIGATSUIPPI_ADR_CODE", ID="ICHIGATSUIPPI_ADR_CODE"),
                info["jan1_address_code"],
            )

        # 屋号
        if info.get("trade_name"):
            _set_text(
                ET.SubElement(it, "NOZEISHA_YAGO", ID="NOZEISHA_YAGO"),
                info["trade_name"],
            )

        # 電話番号
        if info.get("phone"):
            tel = info["phone"].replace("-", "")
            tel_el = ET.SubElement(it, "NOZEISHA_TEL", ID="NOZEISHA_TEL")
            # 簡易的に3分割（市外局番-市内局番-加入者番号）
            if len(tel) >= 10:
                _set_text(ET.SubElement(tel_el, "tel1"), tel[:3])
                _set_text(ET.SubElement(tel_el, "tel2"), tel[3:7])
                _set_text(ET.SubElement(tel_el, "tel3"), tel[7:])

        # 性別
        if info.get("gender"):
            seibetsu = ET.SubElement(it, "SEIBETSU", ID="SEIBETSU")
            _set_text(ET.SubElement(seibetsu, "kubun_CD"), info["gender"])

        # 生年月日
        if info.get("birthday"):
            self._build_birthday(it, info["birthday"])

        # 世帯主
        if info.get("household_head"):
            _set_text(
                ET.SubElement(it, "SETAINUSHI_NM", ID="SETAINUSHI_NM"),
                info["household_head"],
            )
        if info.get("household_relation"):
            _set_text(
                ET.SubElement(it, "SETAINUSHI_ZOKU", ID="SETAINUSHI_ZOKU"),
                info["household_relation"],
            )

        # 職業
        if info.get("occupation"):
            _set_text(
                ET.SubElement(it, "SHOKUGYO", ID="SHOKUGYO"),
                info["occupation"],
            )

        # 事業内容
        if info.get("business_description"):
            _set_text(
                ET.SubElement(it, "JIGYO_NAIYO", ID="JIGYO_NAIYO"),
                info["business_description"],
            )

        # W2: 還付金融機関
        if info.get("refund_bank_name"):
            kanpu = ET.SubElement(it, "KANPU_KINYUKIKAN", ID="KANPU_KINYUKIKAN")
            kinyukikan_nm = ET.SubElement(
                kanpu, "kinyukikan_NM", kinyukikan_KB=info.get("refund_bank_type", "1")
            )
            _set_text(kinyukikan_nm, info["refund_bank_name"])
            shiten_nm = ET.SubElement(
                kanpu, "shiten_NM", shiten_KB=info.get("refund_branch_type", "2")
            )
            _set_text(shiten_nm, info.get("refund_branch_name", ""))
            _set_text(ET.SubElement(kanpu, "yokin"), info.get("refund_deposit_type", ""))
            _set_text(ET.SubElement(kanpu, "koza"), info.get("refund_account_number", ""))

        # 手続き
        tetsuzuki = ET.SubElement(it, "TETSUZUKI", ID="TETSUZUKI")
        _set_text(ET.SubElement(tetsuzuki, "procedure_CD"), procedure_code)

        # 年分（NENBUN）
        nenbun = ET.SubElement(it, "NENBUN", ID="NENBUN")
        _set_text(ET.SubElement(nenbun, "era"), str(ERA_CODES["reiwa"]))
        _set_text(ET.SubElement(nenbun, "yy"), str(to_reiwa_year(self.fiscal_year)))

        # 申告区分
        shinkoku_kbn = ET.SubElement(it, "SHINKOKU_KBN", ID="SHINKOKU_KBN")
        _set_text(ET.SubElement(shinkoku_kbn, "kubun_CD"), "1")

        # W3: 計算書区分（所得税のみ）
        if self.tax_type == "income":
            keisansho_kbn = ET.SubElement(it, "KEISANSHO_KBN", ID="KEISANSHO_KBN")
            _set_text(ET.SubElement(keisansho_kbn, "kubun_CD"), "1")

    def _build_birthday(self, parent: ET.Element, birthday_str: str) -> None:
        """生年月日要素を構築する。YYYY-MM-DD 形式の文字列から和暦に変換。"""
        try:
            parts = birthday_str.split("-")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            return

        # 和暦変換（簡易版: 昭和・平成・令和のみ）
        if year >= 2019:
            era, yy = ERA_CODES["reiwa"], year - 2018
        elif year >= 1989:
            era, yy = ERA_CODES["heisei"], year - 1988
        elif year >= 1926:
            era, yy = ERA_CODES["showa"], year - 1925
        else:
            era, yy = ERA_CODES["taisho"], year - 1911

        birthday = ET.SubElement(parent, "BIRTHDAY", ID="BIRTHDAY")
        _set_text(ET.SubElement(birthday, "era"), str(era))
        _set_text(ET.SubElement(birthday, "yy"), str(yy))
        _set_text(ET.SubElement(birthday, "mm"), str(month))
        _set_text(ET.SubElement(birthday, "dd"), str(day))

    def _create_form_element(self, parent: ET.Element, form: dict[str, Any]) -> ET.Element:
        """帳票要素を作成する（属性のみ、中身なし）。"""
        attrs = {
            "VR": form["version"],
            "page": str(form.get("page", 1)),
            "softNM": self.software_name,
            "sakuseiNM": self.creator_name or self.taxpayer_info.get("name", ""),
            "sakuseiDay": self.creation_date.isoformat(),
        }
        return ET.SubElement(parent, form["form_code"], **attrs)

    def _populate_form_element(self, form_el: ET.Element, form: dict[str, Any]) -> None:
        """帳票要素にフィールドを配置する。

        FORM_NESTING に定義があるフォームは仕様準拠の階層構造で出力する。
        定義がないフォームはフラット構造で出力する（後方互換）。
        """
        nesting_key = form.get("nesting_key", form["form_code"])
        nesting_info = FORM_NESTING.get(nesting_key)

        if nesting_info:
            sub_section_name, field_groups = nesting_info
            # サブセクションラッパー（例: KOA020-1）
            if sub_section_name:
                target = ET.SubElement(form_el, sub_section_name)
            else:
                target = form_el
            self._build_nested_fields(target, form, field_groups)
        else:
            self._build_flat_fields(form_el, form)

    def _build_nested_fields(
        self,
        target: ET.Element,
        form: dict[str, Any],
        field_groups: dict[str, list[str]],
    ) -> None:
        """フィールドをグループ要素の階層構造に配置する。"""
        # IDREF 参照
        idrefs = form.get("idrefs", {})
        for code, ref_id in idrefs.items():
            ET.SubElement(target, code, IDREF=ref_id)

        # グループ要素のキャッシュ（同じパスを複数フィールドで共有）
        group_cache: dict[str, ET.Element] = {}

        # フィールド値をグループ構造に配置
        for code, value in form["fields"].items():
            group_path = field_groups.get(code)
            if group_path:
                parent_el = _ensure_group_path(target, group_path, group_cache)
            else:
                # グループ定義がないフィールドは target 直下
                parent_el = target
            _set_text(ET.SubElement(parent_el, code), _format_value(value))

        # 繰り返しグループもグループ構造内に配置
        repeating = form.get("repeating_groups", {})
        for group_code, items in repeating.items():
            # 繰り返しグループの親グループを探す
            # ABD00010 → ABD00000 の下に配置（field_groups に登録があれば）
            rp_parent_path = field_groups.get(group_code)
            if rp_parent_path:
                rp_parent = _ensure_group_path(target, rp_parent_path, group_cache)
            else:
                rp_parent = target
            for item in items:
                group_el = ET.SubElement(rp_parent, group_code)
                for child_code, child_value in item.items():
                    _set_text(
                        ET.SubElement(group_el, child_code),
                        _format_value(child_value),
                    )

        # サブセクション（手動指定、ネスト構造に加えて追加可能）
        sub_sections = form.get("sub_sections", {})
        for section_name, section_fields in sub_sections.items():
            section_el = ET.SubElement(target, section_name)
            for code, value in section_fields.items():
                if value is not None and value != 0:
                    _set_text(ET.SubElement(section_el, code), _format_value(value))

    def _build_flat_fields(self, form_el: ET.Element, form: dict[str, Any]) -> None:
        """フラット構造でフィールドを出力する（ネスト定義がないフォーム用）。"""
        # IDREF 参照
        idrefs = form.get("idrefs", {})
        for code, ref_id in idrefs.items():
            ET.SubElement(form_el, code, IDREF=ref_id)

        # フィールド値
        for code, value in form["fields"].items():
            _set_text(ET.SubElement(form_el, code), _format_value(value))

        # 繰り返しグループ
        repeating = form.get("repeating_groups", {})
        for group_code, items in repeating.items():
            for item in items:
                group_el = ET.SubElement(form_el, group_code)
                for child_code, child_value in item.items():
                    _set_text(
                        ET.SubElement(group_el, child_code),
                        _format_value(child_value),
                    )

        # サブセクション
        sub_sections = form.get("sub_sections", {})
        for section_name, section_fields in sub_sections.items():
            section_el = ET.SubElement(form_el, section_name)
            for code, value in section_fields.items():
                if value is not None and value != 0:
                    _set_text(ET.SubElement(section_el, code), _format_value(value))


def _ensure_group_path(
    root: ET.Element,
    path: list[str],
    cache: dict[str, ET.Element],
) -> ET.Element:
    """グループ要素のパスを辿り、存在しなければ作成する。

    Args:
        root: パスの起点となる親要素
        path: グループ要素名のリスト (例: ["ABB00000", "ABB00010"])
        cache: パス文字列 → Element のキャッシュ（同じグループを再利用）

    Returns:
        パス末端の Element
    """
    current = root
    key = ""
    for segment in path:
        key = f"{key}/{segment}" if key else segment
        if key in cache:
            current = cache[key]
        else:
            current = ET.SubElement(current, segment)
            cache[key] = current
    return current


def _set_text(element: ET.Element, text: str) -> None:
    """要素にテキストを設定する。サニタイズ済み。"""
    element.text = sanitize_text(text)


def _format_value(value: int | str) -> str:
    """値を XML テキスト用文字列に変換する。金額は int のみ（float 禁止）。"""
    if isinstance(value, int):
        return str(value)
    return str(value)
