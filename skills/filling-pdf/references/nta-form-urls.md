# 国税庁公式PDF様式URLリスト

各年度の確定申告書様式PDFのダウンロードURL。
新年度は上書きせず追記する。

## 令和7年分（2025年課税年度）

様式・手引き等の一覧ページ: https://www.nta.go.jp/taxes/shiraberu/shinkoku/syotoku/r07.htm

### 所得税関連（r07/ ディレクトリ）

**注意**: NTA のファイル番号は帳票の表番号と一致しない。実際の内容を目視確認済み。

| No. | 帳票名 | ページ数 | URL |
|-----|--------|---------|-----|
| 01 | 確定申告書 第一表 + 第二表 | 4p (p1=第一表, p2=第二表) | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/01.pdf |
| 02 | 確定申告書 第三表（分離課税用） | 2p | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/02.pdf |
| 03 | 確定申告書 第四表（損失申告用） | 4p | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/03.pdf |
| 04 | 確定申告書 第四表の付表 | 6p | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/04.pdf |
| 05 | 収支内訳書（一般用） | 4p (/Rotate=90, landscape表示) | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/05.pdf |
| 10 | 青色申告決算書（一般用） | 8p (/Rotate=90, landscape表示) | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/10.pdf |
| 14 | 住宅借入金等特別控除額の計算明細書 | 2p | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/14.pdf |

### 消費税関連（別ディレクトリ）

| 帳票名 | ページ数 | URL |
|--------|---------|-----|
| 消費税及び地方消費税の申告書（一般用） | 2p (p1=申告書, p2=控) | https://www.nta.go.jp/taxes/tetsuzuki/shinsei/shinkoku/shohi/yoshiki01/17.pdf |

### その他添付書類

| 帳票名 | ページ数 | URL |
|--------|---------|-----|
| 医療費控除の明細書【内訳書】 | 2p | https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/02/pdf/ref1.pdf |

### テンプレートの配置先

ダウンロードしたPDFは `templates/` に配置する（`.gitignore` 対象）。
多ページ PDF は pypdf で必要ページを抽出して使う。

```
templates/
  r07/
    01.pdf       ← 第一表+第二表 (4p) → p1=第一表, p2=第二表
    02.pdf       ← 第三表 (2p)
    03.pdf       ← 第四表 (4p)
    05.pdf       ← 収支内訳書 (4p, /Rotate=90)
    10.pdf       ← 青色申告決算書 (8p, /Rotate=90)
    14.pdf       ← 住宅ローン控除明細書 (2p)
  consumption_tax.pdf  ← 消費税申告書 (2p)
  medical_expense.pdf  ← 医療費控除の明細書 (2p)
```

### TEMPLATE_NAMES マッピング

`pdf_coordinates.py` の `TEMPLATE_NAMES` は抽出済み単ページファイルを参照する。
スキル実行時にダウンロード → ページ抽出 → 配置を行う。

```python
TEMPLATE_NAMES = {
    "income_tax_p1": "r07/01.pdf",            # 01.pdf page 1
    "income_tax_p2": "r07/01_p2.pdf",          # 01.pdf page 2 extracted
    "schedule_4": "r07/03.pdf",                # 03.pdf page 1
    "blue_return_pl_p1": "r07/10_p1.pdf",      # 10.pdf page 1 extracted
    "blue_return_pl_p2": "r07/10_p2.pdf",      # 10.pdf page 2 extracted
    "blue_return_pl_p3": "r07/10_p3.pdf",      # 10.pdf page 3 extracted
    "blue_return_bs": "r07/10_p4.pdf",          # 10.pdf page 4 extracted
    "consumption_tax_p1": "consumption_tax_p1.pdf",  # 17.pdf page 1 extracted
    "consumption_tax_p2": "consumption_tax_p2.pdf",  # 17.pdf page 2 extracted
    "housing_loan_p1": "r07/14.pdf",
}
```

### ダウンロード＆ページ抽出コマンド

```bash
mkdir -p templates/r07

# 所得税関連
curl -o templates/r07/01.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/01.pdf"
curl -o templates/r07/02.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/02.pdf"
curl -o templates/r07/03.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/03.pdf"
curl -o templates/r07/05.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/05.pdf"
curl -o templates/r07/10.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/10.pdf"
curl -o templates/r07/14.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/01/shinkokusho/pdf/r07/14.pdf"

# 消費税
curl -o templates/consumption_tax.pdf "https://www.nta.go.jp/taxes/tetsuzuki/shinsei/shinkoku/shohi/yoshiki01/17.pdf"

# 医療費控除
curl -o templates/medical_expense.pdf "https://www.nta.go.jp/taxes/shiraberu/shinkoku/yoshiki/02/pdf/ref1.pdf"
```

```python
# ページ抽出スクリプト
from pypdf import PdfReader, PdfWriter

def extract_page(src: str, dst: str, page_index: int) -> None:
    reader = PdfReader(src)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_index])
    writer.write(dst)

# 第一表/第二表
extract_page("templates/r07/01.pdf", "templates/r07/01_p2.pdf", 1)

# 青色申告決算書 (10.pdf, 8 pages → p1-p4)
for i in range(4):
    extract_page("templates/r07/10.pdf", f"templates/r07/10_p{i+1}.pdf", i)

# 収支内訳書 (05.pdf → rename for clarity)
import shutil
shutil.copy("templates/r07/05.pdf", "templates/r07/05_ie.pdf")

# 消費税 (2 pages → p1, p2)
extract_page("templates/consumption_tax.pdf", "templates/consumption_tax_p1.pdf", 0)
extract_page("templates/consumption_tax.pdf", "templates/consumption_tax_p2.pdf", 1)

# 医療費控除 (page 1 only)
extract_page("templates/medical_expense.pdf", "templates/medical_expense_p1.pdf", 0)

# 住宅ローン (page 1 only)
extract_page("templates/r07/14.pdf", "templates/r07/14_p1.pdf", 0)
```
