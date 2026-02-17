"""xtx 生成ロジック。

config + DB からデータを読み取り、税額計算 → xtx ビルダーで XML を生成する。
CLI スクリプト (scripts/generate_xtx.py) から呼び出す。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shinkoku.config import ShinkokuConfig, load_config
from shinkoku.models import (
    BSItem,
    BSResult,
    ConsumptionTaxInput,
    HousingLoanDetail,
    IncomeTaxInput,
    PLItem,
    PLResult,
)
from shinkoku.tools.ledger import ledger_list_housing_loan_details, ledger_pl, ledger_bs
from shinkoku.tools.tax_calc import calc_consumption_tax, calc_housing_loan_credit, calc_income_tax
from shinkoku.xtx.attachments import build_housing_loan_fields, build_income_breakdown_fields
from shinkoku.xtx.blue_return import build_bs_fields, build_pl_fields
from shinkoku.xtx.consumption_tax import build_consumption_tax_fields
from shinkoku.xtx.field_codes import (
    FORM_VERSIONS,
    P1_HEADER_IDREFS,
    P2_HEADER_IDREFS,
)
from shinkoku.xtx.generator import XtxBuilder
from shinkoku.xtx.income_tax import build_income_tax_p1_fields, build_income_tax_p2_fields


def _build_taxpayer_kwargs(config: ShinkokuConfig) -> dict[str, str]:
    """ShinkokuConfig から set_taxpayer_info() の引数辞書を構築する。"""
    tp = config.taxpayer
    addr = config.address
    biz = config.business
    filing = config.filing
    refund = config.refund_account

    full_name = f"{tp.last_name}{tp.first_name}"
    full_name_kana = f"{tp.last_name_kana}{tp.first_name_kana}"
    full_address = f"{addr.prefecture}{addr.city}{addr.street}"
    if addr.building:
        full_address += f" {addr.building}"

    # 口座種別 → yokin コード（普通=1, 当座=2）
    deposit_type = ""
    if refund.account_type == "普通":
        deposit_type = "1"
    elif refund.account_type == "当座":
        deposit_type = "2"

    return {
        "name": full_name,
        "name_kana": full_name_kana,
        "address": full_address,
        "address_code": "",  # 地方公共団体コード（config 未対応）
        "zip_code": addr.postal_code.replace("-", ""),
        "tax_office_code": "",  # 税務署コード（config 未対応）
        "tax_office_name": filing.tax_office_name,
        "my_number": tp.my_number or "",
        "jan1_address": addr.jan1_address or "",
        "trade_name": biz.trade_name,
        "phone": tp.phone,
        "gender": tp.gender or "",
        "birthday": tp.date_of_birth or "",
        "occupation": biz.industry_type,
        "business_description": biz.business_description,
        # W2-W5 追加フィールド
        "address_kana": addr.address_kana,
        "seiribango": filing.seiribango,
        "refund_bank_name": refund.bank_name,
        "refund_branch_name": refund.branch_name,
        "refund_deposit_type": deposit_type,
        "refund_account_number": refund.account_number,
    }


def _convert_date_to_etax(date_str: str) -> str:
    """日付文字列を e-Tax 形式に変換する（YYYY-MM-DD → era-YY-MM-DD）。

    令和（5）: 2019年5月1日〜
    """
    if not date_str or "-" not in date_str:
        return date_str
    parts = date_str.split("-")
    if len(parts) != 3:
        return date_str
    year = int(parts[0])
    mm = parts[1]
    dd = parts[2]
    # 令和変換（2019年以降）
    if year >= 2019:
        era = 5
        yy = year - 2018
    else:
        # 平成（4）: 1989-2019
        era = 4
        yy = year - 1988
    return f"{era}-{yy:02d}-{mm}-{dd}"


def _get_pl_result(db_path: str, fiscal_year: int) -> PLResult:
    """DB から PL データを取得し PLResult モデルに変換する。"""
    pl_dict = ledger_pl(db_path=db_path, fiscal_year=fiscal_year)
    return PLResult(
        fiscal_year=fiscal_year,
        revenues=[
            PLItem(
                account_code=r["account_code"],
                account_name=r["account_name"],
                amount=r["amount"],
            )
            for r in pl_dict.get("revenues", [])
        ],
        expenses=[
            PLItem(
                account_code=e["account_code"],
                account_name=e["account_name"],
                amount=e["amount"],
            )
            for e in pl_dict.get("expenses", [])
        ],
        total_revenue=pl_dict["total_revenue"],
        total_expense=pl_dict["total_expense"],
        net_income=pl_dict["net_income"],
    )


def _bs_items_from_dicts(items: list[dict]) -> list[BSItem]:
    """dict のリストを BSItem リストに変換するヘルパー。"""
    return [
        BSItem(
            account_code=item["account_code"],
            account_name=item["account_name"],
            amount=item["amount"],
        )
        for item in items
    ]


def _get_bs_result(db_path: str, fiscal_year: int) -> BSResult:
    """DB から BS データを取得し BSResult モデルに変換する。"""
    bs_dict = ledger_bs(db_path=db_path, fiscal_year=fiscal_year)

    # 期首データ（空リストの場合も含めて変換）
    opening_assets_raw = bs_dict.get("opening_assets", [])
    opening_liabilities_raw = bs_dict.get("opening_liabilities", [])
    opening_equity_raw = bs_dict.get("opening_equity", [])

    return BSResult(
        fiscal_year=fiscal_year,
        assets=_bs_items_from_dicts(bs_dict.get("assets", [])),
        liabilities=_bs_items_from_dicts(bs_dict.get("liabilities", [])),
        equity=_bs_items_from_dicts(bs_dict.get("equity", [])),
        total_assets=bs_dict["total_assets"],
        total_liabilities=bs_dict["total_liabilities"],
        total_equity=bs_dict["total_equity"],
        opening_assets=_bs_items_from_dicts(opening_assets_raw) or None,
        opening_liabilities=_bs_items_from_dicts(opening_liabilities_raw) or None,
        opening_equity=_bs_items_from_dicts(opening_equity_raw) or None,
        opening_total_assets=bs_dict.get("opening_total_assets"),
        opening_total_liabilities=bs_dict.get("opening_total_liabilities"),
        opening_total_equity=bs_dict.get("opening_total_equity"),
    )


def generate_income_tax_xtx(
    *,
    config_path: str,
    output_dir: str,
    db_path_override: str = "",
    income_details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """所得税の xtx ファイルを生成する。

    処理フロー:
    1. config 読み込み
    2. DB から PL/BS・住宅ローン明細取得
    3. 所得税計算
    4. XtxBuilder で XML 生成（KOA020, KOA210, KOB060, KOB130）
    5. ファイル書き出し

    Args:
        config_path: 設定ファイルパス
        output_dir: 出力ディレクトリ
        db_path_override: DB パスの上書き（空文字なら config から取得）
        income_details: 所得の内訳リスト（KOB060 用）。各項目は
            income_type, category, payer_name, revenue, withheld_tax 等を持つ dict。

    Returns:
        {"status": "ok", "output_path": str, "forms": [...], "warnings": [...]}
    """
    config = load_config(config_path)
    db_path = db_path_override or _resolve_db_path(config, config_path)
    fiscal_year = config.tax_year
    warnings: list[str] = []

    # PL/BS 取得
    pl = _get_pl_result(db_path, fiscal_year)
    bs = _get_bs_result(db_path, fiscal_year)

    # 所得税計算
    blue_deduction = (
        config.filing.blue_return_deduction if config.filing.return_type == "blue" else 0
    )
    income_tax_input = IncomeTaxInput(
        fiscal_year=fiscal_year,
        business_revenue=pl.total_revenue,
        business_expenses=pl.total_expense,
        blue_return_deduction=blue_deduction,
    )
    income_tax_result = calc_income_tax(income_tax_input)

    # XtxBuilder 構築
    builder = XtxBuilder(tax_type="income", fiscal_year=fiscal_year)
    builder.set_taxpayer_info(**_build_taxpayer_kwargs(config))

    forms_info: list[dict[str, str]] = []

    # 申告書B 第一表
    p1_fields = build_income_tax_p1_fields(
        income_tax_result,
        salary_revenue=0,
        business_revenue=pl.total_revenue,
        blue_return_deduction=income_tax_result.effective_blue_return_deduction,
    )
    builder.add_form(
        "KOA020",
        FORM_VERSIONS["KOA020"],
        p1_fields,
        nesting_key="KOA020-1",
        idrefs=P1_HEADER_IDREFS,
    )
    forms_info.append({"form_code": "KOA020", "description": "申告書B 第一表"})

    # 申告書B 第二表
    p2_result = build_income_tax_p2_fields()
    builder.add_form(
        "KOA020",
        FORM_VERSIONS["KOA020"],
        p2_result.get("fields", {}),
        nesting_key="KOA020-2",
        idrefs=P2_HEADER_IDREFS,
        repeating_groups=p2_result.get("repeating_groups"),
    )
    forms_info.append({"form_code": "KOA020", "description": "申告書B 第二表"})

    # 青色申告決算書 PL
    if config.filing.return_type == "blue":
        pl_fields = build_pl_fields(
            pl, blue_return_deduction=income_tax_result.effective_blue_return_deduction
        )
        builder.add_form(
            "KOA210",
            FORM_VERSIONS["KOA210"],
            pl_fields,
            nesting_key="KOA210",
        )
        forms_info.append({"form_code": "KOA210", "description": "青色申告決算書 損益計算書"})

        # 青色申告決算書 BS
        bs_fields = build_bs_fields(bs)
        builder.add_form(
            "KOA210",
            FORM_VERSIONS["KOA210"],
            bs_fields,
            nesting_key="KOA210-4",
            page=4,
        )
        forms_info.append({"form_code": "KOA210", "description": "青色申告決算書 貸借対照表"})

    # KOB130: 住宅借入金等特別控除額の計算明細書
    hl_result = ledger_list_housing_loan_details(db_path=db_path, fiscal_year=fiscal_year)
    hl_details = hl_result.get("details", [])
    if hl_details:
        # 初年度申告を想定し、最初の住宅ローン明細を使用
        hl = hl_details[0]
        # 居住開始日を e-Tax 形式に変換（YYYY-MM-DD → era-YY-MM-DD）
        move_in_date_etax = _convert_date_to_etax(hl["move_in_date"])

        # 面積: DB は ×100 の整数（10063=100.63㎡） → 小数文字列に変換
        total_area = f"{hl['total_floor_area'] / 100:.2f}" if hl["total_floor_area"] else ""
        living_area = (
            f"{hl['residential_floor_area'] / 100:.2f}" if hl["residential_floor_area"] else ""
        )

        # 年末残高
        balance = hl["year_end_balance"]
        purchase_price = hl["purchase_price"]

        # 控除額計算（tax_calc の住宅ローン控除関数を使用）
        hl_detail_model = HousingLoanDetail(
            housing_type=hl["housing_type"],
            housing_category=hl["housing_category"],
            move_in_date=hl["move_in_date"],
            year_end_balance=balance,
            is_new_construction=hl["is_new_construction"],
            is_childcare_household=hl.get("is_childcare_household", False),
            has_pre_r6_building_permit=hl.get("has_pre_r6_building_permit", False),
        )
        credit_amount = calc_housing_loan_credit(balance, detail=hl_detail_model)

        # 消費税率区分（新築=10%、中古=なし/5% がデフォルト）
        tax_rate = "10pct" if hl["is_new_construction"] else "none_5pct"

        # 居住用割合（全額居住用=100）
        living_ratio = "100"
        if total_area and living_area:
            ratio = float(living_area) / float(total_area) * 100
            living_ratio = str(int(ratio))

        kob130_result = build_housing_loan_fields(
            move_in_date=move_in_date_etax,
            house_acquisition_cost=purchase_price,
            house_total_area=total_area,
            house_living_area=living_area,
            house_real_estate_number=hl.get("property_number") or "",
            tax_rate_category=tax_rate,
            house_share_amount=purchase_price,
            house_net_amount=purchase_price,
            total_share_amount=purchase_price,
            total_net_amount=purchase_price,
            housing_only_loan_balance=balance,
            housing_only_net_balance=balance,
            housing_only_min_amount=min(balance, purchase_price) if purchase_price else balance,
            housing_only_living_ratio=living_ratio,
            housing_only_living_balance=balance,
            total_loan_balance=balance,
            credit_amount=credit_amount,
        )
        builder.add_form(
            "KOB130",
            FORM_VERSIONS["KOB130"],
            kob130_result["fields"],
            nesting_key="KOB130-1",
            idrefs=kob130_result["idrefs"],
        )
        forms_info.append(
            {"form_code": "KOB130", "description": "住宅借入金等特別控除額の計算明細書"}
        )

    # KOB060: 所得の内訳書
    if income_details:
        kob060_result = build_income_breakdown_fields(income_items=income_details)
        builder.add_form(
            "KOB060",
            FORM_VERSIONS["KOB060"],
            kob060_result["fields"],
            nesting_key="KOB060",
            idrefs=kob060_result["idrefs"],
            repeating_groups=kob060_result["repeating_groups"],
        )
        forms_info.append({"form_code": "KOB060", "description": "所得の内訳書"})

    # ファイル書き出し
    reiwa_year = fiscal_year - 2019 + 1
    output_path = Path(output_dir) / f"income_tax_r{reiwa_year:02d}.xtx"
    builder.save(output_path)

    return {
        "status": "ok",
        "output_path": str(output_path),
        "forms": forms_info,
        "warnings": warnings,
        "tax_result": {
            "business_income": income_tax_result.business_income,
            "total_income": income_tax_result.total_income,
            "taxable_income": income_tax_result.taxable_income,
            "total_tax": income_tax_result.total_tax,
            "tax_due": income_tax_result.tax_due,
        },
    }


def generate_consumption_tax_xtx(
    *,
    config_path: str,
    output_dir: str,
    db_path_override: str = "",
) -> dict[str, Any]:
    """消費税の xtx ファイルを生成する。

    Args:
        config_path: 設定ファイルパス
        output_dir: 出力ディレクトリ
        db_path_override: DB パスの上書き（空文字なら config から取得）

    Returns:
        {"status": "ok", "output_path": str, "forms": [...], "warnings": [...]}
    """
    config = load_config(config_path)
    db_path = db_path_override or _resolve_db_path(config, config_path)
    fiscal_year = config.tax_year
    warnings: list[str] = []

    # PL から課税売上を取得
    pl = _get_pl_result(db_path, fiscal_year)

    # 消費税計算（デフォルト: 2割特例、売上は10%税込として扱う）
    ct_input = ConsumptionTaxInput(
        fiscal_year=fiscal_year,
        method="special_20pct",
        taxable_sales_10=pl.total_revenue,
    )
    ct_result = calc_consumption_tax(ct_input)

    # XtxBuilder 構築
    builder = XtxBuilder(tax_type="consumption", fiscal_year=fiscal_year)
    builder.set_taxpayer_info(**_build_taxpayer_kwargs(config))

    forms_info: list[dict[str, str]] = []

    # 消費税申告書
    ct_fields = build_consumption_tax_fields(ct_result)
    builder.add_form(
        "SHA010",
        FORM_VERSIONS["SHA010"],
        ct_fields,
        nesting_key="SHA010",
    )
    forms_info.append({"form_code": "SHA010", "description": "消費税及び地方消費税申告書"})

    # ファイル書き出し
    reiwa_year = fiscal_year - 2019 + 1
    output_path = Path(output_dir) / f"consumption_tax_r{reiwa_year:02d}.xtx"
    builder.save(output_path)

    return {
        "status": "ok",
        "output_path": str(output_path),
        "forms": forms_info,
        "warnings": warnings,
        "tax_result": {
            "tax_due": ct_result.tax_due,
            "local_tax_due": ct_result.local_tax_due,
            "total_due": ct_result.total_due,
        },
    }


def generate_all_xtx(
    *,
    config_path: str,
    output_dir: str,
    db_path_override: str = "",
    income_details: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """所得税と消費税の xtx をまとめて生成する。

    Args:
        config_path: 設定ファイルパス
        output_dir: 出力ディレクトリ
        db_path_override: DB パスの上書き（空文字なら config から取得）
        income_details: 所得の内訳リスト（KOB060 用）

    Returns:
        生成結果のリスト
    """
    results: list[dict[str, Any]] = []

    # 所得税は常に生成
    income_result = generate_income_tax_xtx(
        config_path=config_path,
        output_dir=output_dir,
        db_path_override=db_path_override,
        income_details=income_details,
    )
    results.append(income_result)

    # 消費税も生成
    ct_result = generate_consumption_tax_xtx(
        config_path=config_path, output_dir=output_dir, db_path_override=db_path_override
    )
    results.append(ct_result)

    return results


def _resolve_db_path(config: ShinkokuConfig, config_path: str) -> str:
    """config の db_path を解決する。相対パスの場合は config ファイル基準。"""
    db_path = config.db_path
    if not Path(db_path).is_absolute():
        config_dir = Path(config_path).parent
        db_path = str(config_dir / db_path)
    return db_path
