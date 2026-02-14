"""勘定科目マスタデータ - 個人事業・青色申告用。

Code scheme:
  1xxx: 資産 (asset)
  2xxx: 負債 (liability)
  3xxx: 純資産 (equity)
  4xxx: 収益 (revenue)
  5xxx: 費用 (expense)
"""

MASTER_ACCOUNTS: list[dict] = [
    # ========================================
    # 1xxx: 資産 (asset)
    # ========================================
    # 流動資産 (current_asset)
    {
        "code": "1001",
        "name": "現金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1002",
        "name": "普通預金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1003",
        "name": "当座預金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1004",
        "name": "定期預金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1010",
        "name": "売掛金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1020",
        "name": "受取手形",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1030",
        "name": "棚卸資産",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1040",
        "name": "前払金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1041",
        "name": "前払費用",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1050",
        "name": "立替金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1060",
        "name": "仮払金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1070",
        "name": "未収入金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1080",
        "name": "貸付金",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    {
        "code": "1090",
        "name": "仮払消費税",
        "category": "asset",
        "sub_category": "current_asset",
        "tax_category": None,
    },
    # 固定資産 (fixed_asset)
    {
        "code": "1100",
        "name": "建物",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1101",
        "name": "建物附属設備",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1110",
        "name": "機械装置",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1120",
        "name": "車両運搬具",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1130",
        "name": "工具器具備品",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1140",
        "name": "土地",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1150",
        "name": "ソフトウェア",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    {
        "code": "1160",
        "name": "一括償却資産",
        "category": "asset",
        "sub_category": "fixed_asset",
        "tax_category": None,
    },
    # 事業主勘定 (owner)
    {
        "code": "1200",
        "name": "事業主貸",
        "category": "asset",
        "sub_category": "owner",
        "tax_category": None,
    },
    # ========================================
    # 2xxx: 負債 (liability)
    # ========================================
    # 流動負債 (current_liability)
    {
        "code": "2001",
        "name": "買掛金",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2010",
        "name": "支払手形",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2020",
        "name": "短期借入金",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2030",
        "name": "未払金",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2031",
        "name": "未払費用",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2040",
        "name": "前受金",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2050",
        "name": "預り金",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2060",
        "name": "仮受金",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2070",
        "name": "未払消費税",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    {
        "code": "2080",
        "name": "未払事業税",
        "category": "liability",
        "sub_category": "current_liability",
        "tax_category": None,
    },
    # 固定負債 (long_term_liability)
    {
        "code": "2100",
        "name": "長期借入金",
        "category": "liability",
        "sub_category": "long_term_liability",
        "tax_category": None,
    },
    # ========================================
    # 3xxx: 純資産 (equity)
    # ========================================
    {
        "code": "3001",
        "name": "元入金",
        "category": "equity",
        "sub_category": "capital",
        "tax_category": None,
    },
    {
        "code": "3010",
        "name": "事業主借",
        "category": "equity",
        "sub_category": "owner",
        "tax_category": None,
    },
    {
        "code": "3020",
        "name": "控除前所得金額",
        "category": "equity",
        "sub_category": "retained_earnings",
        "tax_category": None,
    },
    # ========================================
    # 4xxx: 収益 (revenue)
    # ========================================
    # 営業収益 (operating_revenue)
    {
        "code": "4001",
        "name": "売上",
        "category": "revenue",
        "sub_category": "operating_revenue",
        "tax_category": "taxable",
    },
    {
        "code": "4010",
        "name": "売上値引・戻り",
        "category": "revenue",
        "sub_category": "operating_revenue",
        "tax_category": "taxable",
    },
    # 営業外収益 (non_operating_revenue)
    {
        "code": "4100",
        "name": "受取利息",
        "category": "revenue",
        "sub_category": "non_operating_revenue",
        "tax_category": "non_taxable",
    },
    {
        "code": "4110",
        "name": "雑収入",
        "category": "revenue",
        "sub_category": "non_operating_revenue",
        "tax_category": "taxable",
    },
    {
        "code": "4120",
        "name": "家事消費等",
        "category": "revenue",
        "sub_category": "non_operating_revenue",
        "tax_category": "taxable",
    },
    # ========================================
    # 5xxx: 費用 (expense)
    # ========================================
    # 売上原価 (cost_of_sales)
    {
        "code": "5001",
        "name": "仕入",
        "category": "expense",
        "sub_category": "cost_of_sales",
        "tax_category": "taxable",
    },
    # 経費 (operating_expense)
    {
        "code": "5100",
        "name": "租税公課",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "out_of_scope",
    },
    {
        "code": "5110",
        "name": "荷造運賃",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5120",
        "name": "水道光熱費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5130",
        "name": "旅費交通費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5140",
        "name": "通信費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5150",
        "name": "広告宣伝費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5160",
        "name": "接待交際費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5170",
        "name": "損害保険料",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "non_taxable",
    },
    {
        "code": "5180",
        "name": "修繕費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5190",
        "name": "消耗品費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5200",
        "name": "減価償却費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "out_of_scope",
    },
    {
        "code": "5210",
        "name": "福利厚生費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5220",
        "name": "給料賃金",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "out_of_scope",
    },
    {
        "code": "5230",
        "name": "外注工賃",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5240",
        "name": "利子割引料",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "non_taxable",
    },
    {
        "code": "5250",
        "name": "地代家賃",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5260",
        "name": "貸倒金",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "out_of_scope",
    },
    {
        "code": "5270",
        "name": "雑費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5280",
        "name": "専従者給与",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "out_of_scope",
    },
    {
        "code": "5290",
        "name": "新聞図書費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5300",
        "name": "研修費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5310",
        "name": "支払手数料",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5320",
        "name": "車両費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5330",
        "name": "会議費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5340",
        "name": "諸会費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5350",
        "name": "リース料",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5360",
        "name": "事務用品費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5370",
        "name": "ソフトウェア費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
    {
        "code": "5380",
        "name": "取材費",
        "category": "expense",
        "sub_category": "operating_expense",
        "tax_category": "taxable",
    },
]
