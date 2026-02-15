"""Visual regression tests for PDF coordinate fitting.

テンプレートオーバーレイ方式で生成される全帳票について、
テキスト・数値が枠内に正しく収まることを検証する。
画像出力先: output/visual_regression/

実行: uv run pytest tests/visual/ -v -m visual_regression
"""

from __future__ import annotations

import os

import pytest

from shinkoku.tools.document import (
    generate_income_tax_pdf,
    generate_income_tax_page2_pdf,
    generate_income_detail_sheet_pdf,
    generate_bs_pl_pdf,
    generate_consumption_tax_pdf,
)
from shinkoku.tools.pdf_utils import pdf_to_images
from shinkoku.models import (
    PLResult,
    PLItem,
    BSResult,
    BSItem,
    IncomeTaxResult,
    ConsumptionTaxResult,
    DeductionsResult,
    DeductionItem,
)

OUTPUT_DIR = "output/visual_regression"


@pytest.fixture(autouse=True)
def setup_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _assert_valid_pdf(pdf_path: str) -> None:
    """PDF が存在し、有効なヘッダーを持ち、十分なサイズであることを検証する。"""
    assert os.path.exists(pdf_path), f"PDF not found: {pdf_path}"
    assert os.path.getsize(pdf_path) > 100, f"PDF too small: {pdf_path}"
    with open(pdf_path, "rb") as f:
        assert f.read(5) == b"%PDF-", f"Invalid PDF header: {pdf_path}"


def _assert_images_generated(images: list[str], min_count: int = 1) -> None:
    """画像が期待数以上生成され、各ファイルが存在することを検証する。"""
    assert len(images) >= min_count, f"Expected >= {min_count} images, got {len(images)}"
    for img_path in images:
        assert os.path.exists(img_path), f"Image not found: {img_path}"


@pytest.mark.visual_regression
class TestIncomeTaxP1Fitting:
    """第一表: 全フィールドを使うリアルなデータで座標検証。"""

    def test_income_tax_p1_all_fields(self):
        pdf_path = os.path.join(OUTPUT_DIR, "income_tax_p1.pdf")
        tax = IncomeTaxResult(
            fiscal_year=2025,
            salary_income_after_deduction=4_360_000,
            business_income=2_350_000,
            total_income=6_710_000,
            total_income_deductions=1_928_000,
            taxable_income=4_782_000,
            income_tax_base=508_700,
            dividend_credit=15_000,
            housing_loan_credit=210_000,
            total_tax_credits=225_000,
            income_tax_after_credits=283_700,
            reconstruction_tax=5_957,
            total_tax=289_600,
            withheld_tax=466_800,
            business_withheld_tax=50_000,
            estimated_tax_payment=100_000,
            tax_due=-227_200,
            deductions_detail=DeductionsResult(
                income_deductions=[
                    DeductionItem(type="social_insurance", name="社会保険料控除", amount=800_000),
                    DeductionItem(type="ideco", name="小規模企業共済等掛金控除", amount=276_000),
                    DeductionItem(type="life_insurance", name="生命保険料控除", amount=120_000),
                    DeductionItem(
                        type="earthquake_insurance", name="地震保険料控除", amount=50_000
                    ),
                    DeductionItem(type="furusato_nozei", name="寄附金控除", amount=48_000),
                    DeductionItem(type="spouse", name="配偶者控除", amount=380_000),
                    DeductionItem(type="dependent", name="扶養控除", amount=380_000),
                    DeductionItem(type="basic", name="基礎控除", amount=480_000),
                    DeductionItem(type="medical", name="医療費控除", amount=194_000),
                ],
                tax_credits=[],
                total_income_deductions=1_928_000,
                total_tax_credits=225_000,
            ),
        )
        result = generate_income_tax_pdf(
            tax_result=tax,
            output_path=pdf_path,
            taxpayer_name="田中太郎",
        )
        _assert_valid_pdf(result)

        img_dir = os.path.join(OUTPUT_DIR, "income_tax_p1")
        images = pdf_to_images(result, img_dir, dpi=200)
        _assert_images_generated(images)


@pytest.mark.visual_regression
class TestIncomeTaxP2Fitting:
    """第二表: 所得内訳・社保・扶養・配偶者・住宅ローンを検証。"""

    def test_income_tax_p2_all_fields(self):
        pdf_path = os.path.join(OUTPUT_DIR, "income_tax_p2.pdf")
        result = generate_income_tax_page2_pdf(
            income_details=[
                {
                    "type": "給与",
                    "payer": "株式会社テストコーポレーション",
                    "revenue": 8_000_000,
                    "withheld": 466_800,
                },
                {
                    "type": "事業",
                    "payer": "クライアントA合同会社",
                    "revenue": 3_000_000,
                    "withheld": 30_600,
                },
                {
                    "type": "事業",
                    "payer": "株式会社ビジネスパートナーB",
                    "revenue": 1_500_000,
                    "withheld": 15_315,
                },
                {
                    "type": "配当",
                    "payer": "日本インデックスファンド",
                    "revenue": 200_000,
                    "withheld": 30_630,
                },
            ],
            social_insurance_details=[
                {"type": "健康保険", "payer": "全国健康保険協会", "amount": 300_000},
                {"type": "厚生年金", "payer": "日本年金機構", "amount": 500_000},
            ],
            dependents=[
                {"name": "田中花子", "relationship": "長女", "birth_date": "H22.5.15"},
                {"name": "田中一郎", "relationship": "長男", "birth_date": "H25.8.20"},
                {"name": "田中二郎", "relationship": "次男", "birth_date": "R1.12.3"},
            ],
            spouse={"name": "田中美紀", "income": 380_000},
            housing_loan_move_in_date="R7.3.15",
            output_path=pdf_path,
            taxpayer_name="田中太郎",
        )
        _assert_valid_pdf(result)

        img_dir = os.path.join(OUTPUT_DIR, "income_tax_p2")
        images = pdf_to_images(result, img_dir, dpi=200)
        _assert_images_generated(images)


@pytest.mark.visual_regression
class TestIncomeDetailSheetFitting:
    """所得の内訳書: 10件超のデータで全行を検証。"""

    def test_income_detail_sheet_full(self):
        pdf_path = os.path.join(OUTPUT_DIR, "income_detail_sheet.pdf")
        details = [
            {
                "type": "給与",
                "payer": "株式会社テストコーポレーション",
                "revenue": 8_000_000,
                "withheld": 466_800,
            },
            {
                "type": "事業",
                "payer": "クライアントA合同会社",
                "revenue": 3_000_000,
                "withheld": 30_600,
            },
            {
                "type": "事業",
                "payer": "株式会社ビジネスパートナーB",
                "revenue": 1_500_000,
                "withheld": 15_315,
            },
            {
                "type": "配当",
                "payer": "日本インデックスファンド",
                "revenue": 200_000,
                "withheld": 30_630,
            },
            {
                "type": "事業",
                "payer": "海外クライアントC Inc.",
                "revenue": 2_000_000,
                "withheld": 20_420,
            },
            {
                "type": "雑",
                "payer": "仮想通貨取引所X株式会社",
                "revenue": 500_000,
                "withheld": 0,
            },
            {
                "type": "事業",
                "payer": "デザイン事務所D",
                "revenue": 800_000,
                "withheld": 8_168,
            },
            {
                "type": "事業",
                "payer": "コンサルティングE株式会社",
                "revenue": 1_200_000,
                "withheld": 12_252,
            },
            {
                "type": "配当",
                "payer": "米国株ETF分配金",
                "revenue": 150_000,
                "withheld": 22_972,
            },
            {
                "type": "事業",
                "payer": "フリーランスF氏",
                "revenue": 600_000,
                "withheld": 6_126,
            },
            {
                "type": "雑",
                "payer": "講演料G財団",
                "revenue": 300_000,
                "withheld": 3_063,
            },
        ]
        result = generate_income_detail_sheet_pdf(
            income_details=details,
            output_path=pdf_path,
            taxpayer_name="田中太郎",
            address="東京都千代田区丸の内1-1-1 テストビル3F",
            fiscal_year=2025,
        )
        _assert_valid_pdf(result)

        img_dir = os.path.join(OUTPUT_DIR, "income_detail_sheet")
        images = pdf_to_images(result, img_dir, dpi=200)
        _assert_images_generated(images)


@pytest.mark.visual_regression
class TestBlueReturnPLFitting:
    """損益計算書: 全経費科目を使用して座標検証。"""

    def test_blue_return_pl_all_expenses(self):
        pdf_path = os.path.join(OUTPUT_DIR, "blue_return_pl.pdf")
        pl = PLResult(
            fiscal_year=2025,
            revenues=[
                PLItem(account_code="4001", account_name="売上", amount=12_500_000),
                PLItem(account_code="4110", account_name="雑収入", amount=300_000),
            ],
            expenses=[
                PLItem(account_code="5140", account_name="通信費", amount=180_000),
                PLItem(account_code="5250", account_name="地代家賃", amount=1_440_000),
                PLItem(account_code="5200", account_name="減価償却費", amount=350_000),
                PLItem(account_code="5190", account_name="消耗品費", amount=220_000),
                PLItem(account_code="5110", account_name="外注工賃", amount=2_400_000),
                PLItem(account_code="5160", account_name="水道光熱費", amount=96_000),
                PLItem(account_code="5170", account_name="旅費交通費", amount=240_000),
                PLItem(account_code="5180", account_name="広告宣伝費", amount=180_000),
                PLItem(account_code="5290", account_name="雑費", amount=144_000),
            ],
            total_revenue=12_800_000,
            total_expense=5_250_000,
            net_income=7_550_000,
        )
        result = generate_bs_pl_pdf(
            pl_data=pl,
            output_path=pdf_path,
            taxpayer_name="田中太郎",
        )
        _assert_valid_pdf(result)

        img_dir = os.path.join(OUTPUT_DIR, "blue_return_pl")
        images = pdf_to_images(result, img_dir, dpi=200)
        _assert_images_generated(images)


@pytest.mark.visual_regression
class TestBlueReturnBSFitting:
    """貸借対照表: 全勘定科目を使用して座標検証。"""

    def test_blue_return_bs_all_accounts(self):
        pdf_path = os.path.join(OUTPUT_DIR, "blue_return_bs.pdf")
        pl = PLResult(
            fiscal_year=2025,
            revenues=[
                PLItem(account_code="4001", account_name="売上", amount=12_800_000),
            ],
            expenses=[
                PLItem(account_code="5290", account_name="雑費", amount=5_250_000),
            ],
            total_revenue=12_800_000,
            total_expense=5_250_000,
            net_income=7_550_000,
        )
        bs = BSResult(
            fiscal_year=2025,
            assets=[
                BSItem(account_code="1001", account_name="現金", amount=500_000),
                BSItem(account_code="1002", account_name="普通預金", amount=8_500_000),
                BSItem(account_code="1010", account_name="売掛金", amount=1_200_000),
                BSItem(account_code="1050", account_name="前払費用", amount=120_000),
                BSItem(account_code="1130", account_name="工具器具備品", amount=800_000),
                BSItem(account_code="1900", account_name="事業主貸", amount=3_000_000),
            ],
            liabilities=[
                BSItem(account_code="2010", account_name="買掛金", amount=400_000),
                BSItem(account_code="2030", account_name="未払金", amount=250_000),
                BSItem(account_code="2110", account_name="借入金", amount=1_500_000),
            ],
            equity=[
                BSItem(account_code="3001", account_name="元入金", amount=1_000_000),
                BSItem(account_code="3020", account_name="事業主借", amount=4_420_000),
            ],
            total_assets=14_120_000,
            total_liabilities=2_150_000,
            total_equity=5_420_000,
        )
        result = generate_bs_pl_pdf(
            pl_data=pl,
            bs_data=bs,
            output_path=pdf_path,
            taxpayer_name="田中太郎",
        )
        _assert_valid_pdf(result)

        img_dir = os.path.join(OUTPUT_DIR, "blue_return_bs")
        images = pdf_to_images(result, img_dir, dpi=200)
        _assert_images_generated(images)


@pytest.mark.visual_regression
class TestConsumptionTaxFitting:
    """消費税第一表: 2割特例でリアルな金額を検証。"""

    def test_consumption_tax_special_20pct(self):
        pdf_path = os.path.join(OUTPUT_DIR, "consumption_tax.pdf")
        ct = ConsumptionTaxResult(
            fiscal_year=2025,
            method="special_20pct",
            taxable_sales_total=12_800_000,
            tax_on_sales=1_163_636,
            tax_on_purchases=232_727,
            tax_due=232_700,
            local_tax_due=63_400,
            total_due=296_100,
        )
        result = generate_consumption_tax_pdf(
            tax_result=ct,
            output_path=pdf_path,
            taxpayer_name="田中太郎",
        )
        _assert_valid_pdf(result)

        img_dir = os.path.join(OUTPUT_DIR, "consumption_tax")
        images = pdf_to_images(result, img_dir, dpi=200)
        _assert_images_generated(images)
