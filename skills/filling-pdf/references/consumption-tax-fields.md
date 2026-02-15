# 消費税申告書（Consumption Tax Return）フィールド定義

消費税及び地方消費税の申告書の項目名・データソースの対応表。
座標は `src/shinkoku/tools/pdf_coordinates.py` の `CONSUMPTION_TAX_P1` に定義。
用紙: A4 縦（Portrait）

## ヘッダー

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `taxpayer_name` | 氏名 | `config.taxpayer.last_name + first_name` |
| `fiscal_year` | 課税期間 | `令和{fiscal_year - 2018}年分` |

## 課税方式のチェックボックス

| フィールドキー | 項目名 | 条件 |
|--------------|--------|------|
| `method_standard` | 本則課税 | `method == "standard"` |
| `method_simplified` | 簡易課税 | `method == "simplified"` |
| `method_special_20pct` | 2割特例 | `method == "special_20pct"` |

## 税額の計算

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `taxable_sales_amount` | 課税標準額 | `ConsumptionTaxResult.taxable_sales_total` |
| `tax_on_sales` | 課税標準額に対する消費税額 | `ConsumptionTaxResult.tax_on_sales` |
| `tax_on_purchases` | 控除対象仕入税額 | `ConsumptionTaxResult.tax_on_purchases` |
| `tax_due_national` | 差引税額（国税分） | `ConsumptionTaxResult.tax_due` |
| `local_tax_due` | 地方消費税の課税標準額 | `ConsumptionTaxResult.local_tax_due` |
| `total_tax_due` | 合計納付税額 | `ConsumptionTaxResult.total_due` |

## 計算ロジック（方式別）

### 2割特例
```
消費税額 = 課税標準額に対する消費税額 × 20%
```

### 簡易課税
```
控除対象仕入税額 = 課税標準額に対する消費税額 × みなし仕入率
消費税額 = 課税標準額に対する消費税額 − 控除対象仕入税額
```

### 本則課税
```
消費税額 = 課税売上に係る消費税額 − 課税仕入に係る消費税額
```

## 地方消費税

| 項目名 | 計算方法 |
|--------|---------|
| 地方消費税の課税標準額 | = 差引税額（国税分） |
| 地方消費税額 | = 課税標準額 × 22/78 |

## 端数処理

| 対象 | ルール |
|------|--------|
| 課税標準額 | 1,000円未満切り捨て |
| 消費税額（国税） | 100円未満切り捨て |
| 地方消費税額 | 100円未満切り捨て |

## 注意事項

- 免税事業者は消費税申告不要
- インボイス登録事業者の登録番号も記載が必要 → `config.invoice_registration_number`
- 中間納付がある場合は差引計算する
