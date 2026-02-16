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
    FORM_ORDER,
    INCOME_TAX_PROCEDURE,
    INCOME_TAX_PROCEDURE_VR,
    NS_GENERAL,
    NS_SHOHI,
    NS_SHOTOKU,
    REIWA_BASE_YEAR,
    XSD_SEQUENCE_ORDER,
    XSD_TOPLEVEL_ORDER,
    to_reiwa_year,
)

# gen 名前空間プレフィックスを登録（IT部の子要素で使用）
ET.register_namespace("gen", NS_GENERAL)

# gen: 名前空間のタグ名ヘルパー
_GEN = f"{{{NS_GENERAL}}}"


def _gen(tag: str) -> str:
    """gen: 名前空間付きタグ名を返す。"""
    return f"{_GEN}{tag}"


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

        root = ET.Element("DATA", id="DATA")
        root.set("xmlns", default_ns)
        # xmlns:gen は ET.register_namespace("gen", NS_GENERAL) により
        # gen名前空間の子要素が存在すると自動付与される。
        # 明示的に set すると重複属性エラーになるため省略。

        procedure_code, procedure_vr = self._get_procedure_info()
        procedure_el = ET.SubElement(root, procedure_code, id=procedure_code, VR=procedure_vr)

        # CATALOG — e-Tax 確定申告書作成コーナーは CATALOG 内の FORM_SEC を読んで
        # 帳票一覧を認識する。rdf:RDF > rdf:description > IT_SEC + FORM_SEC 構造が必要。
        self._build_catalog(procedure_el)

        contents = ET.SubElement(procedure_el, "CONTENTS", id="CONTENTS")

        # IT部（共通ヘッダ）
        self._build_it_section(contents, procedure_code)

        # XSD の xsd:sequence に準拠した帳票出力順序でソート
        sorted_forms = sorted(
            self.forms,
            key=lambda f: (
                FORM_ORDER.index(f["form_code"])
                if f["form_code"] in FORM_ORDER
                else len(FORM_ORDER)
            ),
        )

        # 同じ form_code のフォームをマージして出力
        form_elements: dict[str, ET.Element] = {}
        for form in sorted_forms:
            form_code = form["form_code"]
            if form_code not in form_elements:
                form_elements[form_code] = self._create_form_element(contents, form)
            self._populate_form_element(form_elements[form_code], form)

        # XML文字列化
        # e-Tax 確定申告書作成コーナーは XML 宣言の直後に DATA 要素が来ることを要求する。
        # newline 不可、standalone 不可、余分な空白不可。
        xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
        # xmlns 属性の順序を e-Tax が期待する形式に修正:
        # xmlns（デフォルト名前空間）を最初に配置する
        xml_str = self._reorder_data_xmlns(xml_str)
        return f'<?xml version="1.0" encoding="UTF-8"?>{xml_str}'

    def save(self, path: Path) -> Path:
        """xtx ファイルを書き出す。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        xml_str = self.build()
        path.write_text(xml_str, encoding="utf-8")
        return path

    # ---- private ----

    @staticmethod
    def _reorder_data_xmlns(xml_str: str) -> str:
        """DATA 要素の xmlns 属性順序を e-Tax が期待する形式に修正する。

        ElementTree は属性を辞書順に出力するため、xmlns:gen, xmlns:rdf が
        xmlns（デフォルト名前空間）より先に来てしまう。
        e-Tax パーサーはこの順序に敏感な可能性があるため、
        xmlns を先頭に移動する。
        """
        import re

        # DATA タグの属性を抽出して並び替え
        data_pattern = re.compile(r"<DATA\s+(.*?)>", re.DOTALL)
        match = data_pattern.search(xml_str)
        if not match:
            return xml_str

        attrs_str = match.group(1)
        # 属性を分割: key="value" のペアを抽出
        attr_pattern = re.compile(r'(\S+?)="([^"]*?)"')
        attrs = attr_pattern.findall(attrs_str)

        # xmlns（デフォルト）を先頭、idを次に、その後は残りの属性
        xmlns_default = []
        id_attr = []
        others = []
        for key, val in attrs:
            if key == "xmlns":
                xmlns_default.append((key, val))
            elif key == "id":
                id_attr.append((key, val))
            else:
                others.append((key, val))

        reordered = xmlns_default + others + id_attr
        new_attrs = " ".join(f'{k}="{v}"' for k, v in reordered)
        return xml_str[: match.start()] + f"<DATA {new_attrs}>" + xml_str[match.end() :]

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

    def _build_catalog(self, procedure_el: ET.Element) -> None:
        """CATALOG セクションを構築する。

        e-Tax 確定申告書作成コーナーは CATALOG > rdf:RDF > rdf:description 内の
        FORM_SEC を読んで帳票一覧を認識する。
        構造: CATALOG > rdf:RDF > rdf:description(id=REPORT) >
              SEND_DATA + IT_SEC + FORM_SEC(> rdf:Seq > rdf:li...)
        """
        ns_rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        ET.register_namespace("rdf", ns_rdf)

        catalog = ET.SubElement(procedure_el, "CATALOG", id="CATALOG")
        rdf_rdf = ET.SubElement(catalog, f"{{{ns_rdf}}}RDF")
        rdf_desc = ET.SubElement(rdf_rdf, f"{{{ns_rdf}}}Description", id="REPORT")

        # SEND_DATA（空要素）
        ET.SubElement(rdf_desc, "SEND_DATA")

        # IT_SEC: IT部への参照
        it_sec = ET.SubElement(rdf_desc, "IT_SEC")
        ET.SubElement(it_sec, f"{{{ns_rdf}}}Description", about="#IT")

        # FORM_SEC: 帳票セクション一覧
        # 同じ form_code のエントリは nesting_key で区別される
        form_sec = ET.SubElement(rdf_desc, "FORM_SEC")
        rdf_seq = ET.SubElement(form_sec, f"{{{ns_rdf}}}Seq")

        # フォームを出力順にソート
        sorted_forms = sorted(
            self.forms,
            key=lambda f: (
                FORM_ORDER.index(f["form_code"])
                if f["form_code"] in FORM_ORDER
                else len(FORM_ORDER)
            ),
        )
        for form in sorted_forms:
            nesting_key = form.get("nesting_key", form["form_code"])
            rdf_li = ET.SubElement(rdf_seq, f"{{{ns_rdf}}}li")
            ET.SubElement(rdf_li, f"{{{ns_rdf}}}Description", about=nesting_key)

    def _build_it_section(self, parent: ET.Element, procedure_code: str) -> None:
        """IT部（共通ヘッダ）を構築する。

        IT部の子要素のうち、汎用データ型（zeimusho_CD, era, yy, mm, dd,
        kubun_CD, zip1, zip2, tel1-3, kojinbango, procedure_CD,
        kinyukikan_NM, shiten_NM, yokin, koza）は general 名前空間で出力する。
        """
        # IT VR は 1.5（最新版）
        it = ET.SubElement(parent, "IT", id="IT", VR="1.5")
        info = self.taxpayer_info

        # 税務署
        zeimusho = ET.SubElement(it, "ZEIMUSHO", ID="ZEIMUSHO")
        _set_gen_text(ET.SubElement(zeimusho, _gen("zeimusho_CD")), info.get("tax_office_code", ""))
        _set_gen_text(ET.SubElement(zeimusho, _gen("zeimusho_NM")), info.get("tax_office_name", ""))

        # 提出年月日
        teisyutsu = ET.SubElement(it, "TEISYUTSU_DAY", ID="TEISYUTSU_DAY")
        _set_gen_text(ET.SubElement(teisyutsu, _gen("era")), str(ERA_CODES["reiwa"]))
        reiwa_year = self.creation_date.year - REIWA_BASE_YEAR + 1
        _set_gen_text(ET.SubElement(teisyutsu, _gen("yy")), str(reiwa_year))
        _set_gen_text(ET.SubElement(teisyutsu, _gen("mm")), str(self.creation_date.month))
        _set_gen_text(ET.SubElement(teisyutsu, _gen("dd")), str(self.creation_date.day))

        # 利用者識別番号（XSD必須）
        _set_text(
            ET.SubElement(it, "NOZEISHA_ID", ID="NOZEISHA_ID"),
            info.get("taxpayer_id", ""),
        )

        # 個人番号
        if info.get("my_number"):
            bango = ET.SubElement(it, "NOZEISHA_BANGO", ID="NOZEISHA_BANGO")
            _set_gen_text(ET.SubElement(bango, _gen("kojinbango")), info["my_number"])

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
            _set_gen_text(ET.SubElement(zip_el, _gen("zip1")), zip_code[:3])
            _set_gen_text(ET.SubElement(zip_el, _gen("zip2")), zip_code[3:7])

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
            if len(tel) >= 10:
                _set_gen_text(ET.SubElement(tel_el, _gen("tel1")), tel[:3])
                _set_gen_text(ET.SubElement(tel_el, _gen("tel2")), tel[3:7])
                _set_gen_text(ET.SubElement(tel_el, _gen("tel3")), tel[7:])

        # 性別
        # kubun_CD は shotoku 名前空間（デフォルト）で出力
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

        # 事業内容（XSD: JIGYO_NAIYO は SHOKUGYO より前）
        if info.get("business_description"):
            _set_text(
                ET.SubElement(it, "JIGYO_NAIYO", ID="JIGYO_NAIYO"),
                info["business_description"],
            )

        # 職業
        if info.get("occupation"):
            _set_text(
                ET.SubElement(it, "SHOKUGYO", ID="SHOKUGYO"),
                info["occupation"],
            )

        # W2: 還付金融機関
        if info.get("refund_bank_name"):
            kanpu = ET.SubElement(it, "KANPU_KINYUKIKAN", ID="KANPU_KINYUKIKAN")
            kinyukikan_nm = ET.SubElement(
                kanpu,
                _gen("kinyukikan_NM"),
                kinyukikan_KB=info.get("refund_bank_type", "1"),
            )
            _set_gen_text(kinyukikan_nm, info["refund_bank_name"])
            shiten_nm = ET.SubElement(
                kanpu,
                _gen("shiten_NM"),
                shiten_KB=info.get("refund_branch_type", "2"),
            )
            _set_gen_text(shiten_nm, info.get("refund_branch_name", ""))
            _set_gen_text(ET.SubElement(kanpu, _gen("yokin")), info.get("refund_deposit_type", ""))
            _set_gen_text(ET.SubElement(kanpu, _gen("koza")), info.get("refund_account_number", ""))

        # 手続き
        # procedure_CD は RKO0010 XSD でローカル要素として再定義されており、
        # shotoku 名前空間（デフォルト）で出力する
        tetsuzuki = ET.SubElement(it, "TETSUZUKI", ID="TETSUZUKI")
        _set_text(ET.SubElement(tetsuzuki, "procedure_CD"), procedure_code)

        # 年分（NENBUN）
        nenbun = ET.SubElement(it, "NENBUN", ID="NENBUN")
        _set_gen_text(ET.SubElement(nenbun, _gen("era")), str(ERA_CODES["reiwa"]))
        _set_gen_text(ET.SubElement(nenbun, _gen("yy")), str(to_reiwa_year(self.fiscal_year)))

        # 申告区分
        # kubun_CD は RKO0010 XSD でローカル要素として再定義されており、
        # shotoku 名前空間（デフォルト）で出力する必要がある（gen: ではない）
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
        _set_gen_text(ET.SubElement(birthday, _gen("era")), str(era))
        _set_gen_text(ET.SubElement(birthday, _gen("yy")), str(yy))
        _set_gen_text(ET.SubElement(birthday, _gen("mm")), str(month))
        _set_gen_text(ET.SubElement(birthday, _gen("dd")), str(day))

    def _create_form_element(self, parent: ET.Element, form: dict[str, Any]) -> ET.Element:
        """帳票要素を作成する（属性のみ、中身なし）。

        id属性は最初のページの nesting_key（例: "KOA020-1"）を使用。
        e-Tax 確定申告書作成コーナーはこの id を CATALOG の about 属性と照合する。
        """
        nesting_key = form.get("nesting_key", form["form_code"])
        attrs = {
            "VR": form["version"],
            "id": nesting_key,
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
            self._build_nested_fields(
                target, form, field_groups, section_name=sub_section_name or nesting_key
            )
        else:
            self._build_flat_fields(form_el, form)

    def _build_nested_fields(
        self,
        target: ET.Element,
        form: dict[str, Any],
        field_groups: dict[str, list[str]],
        *,
        section_name: str = "",
    ) -> None:
        """フィールドをグループ要素の階層構造に配置する。

        XSD の xsd:sequence に準拠するため、全要素をコード順にソートして出力する。
        IDREF参照・フィールド値・繰り返しグループを統合的にソートし、
        ABBコードの昇順（= XSD定義順）で配置する。
        """
        # グループ要素のキャッシュ（同じパスを複数フィールドで共有）
        group_cache: dict[str, ET.Element] = {}

        # 全要素を (code, type, data) のタプルとして収集
        all_items: list[tuple[str, str, Any]] = []

        # IDREF 参照
        idrefs = form.get("idrefs", {})
        for code, ref_id in idrefs.items():
            all_items.append((code, "idref", ref_id))

        # フィールド値
        for code, value in form["fields"].items():
            all_items.append((code, "field", value))

        # 繰り返しグループ
        repeating = form.get("repeating_groups", {})
        for group_code, items in repeating.items():
            all_items.append((group_code, "repeating", items))

        # XSD sequence 順にソート
        # 1. トップレベルグループの XSD 定義順 (XSD_TOPLEVEL_ORDER)
        # 2. 同じ親グループ内で XSD_SEQUENCE_ORDER に定義がある場合はその順序
        # 3. それ以外はコード昇順（ABBコードの昇順 ≒ XSD定義順）
        toplevel_seq = XSD_TOPLEVEL_ORDER.get(section_name, [])

        def _sort_key(item: tuple[str, str, Any]) -> tuple[int, str, int, str]:
            code = item[0]
            group_path = field_groups.get(code, [])
            # トップレベルグループの順序（グループパスの先頭要素）
            top_group = group_path[0] if group_path else code
            if toplevel_seq and top_group in toplevel_seq:
                top_order = toplevel_seq.index(top_group)
            else:
                top_order = len(toplevel_seq)
            # 親グループ内の順序
            # グループパスの各レベルで XSD_SEQUENCE_ORDER を探索し、
            # 最も近い祖先グループの順序を使う。
            # 例: ABB00760 の group_path = [ABB00000, ABB00570, ABB00740]
            #   → ABB00740 は XSD_SEQUENCE_ORDER に定義なし
            #   → ABB00570 に ABB00740 がある → ABB00740 の位置を使う
            parent_group = group_path[-1] if group_path else ""
            seq = XSD_SEQUENCE_ORDER.get(parent_group)
            if seq and code in seq:
                return (top_order, top_group, seq.index(code), code)
            # 親グループに定義がない場合、祖先グループの順序で位置を決定
            # （子要素のコードは親グループ要素と同じ位置に配置される）
            for i in range(len(group_path) - 1, 0, -1):
                ancestor_group = group_path[i - 1]
                ancestor_seq = XSD_SEQUENCE_ORDER.get(ancestor_group)
                if ancestor_seq and group_path[i] in ancestor_seq:
                    return (top_order, top_group, ancestor_seq.index(group_path[i]), code)
            return (top_order, top_group, len(XSD_SEQUENCE_ORDER.get(parent_group, [])), code)

        all_items.sort(key=_sort_key)

        for code, item_type, data in all_items:
            group_path = field_groups.get(code)
            if group_path:
                parent_el = _ensure_group_path(target, group_path, group_cache)
            else:
                parent_el = target

            if item_type == "idref":
                ET.SubElement(parent_el, code, IDREF=data)
            elif item_type == "field":
                if isinstance(data, dict):
                    _build_structured_field(parent_el, code, data)
                else:
                    _set_text(ET.SubElement(parent_el, code), _format_value(data))
            elif item_type == "repeating":
                for item in data:
                    group_el = ET.SubElement(parent_el, code)
                    item_cache: dict[str, ET.Element] = {}
                    for child_code, child_value in item.items():
                        child_group_path = field_groups.get(child_code)
                        if child_group_path:
                            child_parent = _ensure_group_path(
                                group_el, child_group_path, item_cache
                            )
                        else:
                            child_parent = group_el
                        _set_text(
                            ET.SubElement(child_parent, child_code),
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
            if isinstance(value, dict):
                _build_structured_field(form_el, code, value)
            else:
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


def _set_gen_text(element: ET.Element, text: str) -> None:
    """gen: 名前空間要素にテキストを設定する。サニタイズ済み。"""
    element.text = sanitize_text(text)


_GEN_NAMESPACE_TAGS = frozenset(
    {
        "era",
        "yy",
        "mm",
        "dd",  # gen:yymmdd, gen:yy 型
    }
)


def _build_structured_field(parent: ET.Element, code: str, value: dict[str, str]) -> None:
    """構造化フィールドを適切な名前空間の子要素として出力する。

    gen:yymmdd (era/yy/mm/dd) の子要素は general 名前空間で出力。
    gen:kubun/procedure の子要素 (kubun_CD/procedure_CD) は
    帳票スキーマ内でローカル再定義されるため、デフォルト名前空間で出力。
    """
    el = ET.SubElement(parent, code)
    for child_tag, child_text in value.items():
        # era/yy/mm/dd は gen:yymmdd 型から来るため gen 名前空間
        if child_tag in _GEN_NAMESPACE_TAGS:
            tag = _gen(child_tag)
        else:
            # kubun_CD 等は帳票 XSD でローカル再定義されるためデフォルト名前空間
            tag = child_tag
        child = ET.SubElement(el, tag)
        child.text = sanitize_text(str(child_text))


def _format_value(value: int | str) -> str:
    """値を XML テキスト用文字列に変換する。金額は int のみ（float 禁止）。"""
    if isinstance(value, int):
        return str(value)
    return str(value)
