# 青色申告決算書 損益計算書（Blue Return P/L）フィールド定義

国税庁公式様式の項目名・データソースの対応表。
座標は `src/shinkoku/tools/pdf_coordinates.py` の `BLUE_RETURN_PL_P1` に定義。
用紙: A4 横（Landscape）

## ヘッダー

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `taxpayer_name` | 氏名 | `config.taxpayer.last_name + first_name` |
| `fiscal_year` | 年分 | `令和{fiscal_year - 2018}年分` |

## 売上（収入）金額

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `total_revenue` | 売上（収入）金額合計 | `PLResult.total_revenue` |

## 経費の内訳

| フィールドキー | 勘定科目名 | 対応する勘定科目コード |
|--------------|-----------|-------------------|
| `rent` | 地代家賃/賃借料 | 5101 |
| `communication` | 通信費 | 5120 |
| `travel` | 旅費交通費 | 5130 |
| `depreciation` | 減価償却費 | 5200 |
| `supplies` | 消耗品費 | 5150 |
| `outsourcing` | 外注工賃/外注費 | 5250 |
| `utilities` | 水道光熱費 | 5140 |
| `advertising` | 広告宣伝費 | 5160 |
| `miscellaneous` | 雑費 | 5900 |

### 勘定科目名 → フィールドキーのマッピング

`document.py` の `_EXPENSE_FIELD_MAP` に定義:

```python
_EXPENSE_FIELD_MAP = {
    "地代家賃": "rent",
    "賃借料": "rent",
    "通信費": "communication",
    "旅費交通費": "travel",
    "減価償却費": "depreciation",
    "消耗品費": "supplies",
    "外注工賃": "outsourcing",
    "外注費": "outsourcing",
    "水道光熱費": "utilities",
    "広告宣伝費": "advertising",
    "雑費": "miscellaneous",
}
```

## 合計

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `total_expenses` | 経費合計 | `PLResult.total_expense` |
| `net_income` | 差引金額（青色申告特別控除前の所得金額） | `PLResult.net_income` |

## 棚卸関連

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `beginning_inventory` | 期首棚卸高 | `InventoryRecord (period=beginning)` |
| `ending_inventory` | 期末棚卸高 | `InventoryRecord (period=ending)` |

## 注意事項

- 金額は digit_cells 方式（桁別セル）で記入する
- 経費で該当しない科目は空欄（値を設定しない）
- 決算書は P1（損益計算書）〜 P3（月別売上・給料）+ P4（貸借対照表）の4ページ構成
- P2, P3 は現在未実装（将来のPhaseで対応予定）
