"""Blue return xtx field builders (青色申告決算書 PL+BS).

PLResult / BSResult モデルから AMF/AMG コード辞書を生成する。
"""

from __future__ import annotations

from shinkoku.models import BSResult, PLResult
from shinkoku.xtx.field_codes import (
    BS_CODES_BEGINNING,
    BS_CODES_ENDING,
    BS_LIABILITIES_BEGINNING,
    BS_LIABILITIES_ENDING,
    PL_CODES,
)

# 勘定科目名 → PL_CODES キー
_EXPENSE_ACCOUNT_MAP: dict[str, str] = {
    "租税公課": "tax_and_dues",
    "荷造運賃": "packing_shipping",
    "水道光熱費": "utilities",
    "旅費交通費": "travel",
    "通信費": "communication",
    "広告宣伝費": "advertising",
    "接待交際費": "entertainment",
    "損害保険料": "insurance",
    "修繕費": "repairs",
    "消耗品費": "supplies",
    "減価償却費": "depreciation",
    "福利厚生費": "welfare",
    "給料賃金": "salaries",
    "外注工賃": "outsourcing",
    "外注費": "outsourcing",
    "利子割引料": "interest_discount",
    "地代家賃": "rent",
    "賃借料": "rent",
    "貸倒金": "bad_debt",
    "雑費": "miscellaneous",
}

# 資産勘定科目名 → BS_CODES_ENDING キー
_ASSET_ACCOUNT_MAP: dict[str, str] = {
    "現金": "cash",
    "当座預金": "checking",
    "定期預金": "time_deposit",
    "普通預金": "other_deposit",
    "受取手形": "notes_receivable",
    "売掛金": "accounts_receivable",
    "有価証券": "securities",
    "棚卸資産": "inventory",
    "商品": "inventory",
    "前払金": "prepaid",
    "前払費用": "prepaid",
    "貸付金": "loans_receivable",
    "建物": "buildings",
    "建物附属設備": "building_fixtures",
    "機械装置": "machinery",
    "車両運搬具": "vehicles",
    "工具器具備品": "tools_equipment",
    "器具備品": "tools_equipment",
    "土地": "land",
    "事業主貸": "owner_lending",
}

# 負債勘定科目名 → BS_LIABILITIES_ENDING キー
_LIABILITY_ACCOUNT_MAP: dict[str, str] = {
    "支払手形": "notes_payable",
    "買掛金": "accounts_payable",
    "借入金": "borrowings",
    "長期借入金": "borrowings",
    "未払金": "accrued_expenses",
    "未払費用": "accrued_expenses",
    "前受金": "advances_received",
    "預り金": "deposits_received",
    "貸倒引当金": "allowance_bad_debt",
}

_EQUITY_ACCOUNT_MAP: dict[str, str] = {
    "元入金": "capital",
    "事業主借": "owner_borrowing",
}


def _add_if_nonzero(fields: dict[str, int | str], code: str, value: int) -> None:
    if value:
        fields[code] = value


def build_pl_fields(
    pl: PLResult,
    *,
    blue_return_deduction: int = 0,
) -> dict[str, int | str]:
    """青色申告決算書 損益計算書 の AMF コード辞書を生成する。

    Args:
        pl: 損益計算書データ
        blue_return_deduction: 青色申告特別控除額

    Returns:
        {AMFコード: 値} の辞書。0 の値は含まない。
    """
    fields: dict[str, int | str] = {}

    # 売上（収入）金額
    _add_if_nonzero(fields, PL_CODES["revenue"], pl.total_revenue)

    # 経費
    expense_totals: dict[str, int] = {}
    for item in pl.expenses:
        key = _EXPENSE_ACCOUNT_MAP.get(item.account_name, "miscellaneous")
        expense_totals[key] = expense_totals.get(key, 0) + item.amount

    for key, total in expense_totals.items():
        if key in PL_CODES and total:
            fields[PL_CODES[key]] = total

    # 経費計
    _add_if_nonzero(fields, PL_CODES["total_expense"], pl.total_expense)

    # 所得金額
    _add_if_nonzero(fields, PL_CODES["net_income"], pl.net_income)

    # 青色申告特別控除額
    _add_if_nonzero(fields, PL_CODES["blue_return_deduction"], blue_return_deduction)

    return fields


def build_bs_fields(
    bs: BSResult,
) -> dict[str, int | str]:
    """青色申告決算書 貸借対照表 の AMG コード辞書を生成する（期首・期末）。

    Args:
        bs: 貸借対照表データ

    Returns:
        {AMGコード: 値} の辞書。0 の値は含まない。
    """
    fields: dict[str, int | str] = {}

    # 資産の部（期末）
    asset_totals: dict[str, int] = {}
    for item in bs.assets:
        key = _ASSET_ACCOUNT_MAP.get(item.account_name)
        if key:
            asset_totals[key] = asset_totals.get(key, 0) + item.amount

    for key, total in asset_totals.items():
        if key in BS_CODES_ENDING and total:
            fields[BS_CODES_ENDING[key]] = total

    _add_if_nonzero(fields, BS_CODES_ENDING["total_assets"], bs.total_assets)

    # 負債の部（期末）
    liab_totals: dict[str, int] = {}
    for item in bs.liabilities:
        key = _LIABILITY_ACCOUNT_MAP.get(item.account_name)
        if key:
            liab_totals[key] = liab_totals.get(key, 0) + item.amount

    for key, total in liab_totals.items():
        if key in BS_LIABILITIES_ENDING and total:
            fields[BS_LIABILITIES_ENDING[key]] = total

    # 純資産の部（期末）
    equity_totals: dict[str, int] = {}
    for item in bs.equity:
        key = _EQUITY_ACCOUNT_MAP.get(item.account_name)
        if key:
            equity_totals[key] = equity_totals.get(key, 0) + item.amount

    for key, total in equity_totals.items():
        if key in BS_LIABILITIES_ENDING and total:
            fields[BS_LIABILITIES_ENDING[key]] = total

    _add_if_nonzero(fields, BS_LIABILITIES_ENDING["total_liabilities"], bs.total_liabilities)

    # 資産の部（期首）
    if bs.opening_assets is not None:
        opening_asset_totals: dict[str, int] = {}
        for item in bs.opening_assets:
            key = _ASSET_ACCOUNT_MAP.get(item.account_name)
            if key:
                opening_asset_totals[key] = opening_asset_totals.get(key, 0) + item.amount

        for key, total in opening_asset_totals.items():
            if key in BS_CODES_BEGINNING and total:
                fields[BS_CODES_BEGINNING[key]] = total

        if bs.opening_total_assets is not None:
            _add_if_nonzero(fields, BS_CODES_BEGINNING["total_assets"], bs.opening_total_assets)

    # 負債・純資産の部（期首）
    if bs.opening_liabilities is not None:
        opening_liab_totals: dict[str, int] = {}
        for item in bs.opening_liabilities:
            key = _LIABILITY_ACCOUNT_MAP.get(item.account_name)
            if key:
                opening_liab_totals[key] = opening_liab_totals.get(key, 0) + item.amount

        for key, total in opening_liab_totals.items():
            if key in BS_LIABILITIES_BEGINNING and total:
                fields[BS_LIABILITIES_BEGINNING[key]] = total

    if bs.opening_equity is not None:
        opening_equity_totals: dict[str, int] = {}
        for item in bs.opening_equity:
            key = _EQUITY_ACCOUNT_MAP.get(item.account_name)
            if key:
                opening_equity_totals[key] = opening_equity_totals.get(key, 0) + item.amount

        for key, total in opening_equity_totals.items():
            if key in BS_LIABILITIES_BEGINNING and total:
                fields[BS_LIABILITIES_BEGINNING[key]] = total

    return fields
