# 青色申告決算書 貸借対照表（Blue Return B/S）フィールド定義

国税庁公式様式の項目名・データソースの対応表。
座標は `src/shinkoku/tools/pdf_coordinates.py` の `BLUE_RETURN_BS` に定義。
用紙: A4 横（Landscape）

## ヘッダー

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `taxpayer_name` | 氏名 | `config.taxpayer.last_name + first_name` |
| `fiscal_year_end` | 期末日 | `令和{fiscal_year - 2018}年12月31日` |

## 資産の部

| フィールドキー | 勘定科目名 | 対応する勘定科目コード | データソース |
|--------------|-----------|-------------------|-------------|
| `cash` | 現金 | 1001 | `BSResult.assets` |
| `bank_deposit` | 普通預金/当座預金 | 1002/1003 | `BSResult.assets` |
| `accounts_receivable` | 売掛金 | 1010 | `BSResult.assets` |
| `prepaid` | 前払費用/前払金 | 1041/1040 | `BSResult.assets` |
| `buildings` | 建物 | 1100 | `BSResult.assets` |
| `equipment` | 工具器具備品/車両運搬具 | 1120/1110 | `BSResult.assets` |
| `owner_drawing` | 事業主貸 | 1200 | `BSResult.assets` |
| `total_assets` | 資産合計 | — | `BSResult.total_assets` |

### 勘定科目名 → フィールドキーのマッピング

`document.py` の `_ASSET_FIELD_MAP` に定義:

```python
_ASSET_FIELD_MAP = {
    "現金": "cash",
    "普通預金": "bank_deposit",
    "当座預金": "bank_deposit",
    "売掛金": "accounts_receivable",
    "前払費用": "prepaid",
    "前払金": "prepaid",
    "建物": "buildings",
    "工具器具備品": "equipment",
    "器具備品": "equipment",
    "車両運搬具": "equipment",
    "事業主貸": "owner_drawing",
}
```

## 負債の部

| フィールドキー | 勘定科目名 | 対応する勘定科目コード | データソース |
|--------------|-----------|-------------------|-------------|
| `accounts_payable` | 買掛金 | 2001 | `BSResult.liabilities` |
| `unpaid` | 未払金/未払費用 | 2030/2031 | `BSResult.liabilities` |
| `borrowings` | 借入金/長期借入金 | 2050/2051 | `BSResult.liabilities` |
| `total_liabilities` | 負債合計 | — | `BSResult.total_liabilities` |

### 勘定科目名 → フィールドキーのマッピング

```python
_LIABILITY_FIELD_MAP = {
    "買掛金": "accounts_payable",
    "未払金": "unpaid",
    "未払費用": "unpaid",
    "借入金": "borrowings",
    "長期借入金": "borrowings",
}
```

## 純資産（資本）の部

| フィールドキー | 勘定科目名 | 対応する勘定科目コード | データソース |
|--------------|-----------|-------------------|-------------|
| `capital` | 元入金 | 3001 | `BSResult.equity` |
| `owner_investment` | 事業主借 | 3010 | `BSResult.equity` |
| `total_equity` | 純資産合計 | — | `BSResult.total_equity` |

### 勘定科目名 → フィールドキーのマッピング

```python
_EQUITY_FIELD_MAP = {
    "元入金": "capital",
    "事業主借": "owner_investment",
}
```

## 検証ルール

- **貸借一致**: `total_assets == total_liabilities + total_equity` が成立すること
- 一致しない場合は差額を報告し、決算整理仕訳の見直しを促す
