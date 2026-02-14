"""PDF coordinate definitions for Japanese tax form fields.

All coordinates are in ReportLab points (1 point = 1/72 inch).
Origin is bottom-left of the page. A4 = 595.28 x 841.89 points.

Each form definition is a dict mapping field names to position dicts:
  {
      "field_name": {
          "x": float,    # x-coordinate (for text: left edge, for number: right edge)
          "y": float,    # y-coordinate (baseline)
          "font_size": float,
          "type": "text" | "number" | "checkbox",
      }
  }
"""

from reportlab.lib.units import mm


# ============================================================
# Income Tax Form B (Kakutei Shinkoku Sho B)
# ============================================================

INCOME_TAX_FORM_B: dict[str, dict] = {
    # --- Header ---
    "taxpayer_name": {"x": 60 * mm, "y": 268 * mm, "font_size": 10, "type": "text"},
    "taxpayer_address": {"x": 60 * mm, "y": 278 * mm, "font_size": 8, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 288 * mm, "font_size": 10, "type": "text"},
    # --- Income Section (Section A) ---
    "salary_income_revenue": {"x": 95 * mm, "y": 240 * mm, "font_size": 8, "type": "number"},
    "salary_income_amount": {"x": 150 * mm, "y": 240 * mm, "font_size": 8, "type": "number"},
    "business_income_revenue": {"x": 95 * mm, "y": 232 * mm, "font_size": 8, "type": "number"},
    "business_income_amount": {"x": 150 * mm, "y": 232 * mm, "font_size": 8, "type": "number"},
    "total_income": {"x": 150 * mm, "y": 200 * mm, "font_size": 9, "type": "number"},
    # --- Deductions Section (Section B) ---
    "social_insurance_deduction": {"x": 95 * mm, "y": 175 * mm, "font_size": 8, "type": "number"},
    "life_insurance_deduction": {"x": 95 * mm, "y": 167 * mm, "font_size": 8, "type": "number"},
    "earthquake_insurance_deduction": {
        "x": 95 * mm,
        "y": 159 * mm,
        "font_size": 8,
        "type": "number",
    },
    "spouse_deduction": {"x": 95 * mm, "y": 143 * mm, "font_size": 8, "type": "number"},
    "basic_deduction": {"x": 95 * mm, "y": 135 * mm, "font_size": 8, "type": "number"},
    "furusato_deduction": {"x": 95 * mm, "y": 151 * mm, "font_size": 8, "type": "number"},
    "total_deductions": {"x": 95 * mm, "y": 120 * mm, "font_size": 9, "type": "number"},
    # --- Tax Section (Section C) ---
    "taxable_income": {"x": 150 * mm, "y": 110 * mm, "font_size": 9, "type": "number"},
    "income_tax_base": {"x": 150 * mm, "y": 100 * mm, "font_size": 9, "type": "number"},
    "housing_loan_credit": {"x": 150 * mm, "y": 90 * mm, "font_size": 8, "type": "number"},
    "income_tax_after_credits": {"x": 150 * mm, "y": 80 * mm, "font_size": 9, "type": "number"},
    "reconstruction_tax": {"x": 150 * mm, "y": 70 * mm, "font_size": 8, "type": "number"},
    "total_tax": {"x": 150 * mm, "y": 60 * mm, "font_size": 9, "type": "number"},
    "withheld_tax": {"x": 150 * mm, "y": 50 * mm, "font_size": 8, "type": "number"},
    "tax_due": {"x": 150 * mm, "y": 40 * mm, "font_size": 10, "type": "number"},
    # --- Checkboxes ---
    "blue_return_checkbox": {"x": 45 * mm, "y": 288 * mm, "font_size": 0, "type": "checkbox"},
}


# ============================================================
# Blue Return P/L (Profit and Loss Statement)
# ============================================================

BLUE_RETURN_PL: dict[str, dict] = {
    # --- Header ---
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    # --- Revenue ---
    "sales_revenue": {"x": 170 * mm, "y": 240 * mm, "font_size": 9, "type": "number"},
    "other_revenue": {"x": 170 * mm, "y": 232 * mm, "font_size": 8, "type": "number"},
    "total_revenue": {"x": 170 * mm, "y": 220 * mm, "font_size": 9, "type": "number"},
    # --- Cost of Sales ---
    "beginning_inventory": {"x": 170 * mm, "y": 208 * mm, "font_size": 8, "type": "number"},
    "purchases": {"x": 170 * mm, "y": 200 * mm, "font_size": 8, "type": "number"},
    "ending_inventory": {"x": 170 * mm, "y": 192 * mm, "font_size": 8, "type": "number"},
    "cost_of_sales": {"x": 170 * mm, "y": 184 * mm, "font_size": 9, "type": "number"},
    "gross_profit": {"x": 170 * mm, "y": 175 * mm, "font_size": 9, "type": "number"},
    # --- Operating Expenses ---
    "depreciation": {"x": 80 * mm, "y": 155 * mm, "font_size": 8, "type": "number"},
    "rent": {"x": 80 * mm, "y": 147 * mm, "font_size": 8, "type": "number"},
    "communication": {"x": 80 * mm, "y": 139 * mm, "font_size": 8, "type": "number"},
    "travel": {"x": 80 * mm, "y": 131 * mm, "font_size": 8, "type": "number"},
    "supplies": {"x": 80 * mm, "y": 123 * mm, "font_size": 8, "type": "number"},
    "outsourcing": {"x": 80 * mm, "y": 115 * mm, "font_size": 8, "type": "number"},
    "utilities": {"x": 80 * mm, "y": 107 * mm, "font_size": 8, "type": "number"},
    "advertising": {"x": 80 * mm, "y": 99 * mm, "font_size": 8, "type": "number"},
    "miscellaneous": {"x": 80 * mm, "y": 91 * mm, "font_size": 8, "type": "number"},
    "total_expenses": {"x": 170 * mm, "y": 80 * mm, "font_size": 9, "type": "number"},
    # --- Income ---
    "operating_income": {"x": 170 * mm, "y": 68 * mm, "font_size": 9, "type": "number"},
    "blue_return_deduction": {"x": 170 * mm, "y": 56 * mm, "font_size": 9, "type": "number"},
    "net_income": {"x": 170 * mm, "y": 44 * mm, "font_size": 10, "type": "number"},
}


# ============================================================
# Blue Return B/S (Balance Sheet)
# ============================================================

BLUE_RETURN_BS: dict[str, dict] = {
    # --- Header ---
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year_end": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    # --- Assets ---
    "cash": {"x": 80 * mm, "y": 240 * mm, "font_size": 8, "type": "number"},
    "bank_deposit": {"x": 80 * mm, "y": 232 * mm, "font_size": 8, "type": "number"},
    "accounts_receivable": {"x": 80 * mm, "y": 224 * mm, "font_size": 8, "type": "number"},
    "prepaid": {"x": 80 * mm, "y": 216 * mm, "font_size": 8, "type": "number"},
    "buildings": {"x": 80 * mm, "y": 200 * mm, "font_size": 8, "type": "number"},
    "equipment": {"x": 80 * mm, "y": 192 * mm, "font_size": 8, "type": "number"},
    "owner_drawing": {"x": 80 * mm, "y": 180 * mm, "font_size": 8, "type": "number"},
    "total_assets": {"x": 80 * mm, "y": 165 * mm, "font_size": 9, "type": "number"},
    # --- Liabilities ---
    "accounts_payable": {"x": 170 * mm, "y": 240 * mm, "font_size": 8, "type": "number"},
    "unpaid": {"x": 170 * mm, "y": 232 * mm, "font_size": 8, "type": "number"},
    "borrowings": {"x": 170 * mm, "y": 224 * mm, "font_size": 8, "type": "number"},
    "total_liabilities": {"x": 170 * mm, "y": 200 * mm, "font_size": 9, "type": "number"},
    # --- Equity ---
    "capital": {"x": 170 * mm, "y": 185 * mm, "font_size": 8, "type": "number"},
    "owner_investment": {"x": 170 * mm, "y": 177 * mm, "font_size": 8, "type": "number"},
    "net_income_bs": {"x": 170 * mm, "y": 169 * mm, "font_size": 8, "type": "number"},
    "total_equity": {"x": 170 * mm, "y": 165 * mm, "font_size": 9, "type": "number"},
}


# ============================================================
# Consumption Tax Form
# ============================================================

CONSUMPTION_TAX_FORM: dict[str, dict] = {
    # --- Header ---
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    # --- Method checkbox ---
    "method_standard": {"x": 35 * mm, "y": 260 * mm, "font_size": 0, "type": "checkbox"},
    "method_simplified": {"x": 55 * mm, "y": 260 * mm, "font_size": 0, "type": "checkbox"},
    "method_special_20pct": {"x": 75 * mm, "y": 260 * mm, "font_size": 0, "type": "checkbox"},
    # --- Sales ---
    "taxable_sales_total": {"x": 170 * mm, "y": 240 * mm, "font_size": 9, "type": "number"},
    "tax_on_sales": {"x": 170 * mm, "y": 230 * mm, "font_size": 9, "type": "number"},
    # --- Purchases ---
    "tax_on_purchases": {"x": 170 * mm, "y": 215 * mm, "font_size": 9, "type": "number"},
    # --- Tax Due ---
    "national_tax_due": {"x": 170 * mm, "y": 190 * mm, "font_size": 9, "type": "number"},
    "local_tax_due": {"x": 170 * mm, "y": 180 * mm, "font_size": 9, "type": "number"},
    "total_tax_due": {"x": 170 * mm, "y": 165 * mm, "font_size": 10, "type": "number"},
}


# ============================================================
# Deduction Detail Form
# ============================================================

DEDUCTION_DETAIL_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    # Each deduction line (up to 10)
    # line_N_name, line_N_amount
}

# Generate dynamic deduction lines
for i in range(10):
    y_offset = 250 * mm - i * 12 * mm
    DEDUCTION_DETAIL_FORM[f"line_{i}_name"] = {
        "x": 30 * mm,
        "y": y_offset,
        "font_size": 8,
        "type": "text",
    }
    DEDUCTION_DETAIL_FORM[f"line_{i}_amount"] = {
        "x": 170 * mm,
        "y": y_offset,
        "font_size": 8,
        "type": "number",
    }
