"""Attachment xtx field builders (医療費・住宅ローン・所得の内訳).

各種明細データから ABB コード辞書を生成する。
"""

from __future__ import annotations

from typing import Any

from shinkoku.xtx.field_codes import (
    INCOME_BREAKDOWN_CODES,
    KOB060_HEADER_IDREFS,
    KOB130_HEADER_IDREFS,
    MEDICAL_EXPENSE_DETAIL_CODES,
    MEDICAL_EXPENSE_SUMMARY_CODES,
)


def _add_if_nonzero(fields: dict[str, int | str], code: str, value: int) -> None:
    if value:
        fields[code] = value


def _add_if_nonempty(fields: dict[str, int | str], code: str, value: str) -> None:
    if value:
        fields[code] = value


def build_medical_expense_fields(
    *,
    expenses: list[dict[str, Any]] | None = None,
    total_paid: int = 0,
    total_insurance: int = 0,
    total_income: int = 0,
    medical_deduction: int = 0,
) -> dict[str, Any]:
    """医療費控除明細書の DHC/DHD コード辞書を生成する。

    Returns:
        {"fields": {...}, "repeating_groups": {...}}
    """
    fields: dict[str, int | str] = {}
    repeating_groups: dict[str, list[dict[str, Any]]] = {}

    # 明細行（繰り返し）
    if expenses:
        items = []
        for exp in expenses:
            item: dict[str, Any] = {}
            if exp.get("patient_name"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["patient_name"]] = exp["patient_name"]
            if exp.get("institution_name"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["institution_name"]] = exp["institution_name"]
            if exp.get("amount_paid"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["amount_paid"]] = exp["amount_paid"]
            if exp.get("insurance_amount"):
                item[MEDICAL_EXPENSE_DETAIL_CODES["insurance_amount"]] = exp["insurance_amount"]
            items.append(item)
        repeating_groups["DHC00010"] = items

    # 集計
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["total_paid"], total_paid)
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["total_insurance"], total_insurance)

    net = total_paid - total_insurance
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["net_amount"], net)
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["total_income"], total_income)
    _add_if_nonzero(fields, MEDICAL_EXPENSE_SUMMARY_CODES["medical_deduction"], medical_deduction)

    return {
        "fields": fields,
        "repeating_groups": repeating_groups,
    }


def build_income_breakdown_fields(
    *,
    income_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """所得の内訳書 (KOB060) のフィールドを生成する。

    Args:
        income_items: 所得の内訳リスト。各項目は以下のキーを持つ:
            - income_type: 所得の種類（例: "営業等", "給与"）
            - category: 種目（例: "情報サービス", "給料"）
            - payer_name: 支払者の氏名・名称
            - payer_address: 支払者の住所・法人番号（オプション）
            - revenue: 収入金額
            - withheld_tax: 源泉徴収税額
            - payment_date: 支払確定年月（オプション、"yy-mm" 形式）

    Returns:
        {"fields": {}, "idrefs": {...}, "repeating_groups": {"BFC00000": [...]}}
    """
    fields: dict[str, int | str] = {}
    repeating_groups: dict[str, list[dict[str, Any]]] = {}

    # 繰り返し: BFC00000（所得の内訳、最大20件）
    items: list[dict[str, Any]] = []
    for detail in income_items:
        item: dict[str, Any] = {}
        if detail.get("income_type"):
            item[INCOME_BREAKDOWN_CODES["income_type"]] = detail["income_type"]
        if detail.get("category"):
            item[INCOME_BREAKDOWN_CODES["category"]] = detail["category"]
        if detail.get("payer_name"):
            # BFC00050 は BFC00030 の子（field_groups でネスト配置）
            item[INCOME_BREAKDOWN_CODES["payer_name"]] = detail["payer_name"]
        if detail.get("payer_address"):
            item[INCOME_BREAKDOWN_CODES["payer_address"]] = detail["payer_address"]
        if detail.get("revenue"):
            item[INCOME_BREAKDOWN_CODES["revenue"]] = detail["revenue"]
        if detail.get("withheld_tax") is not None:
            # BFC00100 は BFC00090 の子（field_groups でネスト配置）
            item[INCOME_BREAKDOWN_CODES["withheld_tax"]] = detail["withheld_tax"]
        if detail.get("payment_date"):
            item[INCOME_BREAKDOWN_CODES["payment_date"]] = detail["payment_date"]
        items.append(item)

    if items:
        repeating_groups["BFC00000"] = items

    return {
        "fields": fields,
        "idrefs": KOB060_HEADER_IDREFS,
        "repeating_groups": repeating_groups,
    }


def build_housing_loan_fields(
    *,
    # 居住開始
    move_in_date: str = "",
    # 家屋に関する事項
    house_acquisition_cost: int = 0,
    house_total_area: str = "",
    house_living_area: str = "",
    # 土地等に関する事項
    land_acquisition_cost: int = 0,
    land_total_area: str = "",
    land_living_area: str = "",
    # 不動産番号
    house_real_estate_number: str = "",
    land_real_estate_number: str = "",
    # 消費税率区分: "none_5pct", "8pct", "10pct"
    tax_rate_category: str = "10pct",
    # 家屋の取得対価（共有持分計算後）
    house_share_amount: int = 0,
    house_gift_deduction: int = 0,
    house_net_amount: int = 0,
    # 土地の取得対価（共有持分計算後）
    land_share_amount: int = 0,
    land_gift_deduction: int = 0,
    land_net_amount: int = 0,
    # 合計
    total_share_amount: int = 0,
    total_gift_deduction: int = 0,
    total_net_amount: int = 0,
    # 住宅借入金等の年末残高
    # (E) 住宅のみ
    housing_only_loan_balance: int = 0,
    housing_only_net_balance: int = 0,
    housing_only_min_amount: int = 0,
    housing_only_living_ratio: str = "",
    housing_only_living_balance: int = 0,
    # (F) 土地等のみ
    land_only_loan_balance: int = 0,
    land_only_net_balance: int = 0,
    land_only_min_amount: int = 0,
    land_only_living_ratio: str = "",
    land_only_living_balance: int = 0,
    # (G) 住宅及び土地等
    housing_land_loan_balance: int = 0,
    housing_land_net_balance: int = 0,
    housing_land_min_amount: int = 0,
    housing_land_living_ratio: str = "",
    housing_land_living_balance: int = 0,
    # 年末残高の合計額
    total_loan_balance: int = 0,
    # 控除額
    credit_number: str = "",
    credit_amount: int = 0,
) -> dict[str, Any]:
    """住宅借入金等特別控除額の計算明細書 (KOB130) のフィールドを生成する。

    新築住宅取得の初年度申告を想定。
    増改築・特定増改築・連帯債務の場合は追加パラメータが必要。

    Returns:
        {"fields": {...}, "idrefs": {...}}
    """
    fields: dict[str, Any] = {}

    # --- 2. 新築又は購入した家屋等に係る事項 ---
    # 家屋に関する事項 (HAD00010 内)
    # HAD00020 は gen:yymmdd 型: era/yy/mm/dd の構造化子要素で出力
    if move_in_date:
        parts = move_in_date.split("-")
        if len(parts) == 4:
            fields["HAD00020"] = {
                "era": parts[0],
                "yy": parts[1].lstrip("0") or "0",
                "mm": parts[2].lstrip("0") or "0",
                "dd": parts[3].lstrip("0") or "0",
            }
    _add_if_nonzero(fields, "HAD00030", house_acquisition_cost)  # 取得対価の額
    _add_if_nonempty(fields, "HAD00040", house_total_area)  # 総面積
    _add_if_nonempty(fields, "HAD00050", house_living_area)  # 居住用面積

    # 土地等に関する事項 (HAD00060 内)
    _add_if_nonzero(fields, "HAD00080", land_acquisition_cost)
    _add_if_nonempty(fields, "HAD00090", land_total_area)
    _add_if_nonempty(fields, "HAD00100", land_living_area)

    # --- 不動産番号 (HAE30000) ---
    _add_if_nonempty(fields, "HAE30010", house_real_estate_number)
    _add_if_nonempty(fields, "HAE30020", land_real_estate_number)

    # --- 5. 消費税率区分 (HAE20000 > HAE20010) ---
    # HAE20013/16/19 は gen:kubun 型: kubun_CD の構造化子要素で出力
    if tax_rate_category == "none_5pct":
        fields["HAE20013"] = {"kubun_CD": "1"}
    elif tax_rate_category == "8pct":
        fields["HAE20016"] = {"kubun_CD": "1"}
    elif tax_rate_category == "10pct":
        fields["HAE20019"] = {"kubun_CD": "1"}

    # --- 4. 取得対価の額 (HAF00000) ---
    # (A) 家屋
    _add_if_nonzero(fields, "HAF00043", house_share_amount)
    _add_if_nonzero(fields, "HAF00047", house_gift_deduction)
    _add_if_nonzero(fields, "HAF00050", house_net_amount)
    # (B) 土地等
    _add_if_nonzero(fields, "HAF00093", land_share_amount)
    _add_if_nonzero(fields, "HAF00097", land_gift_deduction)
    _add_if_nonzero(fields, "HAF00100", land_net_amount)
    # (C) 合計
    _add_if_nonzero(fields, "HAF00113", total_share_amount)
    _add_if_nonzero(fields, "HAF00117", total_gift_deduction)
    _add_if_nonzero(fields, "HAF00120", total_net_amount)

    # --- 7. 年末残高 (HAG00000) ---
    # (E) 住宅のみ
    _add_if_nonzero(fields, "HAG00020", housing_only_loan_balance)
    _add_if_nonzero(fields, "HAG00040", housing_only_net_balance)
    _add_if_nonzero(fields, "HAG00050", housing_only_min_amount)
    _add_if_nonempty(fields, "HAG00060", housing_only_living_ratio)
    _add_if_nonzero(fields, "HAG00070", housing_only_living_balance)
    # (F) 土地等のみ
    _add_if_nonzero(fields, "HAG00090", land_only_loan_balance)
    _add_if_nonzero(fields, "HAG00110", land_only_net_balance)
    _add_if_nonzero(fields, "HAG00120", land_only_min_amount)
    _add_if_nonempty(fields, "HAG00130", land_only_living_ratio)
    _add_if_nonzero(fields, "HAG00140", land_only_living_balance)
    # (G) 住宅及び土地等
    _add_if_nonzero(fields, "HAG00160", housing_land_loan_balance)
    _add_if_nonzero(fields, "HAG00180", housing_land_net_balance)
    _add_if_nonzero(fields, "HAG00190", housing_land_min_amount)
    _add_if_nonempty(fields, "HAG00200", housing_land_living_ratio)
    _add_if_nonzero(fields, "HAG00210", housing_land_living_balance)
    # 合計額
    _add_if_nonzero(fields, "HAG00355", total_loan_balance)

    # --- 9. 控除額 (HAM00000) ---
    _add_if_nonempty(fields, "HAM00015", credit_number)
    _add_if_nonzero(fields, "HAM00020", credit_amount)

    return {
        "fields": fields,
        "idrefs": KOB130_HEADER_IDREFS,
    }
