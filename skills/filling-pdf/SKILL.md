---
name: filling-pdf
description: >
  PDF帳票テンプレートへの記入手順を定義するサブエージェント用ワークフロー。
  pdf-form-filler エージェントがこのスキルに従って動作する。
  直接ユーザーが呼び出すスキルではない。
---

# PDF帳票記入ワークフロー（Filling PDF Workflow）

`pdf-form-filler` サブエージェントが従うワークフロー。
国税庁公式PDFテンプレートに計算結果を書き込み、提出用PDFを生成する。

## ステップ1: 入力データの確認

spawn 元から渡された以下のデータを確認する:

1. **帳票種類**: どの帳票を生成するか
2. **テンプレートPDFのパス**: `templates/r07/` 内のファイル
3. **入力データ**: 計算結果 + プロフィール情報
4. **出力先パス**: PDF の出力先

## ステップ2: テンプレートPDFの確認

1. テンプレートPDFが `templates/r07/` に存在するか確認する
2. 存在しない場合は `references/nta-form-urls.md` からURLを取得し、ダウンロードする:
   ```bash
   curl -o templates/r07/{filename}.pdf {url}
   ```
3. ダウンロード後、ファイルが正しいPDFであることを確認する

## ステップ3: フィールド → データソース対応の確認

帳票種類に応じた reference ファイルを Read ツールで読み込む:

| 帳票種類 | Reference ファイル |
|---------|-------------------|
| 確定申告書 第一表 | `references/form-b-p1-fields.md` |
| 確定申告書 第二表 | `references/form-b-p2-fields.md` |
| 青色申告決算書 損益計算書 | `references/blue-return-pl-fields.md` |
| 青色申告決算書 貸借対照表 | `references/blue-return-bs-fields.md` |
| 第三表（分離課税） | `references/schedule-3-fields.md` |
| 第四表（損失申告） | `references/schedule-4-fields.md` |
| 収支内訳書 | `references/income-expense-fields.md` |
| 消費税申告書 | `references/consumption-tax-fields.md` |
| 医療費控除の明細書 | （reference ファイルなし — 座標定義を直接参照） |
| 住宅ローン控除計算明細書 | （reference ファイルなし — 座標定義を直接参照） |

## ステップ4: 座標定義の確認

`src/shinkoku/tools/pdf_coordinates.py` を Read ツールで読み込み、
対応する座標定義辞書を確認する:

| 帳票種類 | 座標定義辞書 |
|---------|------------|
| 確定申告書 第一表 | `INCOME_TAX_P1` |
| 確定申告書 第二表 | `INCOME_TAX_P2` |
| 青色申告決算書 損益計算書 P1 | `BLUE_RETURN_PL_P1` |
| 青色申告決算書 損益計算書 P2 | `BLUE_RETURN_PL_P2` |
| 青色申告決算書 損益計算書 P3 | `BLUE_RETURN_PL_P3` |
| 青色申告決算書 貸借対照表 | `BLUE_RETURN_BS` |
| 第三表（分離課税） | `SCHEDULE_3_FORM` |
| 第四表（損失申告） | `SCHEDULE_4_FORM` |
| 消費税申告書 P1 | `CONSUMPTION_TAX_P1` |
| 消費税申告書 P2 | `CONSUMPTION_TAX_P2` |
| 収支内訳書 | `INCOME_EXPENSE_STATEMENT` |
| 医療費控除の明細書 | `MEDICAL_EXPENSE_DETAIL_FORM` |
| 住宅ローン控除計算明細書 | `HOUSING_LOAN_DETAIL_FORM` |

## ステップ5: PDF生成の実行

`src/shinkoku/tools/document.py` の既存ビルダー関数を使用する。
各帳票に対応する関数:

| 帳票種類 | 生成関数 |
|---------|---------|
| 確定申告書 第一表 | `generate_income_tax_pdf()` |
| 確定申告書 第二表 | `generate_income_tax_page2_pdf()` |
| 青色申告決算書 PL/BS | `generate_bs_pl_pdf()` |
| 消費税申告書 | `generate_consumption_tax_pdf()` |
| 収支内訳書 | `generate_income_expense_statement_pdf()` |
| 医療費控除明細書 | `generate_medical_expense_detail_pdf()` |
| 住宅ローン控除明細書 | `generate_housing_loan_detail_pdf()` |
| 第三表 | `generate_schedule_3_pdf()` |
| 第四表 | `generate_schedule_4_pdf()` |
| 全帳票セット | `generate_full_tax_document_set()` |

### 生成方法

既存のビルダー関数を Bash ツールで Python スクリプトとして実行する:

```python
from shinkoku.tools.document import generate_income_tax_pdf
from shinkoku.models import IncomeTaxResult

result = IncomeTaxResult(
    fiscal_year=2025,
    # ... 計算結果の値
)

path = generate_income_tax_pdf(
    tax_result=result,
    output_path="output/income_tax_p1_2025.pdf",
    config_path="shinkoku.config.yaml",
)
print(f"Generated: {path}")
```

## ステップ6: プレビューと検証

1. `pdf_to_images()` で PDF を PNG 画像に変換する:
   ```python
   from shinkoku.tools.pdf_utils import pdf_to_images
   images = pdf_to_images("output/income_tax_p1_2025.pdf", "output/")
   ```
2. 生成された画像を Read ツールで確認する
3. 記入内容が正しい位置に表示されているか検証する
4. 枠からはみ出しやずれがある場合は報告する

## ステップ7: 完了報告

生成結果をまとめて報告する:

- 生成したファイルのパス
- 生成したページ数
- プレビュー画像のパス
- 検証結果（問題があれば詳細）

## 使用可能な描画関数（pdf_utils.py）

| 関数 | 用途 |
|------|------|
| `draw_text(c, x, y, text, font_size)` | テキスト描画 |
| `draw_number(c, x, y, value, font_size)` | 右寄せ数値（カンマ区切り） |
| `draw_checkbox(c, x, y, checked, size)` | チェックボックス |
| `draw_digit_cells(c, x_start, y, value, cell_width, num_cells, font_size)` | 桁別セル（金額欄） |
| `create_overlay(fields, page_size)` | オーバーレイPDF生成 |
| `merge_overlay(template_path, overlay_bytes, output_path)` | テンプレートとマージ |
| `pdf_to_images(pdf_path, output_dir, dpi)` | PDF→PNG変換 |
