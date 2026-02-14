---
name: setup
description: >
  This skill should be used when the user wants to set up shinkoku for the first
  time, initialize their configuration, or update their existing settings.
  Trigger phrases include: "セットアップ", "初期設定", "設定ファイルを作る",
  "shinkokuの設定", "config", "setup", "始め方", "使い方", "設定を更新",
  "configを作り直す".
---

# セットアップウィザード（Setup Wizard）

shinkoku の初回セットアップを対話的に行うスキル。
設定ファイル（`shinkoku.config.yaml`）の生成とデータベースの初期化を実施する。

## ステップ1: 既存設定の確認

CWD の `shinkoku.config.yaml` を Read ツールで読み込む。

- **ファイルが存在する場合**: 内容を表示し、更新するか確認する。更新しない場合はスキルを終了する。
- **ファイルが存在しない場合**: セットアップウィザードを開始する。

## ステップ2: 基本設定のヒアリング

以下の項目を AskUserQuestion で確認する:

### 2-1. 対象年度

- `tax_year`: 確定申告の対象年度（デフォルト: 2025）

### 2-2. 適格請求書発行事業者の登録番号

- `invoice_registration_number`: T + 13桁の番号（任意、スキップ可）

## ステップ3: パス設定

以下のパスを確認する。デフォルト値を提示し、変更がなければそのまま採用する。

- `db_path`: データベースファイルのパス（デフォルト: `./shinkoku.db`）
- `output_dir`: PDF帳票の出力先ディレクトリ（デフォルト: `./output`）

## ステップ4: 書類ディレクトリの設定（任意）

以下のディレクトリを設定するか確認する。スキップ可能。

- `invoices_dir`: 請求書PDF等のディレクトリ
- `withholding_slips_dir`: 源泉徴収票のディレクトリ
- `receipts_dir`: レシート・領収書のディレクトリ
- `bank_statements_dir`: 銀行明細CSVのディレクトリ
- `credit_card_statements_dir`: クレジットカード明細CSVのディレクトリ
- `deductions_dir`: 控除関連書類のディレクトリ
- `past_returns_dir`: 過去の確定申告データのディレクトリ

## ステップ5: 設定のプレビューと保存

1. 収集した設定内容を YAML 形式でプレビュー表示する
2. ユーザーの確認を得る
3. Write ツールで CWD に `shinkoku.config.yaml` を保存する

YAML の形式は以下のテンプレートに従う:

```yaml
# shinkoku ユーザー設定ファイル
# /setup スキルで対話的に生成できます。

# 対象年度
tax_year: {tax_year}

# データベースファイルのパス
db_path: {db_path}

# PDF帳票の出力先ディレクトリ
output_dir: {output_dir}

# 適格請求書発行事業者の登録番号（T + 13桁）
invoice_registration_number: {invoice_registration_number}

# --- 書類ディレクトリ（任意） ---
invoices_dir: {invoices_dir}
withholding_slips_dir: {withholding_slips_dir}
past_returns_dir: {past_returns_dir}
deductions_dir: {deductions_dir}
receipts_dir: {receipts_dir}
bank_statements_dir: {bank_statements_dir}
credit_card_statements_dir: {credit_card_statements_dir}
```

未設定の項目は値を空にする（`key:` のみ）。

## ステップ6: データベースの初期化

1. `db_path` の値を確認し、相対パスの場合は CWD を基準に絶対パスに変換する
2. `ledger_init` ツールを呼び出してデータベースを初期化する:
   - `fiscal_year`: ステップ2 で設定した `tax_year`
   - `db_path`: 絶対パスに変換した値

## ステップ7: 次のステップの案内

セットアップ完了後、以下を案内する:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
セットアップ完了
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 生成されたファイル:
  → shinkoku.config.yaml（設定ファイル）
  → {db_path}（データベース）

■ 次のステップ:
  1. /assess — 申告要否・種類の判定
  2. /gather — 必要書類の確認・収集
  3. /journal — 仕訳入力・帳簿管理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
