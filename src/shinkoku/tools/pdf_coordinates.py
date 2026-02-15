"""PDF coordinate definitions for Japanese tax form fields.

座標はReportLabのポイント単位（1pt = 1/72 inch）。
原点は用紙左下。A4 Portrait = 595.28 x 841.89 pt、A4 Landscape = 841.89 x 595.28 pt。

国税庁公式PDFテンプレートに合わせた座標定義。
年度ごとにセクション化し、様式変更時は新セクションとして追記する（上書き厳禁）。
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

# NTA公式PDFの実ページサイズ（r07/01.pdf等）
# 標準A4 (595.28x841.89) ではないため、オーバーレイ作成時にはこのサイズを使用する
NTA_PORTRAIT = (579.672, 814.791)


# ============================================================
# 確定申告書B 第一表 (Income Tax Form B - Page 1)
# Portrait 595 x 842
# ベンチマークから抽出した座標（digit_cells方式）
# ============================================================

INCOME_TAX_P1: dict[str, dict] = {
    # --- ヘッダー ---
    # NTA r07/01.pdf P1: page size 579.672 x 814.791 (NOT standard A4)
    # 座標は pdfplumber で実測し ReportLab 座標 (y=0 bottom) に変換済み
    # digit_cells: 実測 cell_width=12.6, cell_height=14.0, center-to-center=13.97
    # baseline = page_height - (pdfplumber_top + 14.0) + 3
    # LEFT column: x_start=192.27, 7 cells
    # RIGHT column: x_start=443.87, 7 cells
    #
    # 郵便番号 (7桁): 上3桁 + 下4桁
    # 実測: cell x0=[92.1, 106.0, 120.0] + [140.9, 154.9, 168.9, 182.8], cw=13.97
    "postal_code_upper": {
        "x_start": 91.40,
        "y": 749.6,
        "cell_width": 13.97,
        "num_cells": 3,
        "font_size": 10,
        "type": "digit_cells",
    },
    "postal_code_lower": {
        "x_start": 140.28,
        "y": 749.6,
        "cell_width": 13.97,
        "num_cells": 4,
        "font_size": 10,
        "type": "digit_cells",
    },
    # 住所 (h_line top=70.11-117.54, 内容開始 x=83.9, rl_y=728)
    "address": {
        "x": 84.0,
        "y": 728.0,
        "font_size": 7,
        "type": "text",
    },
    # 氏名（フリガナ）(top=75-88 area, x start after 342.3)
    "name_kana": {
        "x": 344.0,
        "y": 735.0,
        "font_size": 7,
        "type": "text",
    },
    # 氏名（漢字）(top=88-117 area)
    "name_kanji": {
        "x": 344.0,
        "y": 710.0,
        "font_size": 10,
        "type": "text",
    },
    # 生年月日 (入力セル top=72.1, x0=401.9-443.8; ラベル at x~403, top~54)
    "birth_date": {
        "x": 403.0,
        "y": 731.8,
        "font_size": 8,
        "type": "text",
    },
    # 電話番号 (label at x~440, top~138)
    "phone": {
        "x": 456.0,
        "y": 670.0,
        "font_size": 7,
        "type": "text",
    },
    # 令和XX年分 (label "令和" at x=139, top=33; "年分" at x=215-230, top=33)
    # 年号の数字は x=170-200, rl_y=775 付近
    "fiscal_year_label": {
        "x": 170.0,
        "y": 775.0,
        "font_size": 12,
        "type": "text",
    },
    # 青色申告チェック (種類欄 top=141.7, "青" at x=152.9, "色" at x=163.2)
    "blue_return_checkbox": {
        "x": 151.0,
        "y": 665.0,
        "size": 10,
        "type": "checkbox",
    },
    # --- 収入金額等（ア〜ク）LEFT column: x_start=192.27, cw=13.97, 7 cells ---
    # 事業収入（営業等）ア (top=158.0)
    "business_revenue": {
        "x_start": 192.27,
        "y": 645.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 給与収入 オ (top=224.0)
    "salary_revenue": {
        "x_start": 192.27,
        "y": 579.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 雑収入（その他）ク (top=273.5)
    "misc_revenue": {
        "x_start": 192.27,
        "y": 530.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 所得金額等 LEFT column ---
    # 事業所得（営業等）① (top=339.5)
    "business_income": {
        "x_start": 192.27,
        "y": 464.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 給与所得 ⑥ (top=422.0)
    "salary_income": {
        "x_start": 192.27,
        "y": 381.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 合計所得金額 ⑫ (top=520.9)
    "total_income": {
        "x_start": 192.27,
        "y": 282.9,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 所得控除 LEFT column ---
    # 社会保険料控除 ⑬ (top=537.4)
    "social_insurance_deduction": {
        "x_start": 192.27,
        "y": 266.4,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 小規模企業共済等掛金控除 ⑭ iDeCo (top=553.9)
    "ideco_deduction": {
        "x_start": 192.27,
        "y": 249.9,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 生命保険料控除 ⑮ (top=570.4)
    "life_insurance_deduction": {
        "x_start": 192.27,
        "y": 233.4,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 地震保険料控除 ⑯ (top=586.9)
    "earthquake_insurance_deduction": {
        "x_start": 192.27,
        "y": 216.9,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 寄附金控除 ㉙ (top=751.9) ふるさと納税等
    "furusato_deduction": {
        "x_start": 192.27,
        "y": 51.9,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 配偶者控除・配偶者特別控除 ㉑-㉒ (top=636.4) LEFT column
    "spouse_deduction": {
        "x_start": 192.27,
        "y": 167.4,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 扶養控除 ㉓ (top=652.9) LEFT column
    "dependent_deduction": {
        "x_start": 192.27,
        "y": 150.9,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 基礎控除 ㉕ (top=685.9) LEFT column
    "basic_deduction": {
        "x_start": 192.27,
        "y": 117.9,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 医療費控除 ㉘ (top=735.4) LEFT column
    "medical_deduction": {
        "x_start": 192.27,
        "y": 68.4,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 所得控除合計 ㉚ (top=768.4) LEFT column
    "total_deductions": {
        "x_start": 192.27,
        "y": 35.4,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 税金の計算 RIGHT column: x_start=443.87, cw=13.97, 7 cells ---
    # 課税される所得金額 ㉛ (top=158.0, same row as ア revenue)
    "taxable_income": {
        "x_start": 443.87,
        "y": 645.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 上の㉛に対する税額 ㉜ (top=174.5)
    "income_tax_base": {
        "x_start": 443.87,
        "y": 629.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 配当控除 ㉝ (top=191.0)
    "dividend_credit": {
        "x_start": 443.87,
        "y": 612.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 住宅借入金等特別控除 ㉟ (top=224.0)
    "housing_loan_credit": {
        "x_start": 443.87,
        "y": 579.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 差引所得税額 ㊷/#42 (top=273.5)
    "income_tax_after_credits": {
        "x_start": 443.87,
        "y": 530.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 復興特別所得税額 ㊺/#45 (top=323.0)
    "reconstruction_tax": {
        "x_start": 443.87,
        "y": 480.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 所得税及び復興特別所得税の額 ㊻/#46 (top=339.5)
    "total_tax": {
        "x_start": 443.87,
        "y": 464.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 源泉徴収税額 ㊾/#49 (top=372.5)
    "withheld_tax": {
        "x_start": 443.87,
        "y": 431.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 予定納税額 #51 (top=405.5)
    "estimated_tax_payment": {
        "x_start": 443.87,
        "y": 398.3,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 納める税金 #52 / 還付される税金 #53 (top=422.0)
    "tax_due": {
        "x_start": 443.87,
        "y": 381.8,
        "cell_width": 13.97,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
}


# ============================================================
# 確定申告書B 第二表 (Income Tax Form B - Page 2)
# NTA r07/01.pdf のページ1（0-indexed）= 第二表
# page size 579.672 x 814.791 (NOT standard A4)
# 座標は pdfplumber で実測し ReportLab 座標 (y=0 bottom) に変換済み
# 第二表は通常テキスト（カンマ区切り金額）・number型を使用
# ============================================================

INCOME_TAX_P2: dict[str, dict] = {
    # --- ヘッダー ---
    # 氏名: label at top=158.5, x0=48.8-80.4
    # データ入力は label 右側 x=84 以降
    "name_kanji": {
        "x": 84.0,
        "y": 650.3,
        "font_size": 9,
        "type": "text",
    },
    # --- 所得の内訳 (種類/支払者/収入金額/源泉徴収額) ---
    # 左側テーブル: h_lines at top 243.3, 265.3, 287.3, 309.3
    # V-lines: x=41.9, 78.4(種類), 114.1(種目), 199.3(支払者), 250.2(金額), 300.4(右端)
    # 4 data rows (22pt height each), baseline offset 14pt from row top
    # 円 markers: 収入金額 x0=242.6 → right-align x=248; 源泉徴収税額 x0=292.8 → right-align x=298
}

# 所得内訳行（最大4行）— NTA第二表には4行分のスペースのみ
# document.py は最大8行まで参照するため、8行分定義するが row 4-7 は
# テーブル外にはみ出す可能性がある
_INCOME_DETAIL_ROW_TOPS = [243.3, 265.3, 287.3, 309.3]
_INCOME_DETAIL_ROW_HEIGHT = 22.0
_INCOME_DETAIL_BASELINE_OFFSET = 14.0  # 22pt row, 7pt font
_PH = 814.791  # page height

for _i in range(8):
    if _i < 4:
        _row_top = _INCOME_DETAIL_ROW_TOPS[_i]
    else:
        # 4行目以降は外挿（実際のフォームには枠なし）
        _row_top = _INCOME_DETAIL_ROW_TOPS[3] + (_i - 3) * _INCOME_DETAIL_ROW_HEIGHT
    _y = _PH - _row_top - _INCOME_DETAIL_BASELINE_OFFSET
    INCOME_TAX_P2[f"income_detail_{_i}_type"] = {
        "x": 44.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    INCOME_TAX_P2[f"income_detail_{_i}_payer"] = {
        "x": 116.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    INCOME_TAX_P2[f"income_detail_{_i}_revenue"] = {
        "x": 248.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }
    INCOME_TAX_P2[f"income_detail_{_i}_withheld"] = {
        "x": 298.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }

# 社会保険料の内訳（最大4行）
# 右側パネル ⑬⑭セクション: h_lines at top 64.6(header), 83.9, 103.1
# V-lines: x=324.5(左端), x=415.2(種類/金額divider), x=489.4(計/うち divider), x=565.7(右端)
# Row height ~19.2pt, baseline offset 12pt
# 円 markers: 計 x0=481.8 → right-align x=488; うち x0=558.1 → right-align x=564
# NTA第二表には2行分のスペースのみ（83.9-103.1, 103.1-122.4）
# document.py は最大4行参照するため4行分定義するが、row 2-3 は枠外（⑮セクションに重なる）
_SOCIAL_INS_ROW_TOPS = [83.9, 103.1]
_SOCIAL_INS_ROW_HEIGHT = 19.2
_SOCIAL_INS_BASELINE_OFFSET = 12.0

for _i in range(4):
    if _i < 2:
        _row_top = _SOCIAL_INS_ROW_TOPS[_i]
    else:
        # 外挿 — 実際のフォームでは⑮セクションに重なる
        _row_top = _SOCIAL_INS_ROW_TOPS[1] + (_i - 1) * _SOCIAL_INS_ROW_HEIGHT
    _y = _PH - _row_top - _SOCIAL_INS_BASELINE_OFFSET
    INCOME_TAX_P2[f"social_insurance_{_i}_type"] = {
        "x": 327.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    INCOME_TAX_P2[f"social_insurance_{_i}_payer"] = {
        "x": 418.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    INCOME_TAX_P2[f"social_insurance_{_i}_amount"] = {
        "x": 488.0,
        "y": _y,
        "font_size": 7,
        "type": "number",
    }

# 扶養対象者（最大4名）— 配偶者や親族に関する事項
# 全幅テーブル: h_lines at top 453.7, 471.6, 489.4, 507.3, 525.2 (5行)
# Row 0 = 配偶者（spouse は別途定義）, Row 1-4 = 扶養親族
# V-lines: x=41.9, 132.0(氏名right), 303.8(続柄left), 325.1(生年月日), 406.9...
# Row height ~17.9pt, baseline offset 12pt
_DEPENDENT_ROW_TOPS = [471.6, 489.4, 507.3, 525.2]
_DEPENDENT_BASELINE_OFFSET = 12.0

for _i in range(4):
    _y = _PH - _DEPENDENT_ROW_TOPS[_i] - _DEPENDENT_BASELINE_OFFSET
    INCOME_TAX_P2[f"dependent_{_i}_name"] = {
        "x": 44.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    INCOME_TAX_P2[f"dependent_{_i}_relationship"] = {
        "x": 306.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }
    # 生年月日: 元号ラベル(明・大/昭・平/令) が x=326.5 に印刷済み
    # 実データは元号後の年月日 (x=345以降) に記入
    INCOME_TAX_P2[f"dependent_{_i}_birth_date"] = {
        "x": 345.0,
        "y": _y,
        "font_size": 7,
        "type": "text",
    }

# 配偶者情報 — 配偶者や親族テーブルの row 0 (top=453.7-471.6)
# 配偶者氏名: x=44, 配偶者所得（万円）: 万円 at x0=483.0 top=472.7
INCOME_TAX_P2["spouse_name"] = {
    "x": 44.0,
    "y": _PH - 453.7 - _DEPENDENT_BASELINE_OFFSET,
    "font_size": 7,
    "type": "text",
}
INCOME_TAX_P2["spouse_income"] = {
    "x": 483.0,
    "y": _PH - 453.7 - _DEPENDENT_BASELINE_OFFSET,
    "font_size": 7,
    "type": "number",
}

# 住宅ローン居住開始日
# 住民税・事業税セクション内 — 具体的な枠は用紙レイアウトに依存
# 簡易配置: 寄附金控除セクション付近 (top=373.9 area, right side)
INCOME_TAX_P2["housing_loan_move_in_date"] = {
    "x": 340.0,
    "y": _PH - 373.9 - 14.0,
    "font_size": 7,
    "type": "text",
}


# ============================================================
# 青色申告決算書 損益計算書 P1
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_PL_P1: dict[str, dict] = {
    # --- ヘッダー ---
    # 住所（上部右のヘッダー欄）
    # 座標系: Landscape (842x595), y は下端基準
    # NTA r07/10.pdf Page 0: MediaBox 595x842 + /Rotate=90
    # pdfplumber y_top → landscape y = 595 - pdfplumber_top
    # 金額右端: 左列 x=300, 中列 x=538, 右列 x=775
    # --- ヘッダー ---
    # 住所（右上ヘッダー x=487.7-634.4, plumb 75.0-101.1）
    "address": {"x": 490.0, "y": 505.0, "font_size": 7, "type": "text"},
    # 氏名（x=634.4-777.5, plumb 75.0-101.1）
    "taxpayer_name": {"x": 650.0, "y": 505.0, "font_size": 8, "type": "text"},
    # 電話番号（x=676.3-777.5, plumb 127.3-148.7）
    "phone": {"x": 680.0, "y": 453.0, "font_size": 7, "type": "text"},
    # 令和XX年分（年号ボックス x=327-393, plumb 127.3-153.5）
    "fiscal_year": {"x": 340.0, "y": 450.0, "font_size": 8, "type": "text"},
    # --- 左列: 売上（金額右端 x=300） ---
    # 売上(収入)金額 ア（plumb 223.4-232.1 → ly ≈ 366）
    "sales_revenue": {"x": 300.0, "y": 366.0, "font_size": 8, "type": "number"},
    # 計（売上合計）（plumb 249.6-258.3 → ly ≈ 340）
    "total_revenue": {"x": 300.0, "y": 340.0, "font_size": 8, "type": "number"},
    # --- 中央列: 売上原価（金額右端 x=538） ---
    # 期首商品棚卸高（plumb 206-223 → ly ≈ 375）
    "beginning_inventory": {"x": 538.0, "y": 375.0, "font_size": 8, "type": "number"},
    # 仕入金額（plumb 223-241 → ly ≈ 358）
    "purchases": {"x": 538.0, "y": 358.0, "font_size": 8, "type": "number"},
    # 小計（plumb 241-250 → ly ≈ 348）
    "cogs_subtotal": {"x": 538.0, "y": 348.0, "font_size": 8, "type": "number"},
    # 期末商品棚卸高（plumb 250-258 → ly ≈ 340）
    "ending_inventory": {"x": 538.0, "y": 340.0, "font_size": 8, "type": "number"},
    # 差引原価（plumb 258-276 → ly ≈ 322）
    "cost_of_sales": {"x": 538.0, "y": 322.0, "font_size": 8, "type": "number"},
    # 差引金額・売上総利益（plumb 276-293 → ly ≈ 305）
    "gross_profit": {"x": 538.0, "y": 305.0, "font_size": 8, "type": "number"},
    # --- 左列経費（金額右端 x=300） ---
    # 経費行間隔 ≈ 17.5pt
    # 給料賃金（plumb 258.3-275.7 → ly ≈ 322）
    "salary_wages": {"x": 300.0, "y": 322.0, "font_size": 8, "type": "number"},
    # 外注工賃（plumb 275.7-293.2 → ly ≈ 305）
    "outsourcing": {"x": 300.0, "y": 305.0, "font_size": 8, "type": "number"},
    # 減価償却費（plumb 293.2-310.7 → ly ≈ 287）
    "depreciation": {"x": 300.0, "y": 287.0, "font_size": 8, "type": "number"},
    # 貸倒金（plumb 310.7-328.1 → ly ≈ 270）
    "bad_debt": {"x": 300.0, "y": 270.0, "font_size": 8, "type": "number"},
    # 地代家賃（plumb 328.1-345.6 → ly ≈ 252）
    "rent": {"x": 300.0, "y": 252.0, "font_size": 8, "type": "number"},
    # --- 中央列経費（金額右端 x=538） ---
    # 租税公課（plumb 258.3-275.7 → ly ≈ 322）
    "taxes_and_dues": {"x": 538.0, "y": 322.0, "font_size": 8, "type": "number"},
    # 荷造運賃（plumb 275.7-293.2 → ly ≈ 305）
    "packing_shipping": {"x": 538.0, "y": 305.0, "font_size": 8, "type": "number"},
    # 水道光熱費（plumb 293.2-310.7 → ly ≈ 287）
    "utilities": {"x": 538.0, "y": 287.0, "font_size": 8, "type": "number"},
    # 旅費交通費（plumb 310.7-328.1 → ly ≈ 270）
    "travel": {"x": 538.0, "y": 270.0, "font_size": 8, "type": "number"},
    # 通信費（plumb 328.1-345.6 → ly ≈ 252）
    "communication": {"x": 538.0, "y": 252.0, "font_size": 8, "type": "number"},
    # 広告宣伝費（plumb 345.6-363.0 → ly ≈ 235）
    "advertising": {"x": 538.0, "y": 235.0, "font_size": 8, "type": "number"},
    # 接待交際費（plumb 363.0-380.5 → ly ≈ 217）
    "entertainment": {"x": 538.0, "y": 217.0, "font_size": 8, "type": "number"},
    # 損害保険料（plumb 380.5-398.0 → ly ≈ 200）
    "insurance": {"x": 538.0, "y": 200.0, "font_size": 8, "type": "number"},
    # 修繕費（plumb 398.0-415.4 → ly ≈ 183）
    "repairs": {"x": 538.0, "y": 183.0, "font_size": 8, "type": "number"},
    # 消耗品費（plumb 415.4-432.9 → ly ≈ 165）
    "supplies": {"x": 538.0, "y": 165.0, "font_size": 8, "type": "number"},
    # 福利厚生費（plumb 432.9-450.3 → ly ≈ 148）
    "welfare": {"x": 538.0, "y": 148.0, "font_size": 8, "type": "number"},
    # 雑費（plumb 450.3-467.8 → ly ≈ 130）
    "miscellaneous": {"x": 538.0, "y": 130.0, "font_size": 8, "type": "number"},
    # --- 左列 経費小計・合計 ---
    # 利子割引料（plumb 346-363 → ly ≈ 234）— 地代家賃の次行（セクション区切り後）
    "interest_discount": {"x": 300.0, "y": 234.0, "font_size": 8, "type": "number"},
    # 小計（plumb 450.3-467.8 → ly ≈ 130）
    "expenses_left_subtotal": {"x": 300.0, "y": 130.0, "font_size": 8, "type": "number"},
    # 中央列小計（plumb 467.8-485.3 → ly ≈ 113）
    "expenses_right_subtotal": {"x": 538.0, "y": 113.0, "font_size": 8, "type": "number"},
    # 経費合計（plumb 467.8-485.3 → ly ≈ 113）
    "total_expenses": {"x": 300.0, "y": 113.0, "font_size": 8, "type": "number"},
    # 差引金額（plumb 485.3-502.7 → ly ≈ 95）
    "operating_profit_subtotal": {"x": 300.0, "y": 95.0, "font_size": 8, "type": "number"},
    # --- 右列: 各種引当・控除（金額右端 x=775） ---
    # 専従者給与（plumb 424.2-441.6 → ly ≈ 157）
    "family_employee_salary": {"x": 775.0, "y": 157.0, "font_size": 8, "type": "number"},
    # 繰戻額等（plumb 441.6以下 → ly ≈ 148）
    "carryback_etc": {"x": 775.0, "y": 148.0, "font_size": 8, "type": "number"},
    # --- 下部: 所得金額（金額右端 x=775） ---
    # ㊸ 青色申告特別控除前の所得金額（plumb 494.0-511.5 → ly ≈ 87）
    "operating_income": {"x": 775.0, "y": 87.0, "font_size": 8, "type": "number"},
    # ㊹ 青色申告特別控除額（plumb 511.5-528.9 → ly ≈ 69）
    "blue_return_deduction": {"x": 775.0, "y": 69.0, "font_size": 8, "type": "number"},
    # ㊺ 所得金額（plumb 528.9-546.4 → ly ≈ 52）
    "net_income": {"x": 775.0, "y": 52.0, "font_size": 8, "type": "number"},
}


# ============================================================
# 青色申告決算書 損益計算書 P2 (月別売上・仕入)
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_PL_P2: dict[str, dict] = {
    # NTA r07/10.pdf Page 1: MediaBox 595x842 + /Rotate=90
    # Displayed as Landscape 842x595 (pdfplumber)
    # Coordinate transform: rx = 595 - ly, ry = lx, rotate(90)
    # --- ヘッダー ---
    "taxpayer_name": {"x": 120.0, "y": 559.0, "font_size": 9, "type": "text"},
}

# 月別売上（1月〜12月）— Page 1 (idx 1) of r07/10.pdf
# 左側テーブル: 月別売上（収入）金額及び仕入金額
# 12行（月ごと）× 2列（売上・仕入）の縦リスト
# 行間隔: 17.5pt, 最初の行 bottom: plumb 109.4
# 売上金額右端: x=215 (v-line x=218.1 の内側)
# 仕入金額右端: x=341 (v-line x=343.8 の内側)
# baseline = 595 - plumb_bottom + 3 (bottom line の 3pt 上)
_MONTHLY_ROW_SPACING = 17.5
_MONTHLY_FIRST_ROW_BOTTOM = 109.4  # plumb bottom of month 1
_MONTHLY_SALES_X = 215.0  # 売上金額右端
_MONTHLY_PURCHASES_X = 341.0  # 仕入金額右端

for _i in range(12):
    _plumb_bottom = _MONTHLY_FIRST_ROW_BOTTOM + _i * _MONTHLY_ROW_SPACING
    _ly = 595.0 - _plumb_bottom + 3.0
    BLUE_RETURN_PL_P2[f"monthly_sales_{_i + 1}"] = {
        "x": _MONTHLY_SALES_X,
        "y": _ly,
        "font_size": 6,
        "type": "number",
    }
    BLUE_RETURN_PL_P2[f"monthly_purchases_{_i + 1}"] = {
        "x": _MONTHLY_PURCHASES_X,
        "y": _ly,
        "font_size": 6,
        "type": "number",
    }

# 雑収入等 (row 13: plumb 301.5-318.9)
BLUE_RETURN_PL_P2["misc_revenue"] = {
    "x": _MONTHLY_SALES_X,
    "y": 595.0 - 318.9 + 3.0,
    "font_size": 6,
    "type": "number",
}
# 売上計 (row 14: plumb 318.9-336.4)
BLUE_RETURN_PL_P2["annual_sales_total"] = {
    "x": _MONTHLY_SALES_X,
    "y": 595.0 - 336.4 + 3.0,
    "font_size": 7,
    "type": "number",
}
# 仕入計 (row 14: plumb 318.9-336.4)
BLUE_RETURN_PL_P2["annual_purchases_total"] = {
    "x": _MONTHLY_PURCHASES_X,
    "y": 595.0 - 336.4 + 3.0,
    "font_size": 7,
    "type": "number",
}


# ============================================================
# 青色申告決算書 損益計算書 P3 (減価償却・地代家賃)
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_PL_P3: dict[str, dict] = {
    # NTA r07/10.pdf Page 2: MediaBox 595x842 + /Rotate=90
    # Displayed as Landscape 842x595 (pdfplumber)
    # --- ヘッダー ---
    "taxpayer_name": {"x": 120.0, "y": 559.0, "font_size": 9, "type": "text"},
}

# 減価償却費の計算（最大5行）
# Page 2 (idx 2) of r07/10.pdf — full-width 減価償却費の計算セクション
# Section spans x=59.2-810.3, pdfplumber y=296.6-482.9
# Header rows: y=296.6-340.3 (column labels ㋑㋺㋩㋥㋭㋬㋣㋠㋷㋦)
# Data row H-lines: 340.3, 358.2, 376.0, 393.9, 411.8, 429.7, 447.5, 465.4
# 行間隔: 17.9pt, 7 data rows (using first 5)
# V-lines: 59.2, 118.1, 147.6, 177.0, 243.3, 309.6, 339.0, 368.5,
#   397.9, 427.4, 486.3, 545.2, 604.1, 633.5, 692.5, 751.4, 810.3
# Total row: 465.4-482.9
# baseline = 595 - plumb_row_bottom + 3
_DEPR_ROW_SPACING = 17.9
_DEPR_FIRST_ROW_Y = 595.0 - 358.2 + 3.0  # = 239.8 (first data row)

for _i in range(5):
    _y = _DEPR_FIRST_ROW_Y - _i * _DEPR_ROW_SPACING
    # 資産名称 — 左寄せ x=62 (v-line 59.2 の右)
    BLUE_RETURN_PL_P3[f"depr_{_i}_name"] = {
        "x": 62.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    # 取得年月 — 左寄せ Col 2 (v-line 147.6-177.0)
    BLUE_RETURN_PL_P3[f"depr_{_i}_acq_date"] = {
        "x": 150.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    # ㋑ 取得価額 — 右寄せ x=240 (v-line 243.3 の内側)
    BLUE_RETURN_PL_P3[f"depr_{_i}_acq_cost"] = {
        "x": 240.0,
        "y": _y,
        "font_size": 6,
        "type": "number",
    }
    # 償却方法 — 左寄せ x=312 (v-line 309.6 の右)
    BLUE_RETURN_PL_P3[f"depr_{_i}_method"] = {
        "x": 312.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    # 耐用年数 — 左寄せ x=341 (v-line 339.0 の右)
    BLUE_RETURN_PL_P3[f"depr_{_i}_useful_life"] = {
        "x": 341.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    # ㋩ 償却率 — 左寄せ x=371 (v-line 368.5 の右)
    BLUE_RETURN_PL_P3[f"depr_{_i}_ratio"] = {
        "x": 371.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }
    # ㋣ 本年分の償却費合計 — 右寄せ x=601 (v-line 604.1 の内側)
    BLUE_RETURN_PL_P3[f"depr_{_i}_amount"] = {
        "x": 601.0,
        "y": _y,
        "font_size": 6,
        "type": "number",
    }
    # ㋦ 未償却残高 — 右寄せ x=748 (v-line 751.4 の内側)
    BLUE_RETURN_PL_P3[f"depr_{_i}_book_value"] = {
        "x": 748.0,
        "y": _y,
        "font_size": 6,
        "type": "number",
    }

# 減価償却費合計 — row 6 合計行 (plumb 447.5-465.4)
BLUE_RETURN_PL_P3["depr_total"] = {
    "x": 601.0,
    "y": 595.0 - 465.4 + 3.0,
    "font_size": 7,
    "type": "number",
}

# 地代家賃の内訳（最大2行）
# 下部右セクション: plumb y=509.6-565.5, x=442.1-810.3
# H-lines: 527.1, 546.3 (行間隔 19.2pt)
# V-lines: x=611.5, 677.7, 744.0 (within section)
# 2 data rows: 527.1→546.3, 546.3→565.5
_RENT_ROW_SPACING = 19.2
_RENT_FIRST_ROW_Y = 595.0 - 546.3 + 3.0  # = 51.7 (first data row)
for _i in range(2):
    _y = _RENT_FIRST_ROW_Y - _i * _RENT_ROW_SPACING
    # 支払先の住所・氏名 — 左寄せ x=615
    BLUE_RETURN_PL_P3[f"rent_{_i}_landlord"] = {
        "x": 615.0,
        "y": _y,
        "font_size": 5,
        "type": "text",
    }
    # 賃借料（月額）— 右寄せ x=675 (v-line 677.7 の内側)
    BLUE_RETURN_PL_P3[f"rent_{_i}_monthly"] = {
        "x": 675.0,
        "y": _y,
        "font_size": 6,
        "type": "number",
    }
    # 賃借料（年額）— 右寄せ x=741 (v-line 744.0 の内側)
    BLUE_RETURN_PL_P3[f"rent_{_i}_annual"] = {
        "x": 741.0,
        "y": _y,
        "font_size": 6,
        "type": "number",
    }
    # 事業専用割合 — 左寄せ x=755
    BLUE_RETURN_PL_P3[f"rent_{_i}_business_pct"] = {
        "x": 755.0,
        "y": _y,
        "font_size": 6,
        "type": "text",
    }


# ============================================================
# 青色申告決算書 貸借対照表
# Landscape 842 x 595
# ============================================================

BLUE_RETURN_BS: dict[str, dict] = {
    # NTA r07/10.pdf Page 3: MediaBox 595x842 + /Rotate=90
    # Displayed as Landscape 842x595 (pdfplumber)
    # Coordinate transform: rx = 595 - ly, ry = lx, rotate(90)
    # --- ヘッダー ---
    # 氏名欄: タイトル下ヘッダー行（plumb 50-58, 住所/屋号及び氏名ラベル帯）
    "taxpayer_name": {"x": 120.0, "y": 540.0, "font_size": 9, "type": "text"},
    "fiscal_year_end": {"x": 390.0, "y": 545.0, "font_size": 8, "type": "text"},
    # --- 資産の部（期末欄: 右端 x=313, v-line x=315.5 の内側） ---
    # H-lines: 91.7, 109.1, 126.6, 144.0, 161.5, 179.0, 196.4, 213.9, ...
    # 行間隔 ~17.5pt, Row 0 baseline ≈ ly 497
    # Row 0: 現金
    "cash": {"x": 313.0, "y": 497.0, "font_size": 7, "type": "number"},
    # Row 1: 当座預金
    "checking_deposit": {"x": 313.0, "y": 479.5, "font_size": 7, "type": "number"},
    # Row 2: 定期預金
    "time_deposit": {"x": 313.0, "y": 462.0, "font_size": 7, "type": "number"},
    # Row 3: その他の預金
    "bank_deposit": {"x": 313.0, "y": 444.5, "font_size": 7, "type": "number"},
    # Row 4: 受取手形
    "notes_receivable": {"x": 313.0, "y": 427.0, "font_size": 7, "type": "number"},
    # Row 5: 売掛金
    "accounts_receivable": {"x": 313.0, "y": 409.5, "font_size": 7, "type": "number"},
    # Row 6: 有価証券
    "securities": {"x": 313.0, "y": 392.0, "font_size": 7, "type": "number"},
    # Row 7: 棚卸資産
    "inventory": {"x": 313.0, "y": 374.5, "font_size": 7, "type": "number"},
    # Row 8: 前払金
    "prepaid": {"x": 313.0, "y": 357.0, "font_size": 7, "type": "number"},
    # Row 9: 貸付金
    "loans_receivable": {"x": 313.0, "y": 339.5, "font_size": 7, "type": "number"},
    # Row 10: 建物
    "buildings": {"x": 313.0, "y": 322.0, "font_size": 7, "type": "number"},
    # Row 11: 建物附属設備
    "building_fixtures": {"x": 313.0, "y": 304.5, "font_size": 7, "type": "number"},
    # Row 12: 機械装置
    "machinery": {"x": 313.0, "y": 287.0, "font_size": 7, "type": "number"},
    # Row 13: 車両運搬具
    "vehicles": {"x": 313.0, "y": 269.5, "font_size": 7, "type": "number"},
    # Row 14: 工具器具備品
    "equipment": {"x": 313.0, "y": 252.0, "font_size": 7, "type": "number"},
    # Row 15: 土地
    "land": {"x": 313.0, "y": 234.5, "font_size": 7, "type": "number"},
    # Row 16-17: (空行 — 任意追加科目用)
    # Row 18: 事業主貸
    "owner_drawing": {"x": 313.0, "y": 165.0, "font_size": 7, "type": "number"},
    # Row 19: 合計
    "total_assets": {"x": 313.0, "y": 147.5, "font_size": 7, "type": "number"},
    # --- 負債・資本の部（期末欄: 右端 x=555, v-line x=557.5 の内側） ---
    # Row 0: 支払手形
    "notes_payable": {"x": 555.0, "y": 497.0, "font_size": 7, "type": "number"},
    # Row 1: 買掛金
    "accounts_payable": {"x": 555.0, "y": 479.5, "font_size": 7, "type": "number"},
    # Row 2: 借入金
    "borrowings": {"x": 555.0, "y": 462.0, "font_size": 7, "type": "number"},
    # Row 3: 未払金
    "unpaid": {"x": 555.0, "y": 444.5, "font_size": 7, "type": "number"},
    # Row 4: 前受金
    "advance_received": {"x": 555.0, "y": 427.0, "font_size": 7, "type": "number"},
    # Row 5: 預り金
    "deposits_received": {"x": 555.0, "y": 409.5, "font_size": 7, "type": "number"},
    # Row 6-14: (空行)
    # Row 15: 貸倒引当金
    "bad_debt_reserve": {"x": 555.0, "y": 234.5, "font_size": 7, "type": "number"},
    # 負債合計 — NTA様式にはない項目だが document.py から参照されるため定義
    "total_liabilities": {"x": 555.0, "y": 217.0, "font_size": 7, "type": "number"},
    # Row 16-17: (空行)
    # 事業主借
    "owner_investment": {"x": 555.0, "y": 182.5, "font_size": 7, "type": "number"},
    # 元入金
    "capital": {"x": 555.0, "y": 165.0, "font_size": 7, "type": "number"},
    # 青色申告特別控除前の所得金額
    "net_income_bs": {"x": 555.0, "y": 147.5, "font_size": 7, "type": "number"},
    # 合計
    "total_equity": {"x": 555.0, "y": 130.0, "font_size": 7, "type": "number"},
}


# ============================================================
# 消費税確定申告書 第一表
# NTA 17.pdf page 1 — Portrait 597 x 839
# ============================================================

CONSUMPTION_TAX_P1: dict[str, dict] = {
    # --- ヘッダー ---
    # 氏名又は名称（name field, left side）
    "taxpayer_name": {"x": 100.0, "y": 680.0, "font_size": 10, "type": "text"},
    # 課税期間 自（period start, left of title row）
    "fiscal_year": {"x": 56.0, "y": 622.0, "font_size": 7, "type": "text"},
    # --- 課税方式チェックボックス（右上 種類欄）---
    # ○確定申告（一般）
    "method_standard": {"x": 369.0, "y": 641.0, "size": 6, "type": "checkbox"},
    # ○修正申告（簡易）
    "method_simplified": {"x": 369.0, "y": 631.0, "size": 6, "type": "checkbox"},
    # ○還付申告（2割特例）
    "method_special_20pct": {"x": 369.0, "y": 621.0, "size": 6, "type": "checkbox"},
    # --- 消費税の税額の計算（左列 digit_cells）---
    # ① 課税標準額
    "taxable_sales_amount": {
        "x_start": 170.0,
        "y": 519.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    # ② 消費税額
    "tax_on_sales": {
        "x_start": 170.0,
        "y": 505.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    # ④ 控除対象仕入税額
    "tax_on_purchases": {
        "x_start": 170.0,
        "y": 478.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    # ⑨ 差引税額
    "tax_due_national": {
        "x_start": 170.0,
        "y": 408.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 地方消費税の税額の計算（下段）---
    # ⑯ 地方消費税額（譲渡割額）
    "local_tax_due": {
        "x_start": 170.0,
        "y": 256.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    # ㉒ 消費税及び地方消費税合計納付税額
    "total_tax_due": {
        "x_start": 170.0,
        "y": 185.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
}


# ============================================================
# 消費税確定申告書 控（Carbon Copy）
# NTA 17.pdf page 2 — same layout as P1, with 控 watermark
# Portrait 597 x 839
# ============================================================

CONSUMPTION_TAX_P2: dict[str, dict] = {
    # --- ヘッダー ---
    "taxpayer_name": {"x": 100.0, "y": 680.0, "font_size": 10, "type": "text"},
    "fiscal_year": {"x": 56.0, "y": 622.0, "font_size": 7, "type": "text"},
    # --- 課税方式チェックボックス ---
    "method_standard": {"x": 369.0, "y": 641.0, "size": 6, "type": "checkbox"},
    "method_simplified": {"x": 369.0, "y": 631.0, "size": 6, "type": "checkbox"},
    "method_special_20pct": {"x": 369.0, "y": 621.0, "size": 6, "type": "checkbox"},
    # --- 消費税の税額の計算 ---
    "taxable_sales_amount": {
        "x_start": 170.0,
        "y": 519.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_on_sales": {
        "x_start": 170.0,
        "y": 505.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_on_purchases": {
        "x_start": 170.0,
        "y": 478.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_due_national": {
        "x_start": 170.0,
        "y": 408.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 地方消費税の税額の計算 ---
    "local_tax_due": {
        "x_start": 170.0,
        "y": 256.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
    },
    "total_tax_due": {
        "x_start": 170.0,
        "y": 185.0,
        "cell_width": 12.7,
        "num_cells": 11,
        "font_size": 9,
        "type": "digit_cells",
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
# Medical Expense Detail Form (医療費控除の明細書)
# Template: medical_expense.pdf (page 1) — A4 Portrait 595.276 x 841.890
# pdfplumber座標 → ReportLab変換: rl_y = 841.89 - pdfplumber_top
# 主テーブル列境界: 51.0, 144.5, 257.9, 379.8, 462.0, 544.2 (pt)
# 主テーブル行間隔: ~19.8pt (~7.0mm), 先頭行 top=264.2
# ============================================================

MEDICAL_EXPENSE_DETAIL_FORM: dict[str, dict] = {
    # --- ヘッダー ---
    # 氏名欄: x=343-544.2 (「氏名」ラベル右側), bottom line top=107.7
    # テキストベースライン: top≈97 → rl_y=841.89-97=744.9pt≈262.8mm
    "taxpayer_name": {"x": 125 * mm, "y": 263 * mm, "font_size": 9, "type": "text"},
    # 年分: 「年分」テキスト(top=41, x0=222.9)の手前
    "fiscal_year": {"x": 67 * mm, "y": 282 * mm, "font_size": 10, "type": "text"},
    # --- セクション1: 医療費通知 (右側ボックス 297.6-544.2, top=133.7-187.5) ---
    # ⑴ 支払った医療費の額: 上行(133.7-162.0), 右寄せ col right=462.0
    "notification_1_amount": {
        "x": 161 * mm,
        "y": 245 * mm,
        "font_size": 8,
        "type": "number",
    },
    # ⑵ 補填される金額: 下行(162.0-187.5), col right=462.0
    "notification_2_amount": {
        "x": 161 * mm,
        "y": 235 * mm,
        "font_size": 8,
        "type": "number",
    },
    # ⑶ 差引金額: 下行(162.0-187.5), col right=544.2
    "notification_3_amount": {
        "x": 190 * mm,
        "y": 235 * mm,
        "font_size": 8,
        "type": "number",
    },
    # --- セクション2小計 (2の合計): top=584.5-610.0 mid=597 ---
    # ④支払った医療費の合計: col right=462.0
    "sect2_total_amount": {
        "x": 161 * mm,
        "y": 86 * mm,
        "font_size": 8,
        "type": "number",
    },
    # ⑤補填される金額の合計: col right=544.2
    "sect2_total_reimbursement": {
        "x": 190 * mm,
        "y": 86 * mm,
        "font_size": 8,
        "type": "number",
    },
    # --- 医療費の合計 (⑴+2): top=615.7-641.2 mid=628 ---
    # A (支払った医療費の合計): subtot right edge≈425
    "grand_total_a": {
        "x": 148 * mm,
        "y": 75 * mm,
        "font_size": 8,
        "type": "number",
    },
    # B (補填される金額の合計): subtot right edge≈544
    "grand_total_b": {
        "x": 190 * mm,
        "y": 75 * mm,
        "font_size": 8,
        "type": "number",
    },
    # --- セクション3: 控除額の計算 (左下 51.0-257.9, top=661.3-811.3) ---
    # 各行の金額フィールド: col 153.0-257.9 右寄せ (right edge≈253pt=89mm)
    # A 支払った医療費: row 661.3-682.0 mid=671.6 → rl_y=170.2pt=60.1mm
    "section3_a": {"x": 89 * mm, "y": 60 * mm, "font_size": 8, "type": "number"},
    # B 保険金等の補填額: row 682.0-702.7 mid=692.4 → rl_y=149.5pt=52.8mm
    "section3_b": {"x": 89 * mm, "y": 53 * mm, "font_size": 8, "type": "number"},
    # C 差引金額(A-B): row 702.7-723.4 mid=713.0 → rl_y=128.8pt=45.5mm
    "section3_c": {"x": 89 * mm, "y": 45 * mm, "font_size": 8, "type": "number"},
    # D 所得金額の合計額: row 723.4-744.1 mid=733.8 → rl_y=108.1pt=38.1mm
    "section3_d": {"x": 89 * mm, "y": 38 * mm, "font_size": 8, "type": "number"},
    # E D×0.05: row 744.1-764.8 mid=754.5 → rl_y=87.4pt=30.8mm
    "section3_e": {"x": 89 * mm, "y": 31 * mm, "font_size": 8, "type": "number"},
    # F 10万円とEのいずれか少ない方: row 764.8-785.5 mid=775.1 → rl_y=66.7pt=23.5mm
    "section3_f": {"x": 89 * mm, "y": 24 * mm, "font_size": 8, "type": "number"},
    # G 医療費控除額(C-F): row 785.5-811.3 mid=798.4 → rl_y=43.5pt=15.3mm
    "section3_g": {"x": 89 * mm, "y": 15 * mm, "font_size": 8, "type": "number"},
}

# セクション2明細行: 16行, 先頭 top=264.2, 間隔=19.8pt(≈7.0mm)
# テキストベースライン: 行上端から約13pt下 → rl_y = 841.89 - (264.2 + i*19.8 + 13)
# Col: ①氏名(51-144.5) ②支払先(144.5-257.9) ④金額(379.8-462.0) ⑤補填(462.0-544.2)
for _i in range(16):
    _y_mm = round((841.89 - (264.2 + _i * 19.8 + 13)) / mm, 1)
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_patient"] = {
        "x": 19 * mm,
        "y": _y_mm * mm,
        "font_size": 6,
        "type": "text",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_institution"] = {
        "x": 52 * mm,
        "y": _y_mm * mm,
        "font_size": 6,
        "type": "text",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_amount"] = {
        "x": 160 * mm,
        "y": _y_mm * mm,
        "font_size": 7,
        "type": "number",
    }
    MEDICAL_EXPENSE_DETAIL_FORM[f"line_{_i}_reimbursement"] = {
        "x": 189 * mm,
        "y": _y_mm * mm,
        "font_size": 7,
        "type": "number",
    }


# ============================================================
# Housing Loan Detail Form (住宅借入金等特別控除の計算明細書)
# Template: r07/14.pdf (page 1) — Portrait 579.672 x 814.791
# pdfplumber座標 → ReportLab変換: rl_y = 814.79 - pdfplumber_top
# セクション2列境界: 37.9, 118.8, 234.8, 350.8 (家屋/土地)
# セクション7列境界: 132.6, 146.6, 248.6, 350.6, 452.6, 554.6
# ============================================================

HOUSING_LOAN_DETAIL_FORM: dict[str, dict] = {
    # --- セクション1: 住所及び氏名 ---
    # 氏名欄: top≈98 (氏名ラベル位置), x=76.4-302.5
    "taxpayer_name": {"x": 80.0, "y": 714.0, "font_size": 9, "type": "text"},
    # 令和XX年分: 「令和」(x=41.3, top=21.5)の後に年号
    "fiscal_year": {"x": 70.0, "y": 790.0, "font_size": 9, "type": "text"},
    # --- セクション2: 新築又は購入した家屋等に係る事項 ---
    # ㋐ 居住開始年月日: row 134.7-154.0, 家屋col (132.8-234.8)
    # 「令和」(x=134.9, top=146)の右に日付値
    "move_in_date": {"x": 157.0, "y": 670.0, "font_size": 7, "type": "text"},
    # ㋑ 契約日: row 154.0-173.2
    "purchase_date": {"x": 157.0, "y": 651.0, "font_size": 7, "type": "text"},
    # ㋒ 補助金等控除前の取得対価の額: row 173.2-192.5
    # 金額右寄せ、「円」(x=351.5)の手前 → right edge≈348
    "purchase_price": {"x": 348.0, "y": 632.0, "font_size": 7, "type": "number"},
    # ㋓ 交付を受ける補助金等の額: row 192.5-211.7
    "subsidy_amount": {"x": 348.0, "y": 613.0, "font_size": 7, "type": "number"},
    # ㋔ 取得対価の額(㋒−㋓): row 211.7-231.0
    "net_acquisition_cost": {"x": 348.0, "y": 593.0, "font_size": 7, "type": "number"},
    # ㋕ 総（床）面積: row 231.0-250.2, 家屋col (132.8-161.7)
    "total_floor_area": {"x": 138.0, "y": 574.0, "font_size": 7, "type": "text"},
    # ㋖ うち居住用部分の（床）面積: row 250.2-269.5
    "residential_floor_area": {"x": 138.0, "y": 555.0, "font_size": 7, "type": "text"},
    # 不動産番号: top≈275-295 (sect2下), 家屋col
    "property_number": {"x": 138.0, "y": 530.0, "font_size": 7, "type": "text"},
    # --- セクション4: 家屋や土地等の取得対価の額 ---
    # ①共有持分: row 313.5-332.7, Ⓐ家屋 col 146.6-248.6 right=244
    "shared_ratio": {"x": 244.0, "y": 492.0, "font_size": 7, "type": "text"},
    # ②取得対価×持分: row 332.7-360.2
    "cost_after_share": {"x": 244.0, "y": 468.0, "font_size": 7, "type": "number"},
    # ③住宅取得等資金の贈与の特例を受けた金額: row 360.2-379.4
    "gift_special_amount": {"x": 244.0, "y": 445.0, "font_size": 7, "type": "number"},
    # ④あなたの持分に係る取得対価の額(②−③): row 379.4-398.7
    "personal_acquisition_cost": {"x": 244.0, "y": 426.0, "font_size": 7, "type": "number"},
    # --- セクション5: 消費税 ---
    # 消費税区分: row 402-434 area (なし/5%/8%/10%)
    "consumption_tax_type": {"x": 60.0, "y": 393.0, "font_size": 7, "type": "text"},
    # --- セクション7: 住宅借入金等の年末残高 ---
    # Ⓖ住宅及び土地等 col 350.6-452.6, right edge≈448
    # ⑤ 年末残高: row 453.0-472.2
    "year_end_balance": {"x": 448.0, "y": 352.0, "font_size": 7, "type": "number"},
    # ⑥ 連帯債務に係る負担割合: row 472.2-491.5
    "joint_debt_ratio": {"x": 448.0, "y": 333.0, "font_size": 7, "type": "text"},
    # ⑦ 住宅借入金等の年末残高(付表⑯): row 491.5-510.7
    "balance_after_joint": {"x": 448.0, "y": 314.0, "font_size": 7, "type": "number"},
    # ⑧ ④と⑦のいずれか少ない方: row 510.7-530.0
    "capped_balance": {"x": 448.0, "y": 294.0, "font_size": 7, "type": "number"},
    # ⑨ 居住用割合: row 530.0-549.2
    "residential_ratio": {"x": 448.0, "y": 275.0, "font_size": 7, "type": "text"},
    # ⑩ 居住用部分の年末残高(⑧×⑨): row 549.2-568.5
    "residential_balance": {"x": 448.0, "y": 256.0, "font_size": 7, "type": "number"},
    # ⑪ 年末残高の合計額: top≈572-580
    "total_year_end_balance": {"x": 448.0, "y": 240.0, "font_size": 8, "type": "number"},
    # --- セクション9: 控除額 ---
    # ⑳ 控除額: digit cells at 484.8-552.7, row top=688.1-701.8
    # 6 cells: cell_width≈11.5, right edge≈552.7
    "credit_amount": {
        "x_start": 484.8,
        "y": 117.0,
        "cell_width": 11.5,
        "num_cells": 6,
        "font_size": 8,
        "type": "digit_cells",
    },
    # 番号欄: 2 digit cells at 444.9-466.7, cell_width≈11.6
    "credit_type_number": {
        "x_start": 444.9,
        "y": 117.0,
        "cell_width": 11.6,
        "num_cells": 2,
        "font_size": 7,
        "type": "digit_cells",
    },
    # --- セクション10: 控除証明書の交付を要しない場合 ---
    "no_certificate_needed": {"x": 270.0, "y": 42.0, "font_size": 7, "type": "text"},
}


# ============================================================
# Schedule 3 (第三表: 分離課税用)
# Template: r07/02.pdf — Portrait 579.67 x 814.79
# pdfplumber座標 → ReportLab変換: rl_y = 814.79 - pdfplumber_top
# 左テーブル digit_cells: x_start=191.8, cell_width=13.9, num_cells=7
# 右テーブル digit_cells: x_start=448.7, cell_width=14.3, num_cells=7
# ============================================================

SCHEDULE_3_FORM: dict[str, dict] = {
    # --- ヘッダー ---
    # Template: r07/02.pdf — Portrait 579.672 x 814.791
    # 氏名欄は左上ヘッダーボックス内 (pdfplumber実測)
    "taxpayer_name": {"x": 90.0, "y": 658.0, "font_size": 9, "type": "text"},
    # --- 収入金額 (左テーブル, ㋛〜㋥) ---
    # 左列: x_start=192.8, cell_width=14.0, num_cells=7 (pdfplumber実測)
    "rev_short_general": {
        "x_start": 192.8,
        "y": 614.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_short_reduced": {
        "x_start": 192.8,
        "y": 596.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_long_general": {
        "x_start": 192.8,
        "y": 579.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_long_specific": {
        "x_start": 192.8,
        "y": 561.8,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_long_reduced": {
        "x_start": 192.8,
        "y": 544.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_general_stock": {
        "x_start": 192.8,
        "y": 526.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_listed_stock": {
        "x_start": 192.8,
        "y": 509.4,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_listed_dividend": {
        "x_start": 192.8,
        "y": 492.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_futures": {
        "x_start": 192.8,
        "y": 474.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_mountain": {
        "x_start": 192.8,
        "y": 457.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "rev_retirement": {
        "x_start": 192.8,
        "y": 439.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 所得金額 (左テーブル) ---
    "inc_short_general": {
        "x_start": 192.7,
        "y": 422.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_short_reduced": {
        "x_start": 192.7,
        "y": 404.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_long_general": {
        "x_start": 192.7,
        "y": 387.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_long_specific": {
        "x_start": 192.7,
        "y": 369.8,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_long_reduced": {
        "x_start": 192.7,
        "y": 352.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_general_stock": {
        "x_start": 192.7,
        "y": 334.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_listed_stock": {
        "x_start": 192.7,
        "y": 317.4,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_listed_dividend": {
        "x_start": 192.7,
        "y": 300.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_futures": {
        "x_start": 192.7,
        "y": 282.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_mountain": {
        "x_start": 192.7,
        "y": 265.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "inc_retirement": {
        "x_start": 192.7,
        "y": 247.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 税金の計算 (左テーブル) ---
    # ⑫ 総合課税の合計額
    "total_general_income": {
        "x_start": 192.8,
        "y": 230.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # ㉚ 所得控除合計
    "total_deductions": {
        "x_start": 192.8,
        "y": 212.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 課税所得（各対応分）
    "taxable_general": {
        "x_start": 192.8,
        "y": 195.1,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_short": {
        "x_start": 192.8,
        "y": 177.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_long": {
        "x_start": 192.8,
        "y": 160.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_stock": {
        "x_start": 192.8,
        "y": 142.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_listed_dividend": {
        "x_start": 192.8,
        "y": 125.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_futures": {
        "x_start": 192.8,
        "y": 107.8,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_mountain": {
        "x_start": 192.8,
        "y": 90.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "taxable_retirement": {
        "x_start": 192.8,
        "y": 72.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 税額 (右テーブル) ---
    # 右列: x_start=451.2, cell_width=14.0, num_cells=7 (pdfplumber実測)
    "tax_short_general": {
        "x_start": 451.2,
        "y": 614.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_short_reduced": {
        "x_start": 451.2,
        "y": 596.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_long_general": {
        "x_start": 451.2,
        "y": 579.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_long_specific": {
        "x_start": 451.2,
        "y": 561.8,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_long_reduced": {
        "x_start": 451.2,
        "y": 544.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_general_stock": {
        "x_start": 451.2,
        "y": 526.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_listed_stock": {
        "x_start": 451.2,
        "y": 509.4,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_listed_dividend": {
        "x_start": 451.2,
        "y": 492.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_futures": {
        "x_start": 451.2,
        "y": 474.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_mountain": {
        "x_start": 451.2,
        "y": 457.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_retirement": {
        "x_start": 451.2,
        "y": 439.4,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_general": {
        "x_start": 451.2,
        "y": 422.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_after_credits": {
        "x_start": 451.2,
        "y": 404.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    "tax_net": {
        "x_start": 451.2,
        "y": 387.1,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 右下: 上場株式等の源泉徴収税額 ---
    "stock_withheld_total": {
        "x_start": 451.2,
        "y": 223.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
}


# ============================================================
# Schedule 4 (第四表: 損失申告用)
# Template: r07/03.pdf — Portrait 579.67 x 814.79
# Page 1 = 第四表(一): Section 1 (損失額又は所得金額) + Section 2 (損益の通算)
# Page 2 = 第四表(二): Section 3 (繰越損失額) + Section 4 (繰越損失差引計算)
# Section 1 メインテーブル: (48.9, 134.7, 544.8, 514.2) RL=(680.1 to 300.6)
# Section 2 テーブル: (48.9, 549.9, 544.8, 764.4) RL=(264.9 to 50.4)
# 行高さ ≈ 23.4pt
# ============================================================

SCHEDULE_4_FORM: dict[str, dict] = {
    # --- ヘッダー ---
    # Template: r07/03.pdf — Portrait 579.672 x 814.791
    # 氏名欄はヘッダーボックス内、「氏名」ラベルの右側 (plumb: x≈370, top≈70)
    "taxpayer_name": {"x": 375.0, "y": 735.0, "font_size": 9, "type": "text"},
    # --- Section 1: 損失額又は所得金額 ---
    # 右端列 (Ⓔ 損失額又は所得金額) — x right edge ≈ 540 (column border 544.8)
    # 行高さ ≈ 23.4pt, baseline = 行底線の6pt上
    # Row A: 経常所得 (plumb 158.1-187.0)
    "s1_business_income": {"x": 540.0, "y": 634.0, "font_size": 8, "type": "number"},
    # Row B: 短期譲渡（分離/総合）, 長期譲渡（分離/総合）, 一時
    "s1_short_transfer_sep": {"x": 540.0, "y": 610.5, "font_size": 7, "type": "number"},
    "s1_short_transfer_gen": {"x": 540.0, "y": 587.1, "font_size": 7, "type": "number"},
    "s1_long_transfer_sep": {"x": 540.0, "y": 563.7, "font_size": 7, "type": "number"},
    "s1_long_transfer_gen": {"x": 540.0, "y": 540.3, "font_size": 7, "type": "number"},
    "s1_temporary_income": {"x": 540.0, "y": 517.0, "font_size": 7, "type": "number"},
    # Row C: 山林 (plumb 303.8-327.2)
    "s1_mountain_income": {"x": 540.0, "y": 493.6, "font_size": 7, "type": "number"},
    # Row D: 退職 (plumb 327.2-350.6)
    "s1_retirement_income": {"x": 540.0, "y": 470.2, "font_size": 7, "type": "number"},
    # Row E: 一般株式等の譲渡, 上場株式等の譲渡, 上場株式等の配当等
    "s1_general_stock": {"x": 540.0, "y": 400.1, "font_size": 7, "type": "number"},
    "s1_listed_stock": {"x": 540.0, "y": 376.7, "font_size": 7, "type": "number"},
    "s1_listed_dividend": {"x": 540.0, "y": 353.4, "font_size": 7, "type": "number"},
    # Row F: 先物取引 (after plumb 467.4)
    "s1_futures": {"x": 540.0, "y": 335.0, "font_size": 7, "type": "number"},
    # --- Section 2: 損益の通算 ---
    # Ⓐ通算前列: x right edge ≈ 212 (column border 216.5)
    # Ⓔ結果列: x right edge ≈ 540 (column border 544.8)
    # 行高さ ≈ 23.4pt
    "s2_business_before": {"x": 212.0, "y": 220.0, "font_size": 7, "type": "number"},
    "s2_business_result": {"x": 540.0, "y": 220.0, "font_size": 7, "type": "number"},
    "s2_short_gen_before": {"x": 212.0, "y": 196.6, "font_size": 7, "type": "number"},
    "s2_short_gen_result": {"x": 540.0, "y": 196.6, "font_size": 7, "type": "number"},
    "s2_long_sep_before": {"x": 212.0, "y": 173.3, "font_size": 7, "type": "number"},
    "s2_long_sep_result": {"x": 540.0, "y": 173.3, "font_size": 7, "type": "number"},
    "s2_long_gen_before": {"x": 212.0, "y": 149.9, "font_size": 7, "type": "number"},
    "s2_long_gen_result": {"x": 540.0, "y": 149.9, "font_size": 7, "type": "number"},
    "s2_temporary_before": {"x": 212.0, "y": 126.5, "font_size": 7, "type": "number"},
    "s2_temporary_result": {"x": 540.0, "y": 126.5, "font_size": 7, "type": "number"},
    "s2_mountain_before": {"x": 212.0, "y": 103.0, "font_size": 7, "type": "number"},
    "s2_mountain_result": {"x": 540.0, "y": 103.0, "font_size": 7, "type": "number"},
    "s2_retirement_before": {"x": 212.0, "y": 79.5, "font_size": 7, "type": "number"},
    "s2_retirement_result": {"x": 540.0, "y": 79.5, "font_size": 7, "type": "number"},
    # 合計行 (after plumb 741.0)
    "s2_total_result": {"x": 540.0, "y": 60.0, "font_size": 8, "type": "number"},
}


# ============================================================
# Income/Expense Statement (収支内訳書 — 白色申告用)
# Template: r07/05_ie.pdf — Portrait 595x842 + /Rotate=90 (visual landscape 842x595)
# Overlay canvas: (842, 595) — pdfplumber visual座標 = RL座標
# 左列 digit_cells: x_start=162.7, cell_width=14.0, num_cells=7
# 右列 digit_cells: x_start=379.2, cell_width=14.0, num_cells=7
# 右端（給料賃金等）: x_start=719.3〜785.8, cell_width=11.1, num_cells=7
# ============================================================

INCOME_EXPENSE_STATEMENT: dict[str, dict] = {
    # --- ヘッダー ---
    # 住所（左上）
    "taxpayer_name": {"x": 135.0, "y": 510.0, "font_size": 8, "type": "text"},
    # 令和XX年（年ボックス上部）
    "fiscal_year": {"x": 360.0, "y": 538.0, "font_size": 9, "type": "text"},
    # --- 売上（収入）金額 (左列, 上から) ---
    # 売上（収入）金額①  — Row 0: RL_baseline=376.5
    "total_revenue": {
        "x_start": 162.7,
        "y": 376.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # その他の収入②  — Row 1: RL_baseline=359.0
    "other_revenue": {
        "x_start": 162.7,
        "y": 359.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 売上原価 (左列) ---
    # 期首商品棚卸高③  — Row 2: RL_baseline=341.5
    "beginning_inventory": {
        "x_start": 162.7,
        "y": 341.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 仕入金額④  — Row 3: RL_baseline=324.1
    "purchases": {
        "x_start": 162.7,
        "y": 324.1,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 期末商品棚卸高⑤  — Row 4: RL_baseline=306.6
    "ending_inventory": {
        "x_start": 162.7,
        "y": 306.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 差引原価⑥  — Row 5: RL_baseline=289.2
    "cost_of_sales": {
        "x_start": 162.7,
        "y": 289.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 差引金額⑦  — Row 6: RL_baseline=271.7
    "gross_profit": {
        "x_start": 162.7,
        "y": 271.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 経費 (左列) ---
    # 給料賃金⑧  — Row 7: RL_baseline=254.2
    "salaries": {
        "x_start": 162.7,
        "y": 254.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 外注工賃⑨  — Row 8: RL_baseline=236.8
    "outsourcing": {
        "x_start": 162.7,
        "y": 236.8,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 減価償却費⑩  — Row 9: RL_baseline=219.3
    "depreciation": {
        "x_start": 162.7,
        "y": 219.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 地代家賃⑪  — Row 10: RL_baseline=201.9
    "rent": {
        "x_start": 162.7,
        "y": 201.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 利子割引料⑫  — Row 11: RL_baseline=184.4
    "interest": {
        "x_start": 162.7,
        "y": 184.4,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 経費 (右列) ---
    # 租税公課⑬  — Row 0: RL_baseline=376.5
    "taxes": {
        "x_start": 379.2,
        "y": 376.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 荷造運賃⑭  — Row 1: RL_baseline=359.0
    "shipping": {
        "x_start": 379.2,
        "y": 359.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 水道光熱費⑮  — Row 2: RL_baseline=341.5
    "utilities": {
        "x_start": 379.2,
        "y": 341.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 旅費交通費⑯  — Row 3: RL_baseline=324.1
    "travel": {
        "x_start": 379.2,
        "y": 324.1,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 通信費⑰  — Row 4: RL_baseline=306.6
    "communication": {
        "x_start": 379.2,
        "y": 306.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 広告宣伝費⑱  — Row 5: RL_baseline=289.2
    "advertising": {
        "x_start": 379.2,
        "y": 289.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 接待交際費⑲  — Row 6: RL_baseline=271.7
    "entertainment": {
        "x_start": 379.2,
        "y": 271.7,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 損害保険料⑳  — Row 7: RL_baseline=254.2
    "insurance": {
        "x_start": 379.2,
        "y": 254.2,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 修繕費㉑  — Row 8: RL_baseline=236.8
    "repairs": {
        "x_start": 379.2,
        "y": 236.8,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 消耗品費㉒  — Row 9: RL_baseline=219.3
    "supplies": {
        "x_start": 379.2,
        "y": 219.3,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 福利厚生費㉓  — Row 10: RL_baseline=201.9
    "welfare": {
        "x_start": 379.2,
        "y": 201.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 雑費㉔  — Row 11: RL_baseline=184.4
    "miscellaneous": {
        "x_start": 379.2,
        "y": 184.4,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # --- 合計行 (左列・右列共通位置) ---
    # 経費計㉕ (左列)  — Row 12: RL_baseline=166.9
    "total_expenses": {
        "x_start": 162.7,
        "y": 166.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 経費計㉕ (右列にも同じ値を入れる場合)
    "total_expenses_right": {
        "x_start": 379.2,
        "y": 166.9,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 差引金額㉖  — Row 13: RL_baseline=149.5
    "operating_income": {
        "x_start": 162.7,
        "y": 149.5,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 専従者控除㉗  — Row 14: RL_baseline=132.0
    "family_employee_deduction": {
        "x_start": 162.7,
        "y": 132.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 専従者控除㉗ (右列)
    "family_employee_deduction_right": {
        "x_start": 379.2,
        "y": 132.0,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 所得金額㉘ (左列)  — Row 15: RL_baseline=114.6
    "net_income": {
        "x_start": 162.7,
        "y": 114.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
    # 所得金額㉘ (右列)
    "net_income_right": {
        "x_start": 379.2,
        "y": 114.6,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    },
}

# 収支内訳書の行 RL baseline 一覧（pdfplumber実測値）
_IE_ROW_Y = [
    376.5,
    359.0,
    341.5,
    324.1,
    306.6,
    289.2,
    271.7,
    254.2,
    236.8,
    219.3,
    201.9,
    184.4,
    166.9,
    149.5,
    132.0,
    114.6,
]

# 収支内訳書の収入内訳行 (revenue_N_name/amount) — document.py 互換用
# revenue_0〜4 は左列 Row 0〜4 に対応
for _i in range(5):
    INCOME_EXPENSE_STATEMENT[f"revenue_{_i}_name"] = {
        "x": 90.0,
        "y": _IE_ROW_Y[_i],
        "font_size": 7,
        "type": "text",
    }
    INCOME_EXPENSE_STATEMENT[f"revenue_{_i}_amount"] = {
        "x_start": 162.7,
        "y": _IE_ROW_Y[_i],
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    }

# 収支内訳書の経費行 (expense_N_name/amount) — document.py 互換用
# expense_0〜4 = 左列 Row 7〜11 (給料賃金〜利子割引料)
# expense_5〜14 = 右列 Row 0〜9 (租税公課〜消耗品費)
for _i in range(15):
    if _i < 5:
        _y_val = _IE_ROW_Y[7 + _i]
        _x_name = 90.0
        _x_start = 162.7
    else:
        _y_val = _IE_ROW_Y[_i - 5]
        _x_name = 310.0
        _x_start = 379.2
    INCOME_EXPENSE_STATEMENT[f"expense_{_i}_name"] = {
        "x": _x_name,
        "y": _y_val,
        "font_size": 7,
        "type": "text",
    }
    INCOME_EXPENSE_STATEMENT[f"expense_{_i}_amount"] = {
        "x_start": _x_start,
        "y": _y_val,
        "cell_width": 14.0,
        "num_cells": 7,
        "font_size": 9,
        "type": "digit_cells",
    }


# ============================================================
# Template file names (テンプレートPDFのファイル名)
# ============================================================

# --- 令和7年分 ---
# 国税庁公式PDFを直接テンプレートとして使用。
# ファイルは templates/r07/ に配置する。
# 旧ファイル名（freee由来）をフォールバックとして維持。
TEMPLATE_NAMES: dict[str, str] = {
    "income_tax_p1": "r07/01.pdf",
    "income_tax_p2": "r07/01_p2.pdf",
    "schedule_3": "r07/02.pdf",
    "schedule_4": "r07/03.pdf",
    "blue_return_pl_p1": "r07/10_p1.pdf",
    "blue_return_pl_p2": "r07/10_p2.pdf",
    "blue_return_pl_p3": "r07/10_p3.pdf",
    "blue_return_bs": "r07/10_p4.pdf",
    "income_expense": "r07/05_ie.pdf",
    "consumption_tax_p1": "consumption_tax_p1.pdf",
    "consumption_tax_p2": "consumption_tax_p2.pdf",
    "housing_loan_p1": "r07/14.pdf",
    "housing_loan_p2": "housing_loan_p2.pdf",
}
