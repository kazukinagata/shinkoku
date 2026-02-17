"""ABB code constants for e-Tax xtx XML generation.

NTA 仕様書から解析した ABB コードマッピング。
帳票コード別の定数辞書として管理する。
"""

from __future__ import annotations

# ============================================================
# 手続コードとバージョン
# ============================================================

# 所得税申告パッケージ
INCOME_TAX_PROCEDURE = "RKO0010"
INCOME_TAX_PROCEDURE_VR = "25.0.0"
INCOME_TAX_PROCEDURE_NAME = "所得税及び復興特別所得税申告"

# 消費税申告パッケージ（一般・個人）
CONSUMPTION_TAX_PROCEDURE = "RSH0010"
CONSUMPTION_TAX_PROCEDURE_VR = "23.2.0"
CONSUMPTION_TAX_PROCEDURE_NAME = "消費税及び地方消費税申告"

# 消費税申告パッケージ（簡易課税・個人）
CONSUMPTION_TAX_SIMPLIFIED_PROCEDURE = "RSH0030"
CONSUMPTION_TAX_SIMPLIFIED_PROCEDURE_VR = "23.2.0"

# ============================================================
# 名前空間
# ============================================================

NS_SHOTOKU = "http://xml.e-tax.nta.go.jp/XSD/shotoku"
NS_SHOHI = "http://xml.e-tax.nta.go.jp/XSD/shohi"
NS_GENERAL = "http://xml.e-tax.nta.go.jp/XSD/general"
NS_KYOTSU = "http://xml.e-tax.nta.go.jp/XSD/kyotsu"

# ============================================================
# 帳票コードとバージョン
# ============================================================

FORM_VERSIONS: dict[str, str] = {
    # 所得税申告書（第一表〜第四表）
    "KOA020": "23.0",
    # 青色申告決算書（一般用）
    "KOA210": "11.0",
    # 所得の内訳書
    "KOB060": "6.0",
    # 住宅借入金等特別控除額の計算明細書
    "KOB130": "21.0",
    # 医療費控除の明細書
    "KOB560": "18.0",
    # 消費税申告書（一般・個人）
    "SHA010": "10.0",
}

# CONTENTS 内の帳票出力順序（XSD の xsd:sequence 定義に準拠）
# 所得税手続 RKO0010 で使う帳票を XSD 定義順に並べる
FORM_ORDER: list[str] = [
    "KOA020",  # 申告書B
    "KOA210",  # 青色申告決算書（一般用）
    "KOB060",  # 所得の内訳書
    "KOB130",  # 住宅借入金等特別控除額の計算明細書
    "KOB560",  # 医療費控除の明細書
]

# ============================================================
# 和暦コード
# ============================================================

ERA_CODES: dict[str, int] = {
    "meiji": 1,
    "taisho": 2,
    "showa": 3,
    "heisei": 4,
    "reiwa": 5,
}

# 令和元年（2019年）
REIWA_BASE_YEAR = 2019


def to_reiwa_year(western_year: int) -> int:
    """西暦 → 令和年変換。"""
    return western_year - REIWA_BASE_YEAR + 1


# ============================================================
# 第一表 (KOA020-1) ABB コード
# ============================================================

# 収入金額等
INCOME_REVENUE_CODES: dict[str, str] = {
    "business_revenue": "ABB00030",  # ア: 営業等 収入
    "agriculture_revenue": "ABB00040",  # イ: 農業 収入
    "real_estate_revenue": "ABB00050",  # ウ: 不動産 収入
    "dividend_revenue": "ABB00070",  # エ: 配当 収入
    "salary_revenue": "ABB00080",  # オ: 給与 収入
    "pension_revenue": "ABB00100",  # カ: 公的年金等 収入
    "side_business_revenue": "ABB00105",  # キ: 業務 収入
    "other_revenue": "ABB00110",  # ク: その他 収入
    "short_term_transfer": "ABB00130",  # ケ: 総合譲渡 短期
    "long_term_transfer": "ABB00180",  # コ: 総合譲渡 長期
    "one_time_revenue": "ABB00230",  # サ: 一時 収入
}

# 所得金額等
INCOME_AMOUNT_CODES: dict[str, str] = {
    "business_income": "ABB00300",  # (1): 営業等 所得
    "agriculture_income": "ABB00320",  # (2): 農業 所得
    "real_estate_income": "ABB00340",  # (3): 不動産 所得
    "interest_income": "ABB00350",  # (4): 利子 所得
    "dividend_income": "ABB00360",  # (5): 配当 所得
    "salary_income": "ABB00370",  # (6): 給与 所得
    "pension_income": "ABB01060",  # (7): 公的年金等 所得
    "side_business_income": "ABB01090",  # (8): 業務 所得
    "other_income": "ABB01120",  # (9): その他 所得
    "misc_subtotal": "ABB01130",  # (10): (7)〜(9)の計
    "transfer_one_time": "ABB00400",  # (11): 総合譲渡・一時 所得
    "total_income": "ABB00410",  # (12): 合計 所得
}

# 所得から差し引かれる金額
DEDUCTION_CODES: dict[str, str] = {
    "casualty_loss": "ABB00430",  # (13): 雑損控除
    "medical_expense": "ABB00440",  # (14): 医療費控除
    "social_insurance": "ABB00450",  # (15): 社会保険料控除
    "small_enterprise": "ABB00460",  # (16): 小規模企業共済等掛金控除
    "life_insurance": "ABB00470",  # (17): 生命保険料控除
    "earthquake_insurance": "ABB00480",  # (18): 地震保険料控除
    "donation": "ABB00490",  # (19): 寄附金控除
    "widow_single_parent": "ABB00500",  # (20): 寡婦、ひとり親控除
    "student_disability": "ABB00510",  # (21): 勤労学生、障害者控除
    "spouse": "ABB00520",  # (22): 配偶者(特別)控除
    "dependent": "ABB00540",  # (23): 扶養控除
    "specified_relative": "ABB00548",  # (24): 特定親族特別控除
    "basic": "ABB00550",  # (25): 基礎控除
    "subtotal_13_25": "ABB00555",  # (26): (13)〜(25)の計
    "total_deductions": "ABB00560",  # (29): 合計
}

# 税金の計算
TAX_CALCULATION_CODES: dict[str, str] = {
    "taxable_income": "ABB00580",  # (31): 課税される所得金額
    "tax_on_taxable_income": "ABB00590",  # (32): (31)に対する税額
    "dividend_credit": "ABB00600",  # (33): 配当控除
    "housing_loan_credit": "ABB00650",  # (34): 住借金等特別控除
    "political_donation_credit": "ABB00660",  # (35): 政党等寄附金等特別控除
    "housing_seismic_credit": "ABB00663",  # (36): 住宅耐震改修特別控除等
    "income_tax_after_credits": "ABB00670",  # (37): 差引所得税額
    "disaster_reduction": "ABB00680",  # (38): 災害減免額
    "income_tax_net": "ABB01010",  # (39): 再差引所得税額
    "reconstruction_tax": "ABB01020",  # (40): 復興特別所得税額
    "total_income_tax": "ABB01030",  # (41): 所得税等の額
    "foreign_tax_credit": "ABB01040",  # (42): 外国税額控除等
    "withheld_tax": "ABB00710",  # (48): 源泉徴収税額
    "tax_due": "ABB00720",  # (49): 申告納税額
    "estimated_tax": "ABB00730",  # (50): 予定納税額
    "third_installment": "ABB00740",  # (51): 第3期分の税額
    "tax_to_pay": "ABB00750",  # (52): 納める税金
    "tax_refund": "ABB00760",  # (53): 還付される税金
}

# その他（第一表）
OTHER_P1_CODES: dict[str, str] = {
    "pension_other_income": "ABB00775",  # 公的年金等以外の合計所得金額
    "spouse_income": "ABB00780",  # 配偶者の合計所得金額
    "family_employee_salary": "ABB00790",  # 専従者給与（控除）額の合計額
    "blue_return_deduction": "ABB00800",  # 青色申告特別控除額
    "misc_withheld_tax": "ABB00810",  # 雑所得・一時所得等の源泉徴収税額
    "loss_carryforward": "ABB00830",  # 本年分で差し引く繰越損失額
}

# ============================================================
# 第二表 (KOA020-2) ABD/ABH/ABI コード
# ============================================================

# 所得の内訳（繰り返し）
INCOME_DETAIL_CODES: dict[str, str] = {
    "income_type": "ABD00020",  # 所得の種類
    "category": "ABD00025",  # 種目
    "payer_number": "ABD00030",  # 支払者の法人番号/所在地
    "payer_name": "ABD00040",  # 支払者の名称
    "revenue": "ABD00050",  # 収入金額
    "withheld_tax": "ABD00060",  # 源泉徴収税額
}
INCOME_DETAIL_TOTAL_CODE = "ABD00070"  # 源泉徴収税額の合計額

# 社会保険料等の明細
SOCIAL_INSURANCE_DETAIL_CODES: dict[str, str] = {
    "insurance_type": "ABH00130",  # 保険料等の種類
    "premium_total": "ABH00140",  # 支払保険料等の計
    "new_life_insurance": "ABH00215",  # 新生命保険料
    "old_life_insurance": "ABH00220",  # 旧生命保険料
    "new_annuity_insurance": "ABH00225",  # 新個人年金保険料
    "old_annuity_insurance": "ABH00230",  # 旧個人年金保険料
    "medical_care_insurance": "ABH00235",  # 介護医療保険料
    "earthquake_insurance": "ABH00250",  # 地震保険料
    "old_long_term_insurance": "ABH00260",  # 旧長期損害保険料
    "donation_detail": "ABH00300",  # 寄附金
}

# 住民税・事業税
RESIDENT_TAX_CODES: dict[str, str] = {
    "collection_method": "ABI00010",  # 住民税 徴収方法
    "unlisted_small_dividend": "ABI00090",  # 非上場株式の少額配当等
    "dividend_credit": "ABI00104",  # 配当割額控除額
    "stock_transfer_credit": "ABI00106",  # 株式等譲渡所得割額控除額
    "prefecture_municipality_donation": "ABI00240",  # 都道府県・市区町村への寄附
    "joint_fundraising": "ABI00250",  # 共同募金・日赤
    "prefecture_designated": "ABI00270",  # 都道府県条例指定寄附
    "municipality_designated": "ABI00280",  # 市区町村条例指定寄附
    "business_tax_exempt": "ABI00120",  # 事業税 非課税所得
    "pre_offset_real_estate": "ABI00150",  # 損益通算の特例適用前の不動産所得
    "real_estate_blue_deduction": "ABI00170",  # 不動産所得から差し引いた青色控除額
}

# ============================================================
# 青色申告決算書 (KOA210) AMF/AMG コード — 一般用
# ============================================================

# 損益計算書
PL_CODES: dict[str, str] = {
    "revenue": "AMF00100",  # (1): 売上（収入）金額
    "beginning_inventory": "AMF00120",  # 期首商品棚卸高
    "purchases": "AMF00130",  # 仕入金額
    "cogs_subtotal": "AMF00140",  # 小計（期首＋仕入）
    "ending_inventory": "AMF00150",  # 期末商品棚卸高
    "cost_of_goods": "AMF00160",  # 差引原価
    "gross_profit": "AMF00170",  # 差引金額
    "tax_and_dues": "AMF00190",  # 租税公課
    "packing_shipping": "AMF00200",  # 荷造運賃
    "utilities": "AMF00210",  # 水道光熱費
    "travel": "AMF00220",  # 旅費交通費
    "communication": "AMF00230",  # 通信費
    "advertising": "AMF00240",  # 広告宣伝費
    "entertainment": "AMF00250",  # 接待交際費
    "insurance": "AMF00260",  # 損害保険料
    "repairs": "AMF00270",  # 修繕費
    "supplies": "AMF00280",  # 消耗品費
    "depreciation": "AMF00290",  # 減価償却費
    "welfare": "AMF00300",  # 福利厚生費
    "salaries": "AMF00310",  # 給料賃金
    "outsourcing": "AMF00320",  # 外注工賃
    "interest_discount": "AMF00330",  # 利子割引料
    "rent": "AMF00340",  # 地代家賃
    "bad_debt": "AMF00350",  # 貸倒金
    "miscellaneous": "AMF00370",  # 雑費
    "total_expense": "AMF00380",  # 経費計
    "operating_profit": "AMF00390",  # 差引金額
    "family_salary": "AMF00460",  # 専従者給与
    "pre_deduction_income_upper": "AMF00500",  # 青色申告特別控除前の所得金額(上段)
    "pre_deduction_income_lower": "AMF00505",  # 青色申告特別控除前の所得金額(下段)
    "blue_return_deduction": "AMF00510",  # 青色申告特別控除額
    "net_income": "AMF00530",  # (43): 所得金額
}

# 貸借対照表（期首・期末）
BS_CODES_BEGINNING: dict[str, str] = {
    "cash": "AMG00060",
    "checking": "AMG00070",
    "time_deposit": "AMG00080",
    "other_deposit": "AMG00090",
    "notes_receivable": "AMG00100",
    "accounts_receivable": "AMG00110",
    "securities": "AMG00120",
    "inventory": "AMG00130",
    "prepaid": "AMG00140",
    "loans_receivable": "AMG00150",
    "buildings": "AMG00160",
    "building_fixtures": "AMG00170",
    "machinery": "AMG00180",
    "vehicles": "AMG00190",
    "tools_equipment": "AMG00200",
    "land": "AMG00210",
    "total_assets": "AMG00230",
}

BS_CODES_ENDING: dict[str, str] = {
    "cash": "AMG00260",
    "checking": "AMG00270",
    "time_deposit": "AMG00280",
    "other_deposit": "AMG00290",
    "notes_receivable": "AMG00300",
    "accounts_receivable": "AMG00310",
    "securities": "AMG00320",
    "inventory": "AMG00330",
    "prepaid": "AMG00340",
    "loans_receivable": "AMG00350",
    "buildings": "AMG00360",
    "building_fixtures": "AMG00370",
    "machinery": "AMG00380",
    "vehicles": "AMG00390",
    "tools_equipment": "AMG00400",
    "land": "AMG00410",
    "owner_lending": "AMG00430",  # 事業主貸（期末のみ）
    "total_assets": "AMG00440",
}

BS_LIABILITIES_BEGINNING: dict[str, str] = {
    "notes_payable": "AMG00510",
    "accounts_payable": "AMG00520",
    "borrowings": "AMG00530",
    "accrued_expenses": "AMG00540",
    "advances_received": "AMG00550",
    "deposits_received": "AMG00560",
    "allowance_bad_debt": "AMG00580",
    "capital": "AMG00600",
}

BS_LIABILITIES_ENDING: dict[str, str] = {
    "notes_payable": "AMG00640",
    "accounts_payable": "AMG00650",
    "borrowings": "AMG00660",
    "accrued_expenses": "AMG00670",
    "advances_received": "AMG00680",
    "deposits_received": "AMG00690",
    "allowance_bad_debt": "AMG00710",
    "owner_borrowing": "AMG00730",  # 事業主借（期末のみ）
    "capital": "AMG00740",
    "blue_return_income": "AMG00750",  # 青色申告特別控除前の所得金額
    "total_liabilities": "AMG00760",
}

# --- KOA210-4: 貸借対照表（BS）フィールドグループ ---
# XSD: KOA210-4 > AMG00000 > AMG00020(資産) > AMG00240(期末) > AMG002xx
#                           > AMG00450(負債) > AMG00620(期末) > AMG006xx
_BS_ASSET_ENDING_PATH = ["AMG00000", "AMG00020", "AMG00240"]
_BS_LIABILITY_ENDING_PATH = ["AMG00000", "AMG00450", "AMG00620"]

BS_FIELD_GROUPS: dict[str, list[str]] = {}
# 資産の部（期末）: AMG00260〜AMG00440
for _code in BS_CODES_ENDING.values():
    BS_FIELD_GROUPS[_code] = _BS_ASSET_ENDING_PATH
# 負債の部（期末）: AMG00640〜AMG00760
for _code in BS_LIABILITIES_ENDING.values():
    BS_FIELD_GROUPS[_code] = _BS_LIABILITY_ENDING_PATH

# 期首パス（XSD: KOA210-4 > AMG00000 > AMG00020(資産) > AMG00040(期首)）
_BS_ASSET_BEGINNING_PATH = ["AMG00000", "AMG00020", "AMG00040"]
_BS_LIABILITY_BEGINNING_PATH = ["AMG00000", "AMG00450", "AMG00490"]

# 資産の部（期首）: AMG00060〜AMG00230
for _code in BS_CODES_BEGINNING.values():
    BS_FIELD_GROUPS[_code] = _BS_ASSET_BEGINNING_PATH
# 負債の部（期首）: AMG00510〜AMG00600
for _code in BS_LIABILITIES_BEGINNING.values():
    BS_FIELD_GROUPS[_code] = _BS_LIABILITY_BEGINNING_PATH

# ============================================================
# 消費税申告書 (SHA010) AAJ/AAK コード
# ============================================================

CONSUMPTION_TAX_CODES: dict[str, str] = {
    "taxable_base": "AAJ00010",  # (1): 課税標準額
    "consumption_tax": "AAJ00020",  # (2): 消費税額
    "excess_adjustment": "AAJ00030",  # (3): 控除過大調整税額
    "deductible_purchase_tax": "AAJ00050",  # (4): 控除対象仕入税額
    "returned_goods_tax": "AAJ00060",  # (5): 返還等対価に係る税額
    "bad_debt_tax": "AAJ00070",  # (6): 貸倒れに係る税額
    "deduction_subtotal": "AAJ00080",  # (7): 控除税額小計
    "refund_shortfall": "AAJ00090",  # (8): 控除不足還付税額
    "net_tax": "AAJ00100",  # (9): 差引税額
    "interim_payment": "AAJ00110",  # (10): 中間納付税額
    "tax_due": "AAJ00120",  # (11): 納付税額
    "interim_refund": "AAJ00130",  # (12): 中間納付還付税額
    "taxable_transfer_amount": "AAJ00180",  # 課税資産の譲渡等の対価の額
    "total_transfer_amount": "AAJ00190",  # 資産の譲渡等の対価の額
}

# 地方消費税
LOCAL_CONSUMPTION_TAX_CODES: dict[str, str] = {
    "tax_base": "AAK00010",  # 地方消費税の課税標準
    "transfer_tax": "AAK00040",  # 譲渡割額
    "local_tax_due": "AAK00060",  # 納税額
    "paid_transfer_tax": "AAK00080",  # 納付譲渡割額
    "total_tax_due": "AAK00130",  # 消費税及び地方消費税の合計額
}

# ============================================================
# 医療費控除明細書 (KOB560) DHC/DHD/DHE コード
# ============================================================

MEDICAL_EXPENSE_DETAIL_CODES: dict[str, str] = {
    "patient_name": "DHC00020",  # 医療を受けた方の氏名
    "institution_name": "DHC00050",  # 病院・薬局などの支払先の名称
    "amount_paid": "DHC00080",  # 支払った医療費の額
    "insurance_amount": "DHC00090",  # 保険等で補填される金額
}
MEDICAL_EXPENSE_SUMMARY_CODES: dict[str, str] = {
    "total_paid": "DHD00010",  # 支払った医療費（合計）
    "total_insurance": "DHD00020",  # 保険金などで補填される金額
    "net_amount": "DHD00030",  # 差引金額
    "total_income": "DHD00040",  # 所得金額の合計額
    "medical_deduction": "DHD00070",  # 医療費控除額
    "notice_self_pay": "DHE00010",  # 医療費通知の自己負担額
    "notice_actual_pay": "DHE00020",  # 実際に支払った医療費の額
    "notice_insurance": "DHE00030",  # 補填される金額
}

# ============================================================
# 住宅借入金等特別控除 (KOB130) HAA/HAB コード
# ============================================================

HOUSING_LOAN_CODES: dict[str, str] = {
    "address": "HAB00010",
    "name": "HAB00060",
    "fiscal_year": "HAB10000",
    "credit_amount": "HAA80040",  # 住宅借入金等特別控除額
    "credit_r4_r5": "HAA50100",  # 令和4-5年入居
    "credit_used_renovation": "HAA50120",  # 中古・増改築
}

# ============================================================
# 第一表 見出し部 (ABA) コード — IDREF 参照用
# ============================================================

P1_HEADER_IDREFS: dict[str, str] = {
    "ABA00010": "NENBUN",
    "ABA00020": "SHINKOKU_KBN",
    "ABA00030": "ZEIMUSHO",
    "ABA00040": "TEISYUTSU_DAY",
    "ABA00080": "NOZEISHA_ZIP",
    "ABA00090": "NOZEISHA_ADR",
    "ABA00125": "NOZEISHA_BANGO",
    "ABA00130": "NOZEISHA_NM_KN",
    "ABA00140": "NOZEISHA_NM",
    "ABA00160": "SHOKUGYO",
    "ABA00170": "NOZEISHA_YAGO",
    "ABA00200": "BIRTHDAY",
    "ABA00220": "NOZEISHA_TEL",
}

# 第一表 見出し部 IDREF グループネスト
# XSD: KOA020-1 > ABA00000 > ABA00010/20/30/40 + ABA00050 > ABA00060 > ABA00080/90
#                                                            + ABA00125〜ABA00220
P1_HEADER_IDREF_GROUPS: dict[str, list[str]] = {
    "ABA00010": ["ABA00000"],
    "ABA00020": ["ABA00000"],
    "ABA00030": ["ABA00000"],
    "ABA00040": ["ABA00000"],
    "ABA00080": ["ABA00000", "ABA00050", "ABA00060"],
    "ABA00090": ["ABA00000", "ABA00050", "ABA00060"],
    "ABA00125": ["ABA00000", "ABA00050"],
    "ABA00130": ["ABA00000", "ABA00050"],
    "ABA00140": ["ABA00000", "ABA00050"],
    "ABA00160": ["ABA00000", "ABA00050"],
    "ABA00170": ["ABA00000", "ABA00050"],
    "ABA00200": ["ABA00000", "ABA00050"],
    "ABA00220": ["ABA00000", "ABA00050"],
}

# 第二表 見出し部 IDREF
P2_HEADER_IDREFS: dict[str, str] = {
    "ABC00010": "NENBUN",
    "ABC00040": "NOZEISHA_ADR",
    "ABC00060": "NOZEISHA_NM_KN",
    "ABC00070": "NOZEISHA_NM",
}

# 第二表 見出し部 IDREF グループネスト
# XSD: KOA020-2 > ABC00000 > ABC00010 + ABC00020 > ABC00040/60/70
P2_HEADER_IDREF_GROUPS: dict[str, list[str]] = {
    "ABC00010": ["ABC00000"],
    "ABC00040": ["ABC00000", "ABC00020"],
    "ABC00060": ["ABC00000", "ABC00020"],
    "ABC00070": ["ABC00000", "ABC00020"],
}

# ============================================================
# XML ネスト構造定義
# ============================================================
#
# e-Tax スキーマ準拠のグループ要素構造。
# 各帳票の ABB コードをどの親グループ要素の下に配置するかを定義する。
# 構造: {グループ要素名: [子要素名またはABBコードのリスト]}
# ABBコードは値ノードとして出力、グループ要素名は中間構造ノードとして出力。
#
# field_code → group_code のルックアップはビルダー側で構築する。

# --- KOA020-1: 第一表 ---
# ABA00000 見出し部: IDREF のみで構成されるため別途処理
# ABB00000 金額部: 以下の4グループ + その他直下フィールド

# ABB00010 > ABB00020: 収入金額グループ（ア〜サ）
P1_REVENUE_GROUP_CODES = frozenset(
    {
        "ABB00030",
        "ABB00040",
        "ABB00050",
        "ABB00070",
        "ABB00080",
        "ABB00100",
        "ABB00105",
        "ABB00110",
        "ABB00130",
        "ABB00180",
        "ABB00230",
    }
)

# ABB00270: 所得金額グループ（(1)〜(12)）
P1_INCOME_GROUP_CODES = frozenset(
    {
        "ABB00300",
        "ABB00320",
        "ABB00340",
        "ABB00350",
        "ABB00360",
        "ABB00370",
        "ABB01060",
        "ABB01090",
        "ABB01120",
        "ABB01130",
        "ABB00400",
        "ABB00410",
    }
)

# ABB00420: 所得控除グループ（(13)〜(29)）
P1_DEDUCTION_GROUP_CODES = frozenset(
    {
        "ABB00430",
        "ABB00440",
        "ABB00450",
        "ABB00460",
        "ABB00470",
        "ABB00480",
        "ABB00490",
        "ABB00500",
        "ABB00510",
        "ABB00520",
        "ABB00540",
        "ABB00548",
        "ABB00550",
        "ABB00555",
        "ABB00560",
    }
)

# ABB00570: 税金の計算グループ（(31)〜(53)）
# 注: ABB00740 はグループ要素（第3期分の税額）。ABB00750/ABB00760 がその子要素。
P1_TAX_CALC_GROUP_CODES = frozenset(
    {
        "ABB00580",
        "ABB00590",
        "ABB00600",
        "ABB00650",
        "ABB00660",
        "ABB00663",
        "ABB00670",
        "ABB00680",
        "ABB01010",
        "ABB01020",
        "ABB01030",
        "ABB01040",
        "ABB00710",
        "ABB00720",
        "ABB00730",
        "ABB00750",
        "ABB00760",
    }
)

# ABB00000 直下のその他フィールド
P1_OTHER_DIRECT_CODES = frozenset(
    {
        "ABB00775",
        "ABB00780",
        "ABB00790",
        "ABB00800",
        "ABB00810",
        "ABB00830",
        "ABB00950",
    }
)

# 第一表の ABB フィールドからグループへのマッピング
# キー: ABB コード、値: (グループ要素のパス)
# パス例: ["ABB00000", "ABB00010"] は ABB00000 > ABB00010 の下に配置
# XSD 準拠: 中間グループ要素（ABB00020, ABB00090 等）を正しく含める
P1_FIELD_GROUPS: dict[str, list[str]] = {}

# 収入金額等 (ABB00010) — XSD に準拠した中間グループ
# ABB00020: 事業グループ（営業等・農業）
for _code in ("ABB00030", "ABB00040"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00010", "ABB00020"]
# ABB00010 直下: 不動産・配当・給与
for _code in ("ABB00050", "ABB00070", "ABB00080"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00010"]
# ABB00090: 雑グループ（公的年金等・業務・その他）
for _code in ("ABB00100", "ABB00105", "ABB00110"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00010", "ABB00090"]
# ABB00120: 総合譲渡グループ（短期・長期）
for _code in ("ABB00130", "ABB00180"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00010", "ABB00120"]
# ABB00010 直下: 一時
P1_FIELD_GROUPS["ABB00230"] = ["ABB00000", "ABB00010"]

# 所得金額等 (ABB00270) — XSD に準拠した中間グループ
# ABB00280: 事業グループ（営業等・農業）
for _code in ("ABB00300", "ABB00320"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00270", "ABB00280"]
# ABB00270 直下: 不動産・利子・配当・給与
for _code in ("ABB00340", "ABB00350", "ABB00360", "ABB00370"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00270"]
# ABB01050: 雑グループ
P1_FIELD_GROUPS["ABB01060"] = ["ABB00000", "ABB00270", "ABB01050"]  # 公的年金等
# ABB01070: 業務（ABB01050 > ABB01070 > ABB01090）
P1_FIELD_GROUPS["ABB01090"] = ["ABB00000", "ABB00270", "ABB01050", "ABB01070"]
# ABB01100: その他（ABB01050 > ABB01100 > ABB01120）
P1_FIELD_GROUPS["ABB01120"] = ["ABB00000", "ABB00270", "ABB01050", "ABB01100"]
# ABB01050 直下: (7)〜(9)の計
P1_FIELD_GROUPS["ABB01130"] = ["ABB00000", "ABB00270", "ABB01050"]
# ABB00270 直下: 総合譲渡・一時、合計
for _code in ("ABB00400", "ABB00410"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00270"]

# 所得控除 (ABB00420) — XSD に準拠
for _code in P1_DEDUCTION_GROUP_CODES:
    if _code == "ABB00548":
        # ABB00542: 特定親族特別控除グループ
        P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00420", "ABB00542"]
    else:
        P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00420"]

# 税金の計算 (ABB00570) — XSD に準拠
for _code in P1_TAX_CALC_GROUP_CODES:
    if _code in ("ABB00750", "ABB00760"):
        # ABB00740: 第3期分の税額グループ
        P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00570", "ABB00740"]
    elif _code == "ABB00740":
        # ABB00740 自体はグループ要素（値ノードではない）なのでスキップ
        continue
    else:
        P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00570"]

# その他 (ABB00770) — XSD に準拠
# ABB00775〜ABB00830 は ABB00770（その他）グループの下
for _code in ("ABB00775", "ABB00780", "ABB00790", "ABB00800", "ABB00810", "ABB00830"):
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00770"]
# ABB00950 は ABB00940（還付金受取場所）グループの下
P1_FIELD_GROUPS["ABB00950"] = ["ABB00000", "ABB00940"]

# 第一表 見出し部 IDREF のグループパスも P1_FIELD_GROUPS に統合
# XSD: KOA020-1 > ABA00000 > ABA00010/20/30/40
#                           > ABA00050 > ABA00060 > ABA00080/90
#                                      > ABA00125〜ABA00220
P1_FIELD_GROUPS.update(P1_HEADER_IDREF_GROUPS)

# --- KOA020-2: 第二表 ---
# ABD00000 > ABD00010(繰り返し) + ABD00070
P2_FIELD_GROUPS: dict[str, list[str]] = {
    "ABD00070": ["ABD00000"],
    # 繰り返しグループの親パス
    "ABD00010": ["ABD00000"],  # 所得の内訳 繰り返し
    "ABH00120": [
        "ABH00000",
        "ABH00110",
    ],  # 社会保険料等の明細 繰り返し（XSD: ABH00000>ABH00110>ABH00120）
}
# ABD00010 繰り返しグループは ABD00000 の下
P2_REPEATING_PARENT = "ABD00000"

# 第二表 見出し部 IDREF のグループパスも P2_FIELD_GROUPS に統合
# XSD: KOA020-2 > ABC00000 > ABC00010 + ABC00020 > ABC00040/60/70
P2_FIELD_GROUPS.update(P2_HEADER_IDREF_GROUPS)

# --- KOA210: 青色申告決算書 PL ---
# XSD 準拠: AMF00000 > AMF00010 > AMF00090 > 各フィールド
# AMF00090(金額) の下に売上・原価・経費・控除・所得が並ぶ
PL_EXPENSE_GROUP_CODES = frozenset(
    {
        "AMF00190",
        "AMF00200",
        "AMF00210",
        "AMF00220",
        "AMF00230",
        "AMF00240",
        "AMF00250",
        "AMF00260",
        "AMF00270",
        "AMF00280",
        "AMF00290",
        "AMF00300",
        "AMF00310",
        "AMF00320",
        "AMF00330",
        "AMF00340",
        "AMF00350",
        "AMF00370",
        "AMF00380",
    }
)

# 売上原価（AMF00110 グループの子要素）
PL_COGS_GROUP_CODES = frozenset(
    {
        "AMF00120",  # 期首商品棚卸高
        "AMF00130",  # 仕入金額
        "AMF00140",  # 小計
        "AMF00150",  # 期末商品棚卸高
        "AMF00160",  # 差引原価
    }
)

# AMF00090 直下のフィールド（売上、差引金額、青色控除前所得、青色控除額、所得金額）
_PL_AMF90_PATH = ["AMF00000", "AMF00010", "AMF00090"]

PL_FIELD_GROUPS: dict[str, list[str]] = {
    "AMF00100": _PL_AMF90_PATH,  # 売上（収入）金額
    "AMF00170": _PL_AMF90_PATH,  # 差引金額（売上−原価）
    "AMF00390": _PL_AMF90_PATH,  # 差引金額（粗利−経費）
    "AMF00460": [*_PL_AMF90_PATH, "AMF00400", "AMF00450"],  # 専従者給与
    "AMF00500": _PL_AMF90_PATH,  # 青色申告特別控除前の所得金額(上段)
    "AMF00505": _PL_AMF90_PATH,  # 青色申告特別控除前の所得金額(下段)
    "AMF00510": _PL_AMF90_PATH,  # 青色申告特別控除額
    "AMF00530": _PL_AMF90_PATH,  # 所得金額
}
# 売上原価
for _code in PL_COGS_GROUP_CODES:
    PL_FIELD_GROUPS[_code] = [*_PL_AMF90_PATH, "AMF00110"]
# 経費
for _code in PL_EXPENSE_GROUP_CODES:
    PL_FIELD_GROUPS[_code] = [*_PL_AMF90_PATH, "AMF00180"]

# --- SHA010: 消費税 ---
# XSD 準拠: AAJ00000 > フィールド + AAJ00040(控除税額) + AAJ00170(課税売上割合)
# AAJ00000 直下
CT_AAJ_DIRECT_CODES = frozenset(
    {
        "AAJ00010",  # 課税標準額
        "AAJ00020",  # 消費税額
        "AAJ00030",  # 控除過大調整税額
        "AAJ00090",  # 控除不足還付税額
        "AAJ00100",  # 差引税額
        "AAJ00110",  # 中間納付税額
        "AAJ00120",  # 納付税額
        "AAJ00130",  # 中間納付還付税額
    }
)
# AAJ00040: 控除税額グループ
CT_AAJ_DEDUCTION_CODES = frozenset(
    {
        "AAJ00050",  # 控除対象仕入税額
        "AAJ00060",  # 返還等対価に係る税額
        "AAJ00070",  # 貸倒れに係る税額
        "AAJ00080",  # 控除税額小計
    }
)
# AAJ00170: 課税売上割合グループ
CT_AAJ_RATIO_CODES = frozenset(
    {
        "AAJ00180",  # 課税資産の譲渡等の対価の額
        "AAJ00190",  # 資産の譲渡等の対価の額
    }
)
CT_AAK_CODES = frozenset(
    {
        "AAK00010",
        "AAK00040",
        "AAK00060",
        "AAK00080",
        "AAK00130",
    }
)

CT_FIELD_GROUPS: dict[str, list[str]] = {}
for _code in CT_AAJ_DIRECT_CODES:
    CT_FIELD_GROUPS[_code] = ["AAJ00000"]
for _code in CT_AAJ_DEDUCTION_CODES:
    CT_FIELD_GROUPS[_code] = ["AAJ00000", "AAJ00040"]
for _code in CT_AAJ_RATIO_CODES:
    CT_FIELD_GROUPS[_code] = ["AAJ00000", "AAJ00170"]
for _code in CT_AAK_CODES:
    CT_FIELD_GROUPS[_code] = ["AAK00000"]

# ============================================================
# KOB060: 所得の内訳書 ネスト構造
# ============================================================
# KOB060 > BFA00000(納税者等部) + BFB00000(年分) + BFC00000(繰り返し)
# BFA00000 は IDREF のみ → idrefs で処理
# BFC00000 は繰り返しグループ → repeating_groups で処理
# BFC00030(支払者) > BFC00050(名称), BFC00055(住所・法人番号), BFC00060(電話)
# BFC00090(源泉徴収税額欄) > BFC00100(源泉徴収税額), BFC00110(内書き)

KOB060_FIELD_GROUPS: dict[str, list[str]] = {
    # BFA00000 納税者等部（IDREF を BFA00000 の中に配置）
    "BFA00010": ["BFA00000"],  # 住所 IDREF
    "BFA00020": ["BFA00000"],  # 氏名 IDREF
    # BFB00000 は KOB060 直下（グループ定義なし）
    # BFC00000 は繰り返しグループとして処理される
    # BFC00030 内の子要素のグループパス
    "BFC00050": ["BFC00030"],  # 支払者の氏名・名称
    "BFC00055": ["BFC00030"],  # 支払者の住所・法人番号
    "BFC00060": ["BFC00030"],  # 電話番号
    # BFC00090 内の子要素のグループパス
    "BFC00100": ["BFC00090"],  # 源泉徴収税額
    "BFC00110": ["BFC00090"],  # 源泉徴収税額（内書き）
}

# ============================================================
# KOB130: 住宅借入金等特別控除 ネスト構造
# ============================================================
# KOB130 > KOB130-1(一面) > 深い階層構造
# HAB00000(住所・氏名) > HAB00010(住所) > HAB00020/30/40 + HAB00050 + HAB00060
# HAD00000(家屋等) > HAD00010(家屋) > HAD00020/30/40/50 + HAD00060(土地) > HAD00070/80/90/100
# HAE30000(不動産番号) > HAE30010/20
# HAE20000(消費税) > HAE20010(税率区分) > HAE20013/16/19 + HAE20020
# HAF00000(取得対価) > HAF00010(家屋) > HAF00020(持分) > HAF00030/40 + HAF00043/47/50
#                    + HAF00060(土地) > HAF00070(持分) > HAF00080/90 + HAF00093/97/100
#                    + HAF00110(合計) > HAF00113/117/120
#                    + HAF00130(増改築) > HAF00140(持分) > HAF00150/160 + HAF00163/167/170
# HAG00000(年末残高) > HAG00005 + HAG00010(住宅のみ) > HAG00020/30/40/50/60/70
#                    + HAG00080(土地のみ) > HAG00090/100/110/120/130/140
#                    + HAG00150(住宅+土地) > HAG00160/170/180/190/200/210
#                    + HAG00220(増改築) > HAG00230/250/270/290/310/330
#                    + HAG00355
# HAM00000(控除額) > HAM00015/020/042/044/046/048/050

KOB130_P1_FIELD_GROUPS: dict[str, list[str]] = {
    # HAB00000 住所・氏名
    "HAB00020": ["HAB00000", "HAB00010"],  # 郵便番号 IDREF
    "HAB00030": ["HAB00000", "HAB00010"],  # 住所 IDREF
    "HAB00040": ["HAB00000", "HAB00010"],  # 電話番号 IDREF
    "HAB00050": ["HAB00000"],  # フリガナ IDREF
    "HAB00060": ["HAB00000"],  # 氏名 IDREF
    # HAD00000 家屋等に係る事項
    "HAD00020": ["HAD00000", "HAD00010"],  # 居住開始年月日
    "HAD00110": ["HAD00000", "HAD00010"],  # 契約日契約区分（グループ）
    "HAD00115": ["HAD00000", "HAD00010", "HAD00110"],  # 契約区分
    "HAD00130": ["HAD00000", "HAD00010", "HAD00110"],  # 契約日
    "HAD00023": ["HAD00000", "HAD00010"],  # 補助金等控除前の取得対価
    "HAD00027": ["HAD00000", "HAD00010"],  # 補助金等の額
    "HAD00030": ["HAD00000", "HAD00010"],  # 取得対価の額
    "HAD00040": ["HAD00000", "HAD00010"],  # 総面積
    "HAD00050": ["HAD00000", "HAD00010"],  # 居住用部分面積
    # 土地等に関する事項
    "HAD00070": ["HAD00000", "HAD00060"],  # 居住開始年月日
    "HAD00073": ["HAD00000", "HAD00060"],  # 補助金等控除前
    "HAD00077": ["HAD00000", "HAD00060"],  # 補助金等の額
    "HAD00080": ["HAD00000", "HAD00060"],  # 取得対価の額
    "HAD00090": ["HAD00000", "HAD00060"],  # 総面積
    "HAD00100": ["HAD00000", "HAD00060"],  # 居住用部分面積
    # HAE30000 不動産番号
    "HAE30010": ["HAE30000"],  # 家屋
    "HAE30020": ["HAE30000"],  # 土地
    # HAE20000 消費税
    "HAE20013": ["HAE20000", "HAE20010"],  # なし又は5%
    "HAE20016": ["HAE20000", "HAE20010"],  # 8%
    "HAE20019": ["HAE20000", "HAE20010"],  # 10%
    "HAE20020": ["HAE20000"],  # 消費税額合計
    # HAF00000 取得対価の額
    # (A) 家屋
    "HAF00030": ["HAF00000", "HAF00010", "HAF00020"],  # 共有持分 分子
    "HAF00040": ["HAF00000", "HAF00010", "HAF00020"],  # 共有持分 分母
    "HAF00043": ["HAF00000", "HAF00010"],  # 取得対価*持分
    "HAF00047": ["HAF00000", "HAF00010"],  # 贈与特例
    "HAF00050": ["HAF00000", "HAF00010"],  # あなたの取得対価
    # (B) 土地等
    "HAF00080": ["HAF00000", "HAF00060", "HAF00070"],  # 共有持分 分子
    "HAF00090": ["HAF00000", "HAF00060", "HAF00070"],  # 共有持分 分母
    "HAF00093": ["HAF00000", "HAF00060"],  # 取得対価*持分
    "HAF00097": ["HAF00000", "HAF00060"],  # 贈与特例
    "HAF00100": ["HAF00000", "HAF00060"],  # あなたの取得対価
    # (C) 合計
    "HAF00113": ["HAF00000", "HAF00110"],  # 取得対価*持分
    "HAF00117": ["HAF00000", "HAF00110"],  # 贈与特例
    "HAF00120": ["HAF00000", "HAF00110"],  # あなたの取得対価
    # (D) 増改築等
    "HAF00150": ["HAF00000", "HAF00130", "HAF00140"],  # 共有持分 分子
    "HAF00160": ["HAF00000", "HAF00130", "HAF00140"],  # 共有持分 分母
    "HAF00163": ["HAF00000", "HAF00130"],  # 取得対価*持分
    "HAF00167": ["HAF00000", "HAF00130"],  # 贈与特例
    "HAF00170": ["HAF00000", "HAF00130"],  # あなたの取得対価
    # HAG00000 住宅借入金等の年末残高
    "HAG00005": ["HAG00000"],  # 区分
    # (E) 住宅のみ
    "HAG00020": ["HAG00000", "HAG00010"],  # 年末残高
    "HAG00030": ["HAG00000", "HAG00010"],  # 連帯債務割合
    "HAG00040": ["HAG00000", "HAG00010"],  # 年末残高（負担後）
    "HAG00050": ["HAG00000", "HAG00010"],  # min(取得対価, 年末残高)
    "HAG00060": ["HAG00000", "HAG00010"],  # 居住用割合
    "HAG00070": ["HAG00000", "HAG00010"],  # 居住用部分の年末残高
    # (F) 土地等のみ
    "HAG00090": ["HAG00000", "HAG00080"],
    "HAG00100": ["HAG00000", "HAG00080"],
    "HAG00110": ["HAG00000", "HAG00080"],
    "HAG00120": ["HAG00000", "HAG00080"],
    "HAG00130": ["HAG00000", "HAG00080"],
    "HAG00140": ["HAG00000", "HAG00080"],
    # (G) 住宅及び土地等
    "HAG00160": ["HAG00000", "HAG00150"],
    "HAG00170": ["HAG00000", "HAG00150"],
    "HAG00180": ["HAG00000", "HAG00150"],
    "HAG00190": ["HAG00000", "HAG00150"],
    "HAG00200": ["HAG00000", "HAG00150"],
    "HAG00210": ["HAG00000", "HAG00150"],
    # (H) 増改築等
    "HAG00230": ["HAG00000", "HAG00220"],
    "HAG00250": ["HAG00000", "HAG00220"],
    "HAG00270": ["HAG00000", "HAG00220"],
    "HAG00290": ["HAG00000", "HAG00220"],
    "HAG00310": ["HAG00000", "HAG00220"],
    "HAG00330": ["HAG00000", "HAG00220"],
    # 合計額
    "HAG00355": ["HAG00000"],
    # HAM00000 控除額
    "HAM00015": ["HAM00000"],  # 番号
    "HAM00020": ["HAM00000"],  # 控除額
    "HAM00042": ["HAM00000"],  # 8%・10%同一年中取得
    "HAM00044": ["HAM00000"],  # 家屋・増改築等
    "HAM00046": ["HAM00000"],  # (ウ)又は(ソ)の金額
    "HAM00048": ["HAM00000"],  # (A)(4)又は(D)(4)
    "HAM00050": ["HAM00000"],  # 重複適用
    # HAA60000, HAA70000 は KOB130-1 直下
}

# ============================================================
# 所得の内訳書 (KOB060) BFA/BFC コード
# ============================================================

INCOME_BREAKDOWN_CODES: dict[str, str] = {
    # BFA00000 納税者等部（IDREF）
    "address_ref": "BFA00010",  # 住所 IDREF
    "name_ref": "BFA00020",  # 氏名 IDREF
    # BFB00000 年分（IDREF）
    "fiscal_year_ref": "BFB00000",  # 年分 IDREF
    # BFC00000 繰り返し
    "income_type": "BFC00010",  # 所得の種類
    "category": "BFC00020",  # 種目
    "payer_name": "BFC00050",  # 支払者の氏名・名称
    "payer_address": "BFC00055",  # 支払者の住所・法人番号
    "payer_phone": "BFC00060",  # 電話番号
    "asset_quantity": "BFC00075",  # 資産の数量
    "revenue": "BFC00080",  # 収入金額
    "withheld_tax": "BFC00100",  # 源泉徴収税額
    "withheld_tax_inner": "BFC00110",  # 源泉徴収税額（内書き）
    "payment_date": "BFC00120",  # 支払確定年月
}

# KOB060 IDREF 参照マッピング
KOB060_HEADER_IDREFS: dict[str, str] = {
    "BFA00010": "NOZEISHA_ADR",
    "BFA00020": "NOZEISHA_NM",
    "BFB00000": "NENBUN",
}

# KOB130 IDREF 参照マッピング
KOB130_HEADER_IDREFS: dict[str, str] = {
    "HAA00000": "NENBUN",
    "HAB00020": "NOZEISHA_ZIP",
    "HAB00030": "NOZEISHA_ADR",
    "HAB00040": "NOZEISHA_TEL",
    "HAB00050": "NOZEISHA_NM_KN",
    "HAB00060": "NOZEISHA_NM",
}

# ============================================================
# XSD sequence 順序オーバーライド
# ============================================================
# ABBコードの昇順と XSD の xsd:sequence 順序が一致しない場合のオーバーライド。
# キー: 親グループ要素のパス末尾、値: コードのリスト（XSD 定義順）。
# ABB00570 グループは ABB01010-01040 が ABB00680 と ABB00710 の間に挿入される。
XSD_SEQUENCE_ORDER: dict[str, list[str]] = {
    # KOA020-1 ABB00570 グループ: ABB01010-01040 が ABB00680 と ABB00710 の間
    "ABB00570": [
        "ABB00580",
        "ABB00590",
        "ABB00600",
        "ABB00610",
        "ABB00620",
        "ABB00630",
        "ABB00640",
        "ABB00645",
        "ABB00647",
        "ABB00650",
        "ABB00660",
        "ABB00960",
        "ABB01000",
        "ABB00663",
        "ABB00670",
        "ABB00676",
        "ABB00680",
        "ABB01010",
        "ABB01020",
        "ABB01030",
        "ABB01040",
        "ABB00710",
        "ABB00720",
        "ABB00730",
        "ABB00740",
        "ABB00750",
        "ABB00760",
        "ABB00763",
        "ABB00765",
        "ABB00767",
        "ABB00770",
    ],
}

# トップレベルグループの XSD 順序（グループパスの先頭要素でソートする際に使用）
# field_code のグループパス先頭要素を XSD 定義順に並べる
XSD_TOPLEVEL_ORDER: dict[str, list[str]] = {
    # KOB130-1: HAE30000(不動産番号) は HAE20000(消費税率) の前
    "KOB130-1": [
        "HAA00000",
        "HAB00000",
        "HAC00000",
        "HAD00000",
        "HAE00000",
        "HAE30000",
        "HAE20000",
        "HAF00000",
        "HAG00000",
        "HAL00000",
        "HAM00000",
    ],
}

# フォームコード → (サブセクション名, フィールドグループマッピング) の辞書
# ビルダーがフォーム追加時にネスト構造を自動適用するために使用
FORM_NESTING: dict[str, tuple[str | None, dict[str, list[str]]]] = {
    # KOA020 は呼び出し元が KOA020-1/KOA020-2 を指定して add_form する想定
    "KOA020-1": ("KOA020-1", P1_FIELD_GROUPS),
    "KOA020-2": ("KOA020-2", P2_FIELD_GROUPS),
    # KOA210 は KOA210-1(PL一面), KOA210-4(BS) をサブセクションとして持つ
    "KOA210": ("KOA210-1", PL_FIELD_GROUPS),
    "KOA210-4": ("KOA210-4", BS_FIELD_GROUPS),
    "SHA010": (None, CT_FIELD_GROUPS),
    # KOB060: 所得の内訳書（フラット + 繰り返しグループ）
    "KOB060": (None, KOB060_FIELD_GROUPS),
    # KOB130: 住宅借入金等特別控除（一面: 深い階層構造）
    "KOB130-1": ("KOB130-1", KOB130_P1_FIELD_GROUPS),
}
