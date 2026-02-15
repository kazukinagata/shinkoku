# 収支内訳書（Income/Expense Statement）フィールド定義

白色申告者が使用する収支内訳書の項目名・データソースの対応表。
座標は `src/shinkoku/tools/pdf_coordinates.py` の `INCOME_EXPENSE_STATEMENT` に定義。
用紙: A4 縦（Portrait）

## ヘッダー

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `taxpayer_name` | 氏名 | `config.taxpayer.last_name + first_name` |
| `fiscal_year` | 年分 | `令和{fiscal_year - 2018}年分` |

## 収入金額（最大5行）

各行のフィールドキー: `revenue_{n}_name`, `revenue_{n}_amount` (n=1..5)

| 列 | 項目名 | データソース |
|----|--------|-------------|
| 科目名 | 売上、雑収入等 | `PLResult.revenues[n].account_name` |
| 金額 | 収入金額 | `PLResult.revenues[n].amount` |

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `total_revenue` | 収入金額合計 | `PLResult.total_revenue` |

## 経費（最大15行）

各行のフィールドキー: `expense_{n}_name`, `expense_{n}_amount` (n=1..15)

| 列 | 項目名 | データソース |
|----|--------|-------------|
| 科目名 | 地代家賃、通信費等 | `PLResult.expenses[n].account_name` |
| 金額 | 経費金額 | `PLResult.expenses[n].amount` |

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `total_expenses` | 経費合計 | `PLResult.total_expense` |

## 差引金額

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `net_income` | 差引金額（所得金額） | `PLResult.net_income` |

## 注意事項

- 白色申告者は青色申告決算書ではなく収支内訳書を提出する
- 貸借対照表は不要
- 青色申告特別控除は適用不可
- `config.filing.return_type == "white"` の場合にこの帳票を使用する
