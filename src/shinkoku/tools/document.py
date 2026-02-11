"""Document generation tools for tax filing PDFs.

Generates:
- Blue return BS/PL (balance sheet + profit/loss)
- Income tax form B
- Consumption tax form
- Deduction detail form
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.units import mm

from shinkoku.models import (
    PLResult,
    PLItem,
    BSResult,
    BSItem,
    IncomeTaxResult,
    ConsumptionTaxResult,
    DeductionsResult,
)
from shinkoku.tools.pdf_utils import (
    generate_standalone_multi_page_pdf,
    generate_standalone_pdf,
)
from shinkoku.tools.pdf_coordinates import (
    BLUE_RETURN_PL,
    BLUE_RETURN_BS,
    INCOME_TAX_FORM_B,
)


# ============================================================
# Blue Return BS/PL (Task 18)
# ============================================================

def _build_pl_fields(
    pl_data: PLResult,
    taxpayer_name: str = "",
) -> list[dict[str, Any]]:
    """Build field list for P/L page."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append({
        "type": "text",
        "x": 105 * mm, "y": 285 * mm,
        "value": "損益計算書（青色申告決算書）",
        "font_size": 12,
    })

    # Header
    if taxpayer_name:
        fields.append({
            "type": "text",
            "x": BLUE_RETURN_PL["taxpayer_name"]["x"],
            "y": BLUE_RETURN_PL["taxpayer_name"]["y"],
            "value": taxpayer_name,
            "font_size": BLUE_RETURN_PL["taxpayer_name"]["font_size"],
        })

    fields.append({
        "type": "text",
        "x": BLUE_RETURN_PL["fiscal_year"]["x"],
        "y": BLUE_RETURN_PL["fiscal_year"]["y"],
        "value": f"令和{pl_data.fiscal_year - 2018}年分",
        "font_size": BLUE_RETURN_PL["fiscal_year"]["font_size"],
    })

    # Revenue items
    y_start = 240 * mm
    for i, item in enumerate(pl_data.revenues):
        y = y_start - i * 8 * mm
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": item.account_name, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": item.amount, "font_size": 8})

    # Total revenue
    fields.append({
        "type": "text", "x": 30 * mm, "y": 220 * mm, "value": "収入合計", "font_size": 9,
    })
    fields.append({
        "type": "number",
        "x": BLUE_RETURN_PL["total_revenue"]["x"],
        "y": BLUE_RETURN_PL["total_revenue"]["y"],
        "value": pl_data.total_revenue,
        "font_size": 9,
    })

    # Expense items
    y_start = 195 * mm
    for i, item in enumerate(pl_data.expenses):
        y = y_start - i * 8 * mm
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": item.account_name, "font_size": 8})
        fields.append({"type": "number", "x": 80 * mm, "y": y, "value": item.amount, "font_size": 8})

    # Total expenses
    y_total_exp = y_start - len(pl_data.expenses) * 8 * mm - 5 * mm
    fields.append({"type": "text", "x": 30 * mm, "y": y_total_exp, "value": "経費合計", "font_size": 9})
    fields.append({"type": "number", "x": 170 * mm, "y": y_total_exp, "value": pl_data.total_expense, "font_size": 9})

    # Net income
    y_net = y_total_exp - 12 * mm
    fields.append({"type": "text", "x": 30 * mm, "y": y_net, "value": "差引金額（所得金額）", "font_size": 9})
    fields.append({"type": "number", "x": 170 * mm, "y": y_net, "value": pl_data.net_income, "font_size": 10})

    return fields


def _build_bs_fields(
    bs_data: BSResult,
    taxpayer_name: str = "",
) -> list[dict[str, Any]]:
    """Build field list for B/S page."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append({
        "type": "text",
        "x": 105 * mm, "y": 285 * mm,
        "value": "貸借対照表（青色申告決算書）",
        "font_size": 12,
    })

    # Header
    if taxpayer_name:
        fields.append({
            "type": "text",
            "x": BLUE_RETURN_BS["taxpayer_name"]["x"],
            "y": BLUE_RETURN_BS["taxpayer_name"]["y"],
            "value": taxpayer_name,
            "font_size": BLUE_RETURN_BS["taxpayer_name"]["font_size"],
        })

    fields.append({
        "type": "text",
        "x": BLUE_RETURN_BS["fiscal_year_end"]["x"],
        "y": BLUE_RETURN_BS["fiscal_year_end"]["y"],
        "value": f"令和{bs_data.fiscal_year - 2018}年12月31日",
        "font_size": BLUE_RETURN_BS["fiscal_year_end"]["font_size"],
    })

    # Assets
    fields.append({"type": "text", "x": 30 * mm, "y": 250 * mm, "value": "【資産の部】", "font_size": 9})
    y_start = 240 * mm
    for i, item in enumerate(bs_data.assets):
        y = y_start - i * 8 * mm
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": item.account_name, "font_size": 8})
        fields.append({"type": "number", "x": 80 * mm, "y": y, "value": item.amount, "font_size": 8})

    y_total_assets = y_start - len(bs_data.assets) * 8 * mm - 5 * mm
    fields.append({"type": "text", "x": 30 * mm, "y": y_total_assets, "value": "資産合計", "font_size": 9})
    fields.append({"type": "number", "x": 80 * mm, "y": y_total_assets, "value": bs_data.total_assets, "font_size": 9})

    # Liabilities
    y_liab_start = y_total_assets - 15 * mm
    fields.append({"type": "text", "x": 110 * mm, "y": y_liab_start + 10 * mm, "value": "【負債の部】", "font_size": 9})
    for i, item in enumerate(bs_data.liabilities):
        y = y_liab_start - i * 8 * mm
        fields.append({"type": "text", "x": 110 * mm, "y": y, "value": item.account_name, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": item.amount, "font_size": 8})

    y_total_liab = y_liab_start - len(bs_data.liabilities) * 8 * mm - 5 * mm
    fields.append({"type": "text", "x": 110 * mm, "y": y_total_liab, "value": "負債合計", "font_size": 9})
    fields.append({"type": "number", "x": 170 * mm, "y": y_total_liab, "value": bs_data.total_liabilities, "font_size": 9})

    # Equity
    y_eq_start = y_total_liab - 15 * mm
    fields.append({"type": "text", "x": 110 * mm, "y": y_eq_start + 10 * mm, "value": "【純資産の部】", "font_size": 9})
    for i, item in enumerate(bs_data.equity):
        y = y_eq_start - i * 8 * mm
        fields.append({"type": "text", "x": 110 * mm, "y": y, "value": item.account_name, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": item.amount, "font_size": 8})

    y_total_eq = y_eq_start - len(bs_data.equity) * 8 * mm - 5 * mm
    fields.append({"type": "text", "x": 110 * mm, "y": y_total_eq, "value": "純資産合計", "font_size": 9})
    fields.append({"type": "number", "x": 170 * mm, "y": y_total_eq, "value": bs_data.total_equity, "font_size": 9})

    return fields


def generate_bs_pl_pdf(
    pl_data: PLResult,
    bs_data: BSResult | None = None,
    output_path: str = "output/bs_pl.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
) -> str:
    """Generate blue return BS/PL PDF.

    If template_path is provided and exists, overlay onto template.
    Otherwise generate standalone PDF.

    Args:
        pl_data: Profit/Loss data.
        bs_data: Balance Sheet data (optional).
        output_path: Output file path.
        taxpayer_name: Taxpayer name for the header.
        template_path: Path to NTA template PDF.

    Returns:
        The output file path.
    """
    pages: list[list[dict[str, Any]]] = []
    titles: list[str] = []

    # P/L page
    pl_fields = _build_pl_fields(pl_data, taxpayer_name)
    pages.append(pl_fields)
    titles.append("")

    # B/S page (if data provided)
    if bs_data is not None:
        bs_fields = _build_bs_fields(bs_data, taxpayer_name)
        pages.append(bs_fields)
        titles.append("")

    # Use template if available
    if template_path and Path(template_path).exists():
        from shinkoku.tools.pdf_utils import create_multi_page_overlay, merge_overlay
        overlay_bytes = create_multi_page_overlay(pages)
        return merge_overlay(template_path, overlay_bytes, output_path)

    # Standalone generation
    return generate_standalone_multi_page_pdf(
        pages=pages,
        output_path=output_path,
        titles=titles,
    )


# ============================================================
# Income Tax PDF (Task 19)
# ============================================================

def generate_income_tax_pdf(
    tax_result: IncomeTaxResult,
    output_path: str = "output/income_tax.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
) -> str:
    """Generate income tax form B PDF."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append({
        "type": "text", "x": 105 * mm, "y": 285 * mm,
        "value": "所得税及び復興特別所得税の確定申告書B",
        "font_size": 12,
    })

    # Header
    if taxpayer_name:
        fields.append({
            "type": "text",
            "x": INCOME_TAX_FORM_B["taxpayer_name"]["x"],
            "y": INCOME_TAX_FORM_B["taxpayer_name"]["y"],
            "value": taxpayer_name,
            "font_size": 10,
        })

    fields.append({
        "type": "text", "x": 120 * mm, "y": 275 * mm,
        "value": f"令和{tax_result.fiscal_year - 2018}年分",
        "font_size": 10,
    })

    # Income section
    y = 240 * mm
    income_items = [
        ("給与所得（収入後）", tax_result.salary_income_after_deduction),
        ("事業所得", tax_result.business_income),
        ("合計所得金額", tax_result.total_income),
    ]
    for label, value in income_items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "number", "x": 150 * mm, "y": y, "value": value, "font_size": 8})
        y -= 10 * mm

    # Deductions section
    y -= 5 * mm
    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "【所得控除】", "font_size": 9})
    y -= 10 * mm

    if tax_result.deductions_detail:
        for item in tax_result.deductions_detail.income_deductions:
            fields.append({"type": "text", "x": 30 * mm, "y": y, "value": item.name, "font_size": 8})
            fields.append({"type": "number", "x": 95 * mm, "y": y, "value": item.amount, "font_size": 8})
            y -= 8 * mm

    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "所得控除合計", "font_size": 9})
    fields.append({"type": "number", "x": 95 * mm, "y": y, "value": tax_result.total_income_deductions, "font_size": 9})
    y -= 12 * mm

    # Tax calculation section
    tax_items = [
        ("課税所得金額", tax_result.taxable_income),
        ("所得税額", tax_result.income_tax_base),
        ("税額控除", tax_result.total_tax_credits),
        ("税額控除後", tax_result.income_tax_after_credits),
        ("復興特別所得税", tax_result.reconstruction_tax),
        ("申告納税額", tax_result.total_tax),
        ("源泉徴収税額", tax_result.withheld_tax),
        ("差引納付/還付", tax_result.tax_due),
    ]
    for label, value in tax_items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "number", "x": 150 * mm, "y": y, "value": value, "font_size": 9})
        y -= 10 * mm

    if template_path and Path(template_path).exists():
        from shinkoku.tools.pdf_utils import create_overlay, merge_overlay
        overlay_bytes = create_overlay(fields)
        return merge_overlay(template_path, overlay_bytes, output_path)

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Consumption Tax PDF (Task 19)
# ============================================================

def generate_consumption_tax_pdf(
    tax_result: ConsumptionTaxResult,
    output_path: str = "output/consumption_tax.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
) -> str:
    """Generate consumption tax form PDF."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append({
        "type": "text", "x": 105 * mm, "y": 285 * mm,
        "value": "消費税及び地方消費税の確定申告書",
        "font_size": 12,
    })

    if taxpayer_name:
        fields.append({
            "type": "text", "x": 60 * mm, "y": 270 * mm,
            "value": taxpayer_name, "font_size": 10,
        })

    fields.append({
        "type": "text", "x": 120 * mm, "y": 275 * mm,
        "value": f"令和{tax_result.fiscal_year - 2018}年分",
        "font_size": 10,
    })

    # Method
    method_labels = {
        "standard": "本則課税",
        "simplified": "簡易課税",
        "special_20pct": "2割特例",
    }
    fields.append({
        "type": "text", "x": 30 * mm, "y": 255 * mm,
        "value": f"課税方式: {method_labels.get(tax_result.method, tax_result.method)}",
        "font_size": 9,
    })

    # Tax details
    y = 235 * mm
    items = [
        ("課税売上合計（税込）", tax_result.taxable_sales_total),
        ("売上に係る消費税額", tax_result.tax_on_sales),
        ("仕入に係る消費税額", tax_result.tax_on_purchases),
        ("消費税額（国税）", tax_result.tax_due),
        ("地方消費税額", tax_result.local_tax_due),
        ("納付税額合計", tax_result.total_due),
    ]
    for label, value in items:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": value, "font_size": 9})
        y -= 12 * mm

    if template_path and Path(template_path).exists():
        from shinkoku.tools.pdf_utils import create_overlay, merge_overlay
        overlay_bytes = create_overlay(fields)
        return merge_overlay(template_path, overlay_bytes, output_path)

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# Deduction Detail PDF (Task 19)
# ============================================================

def generate_deduction_detail_pdf(
    deductions: DeductionsResult,
    fiscal_year: int,
    output_path: str = "output/deduction_detail.pdf",
    taxpayer_name: str = "",
    template_path: str | None = None,
) -> str:
    """Generate deduction detail form PDF."""
    fields: list[dict[str, Any]] = []

    # Title
    fields.append({
        "type": "text", "x": 105 * mm, "y": 285 * mm,
        "value": "所得控除の内訳書",
        "font_size": 12,
    })

    if taxpayer_name:
        fields.append({
            "type": "text", "x": 60 * mm, "y": 270 * mm,
            "value": taxpayer_name, "font_size": 10,
        })

    fields.append({
        "type": "text", "x": 120 * mm, "y": 275 * mm,
        "value": f"令和{fiscal_year - 2018}年分",
        "font_size": 10,
    })

    # Income deductions
    y = 250 * mm
    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "【所得控除】", "font_size": 9})
    y -= 10 * mm

    for item in deductions.income_deductions:
        label = item.name
        if item.details:
            label += f"（{item.details}）"
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": item.amount, "font_size": 8})
        y -= 8 * mm

    y -= 5 * mm
    fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "所得控除合計", "font_size": 9})
    fields.append({"type": "number", "x": 170 * mm, "y": y, "value": deductions.total_income_deductions, "font_size": 9})
    y -= 15 * mm

    # Tax credits
    if deductions.tax_credits:
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "【税額控除】", "font_size": 9})
        y -= 10 * mm

        for item in deductions.tax_credits:
            label = item.name
            if item.details:
                label += f"（{item.details}）"
            fields.append({"type": "text", "x": 30 * mm, "y": y, "value": label, "font_size": 8})
            fields.append({"type": "number", "x": 170 * mm, "y": y, "value": item.amount, "font_size": 8})
            y -= 8 * mm

        y -= 5 * mm
        fields.append({"type": "text", "x": 30 * mm, "y": y, "value": "税額控除合計", "font_size": 9})
        fields.append({"type": "number", "x": 170 * mm, "y": y, "value": deductions.total_tax_credits, "font_size": 9})

    if template_path and Path(template_path).exists():
        from shinkoku.tools.pdf_utils import create_overlay, merge_overlay
        overlay_bytes = create_overlay(fields)
        return merge_overlay(template_path, overlay_bytes, output_path)

    return generate_standalone_pdf(fields=fields, output_path=output_path)


# ============================================================
# MCP Tool Registration
# ============================================================

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
    ) -> dict:
        """Generate blue return BS/PL PDF from financial data."""
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
            taxpayer_name=taxpayer_name,
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
        total_tax_credits: int = 0,
        income_tax_after_credits: int = 0,
        reconstruction_tax: int = 0,
        total_tax: int = 0,
        withheld_tax: int = 0,
        tax_due: int = 0,
        output_path: str = "output/income_tax.pdf",
        taxpayer_name: str = "",
    ) -> dict:
        """Generate income tax form B PDF."""
        tax_result = IncomeTaxResult(
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
        path = generate_income_tax_pdf(
            tax_result=tax_result,
            output_path=output_path,
            taxpayer_name=taxpayer_name,
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
    ) -> dict:
        """Generate consumption tax form PDF."""
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
            taxpayer_name=taxpayer_name,
        )
        return {"output_path": path}

    @mcp.tool()
    def doc_generate_deduction_detail(
        fiscal_year: int,
        income_deductions: list[dict] | None = None,
        tax_credits: list[dict] | None = None,
        output_path: str = "output/deduction_detail.pdf",
        taxpayer_name: str = "",
    ) -> dict:
        """Generate deduction detail form PDF."""
        from shinkoku.models import DeductionItem
        inc_items = [DeductionItem(**d) for d in (income_deductions or [])]
        tc_items = [DeductionItem(**d) for d in (tax_credits or [])]
        deductions = DeductionsResult(
            income_deductions=inc_items,
            tax_credits=tc_items,
            total_income_deductions=sum(i.amount for i in inc_items),
            total_tax_credits=sum(i.amount for i in tc_items),
        )
        path = generate_deduction_detail_pdf(
            deductions=deductions,
            fiscal_year=fiscal_year,
            output_path=output_path,
            taxpayer_name=taxpayer_name,
        )
        return {"output_path": path}
