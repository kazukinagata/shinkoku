#!/usr/bin/env python3
"""テスト用 xtx ファイル生成スクリプト。

DB/config 依存なしで XtxBuilder を直接使い、テストデータから xtx を生成する。
KOA020（申告書B）、KOA210（青色申告決算書）、KOB130（住宅ローン控除）、KOB060（所得の内訳書）を出力。

使い方:
    uv run python scripts/generate_test_xtx.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from shinkoku.xtx.attachments import (  # noqa: E402
    build_housing_loan_fields,
    build_income_breakdown_fields,
)
from shinkoku.xtx.field_codes import (  # noqa: E402
    DEDUCTION_CODES,
    FORM_VERSIONS,
    INCOME_AMOUNT_CODES,
    INCOME_REVENUE_CODES,
    OTHER_P1_CODES,
    P1_HEADER_IDREFS,
    P2_HEADER_IDREFS,
    PL_CODES,
    TAX_CALCULATION_CODES,
)
from shinkoku.xtx.generator import XtxBuilder  # noqa: E402


def build_test_xtx() -> XtxBuilder:
    """テストデータで XtxBuilder を構築する。"""
    builder = XtxBuilder(tax_type="income", fiscal_year=2025)

    # ---- 納税者情報 ----
    builder.set_taxpayer_info(
        name="永田和樹",
        name_kana="ナガタカズキ",
        address="千葉県千葉市美浜区打瀬2-21 幕張サウスコートA棟 506",
        address_code="12106",  # 千葉市美浜区
        zip_code="2610013",
        tax_office_code="01303",  # 千葉西税務署（XSD enumeration: zeimusho.xsd）
        tax_office_name="千葉西",
        phone="080-4111-1126",
        birthday="1985-11-26",
        occupation="ソフトウェア・情報サービス業",
        business_description="ソフトウェア・情報サービス業",
        # 還付口座
        refund_bank_name="三菱UFJ銀行",
        refund_bank_type="1",  # 銀行
        refund_branch_name="大泉支店",
        refund_branch_type="2",  # 支店
        refund_deposit_type="1",  # 普通
        refund_account_number="5035429",
    )

    # ========================================
    # KOA020: 申告書B 第一表
    # ========================================
    p1_fields: dict[str, int | str] = {}

    # 収入金額等
    p1_fields[INCOME_REVENUE_CODES["business_revenue"]] = 165_000  # ア: 営業等 収入
    p1_fields[INCOME_REVENUE_CODES["salary_revenue"]] = 8_121_000  # オ: 給与 収入

    # 所得金額等
    p1_fields[INCOME_AMOUNT_CODES["business_income"]] = -185_779  # (1): 営業等 所得（赤字）
    p1_fields[INCOME_AMOUNT_CODES["salary_income"]] = 6_208_900  # (6): 給与 所得
    p1_fields[INCOME_AMOUNT_CODES["total_income"]] = 6_023_121  # (12): 合計

    # 所得控除
    p1_fields[DEDUCTION_CODES["social_insurance"]] = 1_145_015  # (15): 社会保険料控除
    p1_fields[DEDUCTION_CODES["life_insurance"]] = 72_636  # (17): 生命保険料控除
    p1_fields[DEDUCTION_CODES["earthquake_insurance"]] = 33_730  # (18): 地震保険料控除
    p1_fields[DEDUCTION_CODES["basic"]] = 630_000  # (25): 基礎控除（令和7年度: 63万円）
    p1_fields[DEDUCTION_CODES["subtotal_13_25"]] = 1_881_381  # (26): 控除小計
    p1_fields[DEDUCTION_CODES["total_deductions"]] = 1_881_381  # (29): 控除合計

    # 税金の計算
    p1_fields[TAX_CALCULATION_CODES["taxable_income"]] = 4_141_000  # (31): 課税所得
    p1_fields[TAX_CALCULATION_CODES["tax_on_taxable_income"]] = 400_700  # (32): 税額
    p1_fields[TAX_CALCULATION_CODES["housing_loan_credit"]] = 140_000  # (34): 住宅ローン控除
    p1_fields[TAX_CALCULATION_CODES["income_tax_after_credits"]] = 260_700  # (37): 差引所得税額
    p1_fields[TAX_CALCULATION_CODES["income_tax_net"]] = 260_700  # (39): 再差引所得税額
    p1_fields[TAX_CALCULATION_CODES["reconstruction_tax"]] = 5_474  # (40): 復興特別所得税
    p1_fields[TAX_CALCULATION_CODES["total_income_tax"]] = 266_174  # (41): 所得税等の額
    p1_fields[TAX_CALCULATION_CODES["withheld_tax"]] = 447_000  # (48): 源泉徴収税額
    p1_fields[TAX_CALCULATION_CODES["tax_due"]] = -180_826  # (49): 申告納税額（負=還付）
    p1_fields[TAX_CALCULATION_CODES["estimated_tax"]] = 195_400  # (50): 予定納税額
    p1_fields[TAX_CALCULATION_CODES["tax_refund"]] = 376_226  # (53): 還付される税金

    # その他
    p1_fields[OTHER_P1_CODES["blue_return_deduction"]] = 0  # 青色申告特別控除額

    builder.add_form(
        "KOA020",
        FORM_VERSIONS["KOA020"],
        p1_fields,
        nesting_key="KOA020-1",
        idrefs=P1_HEADER_IDREFS,
    )

    # ========================================
    # KOA020: 申告書B 第二表
    # ========================================
    p2_fields: dict[str, int | str] = {}
    # 源泉徴収税額の合計
    p2_fields["ABD00070"] = 447_000

    # 所得の内訳（繰り返し）
    income_details = [
        {
            "ABD00020": "営業等",
            "ABD00025": "情報サービス",
            "ABD00040": "（各社）",
            "ABD00050": 165_000,
            "ABD00060": 0,
        },
        {
            "ABD00020": "給与",
            "ABD00025": "給料",
            "ABD00040": "（勤務先）",
            "ABD00050": 8_121_000,
            "ABD00060": 447_000,
        },
    ]

    # 社会保険料等の明細（繰り返し）
    social_insurance_details = [
        {"ABH00130": "源泉徴収票のとおり", "ABH00140": 1_145_015},
    ]

    builder.add_form(
        "KOA020",
        FORM_VERSIONS["KOA020"],
        p2_fields,
        nesting_key="KOA020-2",
        idrefs=P2_HEADER_IDREFS,
        repeating_groups={
            "ABD00010": income_details,
            "ABH00120": social_insurance_details,
        },
    )

    # ========================================
    # KOA210: 青色申告決算書（一般用）PL
    # ========================================
    pl_fields: dict[str, int | str] = {}
    pl_fields[PL_CODES["revenue"]] = 165_000  # 売上金額
    pl_fields[PL_CODES["travel"]] = 8_400  # 旅費交通費
    pl_fields[PL_CODES["communication"]] = 88_969  # 通信費
    pl_fields[PL_CODES["rent"]] = 253_410  # 地代家賃
    pl_fields[PL_CODES["total_expense"]] = 350_779  # 経費計
    pl_fields[PL_CODES["gross_profit"]] = 165_000  # 差引金額（=売上）
    pl_fields[PL_CODES["operating_profit"]] = -185_779  # 差引金額（=売上-経費）
    pl_fields[PL_CODES["pre_deduction_income_upper"]] = -185_779  # 控除前所得
    pl_fields[PL_CODES["blue_return_deduction"]] = 0  # 青色控除額
    pl_fields[PL_CODES["net_income"]] = -185_779  # 所得金額

    # 月別売上は KOA210-2（二面）、地代家賃の内訳は KOA210-3（三面）に属するため
    # PL 一面（KOA210-1）への追加は省略。将来対応時に KOA210-2/3 として add_form する。

    builder.add_form(
        "KOA210",
        FORM_VERSIONS["KOA210"],
        pl_fields,
        nesting_key="KOA210",
    )

    # ========================================
    # KOB130: 住宅借入金等特別控除額の計算明細書
    # ========================================
    kob130_result = build_housing_loan_fields(
        move_in_date="5-07-09-15",  # 令和7年9月15日
        house_acquisition_cost=42_800_000,
        house_total_area="100.63",
        house_living_area="100.63",
        house_real_estate_number="0400001152062",
        tax_rate_category="10pct",
        # 家屋の取得対価（共有持分なし = 全額）
        house_share_amount=42_800_000,
        house_net_amount=42_800_000,
        # 合計
        total_share_amount=42_800_000,
        total_net_amount=42_800_000,
        # 住宅借入金等の年末残高（住宅のみ）
        housing_only_loan_balance=28_139_310,
        housing_only_net_balance=28_139_310,
        housing_only_min_amount=28_139_310,
        housing_only_living_ratio="100",
        housing_only_living_balance=28_139_310,
        total_loan_balance=28_139_310,
        # 控除額
        credit_number="10",  # 令和7年入居、認定住宅（XSD: maxInclusive=12）
        credit_amount=140_000,
    )

    builder.add_form(
        "KOB130",
        FORM_VERSIONS["KOB130"],
        kob130_result["fields"],
        nesting_key="KOB130-1",
        idrefs=kob130_result["idrefs"],
    )

    # ========================================
    # KOB060: 所得の内訳書
    # ========================================
    kob060_result = build_income_breakdown_fields(
        income_items=[
            {
                "income_type": "営業等",
                "category": "情報サービス",
                "payer_name": "（各社）",
                "revenue": 165_000,
                "withheld_tax": 0,
            },
            {
                "income_type": "給与",
                "category": "給料",
                "payer_name": "（勤務先）",
                "revenue": 8_121_000,
                "withheld_tax": 447_000,
            },
        ],
    )

    builder.add_form(
        "KOB060",
        FORM_VERSIONS["KOB060"],
        kob060_result["fields"],
        nesting_key="KOB060",
        idrefs=kob060_result["idrefs"],
        repeating_groups=kob060_result["repeating_groups"],
    )

    return builder


def main() -> int:
    builder = build_test_xtx()

    output_path = Path("output/income_tax_r07.xtx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    builder.save(output_path)

    print("=== xtx 生成完了 ===")
    print(f"出力先: {output_path.resolve()}")
    print()
    print("生成帳票:")
    print(f"  - KOA020 (v{FORM_VERSIONS['KOA020']}): 申告書B 第一表・第二表")
    print(f"  - KOA210 (v{FORM_VERSIONS['KOA210']}): 青色申告決算書（一般用）PL")
    print(f"  - KOB130 (v{FORM_VERSIONS['KOB130']}): 住宅借入金等特別控除額の計算明細書")
    print(f"  - KOB060 (v{FORM_VERSIONS['KOB060']}): 所得の内訳書")
    print()
    print("テストデータ概要:")
    print("  住所: 千葉県千葉市美浜区打瀬2-21 幕張サウスコートA棟 506")
    print("  氏名: 永田和樹")
    print("  事業収入: 165,000円")
    print("  給与収入: 8,121,000円")
    print("  所得合計: 6,023,121円")
    print("  課税所得: 4,141,000円")
    print("  住宅ローン控除: 140,000円")
    print("  還付金額: 376,226円")

    return 0


if __name__ == "__main__":
    sys.exit(main())
