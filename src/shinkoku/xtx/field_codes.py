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
    # 先物取引繰越損失付表
    "KOA050": "17.0",
    # 上場株式等繰越損失付表
    "KOA090": "16.0",
    # 収支内訳書（一般用）
    "KOA110": "12.0",
    # 収支内訳書（不動産所得用）
    "KOA130": "9.0",
    # 青色申告決算書（一般用）
    "KOA210": "11.0",
    # 青色申告決算書（不動産所得用）
    "KOA220": "8.0",
    # 所得の内訳書
    "KOB060": "6.0",
    # 住宅借入金等特別控除額の計算明細書
    "KOB130": "21.0",
    # 政党等寄附金特別控除額の計算明細書
    "KOB200": "17.0",
    # 外国税額控除に関する明細書
    "KOB240": "16.0",
    # 先物取引に係る雑所得等の計算明細書
    "KOB550": "14.0",
    # 医療費控除の明細書
    "KOB560": "18.0",
    # 株式等に係る譲渡所得等の計算明細書
    "KOC080": "19.0",
    # 消費税申告書（一般・個人）
    "SHA010": "10.0",
}

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
# 第三表 (KOA020-3) ABL コード — 分離課税用
# ============================================================

# 分離課税 収入金額
SEPARATE_REVENUE_CODES: dict[str, str] = {
    "short_term_general": "ABL00040",  # (67): 短期譲渡 一般分
    "short_term_reduced": "ABL00050",  # (68): 短期譲渡 軽減分
    "long_term_general": "ABL00070",  # (69): 長期譲渡 一般分
    "long_term_specified": "ABL00080",  # (70): 長期譲渡 特定分
    "long_term_reduced": "ABL00090",  # (71): 長期譲渡 軽課分
    "general_stock": "ABL00125",  # (72): 一般株式等の譲渡
    "listed_stock": "ABL00130",  # (73): 上場株式等の譲渡
    "listed_dividend": "ABL00134",  # (74): 上場株式等の配当等
    "futures": "ABL00140",  # (75): 先物取引
    "timber": "ABL00170",  # (76): 山林
    "retirement": "ABL00180",  # (77): 退職
}

# 分離課税 所得金額
SEPARATE_INCOME_CODES: dict[str, str] = {
    "short_term_general": "ABL00220",  # (67)
    "short_term_reduced": "ABL00230",  # (68)
    "long_term_general": "ABL00250",  # (69)
    "long_term_specified": "ABL00260",  # (70)
    "long_term_reduced": "ABL00270",  # (71)
    "general_stock": "ABL00305",  # (72)
    "listed_stock": "ABL00310",  # (73)
    "listed_dividend": "ABL00320",  # (74)
    "futures": "ABL00330",  # (75)
    "timber": "ABL00360",  # (76)
    "retirement": "ABL00410",  # (77)
}

# 分離課税 税金の計算
SEPARATE_TAX_CODES: dict[str, str] = {
    "comprehensive_total": "ABL00440",  # (78): 総合課税の合計額
    "deductions": "ABL00450",  # (79): 所得から差し引かれる金額
    "taxable_comprehensive": "ABL00470",  # (80): 課税所得 (12)対応分
    "taxable_short_term": "ABL00480",  # (81): 課税所得 (67)(68)対応分
    "taxable_long_term": "ABL00490",  # (82): 課税所得 (69)(70)(71)対応分
    "taxable_stock": "ABL00500",  # (83): 課税所得 (72)(73)対応分
    "taxable_listed_dividend": "ABL00505",  # (84): 課税所得 (74)対応分
    "taxable_futures": "ABL00510",  # (85): 課税所得 (75)対応分
    "taxable_timber": "ABL00520",  # (86): 課税所得 (76)対応分
    "taxable_retirement": "ABL00530",  # (87): 課税所得 (77)対応分
    "tax_comprehensive": "ABL00550",  # (88): 税額 (78)対応分
    "tax_deductions": "ABL00560",  # (89): 税額 (79)対応分
    "tax_short_term": "ABL00570",  # (90): 税額 (80)対応分
    "tax_long_term": "ABL00580",  # (91): 税額 (81)対応分
    "tax_stock": "ABL00585",  # (92): 税額 (82)対応分
    "tax_listed_dividend": "ABL00590",  # (93): 税額 (83)対応分
    "tax_futures": "ABL00600",  # (84)対応分
    "tax_timber": "ABL00610",  # (85)対応分
    "tax_total": "ABL00620",  # (94): (86)〜(93)の合計
}

# ============================================================
# 青色申告決算書 (KOA210) AMF/AMG コード — 一般用
# ============================================================

# 損益計算書
PL_CODES: dict[str, str] = {
    "revenue": "AMF00100",  # (1): 売上（収入）金額
    "beginning_inventory": "AMF00120",  # 期首商品棚卸高
    "purchases": "AMF00130",  # 仕入金額
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
# 先物取引 (KOB550) DGD コード
# ============================================================

FUTURES_DETAIL_CODES: dict[str, str] = {
    "type": "DGD00090",
    "settlement_date": "DGD00100",
    "quantity": "DGD00110",
    "settlement_method": "DGD00120",
    "profit_loss": "DGD00140",
    "total_revenue": "DGD00160",
    "fees": "DGD00180",
    "total_expenses": "DGD00260",
    "net_income": "DGD00270",
}

# ============================================================
# 株式等譲渡 (KOC080) EHD コード
# ============================================================

STOCK_TRANSFER_CODES: dict[str, str] = {
    "general_stock_section": "EHD00030",
    "general_revenue": "EHD00050",
    "general_cost": "EHD00090",
    "general_fees": "EHD00100",
    "general_net": "EHD00140",
    "general_income": "EHD00160",
    "listed_stock_section": "EHD00190",
    "listed_revenue": "EHD00210",
    "listed_cost": "EHD00250",
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

# 第二表 見出し部 IDREF
P2_HEADER_IDREFS: dict[str, str] = {
    "ABC00010": "NENBUN",
    "ABC00040": "NOZEISHA_ADR",
    "ABC00060": "NOZEISHA_NM_KN",
    "ABC00070": "NOZEISHA_NM",
}

# 第三表 見出し部 IDREF
P3_HEADER_IDREFS: dict[str, str] = {
    "ABK00010": "NENBUN",
    "ABK00060": "NOZEISHA_ADR",
    "ABK00070": "NOZEISHA_NM_KN",
    "ABK00080": "NOZEISHA_NM",
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
        "ABB00740",
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
P1_FIELD_GROUPS: dict[str, list[str]] = {}
for _code in P1_REVENUE_GROUP_CODES:
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00010"]
for _code in P1_INCOME_GROUP_CODES:
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00270"]
for _code in P1_DEDUCTION_GROUP_CODES:
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00420"]
for _code in P1_TAX_CALC_GROUP_CODES:
    P1_FIELD_GROUPS[_code] = ["ABB00000", "ABB00570"]
for _code in P1_OTHER_DIRECT_CODES:
    P1_FIELD_GROUPS[_code] = ["ABB00000"]

# --- KOA020-2: 第二表 ---
# ABD00000 > ABD00010(繰り返し) + ABD00070
P2_FIELD_GROUPS: dict[str, list[str]] = {
    "ABD00070": ["ABD00000"],
}
# ABD00010 繰り返しグループは ABD00000 の下
P2_REPEATING_PARENT = "ABD00000"

# --- KOA020-3: 第三表 ---
# ABL コードはすべてフラット（グループ分け不要）

# --- KOA210: 青色申告決算書 PL ---
# AMF00000 > AMF00100(売上), AMF00180(経費グループ), AMF00510(青色控除), AMF00530(所得)
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

PL_FIELD_GROUPS: dict[str, list[str]] = {
    "AMF00100": ["AMF00000"],  # 売上
    "AMF00510": ["AMF00000"],  # 青色申告特別控除額
    "AMF00530": ["AMF00000"],  # 所得金額
}
for _code in PL_EXPENSE_GROUP_CODES:
    PL_FIELD_GROUPS[_code] = ["AMF00000", "AMF00180"]

# --- SHA010: 消費税 ---
# AAJ00000 > AAJ フィールド, AAK00000 > AAK フィールド
CT_AAJ_CODES = frozenset(
    {
        "AAJ00010",
        "AAJ00020",
        "AAJ00030",
        "AAJ00050",
        "AAJ00060",
        "AAJ00070",
        "AAJ00080",
        "AAJ00090",
        "AAJ00100",
        "AAJ00110",
        "AAJ00120",
        "AAJ00130",
        "AAJ00180",
        "AAJ00190",
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
for _code in CT_AAJ_CODES:
    CT_FIELD_GROUPS[_code] = ["AAJ00000"]
for _code in CT_AAK_CODES:
    CT_FIELD_GROUPS[_code] = ["AAK00000"]

# フォームコード → (サブセクション名, フィールドグループマッピング) の辞書
# ビルダーがフォーム追加時にネスト構造を自動適用するために使用
FORM_NESTING: dict[str, tuple[str | None, dict[str, list[str]]]] = {
    # KOA020 は呼び出し元が KOA020-1/KOA020-2 を指定して add_form する想定
    "KOA020-1": ("KOA020-1", P1_FIELD_GROUPS),
    "KOA020-2": ("KOA020-2", P2_FIELD_GROUPS),
    "KOA210": (None, PL_FIELD_GROUPS),
    "SHA010": (None, CT_FIELD_GROUPS),
}
