# shinkoku システム概要書

電子帳簿保存法施行規則第2条第2項第1号に基づく「システム関係書類等」として作成。

## 1. システムの概要

| 項目 | 内容 |
|------|------|
| システム名 | shinkoku（確定申告自動化 CLI） |
| 目的 | 個人事業主・会社員の所得税・消費税の確定申告を支援する帳簿管理・税額計算システム |
| 動作環境 | Python 3.11 以上 |
| データベース | SQLite（WAL モード） |
| インターフェース | CLI（`shinkoku` コマンド） |
| データ入出力 | JSON 形式（stdin/stdout） |

### 対象範囲

- 複式簿記による帳簿管理（仕訳帳・総勘定元帳・残高試算表・損益計算書・貸借対照表）
- 所得税の税額計算（事業所得・給与所得・雑所得等）
- 消費税の計算（2割特例・簡易課税・本則課税）
- 各種控除の計算（青色申告特別控除・生命保険料控除・医療費控除等）
- データ取込（CSV・レシート OCR・請求書 OCR）

## 2. データベース構造

データは SQLite データベースファイル（`.db`）に格納される。接続時に以下の PRAGMA が設定される:

```
PRAGMA journal_mode=WAL     -- 書き込み前ログ方式（読み取り並行性向上）
PRAGMA foreign_keys=ON      -- 外部キー制約の有効化
```

### テーブル一覧

| テーブル名 | 役割 | 主なカラム |
|-----------|------|-----------|
| `fiscal_years` | 年度管理 | year, status (open/closed) |
| `accounts` | 勘定科目マスタ | code, name, category (asset/liability/equity/revenue/expense) |
| `journals` | 仕訳ヘッダ | id, fiscal_year, date, description, content_hash, source |
| `journal_lines` | 仕訳明細（借方・貸方） | journal_id, side (debit/credit), account_code, amount, tax_category |
| `journal_audit_log` | 仕訳の訂正・削除履歴 | journal_id, operation (update/delete), before/after データ |
| `fixed_assets` | 固定資産台帳 | name, acquisition_date, acquisition_cost, useful_life, method |
| `deductions` | 控除情報 | fiscal_year, type, amount |
| `withholding_slips` | 源泉徴収票データ | payer_name, payment_amount, withheld_tax 他 |
| `import_sources` | インポート元ファイル管理 | file_hash, file_name（再インポート防止） |
| `business_withholding` | 事業所得の源泉徴収 | client_name, gross_amount, withholding_tax |
| `loss_carryforward` | 損失繰越 | loss_year, amount, used_amount |
| `medical_expense_details` | 医療費明細 | date, patient_name, medical_institution, amount |
| `rent_details` | 地代家賃の内訳 | landlord_name, monthly_rent, annual_rent, business_ratio |
| `housing_loan_details` | 住宅ローン控除詳細 | housing_type, year_end_balance |
| `furusato_donations` | ふるさと納税寄附データ | municipality_name, amount, date |
| `spouse_info` | 配偶者情報 | name, date_of_birth, income |
| `dependents` | 扶養親族 | name, relationship, date_of_birth, income |
| `other_income_items` | その他所得 | income_type, revenue, expenses |
| `crypto_income_records` | 仮想通貨取引 | exchange_name, gains, expenses |
| `opening_balances` | 期首残高 | account_code, amount |

### 勘定科目コード体系

| コード範囲 | 分類 |
|-----------|------|
| 1xxx | 資産（asset） |
| 2xxx | 負債（liability） |
| 3xxx | 純資産（equity） |
| 4xxx | 収益（revenue） |
| 5xxx | 費用（expense） |

### データの整合性

- 全テーブルで外部キー制約（`FOREIGN KEY ... REFERENCES`）を使用
- 仕訳明細は `ON DELETE CASCADE` で仕訳ヘッダ削除時に自動削除
- 金額は全て整数（円単位の `INTEGER`）で管理（浮動小数点不使用）
- 重複取引検出: 仕訳の content_hash（SHA-256）に UNIQUE 制約

## 3. 帳簿の種類と出力方法

### 帳簿一覧

| 帳簿 | 出力コマンド | 説明 |
|------|------------|------|
| 仕訳帳 | `shinkoku ledger search --db-path <db> --input <params.json>` | 仕訳の一覧・検索 |
| 総勘定元帳 | `shinkoku ledger general-ledger --db-path <db> --fiscal-year <year> --account-code <code>` | 勘定科目別の取引一覧 |
| 残高試算表 | `shinkoku ledger trial-balance --db-path <db> --fiscal-year <year>` | 全勘定科目の借方・貸方残高 |
| 損益計算書 | `shinkoku ledger profit-loss --db-path <db> --fiscal-year <year>` | 収益・費用の集計 |
| 貸借対照表 | `shinkoku ledger balance-sheet --db-path <db> --fiscal-year <year>` | 資産・負債・純資産の集計 |

### 出力形式

全コマンドの出力は JSON 形式で標準出力に出力される。出力例:

```json
{
  "status": "ok",
  "data": { ... }
}
```

エラー時:

```json
{
  "status": "error",
  "message": "エラーの詳細"
}
```

## 4. 入力方法

### 仕訳の登録

```bash
# JSON ファイルで仕訳データを指定
shinkoku ledger journal-add --db-path shinkoku.db --input journal.json
```

`journal.json` の形式:

```json
{
  "fiscal_year": 2025,
  "entry": {
    "date": "2025-01-15",
    "description": "事務用品購入",
    "counterparty": "株式会社ABC",
    "lines": [
      {"side": "debit", "account_code": "5401", "amount": 1000},
      {"side": "credit", "account_code": "1101", "amount": 1000}
    ]
  }
}
```

### データ取込

| 取込元 | コマンド | 説明 |
|--------|---------|------|
| CSV | `shinkoku import csv --file-path <csv>` | 銀行明細等の CSV 取込 |
| レシート | `shinkoku import receipt --file-path <image>` | レシート画像の OCR 取込 |
| 請求書 | `shinkoku import invoice --file-path <image>` | 請求書画像の OCR 取込 |

### 仕訳の訂正・削除

```bash
# 仕訳の訂正（変更前データは journal_audit_log に自動記録）
shinkoku ledger journal-update --db-path shinkoku.db --journal-id 42 --input updated.json

# 仕訳の削除（削除前データは journal_audit_log に自動記録）
shinkoku ledger journal-delete --db-path shinkoku.db --journal-id 42
```

## 5. データの保存方法

### ファイル構成

| ファイル | 内容 |
|---------|------|
| `shinkoku.db` | メインデータベースファイル |
| `shinkoku.db-wal` | WAL（Write-Ahead Log）ファイル（自動生成） |
| `shinkoku.db-shm` | 共有メモリファイル（自動生成） |

### 保存場所

データベースファイルは `--db-path` 引数で指定されたパスに保存される。デフォルトの場所は `shinkoku.db`（カレントディレクトリ）。

### WAL モード

SQLite の WAL（Write-Ahead Logging）モードを使用。書き込み中も読み取りが可能で、データの安全性が確保される。

## 6. 検索方法

`shinkoku ledger search` コマンドで仕訳を検索する。検索条件は JSON ファイルで指定:

### 検索パラメータ

| パラメータ | 型 | 説明 | 必須 |
|-----------|-----|------|------|
| `fiscal_year` | int | 会計年度 | 必須 |
| `date_from` | str | 開始日（ISO形式: "2025-01-01"） | 任意 |
| `date_to` | str | 終了日（ISO形式: "2025-12-31"） | 任意 |
| `account_code` | str | 勘定科目コード | 任意 |
| `description_contains` | str | 摘要の部分一致検索 | 任意 |
| `counterparty_contains` | str | 取引先名の部分一致検索 | 任意 |
| `amount_min` | int | 金額下限（円） | 任意 |
| `amount_max` | int | 金額上限（円） | 任意 |
| `source` | str | データソース（csv_import, receipt_ocr, invoice_ocr, manual, adjustment） | 任意 |
| `limit` | int | 取得件数上限（デフォルト: 100） | 任意 |
| `offset` | int | オフセット（ページング用） | 任意 |

### 検索例

```json
{
  "fiscal_year": 2025,
  "date_from": "2025-04-01",
  "date_to": "2025-06-30",
  "counterparty_contains": "ABC",
  "amount_min": 10000,
  "amount_max": 100000,
  "limit": 50
}
```

上記は「2025年度の4月〜6月、取引先名に"ABC"を含む、金額10,000円〜100,000円の仕訳」を検索する。
日付・金額の範囲指定検索、および複数条件の組合せ検索に対応。

## 7. データのバックアップ

### バックアップ手順

SQLite データベースファイルをコピーすることでバックアップできる:

```bash
# データベースファイルをコピー
cp shinkoku.db shinkoku.db.backup.$(date +%Y%m%d)
```

**注意**: WAL モード使用時は、`.db-wal` と `.db-shm` ファイルも同時にコピーすること。または、コピー前にチェックポイントを実行:

```bash
sqlite3 shinkoku.db "PRAGMA wal_checkpoint(TRUNCATE);"
cp shinkoku.db shinkoku.db.backup.$(date +%Y%m%d)
```

### 復元手順

```bash
# バックアップファイルをリストア
cp shinkoku.db.backup.20250101 shinkoku.db
```

## 8. 監査証跡

仕訳の訂正・削除は `journal_audit_log` テーブルに自動的に記録される。

### 記録される情報

| 項目 | 内容 |
|------|------|
| journal_id | 対象の仕訳ID |
| operation | 操作種別（update: 訂正、delete: 削除） |
| before_* | 変更前の日付・摘要・取引先・仕訳明細（JSON） |
| after_* | 変更後のデータ（訂正の場合のみ） |
| created_at | 操作日時 |

### 監査ログの参照

```bash
shinkoku ledger audit-log --db-path shinkoku.db --journal-id 42
```

---

## 改訂履歴

| 日付 | 内容 |
|------|------|
| 2026-02-26 | 初版作成 |
