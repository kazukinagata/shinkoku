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


# ============================================================
# Additional Income Tax Form B Fields (Phase 1-3)
# ============================================================

# iDeCo / 小規模企業共済等掛金控除
INCOME_TAX_FORM_B["ideco_deduction"] = {
    "x": 95 * mm,
    "y": 127 * mm,
    "font_size": 8,
    "type": "number",
}
# 扶養控除
INCOME_TAX_FORM_B["dependent_deduction"] = {
    "x": 95 * mm,
    "y": 119 * mm,
    "font_size": 8,
    "type": "number",
}
# 医療費控除
INCOME_TAX_FORM_B["medical_deduction"] = {
    "x": 95 * mm,
    "y": 111 * mm,
    "font_size": 8,
    "type": "number",
}
# 事業所得の源泉徴収税額
INCOME_TAX_FORM_B["business_withheld_tax"] = {
    "x": 150 * mm,
    "y": 45 * mm,
    "font_size": 8,
    "type": "number",
}
# 予定納税額
INCOME_TAX_FORM_B["estimated_tax_payment"] = {
    "x": 150 * mm,
    "y": 55 * mm,
    "font_size": 8,
    "type": "number",
}
# 繰越損失適用額
INCOME_TAX_FORM_B["loss_carryforward_applied"] = {
    "x": 150 * mm,
    "y": 195 * mm,
    "font_size": 8,
    "type": "number",
}


# ============================================================
# Medical Expense Detail Form (医療費控除の明細書)
# ============================================================

MEDICAL_EXPENSE_DETAIL_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    "total_amount": {"x": 170 * mm, "y": 50 * mm, "font_size": 9, "type": "number"},
    "total_reimbursement": {"x": 170 * mm, "y": 42 * mm, "font_size": 9, "type": "number"},
    "net_amount": {"x": 170 * mm, "y": 34 * mm, "font_size": 9, "type": "number"},
    "deduction_amount": {"x": 170 * mm, "y": 26 * mm, "font_size": 10, "type": "number"},
}

# Dynamic medical expense lines (up to 15)
for i in range(15):
    y_offset = 250 * mm - i * 12 * mm
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{i}_institution"] = {
        "x": 30 * mm,
        "y": y_offset,
        "font_size": 7,
        "type": "text",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{i}_patient"] = {
        "x": 80 * mm,
        "y": y_offset,
        "font_size": 7,
        "type": "text",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{i}_amount"] = {
        "x": 130 * mm,
        "y": y_offset,
        "font_size": 7,
        "type": "number",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{i}_reimbursement"] = {
        "x": 170 * mm,
        "y": y_offset,
        "font_size": 7,
        "type": "number",
    }


# ============================================================
# Rent Detail Form (地代家賃の内訳書)
# ============================================================

RENT_DETAIL_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    "total_annual_rent": {"x": 170 * mm, "y": 50 * mm, "font_size": 9, "type": "number"},
}

# Dynamic rent detail lines (up to 5)
for i in range(5):
    y_offset = 240 * mm - i * 30 * mm
    RENT_DETAIL_FORM[f"line_{i}_usage"] = {
        "x": 30 * mm,
        "y": y_offset,
        "font_size": 8,
        "type": "text",
    }
    RENT_DETAIL_FORM[f"line_{i}_landlord_name"] = {
        "x": 30 * mm,
        "y": y_offset - 8 * mm,
        "font_size": 8,
        "type": "text",
    }
    RENT_DETAIL_FORM[f"line_{i}_landlord_address"] = {
        "x": 30 * mm,
        "y": y_offset - 16 * mm,
        "font_size": 7,
        "type": "text",
    }
    RENT_DETAIL_FORM[f"line_{i}_monthly_rent"] = {
        "x": 130 * mm,
        "y": y_offset,
        "font_size": 8,
        "type": "number",
    }
    RENT_DETAIL_FORM[f"line_{i}_annual_rent"] = {
        "x": 170 * mm,
        "y": y_offset,
        "font_size": 8,
        "type": "number",
    }
    RENT_DETAIL_FORM[f"line_{i}_business_ratio"] = {
        "x": 170 * mm,
        "y": y_offset - 8 * mm,
        "font_size": 8,
        "type": "text",
    }


# ============================================================
# Housing Loan Detail Form (住宅借入金等特別控除の計算明細書)
# ============================================================

HOUSING_LOAN_DETAIL_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 275 * mm, "font_size": 10, "type": "text"},
    # 住宅情報
    "housing_type": {"x": 100 * mm, "y": 250 * mm, "font_size": 8, "type": "text"},
    "housing_category": {"x": 100 * mm, "y": 240 * mm, "font_size": 8, "type": "text"},
    "move_in_date": {"x": 100 * mm, "y": 230 * mm, "font_size": 8, "type": "text"},
    "is_new_construction": {"x": 100 * mm, "y": 220 * mm, "font_size": 8, "type": "text"},
    # 控除額の計算
    "year_end_balance": {"x": 170 * mm, "y": 198 * mm, "font_size": 8, "type": "number"},
    "balance_limit": {"x": 170 * mm, "y": 188 * mm, "font_size": 8, "type": "number"},
    "capped_balance": {"x": 170 * mm, "y": 178 * mm, "font_size": 8, "type": "number"},
    "credit_rate": {"x": 170 * mm, "y": 168 * mm, "font_size": 8, "type": "text"},
    "credit_period": {"x": 170 * mm, "y": 158 * mm, "font_size": 8, "type": "text"},
    "credit_amount": {"x": 170 * mm, "y": 143 * mm, "font_size": 10, "type": "number"},
    # Gap 6: 住宅ローン控除明細書の追加フィールド
    "purchase_date": {"x": 100 * mm, "y": 210 * mm, "font_size": 8, "type": "text"},
    "purchase_price": {"x": 170 * mm, "y": 210 * mm, "font_size": 8, "type": "number"},
    "total_floor_area": {"x": 100 * mm, "y": 202 * mm, "font_size": 8, "type": "text"},
    "residential_floor_area": {"x": 170 * mm, "y": 202 * mm, "font_size": 8, "type": "text"},
    "property_number": {"x": 100 * mm, "y": 194 * mm, "font_size": 8, "type": "text"},
    "application_submitted": {"x": 170 * mm, "y": 194 * mm, "font_size": 8, "type": "text"},
}


# ============================================================
# Schedule 3 (第三表: 分離課税用)
# ============================================================

SCHEDULE_3_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    # 株式等の譲渡所得
    "stock_gains": {"x": 170 * mm, "y": 240 * mm, "font_size": 8, "type": "number"},
    "stock_losses": {"x": 170 * mm, "y": 232 * mm, "font_size": 8, "type": "number"},
    "stock_net_gain": {"x": 170 * mm, "y": 224 * mm, "font_size": 9, "type": "number"},
    "stock_dividend_separate": {"x": 170 * mm, "y": 216 * mm, "font_size": 8, "type": "number"},
    "stock_dividend_offset": {"x": 170 * mm, "y": 208 * mm, "font_size": 8, "type": "number"},
    "stock_loss_carryforward_used": {
        "x": 170 * mm,
        "y": 200 * mm,
        "font_size": 8,
        "type": "number",
    },
    "stock_taxable_income": {"x": 170 * mm, "y": 192 * mm, "font_size": 9, "type": "number"},
    "stock_income_tax": {"x": 170 * mm, "y": 184 * mm, "font_size": 9, "type": "number"},
    "stock_residential_tax": {"x": 170 * mm, "y": 176 * mm, "font_size": 8, "type": "number"},
    "stock_reconstruction_tax": {"x": 170 * mm, "y": 168 * mm, "font_size": 8, "type": "number"},
    "stock_total_tax": {"x": 170 * mm, "y": 160 * mm, "font_size": 9, "type": "number"},
    "stock_withheld_total": {"x": 170 * mm, "y": 152 * mm, "font_size": 8, "type": "number"},
    "stock_tax_due": {"x": 170 * mm, "y": 144 * mm, "font_size": 9, "type": "number"},
    # FX（先物取引に係る雑所得等）
    "fx_net_income": {"x": 170 * mm, "y": 128 * mm, "font_size": 9, "type": "number"},
    "fx_loss_carryforward_used": {
        "x": 170 * mm,
        "y": 120 * mm,
        "font_size": 8,
        "type": "number",
    },
    "fx_taxable_income": {"x": 170 * mm, "y": 112 * mm, "font_size": 9, "type": "number"},
    "fx_income_tax": {"x": 170 * mm, "y": 104 * mm, "font_size": 9, "type": "number"},
    "fx_residential_tax": {"x": 170 * mm, "y": 96 * mm, "font_size": 8, "type": "number"},
    "fx_reconstruction_tax": {"x": 170 * mm, "y": 88 * mm, "font_size": 8, "type": "number"},
    "fx_total_tax": {"x": 170 * mm, "y": 80 * mm, "font_size": 9, "type": "number"},
    "fx_tax_due": {"x": 170 * mm, "y": 72 * mm, "font_size": 9, "type": "number"},
    # 合計
    "total_separate_tax": {"x": 170 * mm, "y": 56 * mm, "font_size": 10, "type": "number"},
}


# ============================================================
# Schedule 4 (第四表: 損失申告用)
# ============================================================

SCHEDULE_4_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
}

# 損失繰越行（3年×3種別 = 最大9行）
_SCHEDULE_4_Y_START = 240
_SCHEDULE_4_LOSS_TYPES = ["business", "stock", "fx"]
for _i, _loss_type in enumerate(_SCHEDULE_4_LOSS_TYPES):
    _y_base = _SCHEDULE_4_Y_START - _i * 60
    for _year_idx in range(3):
        _y = (_y_base - _year_idx * 16) * mm
        SCHEDULE_4_FORM[f"{_loss_type}_loss_year_{_year_idx}"] = {
            "x": 40 * mm,
            "y": _y,
            "font_size": 8,
            "type": "text",
        }
        SCHEDULE_4_FORM[f"{_loss_type}_loss_amount_{_year_idx}"] = {
            "x": 95 * mm,
            "y": _y,
            "font_size": 8,
            "type": "number",
        }
        SCHEDULE_4_FORM[f"{_loss_type}_used_amount_{_year_idx}"] = {
            "x": 140 * mm,
            "y": _y,
            "font_size": 8,
            "type": "number",
        }
        SCHEDULE_4_FORM[f"{_loss_type}_remaining_{_year_idx}"] = {
            "x": 170 * mm,
            "y": _y,
            "font_size": 8,
            "type": "number",
        }


# ============================================================
# Depreciation Schedule (減価償却明細書)
# ============================================================

DEPRECIATION_SCHEDULE_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    "total_depreciation": {"x": 170 * mm, "y": 50 * mm, "font_size": 9, "type": "number"},
}

# 資産行（最大10行）
for _i in range(10):
    _y_offset = 250 * mm - _i * 18 * mm
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_name"] = {
        "x": 30 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_acquisition_date"] = {
        "x": 65 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_acquisition_cost"] = {
        "x": 95 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "number",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_useful_life"] = {
        "x": 115 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_method"] = {
        "x": 125 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_ratio"] = {
        "x": 140 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_depreciation"] = {
        "x": 155 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "number",
    }
    DEPRECIATION_SCHEDULE_FORM[f"asset_{_i}_book_value"] = {
        "x": 175 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "number",
    }
