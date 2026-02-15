"""Document generation tools for tax filing PDFs.

Generates:
- Blue return BS/PL (balance sheet + profit/loss)
- Income tax form B (pages 1 & 2)
- Consumption tax form
- Medical expense detail form
- Housing loan detail form
- Schedule 3 (separate taxation)
- Schedule 4 (loss carryforward)
- Income/expense statement (white return)
- Full tax document set
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shinkoku.config import ShinkokuConfig

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from shinkoku.models import (
    PLResult,
    PLItem,
    BSResult,
    BSItem,
    IncomeTaxResult,
    ConsumptionTaxResult,
    SeparateTaxResult,
)
from shinkoku.tools.pdf_utils import (
    create_overlay,
    create_multi_page_overlay,
    merge_overlay,
    merge_multi_template_overlay,
    generate_standalone_multi_page_pdf,
    generate_standalone_pdf,
    pdf_to_images,
)
from shinkoku.tools.pdf_coordinates import (
    A4_PORTRAIT,
    A4_LANDSCAPE,
    NTA_PORTRAIT,
    INCOME_TAX_P1,
    INCOME_TAX_P2,
    BLUE_RETURN_PL_P1,
    BLUE_RETURN_BS,
    CONSUMPTION_TAX_P1,
    INCOME_DETAIL_SHEET,
    INCOME_DETAIL_SHEET_SIZE,
    TEMPLATE_NAMES,
)
from shinkoku.tax_constants import (
    HOUSING_LOAN_DEFAULT_LIMIT,
    HOUSING_LOAN_GENERAL_R5_CONFIRMED,
    HOUSING_LOAN_LIMITS_R4_R5,
    HOUSING_LOAN_LIMITS_R6_R7,
    HOUSING_LOAN_LIMITS_R6_R7_CHILDCARE,
    MEDICAL_EXPENSE_INCOME_RATIO,
    MEDICAL_EXPENSE_MAX,
    MEDICAL_EXPENSE_THRESHOLD,
)


# ============================================================
# Template Resolution & Helpers
# ============================================================

TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "templates"


def _resolve_template(name: str) -> Path | None:
    """テンプレートPDFのパスを解決する。存在しなければ None。"""
    filename = TEMPLATE_NAMES.get(name, f"{name}.pdf")
    path = TEMPLATE_DIR / filename
    return path if path.exists() else None


def _coord_field(coord: dict, value: Any) -> dict[str, Any]:
    """座標定義と値をマージしてフィールド dict を生成する。"""
    return {**coord, "value": value}


# 勘定科目名 → BLUE_RETURN_PL_P1 フィールド名
_EXPENSE_FIELD_MAP: dict[str, str] = {
    "地代家賃": "rent",
    "賃借料": "rent",
    "通信費": "communication",
    "旅費交通費": "travel",
    "減価償却費": "depreciation",
    "消耗品費": "supplies",
    "外注工賃": "outsourcing",
    "外注費": "outsourcing",
    "水道光熱費": "utilities",
    "広告宣伝費": "advertising",
    "雑費": "miscellaneous",
}

# 勘定科目名 → BLUE_RETURN_BS フィールド名
_ASSET_FIELD_MAP: dict[str, str] = {
    "現金": "cash",
    "普通預金": "bank_deposit",
    "当座預金": "bank_deposit",
    "売掛金": "accounts_receivable",
    "前払費用": "prepaid",
    "前払金": "prepaid",
    "建物": "buildings",
    "工具器具備品": "equipment",
    "器具備品": "equipment",
    "車両運搬具": "equipment",
    "事業主貸": "owner_drawing",
}

_LIABILITY_FIELD_MAP: dict[str, str] = {
    "買掛金": "accounts_payable",
    "未払金": "unpaid",
    "未払費用": "unpaid",
    "借入金": "borrowings",
    "長期借入金": "borrowings",
}

_EQUITY_FIELD_MAP: dict[str, str] = {
    "元入金": "capital",
    "事業主借": "owner_investment",
}

# 控除名 → INCOME_TAX_P1 フィールド名
_DEDUCTION_FIELD_MAP: dict[str, str] = {
    "社会保険料控除": "social_insurance_deduction",
    "小規模企業共済等掛金控除": "ideco_deduction",
    "生命保険料控除": "life_insurance_deduction",
    "地震保険料控除": "earthquake_insurance_deduction",
    "寄附金控除": "furusato_deduction",
    "配偶者控除": "spouse_deduction",
    "配偶者特別控除": "spouse_deduction",
    "扶養控除": "dependent_deduction",
    "基礎控除": "basic_deduction",
    "医療費控除": "medical_deduction",
}


# ============================================================
# Blue Return BS/PL (Task 18)
# ============================================================


def _build_pl_fields(
    pl_data: PLResult,
    taxpayer_name: str = "",
) -> list[dict[str, Any]]:
    """P/L P1のフィールドを構築する。BLUE_RETURN_PL_P1 座標を使用。"""
    fields: list[dict[str, Any]] = []

    # ヘッダー
    if taxpayer_name:
        fields.append(_coord_field(BLUE_RETURN_PL_P1["taxpayer_name"], taxpayer_name))

    fields.append(
        _coord_field(
            BLUE_RETURN_PL_P1["fiscal_year"],
            f"令和{pl_data.fiscal_year - 2018}年分",
        )
    )

    # 売上（収入）金額
    fields.append(_coord_field(BLUE_RETURN_PL_P1["total_revenue"], pl_data.total_revenue))

    # 経費を勘定科目名で分類し、同一フィールドは合算
    expense_totals: dict[str, int] = {}
    for item in pl_data.expenses:
        field_name = _EXPENSE_FIELD_MAP.get(item.account_name, "miscellaneous")
        if field_name in BLUE_RETURN_PL_P1:
            expense_totals[field_name] = expense_totals.get(field_name, 0) + item.amount

    for field_name, total in expense_totals.items():
        fields.append(_coord_field(BLUE_RETURN_PL_P1[field_name], total))

    # 経費合計
    fields.append(_coord_field(BLUE_RETURN_PL_P1["total_expenses"], pl_data.total_expense))

    # 差引金額（所得金額）
    fields.append(_coord_field(BLUE_RETURN_PL_P1["net_income"], pl_data.net_income))

    return fields


def _build_bs_fields(
    bs_data: BSResult,
    taxpayer_name: str = "",
) -> list[dict[str, Any]]:
    """B/Sのフィールドを構築する。BLUE_RETURN_BS 座標を使用。"""
    fields: list[dict[str, Any]] = []

    # ヘッダー
    if taxpayer_name:
        fields.append(_coord_field(BLUE_RETURN_BS["taxpayer_name"], taxpayer_name))

    fields.append(
        _coord_field(
            BLUE_RETURN_BS["fiscal_year_end"],
            f"令和{bs_data.fiscal_year - 2018}年12月31日",
        )
    )

    # 資産の部（勘定科目名で分類、同一フィールドは合算）
    asset_totals: dict[str, int] = {}
    for item in bs_data.assets:
        field_name = _ASSET_FIELD_MAP.get(item.account_name)
        if field_name and field_name in BLUE_RETURN_BS:
            asset_totals[field_name] = asset_totals.get(field_name, 0) + item.amount

    for field_name, total in asset_totals.items():
        fields.append(_coord_field(BLUE_RETURN_BS[field_name], total))

    fields.append(_coord_field(BLUE_RETURN_BS["total_assets"], bs_data.total_assets))

    # 負債の部
    liab_totals: dict[str, int] = {}
    for item in bs_data.liabilities:
        field_name = _LIABILITY_FIELD_MAP.get(item.account_name)
        if field_name and field_name in BLUE_RETURN_BS:
            liab_totals[field_name] = liab_totals.get(field_name, 0) + item.amount

    for field_name, total in liab_totals.items():
        fields.append(_coord_field(BLUE_RETURN_BS[field_name], total))

    fields.append(_coord_field(BLUE_RETURN_BS["total_liabilities"], bs_data.total_liabilities))

    # 純資産の部
    equity_totals: dict[str, int] = {}
    for item in bs_data.equity:
        field_name = _EQUITY_FIELD_MAP.get(item.account_name)
        if field_name and field_name in BLUE_RETURN_BS:
            equity_totals[field_name] = equity_totals.get(field_name, 0) + item.amount

    for field_name, total in equity_totals.items():
        fields.append(_coord_field(BLUE_RETURN_BS[field_name], total))

    fields.append(_coord_field(BLUE_RETURN_BS["total_equity"], bs_data.total_equity))

    return fields


def generate_bs_pl_pdf(
    pl_data: PLResult,
    bs_data: BSResult | None = None,
    output_path: str = "output/bs_pl.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
) -> str:
    """青色申告決算書（損益計算書 + 貸借対照表）PDFを生成する。

    テンプレートPDFが存在する場合はオーバーレイ方式で生成。
    ない場合はスタンドアロン方式にフォールバック。
    """
    pages: list[list[dict[str, Any]]] = []
    template_paths: list[str] = []
    page_sizes: list[tuple[float, float]] = []

    # P/L P1
    pl_fields = _build_pl_fields(pl_data, taxpayer_name)
    pages.append(pl_fields)
    page_sizes.append(A4_LANDSCAPE)
    tmpl = _resolve_template("blue_return_pl_p1")
    template_paths.append(str(tmpl) if tmpl else "")

    # B/S (if data provided)
    if bs_data is not None:
        bs_fields = _build_bs_fields(bs_data, taxpayer_name)
        pages.append(bs_fields)
        page_sizes.append(A4_LANDSCAPE)
        tmpl = _resolve_template("blue_return_bs")
        template_paths.append(str(tmpl) if tmpl else "")

    # テンプレートが1つでもあればオーバーレイ方式
    has_any_template = any(p for p in template_paths)

    if has_any_template:
        # NTA 青色申告決算書 (r07/10.pdf) は portrait MediaBox + /Rotate=90
        page_rotations = [90] * len(pages)
        overlay_bytes = create_multi_page_overlay(
            pages,
            page_sizes=page_sizes,
            page_rotations=page_rotations,
        )
        return merge_multi_template_overlay(template_paths, overlay_bytes, output_path)

    # Standalone fallback
    return generate_standalone_multi_page_pdf(
        pages=pages,
        output_path=output_path,
        page_sizes=page_sizes,
    )


# ============================================================
# Income/Expense Statement (収支内訳書 — 白色申告用)
# ============================================================


def generate_income_expense_statement_pdf(
    pl_data: PLResult,
    output_path: str = "output/income_expense_statement.pdf",
    taxpayer_name: str = "",
) -> str:
    """Generate income/expense statement PDF for white return (白色申告用収支内訳書).

    白色申告では青色申告決算書（BS/PL）の代わりに収支内訳書を提出する。
    損益計算書のみで、貸借対照表は不要。

    Args:
        pl_data: Profit/Loss data.
        output_path: Output file path.
        taxpayer_name: Taxpayer name for the header.

    Returns:
        The output file path.
    """
    from shinkoku.tools.pdf_coordinates import INCOME_EXPENSE_STATEMENT

    fields: list[dict[str, Any]] = []

    # Title
    fields.append(
        {
            "type": "text",
            "x": 105 * mm,
            "y": 285 * mm,
            "value": "収支内訳書（一般用）",
            "font_size": 12,
        }
    )

    # Header
    if taxpayer_name:
        fields.append(
            {
                "type": "text",
                "x": INCOME_EXPENSE_STATEMENT["taxpayer_name"]["x"],
                "y": INCOME_EXPENSE_STATEMENT["taxpayer_name"]["y"],
                "value": taxpayer_name,
                "font_size": INCOME_EXPENSE_STATEMENT["taxpayer_name"]["font_size"],
            }
        )

    fields.append(
        {
            "type": "text",
            "x": INCOME_EXPENSE_STATEMENT["fiscal_year"]["x"],
            "y": INCOME_EXPENSE_STATEMENT["fiscal_year"]["y"],
            "value": f"令和{pl_data.fiscal_year - 2018}年分",
            "font_size": INCOME_EXPENSE_STATEMENT["fiscal_year"]["font_size"],
        }
    )

    # Revenue items
    for i, item in enumerate(pl_data.revenues[:5]):
        fields.append(
            {
                "type": "text",
                "x": INCOME_EXPENSE_STATEMENT[f"revenue_{i}_name"]["x"],
                "y": INCOME_EXPENSE_STATEMENT[f"revenue_{i}_name"]["y"],
                "value": item.account_name,
                "font_size": INCOME_EXPENSE_STATEMENT[f"revenue_{i}_name"]["font_size"],
            }
        )
        fields.append(
            {
                "type": "number",
                "x": INCOME_EXPENSE_STATEMENT[f"revenue_{i}_amount"]["x"],
                "y": INCOME_EXPENSE_STATEMENT[f"revenue_{i}_amount"]["y"],
                "value": item.amount,
                "font_size": INCOME_EXPENSE_STATEMENT[f"revenue_{i}_amount"]["font_size"],
            }
        )

    # Total revenue
    fields.append(
        {
            "type": "number",
            "x": INCOME_EXPENSE_STATEMENT["total_revenue"]["x"],
            "y": INCOME_EXPENSE_STATEMENT["total_revenue"]["y"],
            "value": pl_data.total_revenue,
            "font_size": INCOME_EXPENSE_STATEMENT["total_revenue"]["font_size"],
        }
    )

    # Expense items
    for i, item in enumerate(pl_data.expenses[:15]):
        fields.append(
            {
                "type": "text",
                "x": INCOME_EXPENSE_STATEMENT[f"expense_{i}_name"]["x"],
                "y": INCOME_EXPENSE_STATEMENT[f"expense_{i}_name"]["y"],
                "value": item.account_name,
                "font_size": INCOME_EXPENSE_STATEMENT[f"expense_{i}_name"]["font_size"],
            }
        )
        fields.append(
            {
                "type": "number",
                "x": INCOME_EXPENSE_STATEMENT[f"expense_{i}_amount"]["x"],
                "y": INCOME_EXPENSE_STATEMENT[f"expense_{i}_amount"]["y"],
                "value": item.amount,
                "font_size": INCOME_EXPENSE_STATEMENT[f"expense_{i}_amount"]["font_size"],
            }
        )

    # Total expenses
    fields.append(
        {
            "type": "number",
            "x": INCOME_EXPENSE_STATEMENT["total_expenses"]["x"],
            "y": INCOME_EXPENSE_STATEMENT["total_expenses"]["y"],
            "value": pl_data.total_expense,
            "font_size": INCOME_EXPENSE_STATEMENT["total_expenses"]["font_size"],
        }
    )

    # Net income
    fields.append(
        {
            "type": "number",
            "x": INCOME_EXPENSE_STATEMENT["net_income"]["x"],
            "y": INCOME_EXPENSE_STATEMENT["net_income"]["y"],
            "value": pl_data.net_income,
            "font_size": INCOME_EXPENSE_STATEMENT["net_income"]["font_size"],
        }
    )

    return generate_standalone_pdf(
        fields=fields,
        output_path=output_path,
        title="",
    )


# ============================================================
# Income Tax PDF (Task 19)
# ============================================================


def _build_income_tax_p1_fields(
    tax_result: IncomeTaxResult,
    taxpayer_name: str = "",
    config: ShinkokuConfig | None = None,
) -> list[dict[str, Any]]:
    """第一表のフィールドを構築する。INCOME_TAX_P1 座標（digit_cells方式）を使用。"""
    fields: list[dict[str, Any]] = []

    # --- ヘッダー: config からプロフィール情報を出力 ---
    if config:
        # 郵便番号
        postal = config.address.postal_code.replace("-", "")
        if len(postal) == 7:
            fields.append(_coord_field(INCOME_TAX_P1["postal_code_upper"], int(postal[:3])))
            fields.append(_coord_field(INCOME_TAX_P1["postal_code_lower"], int(postal[3:])))

        # 住所
        addr = (
            config.address.prefecture
            + config.address.city
            + config.address.street
            + config.address.building
        )
        if addr:
            fields.append(_coord_field(INCOME_TAX_P1["address"], addr))

        # 氏名（漢字・カナ）
        name = f"{config.taxpayer.last_name} {config.taxpayer.first_name}".strip()
        if name:
            fields.append(_coord_field(INCOME_TAX_P1["name_kanji"], name))
        kana = f"{config.taxpayer.last_name_kana} {config.taxpayer.first_name_kana}".strip()
        if kana:
            fields.append(_coord_field(INCOME_TAX_P1["name_kana"], kana))

        # 電話番号
        if config.taxpayer.phone:
            fields.append(_coord_field(INCOME_TAX_P1["phone"], config.taxpayer.phone))

        # 生年月日
        if config.taxpayer.date_of_birth:
            fields.append(_coord_field(INCOME_TAX_P1["birth_date"], config.taxpayer.date_of_birth))

        # 青色申告チェックボックス
        if config.filing.return_type == "blue" and "blue_return_checkbox" in INCOME_TAX_P1:
            fields.append(_coord_field(INCOME_TAX_P1["blue_return_checkbox"], True))
    elif taxpayer_name:
        fields.append(_coord_field(INCOME_TAX_P1["name_kanji"], taxpayer_name))

    fields.append(
        _coord_field(
            INCOME_TAX_P1["fiscal_year_label"],
            f"令和{tax_result.fiscal_year - 2018}年分",
        )
    )

    # --- 所得金額等 ---
    if tax_result.business_income != 0:
        fields.append(
            _coord_field(
                INCOME_TAX_P1["business_income"],
                tax_result.business_income,
            )
        )

    if tax_result.salary_income_after_deduction != 0:
        fields.append(
            _coord_field(
                INCOME_TAX_P1["salary_income"],
                tax_result.salary_income_after_deduction,
            )
        )

    fields.append(_coord_field(INCOME_TAX_P1["total_income"], tax_result.total_income))

    # --- 所得控除 ---
    if tax_result.deductions_detail:
        for item in tax_result.deductions_detail.income_deductions:
            field_name = _DEDUCTION_FIELD_MAP.get(item.name)
            if field_name and field_name in INCOME_TAX_P1:
                fields.append(_coord_field(INCOME_TAX_P1[field_name], item.amount))

    fields.append(
        _coord_field(
            INCOME_TAX_P1["total_deductions"],
            tax_result.total_income_deductions,
        )
    )

    # --- 税額の計算 ---
    fields.append(_coord_field(INCOME_TAX_P1["taxable_income"], tax_result.taxable_income))
    fields.append(_coord_field(INCOME_TAX_P1["income_tax_base"], tax_result.income_tax_base))

    # 配当控除（㉜欄）
    if tax_result.dividend_credit > 0 and "dividend_credit" in INCOME_TAX_P1:
        fields.append(_coord_field(INCOME_TAX_P1["dividend_credit"], tax_result.dividend_credit))

    # 住宅ローン控除（㉝欄）
    if tax_result.housing_loan_credit > 0:
        fields.append(
            _coord_field(
                INCOME_TAX_P1["housing_loan_credit"],
                tax_result.housing_loan_credit,
            )
        )

    fields.append(
        _coord_field(
            INCOME_TAX_P1["income_tax_after_credits"],
            tax_result.income_tax_after_credits,
        )
    )
    fields.append(_coord_field(INCOME_TAX_P1["reconstruction_tax"], tax_result.reconstruction_tax))
    fields.append(_coord_field(INCOME_TAX_P1["total_tax"], tax_result.total_tax))

    # 源泉徴収税額（給与 + 事業を合算）
    total_withheld = tax_result.withheld_tax + tax_result.business_withheld_tax
    if total_withheld > 0:
        fields.append(_coord_field(INCOME_TAX_P1["withheld_tax"], total_withheld))

    if tax_result.estimated_tax_payment > 0:
        fields.append(
            _coord_field(
                INCOME_TAX_P1["estimated_tax_payment"],
                tax_result.estimated_tax_payment,
            )
        )

    # 納付/還付
    fields.append(_coord_field(INCOME_TAX_P1["tax_due"], tax_result.tax_due))

    return fields


def generate_income_tax_pdf(
    tax_result: IncomeTaxResult,
    output_path: str = "output/income_tax.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
    config_path: str | None = None,
) -> str:
    """確定申告書B 第一表 PDFを生成する。"""
    config = _resolve_config(config_path)
    fields = _build_income_tax_p1_fields(tax_result, taxpayer_name, config=config)

    # テンプレート解決（明示指定 > 自動解決）
    tmpl = template_path if template_path and Path(template_path).exists() else None
    if tmpl is None:
        resolved = _resolve_template("income_tax_p1")
        tmpl = str(resolved) if resolved else None

    if tmpl:
        overlay_bytes = create_overlay(fields, page_size=NTA_PORTRAIT)
        return merge_overlay(tmpl, overlay_bytes, output_path)

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Consumption Tax PDF (Task 19)
# ============================================================


def _build_consumption_tax_fields(
    tax_result: ConsumptionTaxResult,
    taxpayer_name: str = "",
) -> list[dict[str, Any]]:
    """消費税第一表のフィールドを構築する。CONSUMPTION_TAX_P1 座標を使用。"""
    fields: list[dict[str, Any]] = []

    # ヘッダー
    if taxpayer_name:
        fields.append(_coord_field(CONSUMPTION_TAX_P1["taxpayer_name"], taxpayer_name))

    fields.append(
        _coord_field(
            CONSUMPTION_TAX_P1["fiscal_year"],
            f"令和{tax_result.fiscal_year - 2018}年分",
        )
    )

    # 課税方式チェックボックス
    method_checkbox_map = {
        "standard": "method_standard",
        "simplified": "method_simplified",
        "special_20pct": "method_special_20pct",
    }
    for method_key, field_name in method_checkbox_map.items():
        if field_name in CONSUMPTION_TAX_P1:
            fields.append(
                _coord_field(
                    CONSUMPTION_TAX_P1[field_name],
                    tax_result.method == method_key,
                )
            )

    # 税額（digit_cells）
    if tax_result.taxable_sales_total > 0:
        fields.append(
            _coord_field(
                CONSUMPTION_TAX_P1["taxable_sales_amount"],
                tax_result.taxable_sales_total,
            )
        )

    fields.append(_coord_field(CONSUMPTION_TAX_P1["tax_on_sales"], tax_result.tax_on_sales))
    fields.append(
        _coord_field(
            CONSUMPTION_TAX_P1["tax_on_purchases"],
            tax_result.tax_on_purchases,
        )
    )
    fields.append(_coord_field(CONSUMPTION_TAX_P1["tax_due_national"], tax_result.tax_due))
    fields.append(_coord_field(CONSUMPTION_TAX_P1["local_tax_due"], tax_result.local_tax_due))
    fields.append(_coord_field(CONSUMPTION_TAX_P1["total_tax_due"], tax_result.total_due))

    return fields


def generate_consumption_tax_pdf(
    tax_result: ConsumptionTaxResult,
    output_path: str = "output/consumption_tax.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
) -> str:
    """消費税確定申告書 PDFを生成する。"""
    fields = _build_consumption_tax_fields(tax_result, taxpayer_name)

    # テンプレート解決
    tmpl = template_path if template_path and Path(template_path).exists() else None
    if tmpl is None:
        resolved = _resolve_template("consumption_tax_p1")
        tmpl = str(resolved) if resolved else None

    if tmpl:
        overlay_bytes = create_overlay(fields, page_size=A4)
        return merge_overlay(tmpl, overlay_bytes, output_path)

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Medical Expense Detail PDF
# ============================================================


def generate_medical_expense_detail_pdf(
    expenses: list[dict],
    fiscal_year: int,
    total_income: int = 0,
    output_path: str = "output/medical_expense_detail.pdf",
    taxpayer_name: str = "",
) -> str:
    """Generate medical expense detail form PDF (医療費控除の明細書)."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append(
        {
            "type": "text",
            "x": 105 * mm,
            "y": 285 * mm,
            "value": "医療費控除の明細書",
            "font_size": 12,
        }
    )

    if taxpayer_name:
        fields.append(
            {"type": "text", "x": 60 * mm, "y": 270 * mm, "value": taxpayer_name, "font_size": 10}
        )

    fields.append(
        {
            "type": "text",
            "x": 120 * mm,
            "y": 275 * mm,
            "value": f"令和{fiscal_year - 2018}年分",
            "font_size": 10,
        }
    )

    # Detail lines
    y = 250 * mm
    total_amount = 0
    total_reimbursement = 0

    for exp in expenses[:15]:  # 最大15行
        institution = exp.get("medical_institution", "")
        patient = exp.get("patient_name", "")
        amount = exp.get("amount", 0)
        reimbursement = exp.get("insurance_reimbursement", 0)

        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": institution, "font_size": 7})
        fields.append({"type": "text", "x": 80 * mm, "y": y, "value": patient, "font_size": 7})
        fields.append({"type": "number", "x": 130 * mm, "y": y, "value": amount, "font_size": 7})
        if reimbursement > 0:
            fields.append(
                {"type": "number", "x": 170 * mm, "y": y, "value": reimbursement, "font_size": 7}
            )
        y -= 12 * mm
        total_amount += amount
        total_reimbursement += reimbursement

    # Summary
    y -= 10 * mm
    net_amount = total_amount - total_reimbursement
    medical_threshold = (
        min(MEDICAL_EXPENSE_THRESHOLD, total_income * MEDICAL_EXPENSE_INCOME_RATIO // 100)
        if total_income > 0
        else MEDICAL_EXPENSE_THRESHOLD
    )
    deduction = max(0, min(net_amount - medical_threshold, MEDICAL_EXPENSE_MAX))

    summary_items = [
        ("医療費合計", total_amount),
        ("保険金等の補填額", total_reimbursement),
        ("差引金額", net_amount),
        ("控除額", deduction),
    ]
    for label, value in summary_items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 9})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": value, "font_size": 9})
        y -= 10 * mm

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Housing Loan Credit Detail PDF (住宅借入金等特別控除の計算明細書)
# ============================================================

# 住宅区分ラベル
_HOUSING_TYPE_LABELS: dict[str, str] = {
    "new_custom": "注文住宅（新築）",
    "new_subdivision": "分譲住宅（新築）",
    "resale": "中古住宅",
    "used": "既存住宅",
    "renovation": "増改築等",
}

_HOUSING_CATEGORY_LABELS: dict[str, str] = {
    "general": "一般住宅",
    "certified": "認定住宅（長期優良/低炭素）",
    "zeh": "ZEH水準省エネ住宅",
    "energy_efficient": "省エネ基準適合住宅",
}


def generate_housing_loan_detail_pdf(
    housing_detail: dict,
    credit_amount: int,
    fiscal_year: int,
    output_path: str = "output/housing_loan_detail.pdf",
    taxpayer_name: str = "",
) -> str:
    """Generate housing loan credit calculation detail PDF (住宅借入金等特別控除の計算明細書).

    Args:
        housing_detail: HousingLoanDetail as dict.
        credit_amount: Calculated housing loan credit amount.
        fiscal_year: Fiscal year.
        output_path: Output file path.
        taxpayer_name: Taxpayer name.
    """
    fields: list[dict[str, Any]] = []

    # Title
    fields.append(
        {
            "type": "text",
            "x": 105 * mm,
            "y": 285 * mm,
            "value": "住宅借入金等特別控除額の計算明細書",
            "font_size": 12,
        }
    )

    if taxpayer_name:
        fields.append(
            {"type": "text", "x": 60 * mm, "y": 270 * mm, "value": taxpayer_name, "font_size": 10}
        )

    fields.append(
        {
            "type": "text",
            "x": 120 * mm,
            "y": 275 * mm,
            "value": f"令和{fiscal_year - 2018}年分",
            "font_size": 10,
        }
    )

    # Housing info
    y = 250 * mm
    housing_type = housing_detail.get("housing_type", "")
    housing_category = housing_detail.get("housing_category", "")
    move_in_date = housing_detail.get("move_in_date", "")
    year_end_balance = housing_detail.get("year_end_balance", 0)
    is_new = housing_detail.get("is_new_construction", True)

    type_label = _HOUSING_TYPE_LABELS.get(housing_type, housing_type)
    category_label = _HOUSING_CATEGORY_LABELS.get(housing_category, housing_category)

    info_items = [
        ("住宅の区分", type_label),
        ("住宅の性能", category_label),
        ("入居年月日", move_in_date),
        ("新築/中古", "新築" if is_new else "中古"),
    ]
    for label, value in info_items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "text", "x": 100 * mm, "y": y, "value": str(value), "font_size": 8})
        y -= 10 * mm

    # Calculation
    y -= 10 * mm
    fields.append(
        {"type": "text", "x": 30 * mm, "y": y, "value": "【控除額の計算】", "font_size": 9}
    )
    y -= 12 * mm

    # 年末残高
    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "年末残高", "font_size": 8})
    fields.append(
        {"type": "number", "x": 170 * mm, "y": y, "value": year_end_balance, "font_size": 8}
    )
    y -= 10 * mm

    # 上限額（入居年・世帯区分に基づきテーブル選択）
    key = (housing_category, is_new)
    is_childcare = housing_detail.get("is_childcare_household", False)
    has_pre_r6_permit = housing_detail.get("has_pre_r6_building_permit", False)
    move_in_year = int(move_in_date[:4]) if move_in_date else 2024
    if move_in_year <= 2023:
        limits = HOUSING_LOAN_LIMITS_R4_R5
    elif is_childcare:
        limits = HOUSING_LOAN_LIMITS_R6_R7_CHILDCARE
    else:
        limits = HOUSING_LOAN_LIMITS_R6_R7
    balance_limit = limits.get(key, HOUSING_LOAN_DEFAULT_LIMIT)
    if balance_limit == 0 and housing_category == "general" and is_new and has_pre_r6_permit:
        balance_limit = HOUSING_LOAN_GENERAL_R5_CONFIRMED
    fields.append(
        {
            "type": "text",
            "x": 30 * mm,
            "y": y,
            "value": "借入金等の年末残高の限度額",
            "font_size": 8,
        }
    )
    fields.append({"type": "number", "x": 170 * mm, "y": y, "value": balance_limit, "font_size": 8})
    y -= 10 * mm

    # 控除対象残高
    capped_balance = min(year_end_balance, balance_limit)
    fields.append(
        {"type": "text", "x": 30 * mm, "y": y, "value": "控除対象借入金等の額", "font_size": 8}
    )
    fields.append(
        {"type": "number", "x": 170 * mm, "y": y, "value": capped_balance, "font_size": 8}
    )
    y -= 10 * mm

    # 控除率
    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "控除率", "font_size": 8})
    fields.append({"type": "text", "x": 170 * mm, "y": y, "value": "0.7%", "font_size": 8})
    y -= 10 * mm

    # 控除期間
    period = 13 if is_new else 10
    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "控除期間", "font_size": 8})
    fields.append({"type": "text", "x": 170 * mm, "y": y, "value": f"{period}年間", "font_size": 8})
    y -= 15 * mm

    # 控除額
    fields.append(
        {"type": "text", "x": 30 * mm, "y": y, "value": "住宅借入金等特別控除額", "font_size": 10}
    )
    fields.append(
        {"type": "number", "x": 170 * mm, "y": y, "value": credit_amount, "font_size": 10}
    )

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Schedule 3 PDF (第三表: 分離課税用)
# ============================================================


def generate_schedule_3_pdf(
    tax_result: SeparateTaxResult,
    output_path: str = "output/schedule_3.pdf",
    taxpayer_name: str = "",
) -> str:
    """Generate Schedule 3 PDF (分離課税用)."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append(
        {
            "type": "text",
            "x": 105 * mm,
            "y": 285 * mm,
            "value": "確定申告書 第三表（分離課税用）",
            "font_size": 12,
        }
    )

    if taxpayer_name:
        fields.append(
            {"type": "text", "x": 60 * mm, "y": 270 * mm, "value": taxpayer_name, "font_size": 10}
        )

    fields.append(
        {
            "type": "text",
            "x": 120 * mm,
            "y": 275 * mm,
            "value": f"令和{tax_result.fiscal_year - 2018}年分",
            "font_size": 10,
        }
    )

    # 株式等の譲渡所得
    y = 245 * mm
    fields.append(
        {"type": "text", "x": 30 * mm, "y": y, "value": "【株式等の譲渡所得等】", "font_size": 9}
    )
    y -= 10 * mm

    stock_items = [
        ("譲渡益（損）", tax_result.stock_net_gain),
        ("配当との損益通算額", tax_result.stock_dividend_offset),
        ("繰越損失適用額", tax_result.stock_loss_carryforward_used),
        ("課税所得金額", tax_result.stock_taxable_income),
        ("所得税額（15%）", tax_result.stock_income_tax),
        ("住民税額（5%）", tax_result.stock_residential_tax),
        ("復興特別所得税", tax_result.stock_reconstruction_tax),
        ("税額合計", tax_result.stock_total_tax),
        ("源泉徴収税額", tax_result.stock_withheld_total),
        ("差引納付/還付", tax_result.stock_tax_due),
    ]
    for label, value in stock_items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": value, "font_size": 8})
        y -= 10 * mm

    # FX（先物取引に係る雑所得等）
    y -= 5 * mm
    fields.append(
        {
            "type": "text",
            "x": 30 * mm,
            "y": y,
            "value": "【先物取引に係る雑所得等】",
            "font_size": 9,
        }
    )
    y -= 10 * mm

    fx_items = [
        ("所得金額", tax_result.fx_net_income),
        ("繰越損失適用額", tax_result.fx_loss_carryforward_used),
        ("課税所得金額", tax_result.fx_taxable_income),
        ("所得税額（15%）", tax_result.fx_income_tax),
        ("住民税額（5%）", tax_result.fx_residential_tax),
        ("復興特別所得税", tax_result.fx_reconstruction_tax),
        ("税額合計", tax_result.fx_total_tax),
        ("納付税額", tax_result.fx_tax_due),
    ]
    for label, value in fx_items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": value, "font_size": 8})
        y -= 10 * mm

    # 合計
    y -= 5 * mm
    fields.append(
        {"type": "text", "x": 30 * mm, "y": y, "value": "分離課税 税額合計", "font_size": 10}
    )
    fields.append(
        {
            "type": "number",
            "x": 170 * mm,
            "y": y,
            "value": tax_result.total_separate_tax,
            "font_size": 10,
        }
    )

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Schedule 4 PDF (第四表: 損失申告用)
# ============================================================


def generate_schedule_4_pdf(
    losses: list[dict],
    fiscal_year: int,
    output_path: str = "output/schedule_4.pdf",
    taxpayer_name: str = "",
) -> str:
    """Generate Schedule 4 PDF (損失申告用).

    Args:
        losses: List of loss records, each with: loss_type, loss_year, amount, used_amount.
        fiscal_year: Fiscal year.
        output_path: Output file path.
        taxpayer_name: Taxpayer name.
    """
    fields: list[dict[str, Any]] = []

    # Title
    fields.append(
        {
            "type": "text",
            "x": 105 * mm,
            "y": 285 * mm,
            "value": "確定申告書 第四表（損失申告用）",
            "font_size": 12,
        }
    )

    if taxpayer_name:
        fields.append(
            {"type": "text", "x": 60 * mm, "y": 270 * mm, "value": taxpayer_name, "font_size": 10}
        )

    fields.append(
        {
            "type": "text",
            "x": 120 * mm,
            "y": 275 * mm,
            "value": f"令和{fiscal_year - 2018}年分",
            "font_size": 10,
        }
    )

    # 損失種別ごとにセクション分け
    _type_labels = {
        "business": "事業所得の損失",
        "stock": "株式等の譲渡損失",
        "fx": "先物取引の損失",
    }

    y = 250 * mm
    for loss_type, label in _type_labels.items():
        type_losses = [lo for lo in losses if lo.get("loss_type") == loss_type]
        if not type_losses:
            continue

        fields.append(
            {"type": "text", "x": 30 * mm, "y": y, "value": f"【{label}】", "font_size": 9}
        )
        y -= 10 * mm

        # Column headers
        for hx, htext in [
            (40 * mm, "損失発生年"),
            (95 * mm, "損失額"),
            (140 * mm, "控除済額"),
            (170 * mm, "繰越残額"),
        ]:
            fields.append({"type": "text", "x": hx, "y": y, "value": htext, "font_size": 7})
        y -= 8 * mm

        for lo in type_losses[:3]:  # 最大3年
            loss_year = lo.get("loss_year", 0)
            amount = lo.get("amount", 0)
            used = lo.get("used_amount", 0)
            remaining = amount - used

            fields.append(
                {
                    "type": "text",
                    "x": 40 * mm,
                    "y": y,
                    "value": f"令和{loss_year - 2018}年",
                    "font_size": 8,
                }
            )
            fields.append({"type": "number", "x": 95 * mm, "y": y, "value": amount, "font_size": 8})
            fields.append({"type": "number", "x": 140 * mm, "y": y, "value": used, "font_size": 8})
            fields.append(
                {"type": "number", "x": 170 * mm, "y": y, "value": remaining, "font_size": 8}
            )
            y -= 12 * mm

        y -= 5 * mm

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Income Tax Page 2 (確定申告書B 第二表)
# ============================================================

# 社会保険料グループ — 第二表の2行枠に合算するための分類
_SOCIAL_INSURANCE_GROUP: dict[str, str] = {
    "健康保険": "健康保険等",
    "介護保険": "健康保険等",
    "雇用保険": "健康保険等",
    "厚生年金": "年金",
    "国民年金": "年金",
    "国民年金基金": "年金",
}


def _consolidate_social_insurance(items: list[dict]) -> list[dict]:
    """社会保険料を2行以内に合算する。

    2行以下の場合はそのまま返す。3行以上の場合は健康保険等/年金に
    グループ化して合算し、それでも2行を超える場合は1行に全合計する。
    """
    if len(items) <= 2:
        return items
    grouped: dict[str, int] = {}
    for item in items:
        key = _SOCIAL_INSURANCE_GROUP.get(item.get("type", ""), item.get("type", "その他"))
        grouped[key] = grouped.get(key, 0) + item.get("amount", 0)
    result = [{"type": k, "payer": "", "amount": v} for k, v in grouped.items()]
    if len(result) > 2:
        total = sum(r["amount"] for r in result)
        return [{"type": "社会保険料合計", "payer": "", "amount": total}]
    return result[:2]


def _build_income_tax_p2_fields(
    taxpayer_name: str = "",
    income_details: list[dict] | None = None,
    social_insurance_details: list[dict] | None = None,
    dependents: list[dict] | None = None,
    spouse: dict | None = None,
    housing_loan_move_in_date: str = "",
) -> tuple[list[dict[str, Any]], list[dict]]:
    """第二表のフィールドを構築する。INCOME_TAX_P2 座標を使用。

    Returns:
        (fields, overflow_income_details):
        - fields: P2に描画するフィールドリスト
        - overflow_income_details: 5件以上の所得内訳がある場合、
          全件を所得の内訳書に出力するためのリスト（4件以下なら空リスト）
    """
    fields: list[dict[str, Any]] = []
    overflow_income_details: list[dict] = []

    if taxpayer_name:
        fields.append(_coord_field(INCOME_TAX_P2["name_kanji"], taxpayer_name))

    # 所得の内訳（最大4行 — フォームの枠数に合わせる）
    details = income_details or []
    if len(details) <= 4:
        # 4行以下: 通常処理
        for i, detail in enumerate(details):
            prefix = f"income_detail_{i}"
            if detail.get("type"):
                fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_type"], detail["type"]))
            if detail.get("payer"):
                fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_payer"], detail["payer"]))
            if detail.get("revenue"):
                fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_revenue"], detail["revenue"]))
            if detail.get("withheld"):
                fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_withheld"], detail["withheld"]))
    else:
        # 5行以上: P2には「別紙のとおり」+ 合計のみ記載、全件をoverflowへ
        total_revenue = sum(d.get("revenue", 0) for d in details)
        total_withheld = sum(d.get("withheld", 0) for d in details)
        prefix = "income_detail_0"
        fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_type"], "各種"))
        fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_payer"], "別紙のとおり"))
        if total_revenue:
            fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_revenue"], total_revenue))
        if total_withheld:
            fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_withheld"], total_withheld))
        overflow_income_details = details

    # 社会保険料の内訳（合算して2行以内に収める）
    consolidated = _consolidate_social_insurance(social_insurance_details or [])
    for i, si in enumerate(consolidated[:2]):
        prefix = f"social_insurance_{i}"
        if si.get("type"):
            fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_type"], si["type"]))
        if si.get("payer"):
            fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_payer"], si["payer"]))
        if si.get("amount"):
            fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_amount"], si["amount"]))

    # 扶養控除対象者（最大4名）
    for i, dep in enumerate((dependents or [])[:4]):
        prefix = f"dependent_{i}"
        if dep.get("name"):
            fields.append(_coord_field(INCOME_TAX_P2[f"{prefix}_name"], dep["name"]))
        if dep.get("relationship"):
            fields.append(
                _coord_field(
                    INCOME_TAX_P2[f"{prefix}_relationship"],
                    dep["relationship"],
                )
            )
        if dep.get("birth_date"):
            fields.append(
                _coord_field(
                    INCOME_TAX_P2[f"{prefix}_birth_date"],
                    dep["birth_date"],
                )
            )

    # 配偶者情報
    if spouse:
        if spouse.get("name"):
            fields.append(_coord_field(INCOME_TAX_P2["spouse_name"], spouse["name"]))
        if spouse.get("income"):
            fields.append(_coord_field(INCOME_TAX_P2["spouse_income"], spouse["income"]))

    # 住宅ローン居住開始日
    if housing_loan_move_in_date:
        fields.append(
            _coord_field(
                INCOME_TAX_P2["housing_loan_move_in_date"],
                housing_loan_move_in_date,
            )
        )

    return fields, overflow_income_details


def _build_income_detail_sheet_fields(
    income_details: list[dict],
    taxpayer_name: str = "",
    address: str = "",
    fiscal_year: int = 2025,
) -> list[dict[str, Any]]:
    """所得の内訳書のフィールドを構築する。INCOME_DETAIL_SHEET 座標を使用。

    NTA公式テンプレートに最大19行の所得明細を記入する。
    """
    fields: list[dict[str, Any]] = []

    # ヘッダー
    if taxpayer_name:
        fields.append(_coord_field(INCOME_DETAIL_SHEET["name_kanji"], taxpayer_name))
    if address:
        fields.append(_coord_field(INCOME_DETAIL_SHEET["address"], address))
    fields.append(
        _coord_field(
            INCOME_DETAIL_SHEET["fiscal_year"],
            f"令和{fiscal_year - 2018}年分",
        )
    )

    # データ行（最大19行）
    total_revenue = 0
    total_withheld = 0
    for i, detail in enumerate(income_details[:19]):
        prefix = f"row_{i}"
        if detail.get("type"):
            fields.append(_coord_field(INCOME_DETAIL_SHEET[f"{prefix}_type"], detail["type"]))
        if detail.get("payer"):
            fields.append(_coord_field(INCOME_DETAIL_SHEET[f"{prefix}_payer"], detail["payer"]))
        revenue = detail.get("revenue", 0)
        withheld = detail.get("withheld", 0)
        if revenue:
            fields.append(_coord_field(INCOME_DETAIL_SHEET[f"{prefix}_revenue"], revenue))
            total_revenue += revenue
        if withheld:
            fields.append(_coord_field(INCOME_DETAIL_SHEET[f"{prefix}_withheld"], withheld))
            total_withheld += withheld

    # 合計行
    if total_revenue:
        fields.append(_coord_field(INCOME_DETAIL_SHEET["total_revenue"], total_revenue))
    if total_withheld:
        fields.append(_coord_field(INCOME_DETAIL_SHEET["total_withheld"], total_withheld))

    return fields


def generate_income_detail_sheet_pdf(
    income_details: list[dict],
    output_path: str = "output/income_detail_sheet.pdf",
    taxpayer_name: str = "",
    address: str = "",
    fiscal_year: int = 2025,
) -> str:
    """所得の内訳書 PDFを生成する。

    NTA公式テンプレートにオーバーレイして所得明細を記入する。
    """
    fields = _build_income_detail_sheet_fields(
        income_details=income_details,
        taxpayer_name=taxpayer_name,
        address=address,
        fiscal_year=fiscal_year,
    )

    tmpl = _resolve_template("income_detail_sheet")
    if tmpl:
        overlay_bytes = create_overlay(fields, page_size=INCOME_DETAIL_SHEET_SIZE)
        return merge_overlay(str(tmpl), overlay_bytes, output_path)

    return generate_standalone_pdf(fields=fields, output_path=output_path)


def generate_income_tax_page2_pdf(
    income_details: list[dict] | None = None,
    social_insurance_details: list[dict] | None = None,
    dependents: list[dict] | None = None,
    spouse: dict | None = None,
    housing_loan_move_in_date: str = "",
    output_path: str = "output/income_tax_p2.pdf",
    taxpayer_name: str = "",
) -> str:
    """確定申告書B 第二表 PDFを生成する。

    所得内訳が5件以上の場合、別途「所得の内訳書」PDFも生成する。
    """
    fields, overflow = _build_income_tax_p2_fields(
        taxpayer_name=taxpayer_name,
        income_details=income_details,
        social_insurance_details=social_insurance_details,
        dependents=dependents,
        spouse=spouse,
        housing_loan_move_in_date=housing_loan_move_in_date,
    )

    tmpl = _resolve_template("income_tax_p2")
    if tmpl:
        overlay_bytes = create_overlay(fields, page_size=NTA_PORTRAIT)
        result_path = merge_overlay(str(tmpl), overlay_bytes, output_path)
    else:
        result_path = generate_standalone_pdf(fields=fields, output_path=output_path)

    # overflow がある場合、所得の内訳書も生成
    if overflow:
        detail_output = str(Path(output_path).parent / "income_detail_sheet.pdf")
        generate_income_detail_sheet_pdf(
            income_details=overflow,
            output_path=detail_output,
            taxpayer_name=taxpayer_name,
        )

    return result_path


# ============================================================
# Full Tax Document Set (全帳票セット一括生成)
# ============================================================


def generate_full_tax_document_set(
    income_tax: IncomeTaxResult,
    pl_data: PLResult,
    bs_data: BSResult | None = None,
    consumption_tax: ConsumptionTaxResult | None = None,
    income_details: list[dict] | None = None,
    social_insurance_details: list[dict] | None = None,
    dependents: list[dict] | None = None,
    spouse: dict | None = None,
    housing_loan_move_in_date: str = "",
    output_path: str = "output/full_tax_set.pdf",
    taxpayer_name: str = "",
    config: ShinkokuConfig | None = None,
) -> str:
    """全帳票を1つのPDFに結合して出力する。

    ページ順序:
    1. 確定申告書B 第一表
    2. 確定申告書B 第二表
    2a. 所得の内訳書 (所得内訳5件以上の場合)
    3. 青色申告決算書 損益計算書 P1
    4. 青色申告決算書 貸借対照表 (if bs_data)
    5-6. 消費税 (if consumption_tax)
    """
    pages: list[list[dict[str, Any]]] = []
    template_paths: list[str] = []
    page_sizes: list[tuple[float, float]] = []
    page_rotations: list[int] = []

    def _add_page(
        fields: list[dict[str, Any]],
        size: tuple[float, float],
        template_name: str,
        rotation: int = 0,
    ) -> None:
        pages.append(fields)
        page_sizes.append(size)
        page_rotations.append(rotation)
        tmpl = _resolve_template(template_name)
        template_paths.append(str(tmpl) if tmpl else "")

    # 1. 確定申告書B 第一表 — NTA テンプレートは標準A4ではない
    _add_page(
        _build_income_tax_p1_fields(income_tax, taxpayer_name, config=config),
        NTA_PORTRAIT,
        "income_tax_p1",
    )

    # 2. 確定申告書B 第二表
    p2_fields, overflow_income_details = _build_income_tax_p2_fields(
        taxpayer_name=taxpayer_name,
        income_details=income_details,
        social_insurance_details=social_insurance_details,
        dependents=dependents,
        spouse=spouse,
        housing_loan_move_in_date=housing_loan_move_in_date,
    )
    _add_page(p2_fields, NTA_PORTRAIT, "income_tax_p2")

    # 2a. 所得の内訳書（overflow がある場合のみ）
    if overflow_income_details:
        # config から住所を取得（あれば）
        addr = ""
        if config and config.address:
            addr = (
                config.address.prefecture
                + config.address.city
                + config.address.street
                + config.address.building
            )
        detail_fields = _build_income_detail_sheet_fields(
            income_details=overflow_income_details,
            taxpayer_name=taxpayer_name,
            address=addr,
            fiscal_year=income_tax.fiscal_year,
        )
        _add_page(detail_fields, INCOME_DETAIL_SHEET_SIZE, "income_detail_sheet")

    # 3. 青色申告決算書 損益計算書 P1 — NTA PDF は portrait + /Rotate=90
    _add_page(
        _build_pl_fields(pl_data, taxpayer_name),
        A4_LANDSCAPE,
        "blue_return_pl_p1",
        rotation=90,
    )

    # 4. 青色申告決算書 貸借対照表 — 同上
    if bs_data is not None:
        _add_page(
            _build_bs_fields(bs_data, taxpayer_name),
            A4_LANDSCAPE,
            "blue_return_bs",
            rotation=90,
        )

    # 5-6. 消費税
    if consumption_tax is not None:
        _add_page(
            _build_consumption_tax_fields(consumption_tax, taxpayer_name),
            A4_PORTRAIT,
            "consumption_tax_p1",
        )
        # 付表（データなし — テンプレートのみ表示）
        _add_page([], A4_PORTRAIT, "consumption_tax_p2")

    # Generate
    overlay_bytes = create_multi_page_overlay(
        pages,
        page_sizes=page_sizes,
        page_rotations=page_rotations,
    )
    has_any_template = any(p for p in template_paths)

    if has_any_template:
        return merge_multi_template_overlay(template_paths, overlay_bytes, output_path)

    return generate_standalone_multi_page_pdf(
        pages=pages,
        output_path=output_path,
        page_sizes=page_sizes,
    )


# ============================================================
# MCP Tool Registration
# ============================================================


def _resolve_config(
    config_path: str | None,
) -> ShinkokuConfig | None:
    """Load ShinkokuConfig from YAML. Returns None if unavailable."""
    if config_path:
        try:
            from shinkoku.config import load_config

            return load_config(config_path)
        except Exception:
            pass
    return None


def _resolve_taxpayer_name(taxpayer_name: str, config_path: str | None) -> str:
    """Resolve taxpayer name: use provided name, or load from config."""
    if taxpayer_name:
        return taxpayer_name
    config = _resolve_config(config_path)
    if config:
        name = f"{config.taxpayer.last_name} {config.taxpayer.first_name}".strip()
        return name
    return ""


def register(mcp) -> None:
    """Register document generation tools with the MCP server."""

    @mcp.tool()
    def doc_generate_bs_pl(
        fiscal_year: int,
        pl_revenues: list[dict] | None = None,
        pl_expenses: list[dict] | None = None,
        bs_assets: list[dict] | None = None,
        bs_liabilities: list[dict] | None = None,
        bs_equity: list[dict] | None = None,
        output_path: str = "output/bs_pl.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate blue return BS/PL PDF from financial data."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        pl_rev_items = [PLItem(**r) for r in (pl_revenues or [])]
        pl_exp_items = [PLItem(**e) for e in (pl_expenses or [])]
        total_rev = sum(i.amount for i in pl_rev_items)
        total_exp = sum(i.amount for i in pl_exp_items)

        pl_data = PLResult(
            fiscal_year=fiscal_year,
            revenues=pl_rev_items,
            expenses=pl_exp_items,
            total_revenue=total_rev,
            total_expense=total_exp,
            net_income=total_rev - total_exp,
        )

        bs_data = None
        if bs_assets is not None:
            bs_asset_items = [BSItem(**a) for a in (bs_assets or [])]
            bs_liab_items = [BSItem(**li) for li in (bs_liabilities or [])]
            bs_eq_items = [BSItem(**e) for e in (bs_equity or [])]
            bs_data = BSResult(
                fiscal_year=fiscal_year,
                assets=bs_asset_items,
                liabilities=bs_liab_items,
                equity=bs_eq_items,
                total_assets=sum(i.amount for i in bs_asset_items),
                total_liabilities=sum(i.amount for i in bs_liab_items),
                total_equity=sum(i.amount for i in bs_eq_items),
            )

        path = generate_bs_pl_pdf(
            pl_data=pl_data,
            bs_data=bs_data,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path, "pages": 2 if bs_data else 1}

    @mcp.tool()
    def doc_generate_income_tax(
        fiscal_year: int,
        salary_income_after_deduction: int = 0,
        business_income: int = 0,
        total_income: int = 0,
        total_income_deductions: int = 0,
        taxable_income: int = 0,
        income_tax_base: int = 0,
        dividend_credit: int = 0,
        housing_loan_credit: int = 0,
        total_tax_credits: int = 0,
        income_tax_after_credits: int = 0,
        reconstruction_tax: int = 0,
        total_tax: int = 0,
        withheld_tax: int = 0,
        tax_due: int = 0,
        output_path: str = "output/income_tax.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate income tax form B PDF."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        tax_result = IncomeTaxResult(
            fiscal_year=fiscal_year,
            salary_income_after_deduction=salary_income_after_deduction,
            business_income=business_income,
            total_income=total_income,
            total_income_deductions=total_income_deductions,
            taxable_income=taxable_income,
            income_tax_base=income_tax_base,
            dividend_credit=dividend_credit,
            housing_loan_credit=housing_loan_credit,
            total_tax_credits=total_tax_credits,
            income_tax_after_credits=income_tax_after_credits,
            reconstruction_tax=reconstruction_tax,
            total_tax=total_tax,
            withheld_tax=withheld_tax,
            tax_due=tax_due,
        )
        path = generate_income_tax_pdf(
            tax_result=tax_result,
            output_path=output_path,
            taxpayer_name=resolved_name,
            config_path=config_path,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_consumption_tax(
        fiscal_year: int,
        method: str = "special_20pct",
        taxable_sales_total: int = 0,
        tax_on_sales: int = 0,
        tax_on_purchases: int = 0,
        tax_due: int = 0,
        local_tax_due: int = 0,
        total_due: int = 0,
        output_path: str = "output/consumption_tax.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate consumption tax form PDF."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        tax_result = ConsumptionTaxResult(
            fiscal_year=fiscal_year,
            method=method,
            taxable_sales_total=taxable_sales_total,
            tax_on_sales=tax_on_sales,
            tax_on_purchases=tax_on_purchases,
            tax_due=tax_due,
            local_tax_due=local_tax_due,
            total_due=total_due,
        )
        path = generate_consumption_tax_pdf(
            tax_result=tax_result,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_medical_expense_detail(
        fiscal_year: int,
        expenses: list[dict] | None = None,
        total_income: int = 0,
        output_path: str = "output/medical_expense_detail.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate medical expense detail form PDF (医療費控除の明細書)."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        path = generate_medical_expense_detail_pdf(
            expenses=expenses or [],
            fiscal_year=fiscal_year,
            total_income=total_income,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_housing_loan_detail(
        fiscal_year: int,
        housing_detail: dict | None = None,
        credit_amount: int = 0,
        output_path: str = "output/housing_loan_detail.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate housing loan credit calculation detail PDF (住宅借入金等特別控除の計算明細書)."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        path = generate_housing_loan_detail_pdf(
            housing_detail=housing_detail or {},
            credit_amount=credit_amount,
            fiscal_year=fiscal_year,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_schedule_3(
        fiscal_year: int,
        stock_net_gain: int = 0,
        stock_dividend_offset: int = 0,
        stock_taxable_income: int = 0,
        stock_loss_carryforward_used: int = 0,
        stock_income_tax: int = 0,
        stock_residential_tax: int = 0,
        stock_reconstruction_tax: int = 0,
        stock_total_tax: int = 0,
        stock_withheld_total: int = 0,
        stock_tax_due: int = 0,
        fx_net_income: int = 0,
        fx_taxable_income: int = 0,
        fx_loss_carryforward_used: int = 0,
        fx_income_tax: int = 0,
        fx_residential_tax: int = 0,
        fx_reconstruction_tax: int = 0,
        fx_total_tax: int = 0,
        fx_tax_due: int = 0,
        total_separate_tax: int = 0,
        output_path: str = "output/schedule_3.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate Schedule 3 PDF (第三表: 分離課税用)."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        tax_result = SeparateTaxResult(
            fiscal_year=fiscal_year,
            stock_net_gain=stock_net_gain,
            stock_dividend_offset=stock_dividend_offset,
            stock_taxable_income=stock_taxable_income,
            stock_loss_carryforward_used=stock_loss_carryforward_used,
            stock_income_tax=stock_income_tax,
            stock_residential_tax=stock_residential_tax,
            stock_reconstruction_tax=stock_reconstruction_tax,
            stock_total_tax=stock_total_tax,
            stock_withheld_total=stock_withheld_total,
            stock_tax_due=stock_tax_due,
            fx_net_income=fx_net_income,
            fx_taxable_income=fx_taxable_income,
            fx_loss_carryforward_used=fx_loss_carryforward_used,
            fx_income_tax=fx_income_tax,
            fx_residential_tax=fx_residential_tax,
            fx_reconstruction_tax=fx_reconstruction_tax,
            fx_total_tax=fx_total_tax,
            fx_tax_due=fx_tax_due,
            total_separate_tax=total_separate_tax,
        )
        path = generate_schedule_3_pdf(
            tax_result=tax_result,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_schedule_4(
        fiscal_year: int,
        losses: list[dict] | None = None,
        output_path: str = "output/schedule_4.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate Schedule 4 PDF (第四表: 損失申告用)."""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        path = generate_schedule_4_pdf(
            losses=losses or [],
            fiscal_year=fiscal_year,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_income_expense_statement(
        fiscal_year: int,
        pl_revenues: list[dict] | None = None,
        pl_expenses: list[dict] | None = None,
        output_path: str = "output/income_expense_statement.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """Generate income/expense statement PDF (収支内訳書: 白色申告用).

        白色申告の場合に青色申告決算書の代わりに提出する。
        損益計算書のみで貸借対照表は不要。
        """
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        rev_items = [PLItem(**r) for r in (pl_revenues or [])]
        exp_items = [PLItem(**e) for e in (pl_expenses or [])]
        pl_data = PLResult(
            fiscal_year=fiscal_year,
            revenues=rev_items,
            expenses=exp_items,
            total_revenue=sum(r.amount for r in rev_items),
            total_expense=sum(e.amount for e in exp_items),
            net_income=sum(r.amount for r in rev_items) - sum(e.amount for e in exp_items),
        )
        path = generate_income_expense_statement_pdf(
            pl_data=pl_data,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_income_tax_page2(
        income_details: list[dict] | None = None,
        social_insurance_details: list[dict] | None = None,
        dependents: list[dict] | None = None,
        spouse: dict | None = None,
        housing_loan_move_in_date: str = "",
        output_path: str = "output/income_tax_p2.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """確定申告書B 第二表 PDFを生成する。

        所得の内訳、社会保険料、扶養控除対象者、配偶者情報を記載。
        """
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)
        path = generate_income_tax_page2_pdf(
            income_details=income_details,
            social_insurance_details=social_insurance_details,
            dependents=dependents,
            spouse=spouse,
            housing_loan_move_in_date=housing_loan_move_in_date,
            output_path=output_path,
            taxpayer_name=resolved_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_full_set(
        fiscal_year: int,
        salary_income_after_deduction: int = 0,
        business_income: int = 0,
        total_income: int = 0,
        total_income_deductions: int = 0,
        taxable_income: int = 0,
        income_tax_base: int = 0,
        total_tax_credits: int = 0,
        income_tax_after_credits: int = 0,
        reconstruction_tax: int = 0,
        total_tax: int = 0,
        withheld_tax: int = 0,
        tax_due: int = 0,
        pl_revenues: list[dict] | None = None,
        pl_expenses: list[dict] | None = None,
        bs_assets: list[dict] | None = None,
        bs_liabilities: list[dict] | None = None,
        bs_equity: list[dict] | None = None,
        consumption_method: str | None = None,
        consumption_taxable_sales_total: int = 0,
        consumption_tax_on_sales: int = 0,
        consumption_tax_on_purchases: int = 0,
        consumption_tax_due: int = 0,
        consumption_local_tax_due: int = 0,
        consumption_total_due: int = 0,
        output_path: str = "output/full_tax_set.pdf",
        taxpayer_name: str = "",
        config_path: str | None = None,
    ) -> dict:
        """全帳票セットを1つのPDFに結合して生成する。"""
        resolved_name = _resolve_taxpayer_name(taxpayer_name, config_path)

        income_tax = IncomeTaxResult(
            fiscal_year=fiscal_year,
            salary_income_after_deduction=salary_income_after_deduction,
            business_income=business_income,
            total_income=total_income,
            total_income_deductions=total_income_deductions,
            taxable_income=taxable_income,
            income_tax_base=income_tax_base,
            total_tax_credits=total_tax_credits,
            income_tax_after_credits=income_tax_after_credits,
            reconstruction_tax=reconstruction_tax,
            total_tax=total_tax,
            withheld_tax=withheld_tax,
            tax_due=tax_due,
        )

        rev_items = [PLItem(**r) for r in (pl_revenues or [])]
        exp_items = [PLItem(**e) for e in (pl_expenses or [])]
        pl_data = PLResult(
            fiscal_year=fiscal_year,
            revenues=rev_items,
            expenses=exp_items,
            total_revenue=sum(r.amount for r in rev_items),
            total_expense=sum(e.amount for e in exp_items),
            net_income=sum(r.amount for r in rev_items) - sum(e.amount for e in exp_items),
        )

        bs_data = None
        if bs_assets is not None:
            bs_asset_items = [BSItem(**a) for a in (bs_assets or [])]
            bs_liab_items = [BSItem(**li) for li in (bs_liabilities or [])]
            bs_eq_items = [BSItem(**e) for e in (bs_equity or [])]
            bs_data = BSResult(
                fiscal_year=fiscal_year,
                assets=bs_asset_items,
                liabilities=bs_liab_items,
                equity=bs_eq_items,
                total_assets=sum(i.amount for i in bs_asset_items),
                total_liabilities=sum(i.amount for i in bs_liab_items),
                total_equity=sum(i.amount for i in bs_eq_items),
            )

        consumption_tax = None
        if consumption_method:
            consumption_tax = ConsumptionTaxResult(
                fiscal_year=fiscal_year,
                method=consumption_method,
                taxable_sales_total=consumption_taxable_sales_total,
                tax_on_sales=consumption_tax_on_sales,
                tax_on_purchases=consumption_tax_on_purchases,
                tax_due=consumption_tax_due,
                local_tax_due=consumption_local_tax_due,
                total_due=consumption_total_due,
            )

        config = _resolve_config(config_path)
        path = generate_full_tax_document_set(
            income_tax=income_tax,
            pl_data=pl_data,
            bs_data=bs_data,
            consumption_tax=consumption_tax,
            output_path=output_path,
            taxpayer_name=resolved_name,
            config=config,
        )

        num_pages = 3  # P1 + P2 + PL
        # 所得の内訳書（income_details が5件以上あれば追加）
        # generate_full_tax_document_set 内で自動判定されるが、
        # ここでも件数でカウント
        if bs_data:
            num_pages += 1
        if consumption_tax:
            num_pages += 2

        return {"output_path": path, "pages": num_pages}

    @mcp.tool()
    def doc_preview_pdf(
        pdf_path: str,
        output_dir: str = "output/preview",
        dpi: int = 150,
    ) -> dict:
        """生成済みPDFをページごとの画像に変換し、目視確認用のプレビューを生成する。"""
        images = pdf_to_images(pdf_path, output_dir, dpi)
        return {"images": images, "num_pages": len(images)}
