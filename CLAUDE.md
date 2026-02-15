# shinkoku

確定申告自動化 Claude Code Plugin。Python 3.11+、SQLite WAL モードで動作する。
会社員＋副業（事業所得・青色申告）の所得税・消費税確定申告をエンドツーエンドで支援する。

## 対象ペルソナ

| ペルソナ | 対応状況 | 備考 |
|---------|---------|------|
| 給与所得のみ（会社員） | 対応 | 源泉徴収票取込、年末調整確認 |
| 会社員＋副業（事業所得） | 対応 | 主要ターゲット |
| フリーランス/個人事業主 | 対応 | 青色/白色申告対応 |
| 株式投資家 | 対応 | 分離課税、損益通算、繰越損失 |
| FXトレーダー | 対応 | 先物取引に係る雑所得等 |
| 仮想通貨トレーダー | 対応 | 雑所得（総合課税） |
| ふるさと納税利用者 | 対応 | CRUD + 控除計算 + 限度額推定 |
| 不動産所得（家賃収入） | 部分対応 | 仕訳で追跡可能だが専用所得区分なし |
| 退職所得 | 部分対応 | 1/2課税・退職所得控除の専用計算なし |
| 譲渡所得（不動産売却） | 未対応 | 長期/短期税率、3000万控除なし |
| 外国税額控除 | 未対応 | 外国税支払額の追跡・控除計算なし |
| 農業所得 | 未対応 | 専用所得区分なし |
| 山林所得 | 未対応 | 5分5乗方式なし |
| 非居住者 | 対象外 | 日本居住者専用 |

## 対象外の機能

| 機能 | 理由 |
|------|------|
| マイナポータル連携 | freee 等の SaaS 固有機能（API 連携が前提） |

## アーキテクチャ

```
agents/ (*.md)              ← サブエージェント定義（OCR等の委任先）
skills/ (SKILL.md)          ← 対話フロー定義（9スキル、setup 含む）
skills/*/scripts/*.py       ← CLI スクリプト（Bash 経由で呼び出し）
  ↓
src/shinkoku/tools/         ← ビジネスロジック（純粋関数）
  ↓
src/shinkoku/               ← コア（models, db, master_accounts）
```

- ツール呼び出し: `skills/*/scripts/*.py` を `uv run python` で実行（argparse サブコマンド + JSON 入出力）
- ビジネスロジック: `src/shinkoku/tools/*.py` に純粋関数として定義（CLI スクリプトから呼び出し）

## コマンド

```bash
make dev          # Claude Code をプラグインモードで起動
make test         # 全テスト実行
make lint         # Ruff lint チェック

uv run pytest tests/unit/ -v      # ユニットテストのみ
uv run pytest tests/scripts/ -v   # CLI スクリプトテスト
uv run pytest tests/visual/ -v    # PDF ビジュアルリグレッションテスト

uv run mypy src/shinkoku/ --ignore-missing-imports  # 型チェック
uv run ruff format --check src/ tests/              # フォーマットチェック
```

### CLI スクリプト呼び出し例

```bash
# 帳簿 CRUD
uv run python skills/journal/scripts/ledger.py init --db-path shinkoku.db --fiscal-year 2025
uv run python skills/journal/scripts/ledger.py journal-add --db-path shinkoku.db --input journal.json
uv run python skills/journal/scripts/ledger.py trial-balance --db-path shinkoku.db --fiscal-year 2025

# 税額計算
uv run python skills/income-tax/scripts/tax_calc.py calc-income --input income_params.json

# PDF 帳票生成
uv run python skills/document/scripts/doc_generate.py income-tax --input tax_result.json --output-path output/

# データ取込
uv run python skills/journal/scripts/import_data.py csv --file-path transactions.csv

# ふるさと納税
uv run python skills/furusato/scripts/furusato.py summary --db-path shinkoku.db --fiscal-year 2025

# プロファイル
uv run python skills/setup/scripts/profile.py --config shinkoku.config.yaml
```

## コーディング規約

### 金額は必ず int（円）

- **float 禁止** — 金額を扱う変数・フィールドは全て `int`（円単位の整数）
- 消費税の按分計算も整数演算（`//` 演算子）で行う
- `amount: int = Field(gt=0, description="円単位の整数")`

### 端数処理

| 対象 | ルール |
|------|--------|
| 課税所得 | 1,000円未満切捨て `(amount // 1_000) * 1_000` |
| 申告納税額（所得税） | 100円未満切捨て `(amount // 100) * 100` |
| 復興特別所得税 | 1円未満切捨て `int(tax * 21 // 1000)` |
| 消費税（国税） | 100円未満切捨て `(amount // 100) * 100` |

### 型ヒント

- 全関数に型ヒントを付与する
- ファイル先頭に `from __future__ import annotations` を記述
- `X | None` 記法を使う（`Optional[X]` は使わない）

### Pydantic モデル命名

- `*Input` — ツールへの入力（例: `IncomeTaxInput`）
- `*Result` — ツールからの出力（例: `IncomeTaxResult`）
- `*Params` — 検索条件（例: `JournalSearchParams`）
- `*Record` — DBレコード（例: `JournalRecord`）
- 定義は `src/shinkoku/models.py` に集約する

### CLI スクリプト規約

- 各スクリプトは argparse サブコマンド方式
- 入力: 複雑なパラメータは `--input <json_file>` で JSON ファイル受け取り。単純パラメータは CLI 引数
- 出力: JSON を stdout に出力。PDF 生成系は `--output-path` でファイル出力 + メタ情報を stdout
- エラー: `{"status": "error", "message": "..."}` を stdout + exit code 1
- DB 系: `--db-path` 引数で SQLite パスを受け取り
- ビジネスロジックは `src/shinkoku/tools/` の純粋関数として分離する

### Ruff

- `line-length`: 100
- `target-version`: py311

### コメント

- ドメイン固有ロジック（税法の計算根拠、勘定科目の説明等）には日本語コメントを付ける
- 自明なコードにはコメントを付けない

### コミットメッセージ

- 形式: `[type]: [description]`（英語）
- type: `feat` / `fix` / `ci` / `refactor` / `test` / `docs`

## DB 規約

- SQLite WAL モード + `foreign_keys=ON`
- 接続は `db.get_connection()` / 初期化は `db.init_db()` を使う
- 勘定科目コード体系:
  - `1xxx`: 資産（asset）
  - `2xxx`: 負債（liability）
  - `3xxx`: 純資産（equity）
  - `4xxx`: 収益（revenue）
  - `5xxx`: 費用（expense）

## テスト規約

- 構成: `tests/unit/` / `tests/scripts/` / `tests/visual/`
- `tests/scripts/`: CLI スクリプトの統合テスト（subprocess でスクリプトを呼び出し、JSON 出力を検証）
- `tests/unit/`: DB・config・xtx 等のコアモジュールのユニットテスト
- `tests/visual/`: PDF ビジュアルリグレッションテスト
- 共有フィクスチャ: `in_memory_db`, `in_memory_db_with_accounts`, `sample_journals`
- マーカー: `@pytest.mark.slow`, `@pytest.mark.visual_regression`

## 主要ファイル

### コアモジュール

| ファイルパス | 役割 |
|------------|------|
| `src/shinkoku/models.py` | Pydantic モデル定義（全ツールの入出力型） |
| `src/shinkoku/db.py` | SQLite 接続管理・マイグレーション |
| `src/shinkoku/master_accounts.py` | 勘定科目マスタ（1xxx〜5xxx） |
| `src/shinkoku/tax_constants.py` | 税制定数の一元管理（税率・控除額・速算表等） |

### ビジネスロジック（純粋関数）

| ファイルパス | 役割 |
|------------|------|
| `src/shinkoku/tools/ledger.py` | 帳簿管理（仕訳CRUD・財務諸表） |
| `src/shinkoku/tools/tax_calc.py` | 税額計算（所得税・消費税・控除・減価償却） |
| `src/shinkoku/tools/import_data.py` | データ取り込み（CSV・レシート・請求書） |
| `src/shinkoku/tools/document.py` | PDF帳票生成 |
| `src/shinkoku/tools/furusato.py` | ふるさと納税 CRUD・集計 |
| `src/shinkoku/tools/profile.py` | 納税者プロファイル取得 |
| `src/shinkoku/tools/separate_tax.py` | 分離課税（株式・FX） |
| `src/shinkoku/tools/pdf_utils.py` | PDF生成ユーティリティ |
| `src/shinkoku/tools/pdf_coordinates.py` | PDF帳票の座標定義 |

### CLI スクリプト（skills/*/scripts/）

| ファイルパス | サブコマンド数 | 役割 |
|------------|-------------|------|
| `skills/journal/scripts/ledger.py` | 67 | 帳簿管理 CLI（init, journal-add, search, trial-balance 等） |
| `skills/income-tax/scripts/tax_calc.py` | 9 | 税額計算 CLI（calc-income, calc-deductions 等） |
| `skills/document/scripts/doc_generate.py` | 11 | PDF帳票生成 CLI（income-tax, bs-pl, full-set 等） |
| `skills/journal/scripts/import_data.py` | 9 | データ取込 CLI（csv, receipt, invoice 等） |
| `skills/furusato/scripts/furusato.py` | 4 | ふるさと納税 CLI（add, list, delete, summary） |
| `skills/setup/scripts/profile.py` | 1 | プロファイル取得 CLI |

### xtx（e-Tax XML）

| ファイルパス | 役割 |
|------------|------|
| `src/shinkoku/xtx/generator.py` | xtx 生成エンジン（XtxBuilder クラス） |
| `src/shinkoku/xtx/field_codes.py` | ABB コード定数辞書・名前空間・ネスト構造定義 |
| `src/shinkoku/xtx/income_tax.py` | 所得税申告書B 第一表・第二表 xtx ビルダー |
| `src/shinkoku/xtx/blue_return.py` | 青色申告決算書 PL・BS xtx ビルダー |
| `src/shinkoku/xtx/consumption_tax.py` | 消費税申告書 xtx ビルダー |
| `src/shinkoku/xtx/schedules.py` | 第三表（分離課税）xtx ビルダー |
| `src/shinkoku/xtx/attachments.py` | 医療費・住宅ローン控除明細書 xtx ビルダー |
| `src/shinkoku/xtx/generate_xtx.py` | xtx 生成オーケストレーション（DB→計算→XML出力） |
| `scripts/generate_xtx.py` | xtx 生成 CLI エントリーポイント |

### スキル・エージェント

| ファイルパス | 役割 |
|------------|------|
| `skills/e-tax/SKILL.md` | e-Tax 電子申告スキル（xtx 生成→アップロード案内） |
| `skills/setup/SKILL.md` | セットアップウィザード（設定ファイル生成・DB初期化） |
| `agents/receipt-reader.md` | レシート画像OCRサブエージェント（Vision トークン分離） |

## 注意事項

- `output/` は `.gitignore` 対象 — 実行時に自動生成される
- `shinkoku.config.yaml` はコミットしない（テンプレートは `shinkoku.config.example.yaml`、`/setup` スキルで対話生成可能）
- 税法計算は令和7年分（2025年課税年度）の改正を反映済み
