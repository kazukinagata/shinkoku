"""PDF coordinate definitions for Japanese tax form fields.

座標はReportLabのポイント単位（1pt = 1/72 inch）。
原点は用紙左下。A4 Portrait = 595.28 x 841.89 pt、A4 Landscape = 841.89 x 595.28 pt。

ベンチマークPDF（freee出力）からpdfplumberで抽出した座標をベースに定義。
pdfplumber座標(y=0が上) → ReportLab座標(y=0が下) の変換:
    reportlab_y = page_height - pdfplumber_top

フィールド型:
  digit_cells: 桁別セル（第一表の金額欄、郵便番号等）
    {"x_start": float, "y": float, "cell_width": float, "num_cells": int,
     "font_size": float, "type": "digit_cells"}

  text: 通常テキスト（第二表、氏名、住所等）
    {"x": float, "y": float, "font_size": float, "type": "text"}

  number: 右寄せカンマ区切り数値
    {"x": float, "y": float, "font_size": float, "type": "number"}

  checkbox: チェックボックス
    {"x": float, "y": float, "size": float, "type": "checkbox"}
"""

from __future__ import annotations

from reportlab.lib.units import mm


# ============================================================
# Page size constants
# ============================================================

A4_PORTRAIT = (595.28, 841.89)
A4_LANDSCAPE = (841.89, 595.28)


# ============================================================
# 確定申告書B 第一表 (Income Tax Form B - Page 1)
# Portrait 595 x 842
# ベンチマークから抽出した座標（digit_cells方式）
# ============================================================

INCOME_TAX_P1: dict[str, dict] = {
    # --- ヘッダー ---
    # 郵便番号 (7桁): 上3桁 + 下4桁
    "postal_code_upper": {
        "x_start": 88.5,
        "y": 793.8,
        "cell_width": 14.4,
        "num_cells": 3,
        "font_size": 10,
        "type": "digit_cells",
    },
    "postal_code_lower": {
        "x_start": 140.0,
        "y": 793.8,
        "cell_width": 14.4,
        "num_cells": 4,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 住所
    "address": {
        "x": 78.5,
        "y": 766.6,
        "font_size": 8,
        "type": "text",
    },
    # 氏名（フリガナ）
    "name_kana": {
        "x": 352.8,
        "y": 772.2,
        "font_size": 8,
        "type": "text",
    },
    # 氏名（漢字）
    "name_kanji": {
        "x": 352.8,
        "y": 747.1,
        "font_size": 11.5,
        "type": "text",
    },
    # 生年月日
    "birth_date": {
        "x": 480.0,
        "y": 747.1,
        "font_size": 8,
        "type": "text",
    },
    # 電話番号
    "phone": {
        "x": 480.0,
        "y": 772.2,
        "font_size": 8,
        "type": "text",
    },
    # 令和XX年分
    "fiscal_year_label": {
        "x": 240.0,
        "y": 810.0,
        "font_size": 10,
        "type": "text",
    },
    # 青色申告チェック
    "blue_return_checkbox": {
        "x": 178.0,
        "y": 810.0,
        "size": 8,
        "type": "checkbox",
    },
    # --- 収入金額等（ア〜ス）---
    # 事業収入（営業等）ア
    "business_revenue": {
        "x_start": 133.2,
        "y": 684.5,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 給与収入 カ
    "salary_revenue": {
        "x_start": 133.2,
        "y": 652.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 雑収入（その他）ク
    "misc_revenue": {
        "x_start": 133.2,
        "y": 620.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # --- 所得金額等 ---
    # 事業所得（営業等）1
    "business_income": {
        "x_start": 345.0,
        "y": 684.5,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 給与所得 6
    "salary_income": {
        "x_start": 345.0,
        "y": 652.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 合計所得金額 12
    "total_income": {
        "x_start": 345.0,
        "y": 588.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # --- 所得控除 ---
    # 社会保険料控除 13
    "social_insurance_deduction": {
        "x_start": 133.2,
        "y": 530.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 小規模企業共済等掛金控除 14 (iDeCo)
    "ideco_deduction": {
        "x_start": 133.2,
        "y": 514.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 生命保険料控除 15
    "life_insurance_deduction": {
        "x_start": 133.2,
        "y": 498.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 地震保険料控除 16
    "earthquake_insurance_deduction": {
        "x_start": 133.2,
        "y": 482.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 寄附金控除 17 (ふるさと納税等)
    "furusato_deduction": {
        "x_start": 133.2,
        "y": 466.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 配偶者控除・配偶者特別控除 21-22
    "spouse_deduction": {
        "x_start": 345.0,
        "y": 530.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 扶養控除 23
    "dependent_deduction": {
        "x_start": 345.0,
        "y": 514.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 基礎控除 24
    "basic_deduction": {
        "x_start": 345.0,
        "y": 498.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 医療費控除 18
    "medical_deduction": {
        "x_start": 133.2,
        "y": 450.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 所得控除合計 25
    "total_deductions": {
        "x_start": 345.0,
        "y": 450.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # --- 税額の計算 ---
    # 課税される所得金額 26
    "taxable_income": {
        "x_start": 133.2,
        "y": 410.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 上の26に対する税額 27
    "income_tax_base": {
        "x_start": 133.2,
        "y": 394.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 住宅ローン控除 30
    "housing_loan_credit": {
        "x_start": 345.0,
        "y": 394.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 差引所得税額 31
    "income_tax_after_credits": {
        "x_start": 133.2,
        "y": 362.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 復興特別所得税額 32
    "reconstruction_tax": {
        "x_start": 133.2,
        "y": 346.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 所得税及び復興特別所得税の額 33
    "total_tax": {
        "x_start": 133.2,
        "y": 330.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 源泉徴収税額 44
    "withheld_tax": {
        "x_start": 133.2,
        "y": 282.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 予定納税額 43
    "estimated_tax_payment": {
        "x_start": 133.2,
        "y": 298.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 申告納税額（納める税金/還付される税金）45-47
    "tax_due": {
        "x_start": 133.2,
        "y": 250.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
}


# ============================================================
# 確定申告書B 第二表 (Income Tax Form B - Page 2)
# Portrait 595 x 842
# 第二表は通常テキスト（カンマ区切り金額）
# ============================================================

INCOME_TAX_P2: dict[str, dict] = {
    # --- ヘッダー ---
    "name_kanji": {
        "x": 70.0,
        "y": 790.0,
        "font_size": 10,
        "type": "text",
    },
    # --- 所得の内訳 (種類/支払者/収入金額/源泉徴収額) ---
    # 最大8行
}

# 所得内訳行（最大8行）
for _i in range(8):
    _y = 720.0 - _i * 18.0
    INCOME_TAX_P2[f"income_detail_{_i}_type"] = {
        "x": 30.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"income_detail_{_i}_payer"] = {
        "x": 130.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"income_detail_{_i}_revenue"] = {
        "x": 340.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }
    INCOME_TAX_P2[f"income_detail_{_i}_withheld"] = {
        "x": 470.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }

# 社会保険料の内訳（最大4行）
for _i in range(4):
    _y = 540.0 - _i * 18.0
    INCOME_TAX_P2[f"social_insurance_{_i}_type"] = {
        "x": 30.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"social_insurance_{_i}_payer"] = {
        "x": 180.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"social_insurance_{_i}_amount"] = {
        "x": 340.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }

# 扶養対象者（最大4名）
for _i in range(4):
    _y = 420.0 - _i * 18.0
    INCOME_TAX_P2[f"dependent_{_i}_name"] = {
        "x": 30.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"dependent_{_i}_relationship"] = {
        "x": 180.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"dependent_{_i}_birth_date"] = {
        "x": 260.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }

# 配偶者情報
INCOME_TAX_P2["spouse_name"] = {
    "x": 30.0,
    "y": 340.0,
    "font_size": 8,
    "type": "text",
}
INCOME_TAX_P2["spouse_income"] = {
    "x": 340.0,
    "y": 340.0,
    "font_size": 8,
    "type": "number",
}

# 住宅ローン居住開始日
INCOME_TAX_P2["housing_loan_move_in_date"] = {
    "x": 30.0,
    "y": 300.0,
    "font_size": 8,
    "type": "text",
}


# ============================================================
# 青色申告決算書 損益計算書 P1
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_PL_P1: dict[str, dict] = {
    # --- ヘッダー ---
    "taxpayer_name": {"x": 180.0, "y": 558.0, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 360.0, "y": 574.0, "font_size": 10, "type": "text"},
    # --- 売上（収入）金額 ---
    "sales_revenue": {"x": 520.0, "y": 510.0, "font_size": 9, "type": "number"},
    "other_revenue": {"x": 520.0, "y": 492.0, "font_size": 8, "type": "number"},
    "total_revenue": {"x": 520.0, "y": 470.0, "font_size": 9, "type": "number"},
    # --- 売上原価 ---
    "beginning_inventory": {"x": 520.0, "y": 448.0, "font_size": 8, "type": "number"},
    "purchases": {"x": 520.0, "y": 430.0, "font_size": 8, "type": "number"},
    "ending_inventory": {"x": 520.0, "y": 412.0, "font_size": 8, "type": "number"},
    "cost_of_sales": {"x": 520.0, "y": 394.0, "font_size": 9, "type": "number"},
    "gross_profit": {"x": 520.0, "y": 376.0, "font_size": 9, "type": "number"},
    # --- 経費 ---
    "rent": {"x": 280.0, "y": 340.0, "font_size": 8, "type": "number"},
    "communication": {"x": 280.0, "y": 322.0, "font_size": 8, "type": "number"},
    "travel": {"x": 280.0, "y": 304.0, "font_size": 8, "type": "number"},
    "depreciation": {"x": 280.0, "y": 286.0, "font_size": 8, "type": "number"},
    "supplies": {"x": 520.0, "y": 340.0, "font_size": 8, "type": "number"},
    "outsourcing": {"x": 520.0, "y": 322.0, "font_size": 8, "type": "number"},
    "utilities": {"x": 520.0, "y": 304.0, "font_size": 8, "type": "number"},
    "advertising": {"x": 520.0, "y": 286.0, "font_size": 8, "type": "number"},
    "miscellaneous": {"x": 520.0, "y": 268.0, "font_size": 8, "type": "number"},
    "total_expenses": {"x": 520.0, "y": 240.0, "font_size": 9, "type": "number"},
    # --- 所得金額 ---
    "operating_income": {"x": 520.0, "y": 210.0, "font_size": 9, "type": "number"},
    "blue_return_deduction": {"x": 520.0, "y": 190.0, "font_size": 9, "type": "number"},
    "net_income": {"x": 520.0, "y": 160.0, "font_size": 10, "type": "number"},
}


# ============================================================
# 青色申告決算書 損益計算書 P2 (月別売上・仕入)
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_PL_P2: dict[str, dict] = {
    "taxpayer_name": {"x": 180.0, "y": 558.0, "font_size": 10, "type": "text"},
}

# 月別売上（1月〜12月 + 合計）
for _i in range(12):
    _x = 120.0 + _i * 52.0
    BLUE_RETURN_PL_P2[f"monthly_sales_{_i + 1}"] = {
        "x": _x,
        "y": 480.0,
        "font_size": 7,
        "type": "number",
    }
    BLUE_RETURN_PL_P2[f"monthly_purchases_{_i + 1}"] = {
        "x": _x,
        "y": 380.0,
        "font_size": 7,
        "type": "number",
    }

BLUE_RETURN_PL_P2["annual_sales_total"] = {
    "x": 760.0,
    "y": 480.0,
    "font_size": 8,
    "type": "number",
}
BLUE_RETURN_PL_P2["annual_purchases_total"] = {
    "x": 760.0,
    "y": 380.0,
    "font_size": 8,
    "type": "number",
}


# ============================================================
# 青色申告決算書 損益計算書 P3 (減価償却・地代家賃)
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_PL_P3: dict[str, dict] = {
    "taxpayer_name": {"x": 180.0, "y": 558.0, "font_size": 10, "type": "text"},
}

# 減価償却資産（最大8行）
for _i in range(8):
    _y = 490.0 - _i * 20.0
    BLUE_RETURN_PL_P3[f"depr_{_i}_name"] = {
        "x": 50.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_acq_date"] = {
        "x": 180.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_acq_cost"] = {
        "x": 300.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_useful_life"] = {
        "x": 390.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_method"] = {
        "x": 440.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_ratio"] = {
        "x": 510.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_amount"] = {
        "x": 600.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }
    BLUE_RETURN_PL_P3[f"depr_{_i}_book_value"] = {
        "x": 720.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }

BLUE_RETURN_PL_P3["depr_total"] = {
    "x": 600.0,
    "y": 320.0,
    "font_size": 8,
    "type": "number",
}

# 地代家賃（最大4行）
for _i in range(4):
    _y = 270.0 - _i * 22.0
    BLUE_RETURN_PL_P3[f"rent_{_i}_usage"] = {
        "x": 50.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"rent_{_i}_landlord"] = {
        "x": 200.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    BLUE_RETURN_PL_P3[f"rent_{_i}_monthly"] = {
        "x": 450.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }
    BLUE_RETURN_PL_P3[f"rent_{_i}_annual"] = {
        "x": 600.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }
    BLUE_RETURN_PL_P3[f"rent_{_i}_business_pct"] = {
        "x": 720.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }


# ============================================================
# 青色申告決算書 貸借対照表
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_BS: dict[str, dict] = {
    # --- ヘッダー ---
    "taxpayer_name": {"x": 180.0, "y": 558.0, "font_size": 10, "type": "text"},
    "fiscal_year_end": {"x": 360.0, "y": 574.0, "font_size": 10, "type": "text"},
    # --- 資産の部 ---
    "cash": {"x": 200.0, "y": 500.0, "font_size": 8, "type": "number"},
    "bank_deposit": {"x": 200.0, "y": 482.0, "font_size": 8, "type": "number"},
    "accounts_receivable": {"x": 200.0, "y": 464.0, "font_size": 8, "type": "number"},
    "prepaid": {"x": 200.0, "y": 446.0, "font_size": 8, "type": "number"},
    "buildings": {"x": 200.0, "y": 410.0, "font_size": 8, "type": "number"},
    "equipment": {"x": 200.0, "y": 392.0, "font_size": 8, "type": "number"},
    "owner_drawing": {"x": 200.0, "y": 360.0, "font_size": 8, "type": "number"},
    "total_assets": {"x": 200.0, "y": 320.0, "font_size": 9, "type": "number"},
    # --- 負債の部 ---
    "accounts_payable": {"x": 580.0, "y": 500.0, "font_size": 8, "type": "number"},
    "unpaid": {"x": 580.0, "y": 482.0, "font_size": 8, "type": "number"},
    "borrowings": {"x": 580.0, "y": 464.0, "font_size": 8, "type": "number"},
    "total_liabilities": {"x": 580.0, "y": 410.0, "font_size": 9, "type": "number"},
    # --- 純資産の部 ---
    "capital": {"x": 580.0, "y": 380.0, "font_size": 8, "type": "number"},
    "owner_investment": {"x": 580.0, "y": 362.0, "font_size": 8, "type": "number"},
    "net_income_bs": {"x": 580.0, "y": 344.0, "font_size": 8, "type": "number"},
    "total_equity": {"x": 580.0, "y": 320.0, "font_size": 9, "type": "number"},
}


# ============================================================
# 消費税確定申告書 第一表
# Portrait 595 x 842
# ============================================================

CONSUMPTION_TAX_P1: dict[str, dict] = {
    # --- ヘッダー ---
    "taxpayer_name": {"x": 70.0, "y": 770.0, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 240.0, "y": 810.0, "font_size": 10, "type": "text"},
    # --- 課税方式チェックボックス ---
    "method_standard": {"x": 120.0, "y": 750.0, "size": 8, "type": "checkbox"},
    "method_simplified": {"x": 220.0, "y": 750.0, "size": 8, "type": "checkbox"},
    "method_special_20pct": {"x": 320.0, "y": 750.0, "size": 8, "type": "checkbox"},
    # --- 課税標準額・税額 ---
    # 課税売上額（税抜）1
    "taxable_sales_amount": {
        "x_start": 345.0,
        "y": 700.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 消費税額 2
    "tax_on_sales": {
        "x_start": 345.0,
        "y": 678.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 控除対象仕入税額 4
    "tax_on_purchases": {
        "x_start": 345.0,
        "y": 634.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 差引税額 9
    "tax_due_national": {
        "x_start": 345.0,
        "y": 568.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 地方消費税額 21
    "local_tax_due": {
        "x_start": 345.0,
        "y": 440.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 納付税額合計 26
    "total_tax_due": {
        "x_start": 345.0,
        "y": 360.0,
        "cell_width": 14.4,
        "num_cells": 11,
        "font_size": 10,
        "type": "digit_cells",
    },
}


# ============================================================
# 消費税 付表 (Consumption Tax - Appendix)
# Portrait 595 x 842
# ============================================================

CONSUMPTION_TAX_P2: dict[str, dict] = {
    # --- ヘッダー ---
    "taxpayer_name": {"x": 70.0, "y": 770.0, "font_size": 10, "type": "text"},
    # 課税売上合計（税込）
    "taxable_sales_total": {
        "x": 470.0,
        "y": 700.0,
        "font_size": 8,
        "type": "number",
    },
    # 標準税率(10%)対象
    "taxable_sales_10": {
        "x": 470.0,
        "y": 670.0,
        "font_size": 8,
        "type": "number",
    },
    # 軽減税率(8%)対象
    "taxable_sales_8": {
        "x": 470.0,
        "y": 640.0,
        "font_size": 8,
        "type": "number",
    },
}


# ============================================================
# 住宅ローン控除 P1 (Housing Loan Credit Detail - Page 1)
# Portrait 595 x 842
# ============================================================

HOUSING_LOAN_P1: dict[str, dict] = {
    "taxpayer_name": {"x": 70.0, "y": 770.0, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 240.0, "y": 810.0, "font_size": 10, "type": "text"},
    # 住宅情報
    "housing_type": {"x": 200.0, "y": 700.0, "font_size": 8, "type": "text"},
    "housing_category": {"x": 200.0, "y": 680.0, "font_size": 8, "type": "text"},
    "move_in_date": {"x": 200.0, "y": 660.0, "font_size": 8, "type": "text"},
    "is_new_construction": {"x": 200.0, "y": 640.0, "font_size": 8, "type": "text"},
    # 控除計算
    "year_end_balance": {"x": 470.0, "y": 580.0, "font_size": 8, "type": "number"},
    "balance_limit": {"x": 470.0, "y": 560.0, "font_size": 8, "type": "number"},
    "capped_balance": {"x": 470.0, "y": 540.0, "font_size": 8, "type": "number"},
    "credit_rate": {"x": 470.0, "y": 520.0, "font_size": 8, "type": "text"},
    "credit_period": {"x": 470.0, "y": 500.0, "font_size": 8, "type": "text"},
    "credit_amount": {"x": 470.0, "y": 460.0, "font_size": 10, "type": "number"},
}


# ============================================================
# 住宅ローン控除 P2 (Housing Loan Credit Detail - Page 2)
# Portrait 595 x 842
# ============================================================

HOUSING_LOAN_P2: dict[str, dict] = {
    "taxpayer_name": {"x": 70.0, "y": 770.0, "font_size": 10, "type": "text"},
    # 取得情報
    "purchase_date": {"x": 200.0, "y": 700.0, "font_size": 8, "type": "text"},
    "purchase_price": {"x": 470.0, "y": 700.0, "font_size": 8, "type": "number"},
    "total_floor_area": {"x": 200.0, "y": 680.0, "font_size": 8, "type": "text"},
    "residential_floor_area": {"x": 470.0, "y": 680.0, "font_size": 8, "type": "text"},
}


# ============================================================
# Legacy aliases for backward compatibility
# 既存の document.py からの参照を維持する
# ============================================================

# 旧名 → 新名のエイリアス
INCOME_TAX_FORM_B = INCOME_TAX_P1
BLUE_RETURN_PL = BLUE_RETURN_PL_P1
BLUE_RETURN_BS_LEGACY = BLUE_RETURN_BS

# 以下は旧pdf_coordinates.pyと同じインターフェースで残す
# document.py のフィールドビルダーが参照する
CONSUMPTION_TAX_FORM = CONSUMPTION_TAX_P1


# ============================================================
# Deduction Detail Form (所得控除の内訳書)
# ============================================================

DEDUCTION_DETAIL_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
}

for _i in range(10):
    _y_offset = 250 * mm - _i * 12 * mm
    DEDUCTION_DETAIL_FORM[f"line_{_i}_name"] = {
        "x": 30 * mm,
        "y": _y_offset,
        "font_size": 8,
        "type": "text",
    }
    DEDUCTION_DETAIL_FORM[f"line_{_i}_amount"] = {
        "x": 170 * mm,
        "y": _y_offset,
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

for _i in range(15):
    _y_offset = 250 * mm - _i * 12 * mm
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_institution"] = {
        "x": 30 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_patient"] = {
        "x": 80 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_amount"] = {
        "x": 130 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "number",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_reimbursement"] = {
        "x": 170 * mm,
        "y": _y_offset,
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

for _i in range(5):
    _y_offset = 240 * mm - _i * 30 * mm
    RENT_DETAIL_FORM[f"line_{_i}_usage"] = {
        "x": 30 * mm,
        "y": _y_offset,
        "font_size": 8,
        "type": "text",
    }
    RENT_DETAIL_FORM[f"line_{_i}_landlord_name"] = {
        "x": 30 * mm,
        "y": _y_offset - 8 * mm,
        "font_size": 8,
        "type": "text",
    }
    RENT_DETAIL_FORM[f"line_{_i}_landlord_address"] = {
        "x": 30 * mm,
        "y": _y_offset - 16 * mm,
        "font_size": 7,
        "type": "text",
    }
    RENT_DETAIL_FORM[f"line_{_i}_monthly_rent"] = {
        "x": 130 * mm,
        "y": _y_offset,
        "font_size": 8,
        "type": "number",
    }
    RENT_DETAIL_FORM[f"line_{_i}_annual_rent"] = {
        "x": 170 * mm,
        "y": _y_offset,
        "font_size": 8,
        "type": "number",
    }
    RENT_DETAIL_FORM[f"line_{_i}_business_ratio"] = {
        "x": 170 * mm,
        "y": _y_offset - 8 * mm,
        "font_size": 8,
        "type": "text",
    }


# ============================================================
# Housing Loan Detail Form (住宅借入金等特別控除の計算明細書)
# ============================================================

HOUSING_LOAN_DETAIL_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 275 * mm, "font_size": 10, "type": "text"},
    "housing_type": {"x": 100 * mm, "y": 250 * mm, "font_size": 8, "type": "text"},
    "housing_category": {"x": 100 * mm, "y": 240 * mm, "font_size": 8, "type": "text"},
    "move_in_date": {"x": 100 * mm, "y": 230 * mm, "font_size": 8, "type": "text"},
    "is_new_construction": {"x": 100 * mm, "y": 220 * mm, "font_size": 8, "type": "text"},
    "year_end_balance": {"x": 170 * mm, "y": 198 * mm, "font_size": 8, "type": "number"},
    "balance_limit": {"x": 170 * mm, "y": 188 * mm, "font_size": 8, "type": "number"},
    "capped_balance": {"x": 170 * mm, "y": 178 * mm, "font_size": 8, "type": "number"},
    "credit_rate": {"x": 170 * mm, "y": 168 * mm, "font_size": 8, "type": "text"},
    "credit_period": {"x": 170 * mm, "y": 158 * mm, "font_size": 8, "type": "text"},
    "credit_amount": {"x": 170 * mm, "y": 143 * mm, "font_size": 10, "type": "number"},
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
    "total_separate_tax": {"x": 170 * mm, "y": 56 * mm, "font_size": 10, "type": "number"},
}


# ============================================================
# Schedule 4 (第四表: 損失申告用)
# ============================================================

SCHEDULE_4_FORM: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
}

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
# Income/Expense Statement (収支内訳書 — 白色申告用)
# ============================================================

INCOME_EXPENSE_STATEMENT: dict[str, dict] = {
    "taxpayer_name": {"x": 60 * mm, "y": 270 * mm, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 120 * mm, "y": 280 * mm, "font_size": 10, "type": "text"},
    "total_revenue": {"x": 170 * mm, "y": 240 * mm, "font_size": 9, "type": "number"},
    "total_expenses": {"x": 170 * mm, "y": 100 * mm, "font_size": 9, "type": "number"},
    "net_income": {"x": 170 * mm, "y": 70 * mm, "font_size": 10, "type": "number"},
}

for _i in range(5):
    _y_offset = 235 * mm - _i * 8 * mm
    INCOME_EXPENSE_STATEMENT[f"revenue_{_i}_name"] = {
        "x": 30 * mm,
        "y": _y_offset,
        "font_size": 8,
        "type": "text",
    }
    INCOME_EXPENSE_STATEMENT[f"revenue_{_i}_amount"] = {
        "x": 170 * mm,
        "y": _y_offset,
        "font_size": 8,
        "type": "number",
    }

for _i in range(15):
    _y_offset = 190 * mm - _i * 6 * mm
    INCOME_EXPENSE_STATEMENT[f"expense_{_i}_name"] = {
        "x": 30 * mm,
        "y": _y_offset,
        "font_size": 7,
        "type": "text",
    }
    INCOME_EXPENSE_STATEMENT[f"expense_{_i}_amount"] = {
        "x": 170 * mm,
        "y": _y_offset,
        "font_size": 7,
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


# ============================================================
# Template file names (テンプレートPDFのファイル名)
# ============================================================

TEMPLATE_NAMES: dict[str, str] = {
    "income_tax_p1": "income_tax_p1.pdf",
    "income_tax_p2": "income_tax_p2.pdf",
    "blue_return_pl_p1": "blue_return_pl_p1.pdf",
    "blue_return_pl_p2": "blue_return_pl_p2.pdf",
    "blue_return_pl_p3": "blue_return_pl_p3.pdf",
    "blue_return_bs": "blue_return_bs.pdf",
    "consumption_tax_p1": "consumption_tax_p1.pdf",
    "consumption_tax_p2": "consumption_tax_p2.pdf",
    "housing_loan_p1": "housing_loan_p1.pdf",
    "housing_loan_p2": "housing_loan_p2.pdf",
}
