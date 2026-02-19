# shinkoku

確定申告自動化 Claude Code Plugin。Python 3.11+、SQLite WAL モードで動作する。
会社員＋副業（事業所得・青色申告）の所得税・消費税確定申告をエンドツーエンドで支援する。
帳簿管理・税額計算は CLI で実行し、確定申告書等作成コーナーへの入力は Claude in Chrome が代行する。

## 対象ペルソナ

Full = 計算＋確定申告書等作成コーナーへの入力代行、Out = 対象外

| ペルソナ | 対応レベル | 備考 |
|---------|-----------|------|
| 個人事業主（青色申告・一般用） | Full | メインターゲット。帳簿→決算書→税額計算→作成コーナー入力 |
| 会社員＋副業（事業所得） | Full | 源泉徴収票＋事業所得の税額計算→作成コーナー入力 |
| 給与所得のみ（会社員） | Full | 還付申告・医療費控除等→作成コーナー入力 |
| 消費税課税事業者 | Full | 2割特例・簡易課税・本則課税すべて対応 |
| ふるさと納税利用者 | Full | CRUD + 控除計算 + 限度額推定 |
| 住宅ローン控除（初年度） | Full | 控除額計算。初年度は添付書類が別途必要 |
| 医療費控除 | Full | 明細集計＋控除額計算 |
| 仮想通貨トレーダー | Full | 雑所得（総合課税）として税額計算に自動反映 |
| 株式投資家（分離課税） | Out | 株式譲渡所得・配当の分離課税には対応していません |
| FXトレーダー | Out | 先物取引に係る雑所得等には対応していません |
| 不動産所得 | Out | 不動産所得用の決算書・申告に対応していません |
| 退職所得 | Out | 退職所得控除の計算に対応していません |
| 譲渡所得（不動産売却） | Out | 長期/短期税率、3,000万円特別控除なし |
| 外国税額控除 | Out | 外国税支払額の追跡・控除計算なし |
| 農業所得・山林所得 | Out | 専用所得区分なし |
| 非居住者 | Out | 日本居住者専用 |

## 対象外の機能

| 機能 | 理由 |
|------|------|
| マイナポータル連携 | freee 等の SaaS 固有機能（API 連携が前提） |

## アーキテクチャ

```
skills/ (SKILL.md)          ← 対話フロー定義（オープン標準 Agent Skills 仕様）
  skills/reading-*/SKILL.md ← OCR 画像読取スキル（旧 agents/ の後継）
src/shinkoku/cli/           ← CLI エントリーポイント（shinkoku コマンド）
  ↓
src/shinkoku/tools/         ← ビジネスロジック（純粋関数）
  ↓
src/shinkoku/               ← コア（models, db, master_accounts）
```

- ツール呼び出し: `shinkoku <command> <subcommand>` で実行（argparse サブコマンド + JSON 入出力）
- ビジネスロジック: `src/shinkoku/tools/*.py` に純粋関数として定義（CLI から呼び出し）

## コマンド

```bash
make dev          # Claude Code をプラグインモードで起動
make test         # 全テスト実行
make lint         # Ruff lint チェック

uv run pytest tests/unit/ -v      # ユニットテストのみ
uv run pytest tests/scripts/ -v   # CLI スクリプトテスト
uv run pytest tests/integration/ -v  # 統合テスト

uv run mypy src/shinkoku/ --ignore-missing-imports  # 型チェック
uv run ruff format --check src/ tests/              # フォーマットチェック
```

### CLI 呼び出し例

```bash
# 帳簿 CRUD
uv run shinkoku ledger init --db-path shinkoku.db --fiscal-year 2025
uv run shinkoku ledger journal-add --db-path shinkoku.db --input journal.json
uv run shinkoku ledger trial-balance --db-path shinkoku.db --fiscal-year 2025

# 税額計算
uv run shinkoku tax calc-income --input income_params.json

# データ取込
uv run shinkoku import csv --file-path transactions.csv

# ふるさと納税
uv run shinkoku furusato summary --db-path shinkoku.db --fiscal-year 2025

# プロファイル
uv run shinkoku profile --config shinkoku.config.yaml
```

## コーディング規約

### 金額は必ず int（円）

- **float 禁止** — 金額を扱う変数・フィールドは全て `int`（円単位の整数）
- 消費税の按分計算も整数演算（`//` 演算子）で行う
- `amount: int = Field(gt=0, description="円単位の整数")`

### 端数処理

#### 所得税

| 対象 | ルール | 法的根拠 |
|------|--------|---------|
| 課税所得 | 1,000円未満切捨て `(amount // 1_000) * 1_000` | 国税通則法118条 |
| 復興特別所得税 | 1円未満切捨て `tax * 21 // 1000` | 復興財源確保法13条 |
| 所得税及び復興特別所得税の額（㊺） | 端数処理なし | — |
| 申告納税額（納付の場合のみ） | 100円未満切捨て `(amount // 100) * 100` | 国税通則法119条 |
| 還付金 | 1円単位（切捨てなし） | 国税通則法120条 |

#### 消費税

| 対象 | ルール | 法的根拠 |
|------|--------|---------|
| 課税標準額 | 1,000円未満切捨て `(amount // 1_000) * 1_000` | 国税通則法118条 |
| 消費税額（国税） | 課税標準額 × 78/1000（標準）or 624/10000（軽減） | 消費税法29条 |
| 差引税額 | 100円未満切捨て `(amount // 100) * 100` | 国税通則法119条 |
| 地方消費税 | 差引税額 × 22/78、100円未満切捨て | 地方税法72条の89 |

#### 各種控除

| 対象 | ルール | 法的根拠 |
|------|--------|---------|
| 生命保険料控除 | 1円未満切り上げ `-(-amount // divisor)` | 所得税法76条 |
| 地震保険料控除 | 1円未満切り上げ `-(-amount // divisor)` | 所得税法77条 |
| 住宅ローン控除 | 100円未満切捨て | 租税特別措置法41条2項 |
| 減価償却費 | 1円未満切捨て | 所得税法49条 |

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

### CLI モジュール規約

- エントリーポイント: `src/shinkoku/cli/__init__.py` の `main()` で全サブコマンドを登録
- 各モジュール（`src/shinkoku/cli/*.py`）は `register(subparsers)` 関数を公開し、サブコマンドを登録する
- 入力: 複雑なパラメータは `--input <json_file>` で JSON ファイル受け取り。単純パラメータは CLI 引数
- 出力: JSON を stdout に出力
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

- 構成: `tests/unit/` / `tests/scripts/` / `tests/integration/`
- `tests/scripts/`: CLI の統合テスト（subprocess で `shinkoku` コマンドを呼び出し、JSON 出力を検証）
- `tests/unit/`: DB・config 等のコアモジュールのユニットテスト
- `tests/integration/`: 複数モジュールの結合テスト
- 共有フィクスチャ: `in_memory_db`, `in_memory_db_with_accounts`, `sample_journals`
- マーカー: `@pytest.mark.slow`

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
| `src/shinkoku/tools/furusato.py` | ふるさと納税 CRUD・集計 |
| `src/shinkoku/tools/profile.py` | 納税者プロファイル取得 |

### CLI モジュール（src/shinkoku/cli/）

| ファイルパス | サブコマンド数 | 役割 |
|------------|-------------|------|
| `src/shinkoku/cli/__init__.py` | — | CLI エントリーポイント（`main()` + サブコマンド登録） |
| `src/shinkoku/cli/__main__.py` | — | `python -m shinkoku.cli` 実行用 |
| `src/shinkoku/cli/ledger.py` | 71 | 帳簿管理 CLI（init, journal-add, search, trial-balance 等） |
| `src/shinkoku/cli/tax_calc.py` | 8 | 税額計算 CLI（calc-income, calc-deductions 等） |
| `src/shinkoku/cli/import_data.py` | 9 | データ取込 CLI（csv, receipt, invoice 等） |
| `src/shinkoku/cli/furusato.py` | 4 | ふるさと納税 CLI（add, list, delete, summary） |
| `src/shinkoku/cli/profile.py` | 1 | プロファイル取得 CLI |

### スキル（skills/）

| ファイルパス | 役割 |
|------------|------|
| `skills/e-tax/SKILL.md` | e-Tax 電子申告スキル（Claude in Chrome で確定申告書等作成コーナーに入力） |
| `skills/setup/SKILL.md` | セットアップウィザード（設定ファイル生成・DB初期化） |
| `skills/reading-receipt/SKILL.md` | レシート画像 OCR スキル |
| `skills/reading-withholding/SKILL.md` | 源泉徴収票 OCR スキル |
| `skills/reading-invoice/SKILL.md` | 請求書 OCR スキル |
| `skills/reading-deduction-cert/SKILL.md` | 控除証明書 OCR スキル |
| `skills/reading-payment-statement/SKILL.md` | 支払調書 OCR スキル |

## 注意事項

- `output/` は `.gitignore` 対象 — 実行時に自動生成される
- `shinkoku.config.yaml` はコミットしない（テンプレートは `shinkoku.config.example.yaml`、`/setup` スキルで対話生成可能）
- 税法計算は令和7年分（2025年課税年度）の改正を反映済み
