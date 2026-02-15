# shinkoku

確定申告自動化 Claude Code Plugin（MCP Server）。Python 3.11+、SQLite WAL モードで動作する。
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
agents/ (*.md)         ← サブエージェント定義（OCR等の委任先）
skills/ (SKILL.md)     ← 対話フロー定義（9スキル、setup 含む）
  ↓
src/shinkoku/tools/    ← MCP ツール（register(mcp) で登録）
  ↓
src/shinkoku/          ← コア（models, db, master_accounts）
```

- エントリーポイント: `src/shinkoku/server.py` — `FastMCP("shinkoku")` を生成し `mcp.run()` で起動
- ツール登録: 各 `tools/*.py` の `register(mcp)` 関数で MCP ツールを登録

## コマンド

```bash
make dev          # Claude Code をプラグインモードで起動
make test         # 全テスト実行
make lint         # Ruff lint チェック

uv run pytest tests/unit/ -v         # ユニットテストのみ
uv run pytest tests/integration/ -v  # 統合テストのみ
uv run pytest tests/e2e/ -v          # E2Eテストのみ

uv run mypy src/shinkoku/ --ignore-missing-imports  # 型チェック
uv run ruff format --check src/ tests/              # フォーマットチェック
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

### MCP ツール登録

- 各ツールファイルで `register(mcp)` 関数を定義し、その中で `@mcp.tool()` デコレータを使用
- ツール関数は `dict` を返す（`result.model_dump()`）
- ビジネスロジックはツール関数の外に純粋関数として分離する

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

- 構成: `tests/unit/` / `tests/integration/` / `tests/e2e/`
- 共有フィクスチャ: `in_memory_db`, `in_memory_db_with_accounts`, `sample_journals`
- マーカー: `@pytest.mark.slow`, `@pytest.mark.visual_regression`
- asyncio_mode: `auto`

## 主要ファイル

| ファイルパス | 役割 |
|------------|------|
| `src/shinkoku/server.py` | MCP Server エントリーポイント |
| `src/shinkoku/models.py` | Pydantic モデル定義（全ツールの入出力型） |
| `src/shinkoku/db.py` | SQLite 接続管理・マイグレーション |
| `src/shinkoku/master_accounts.py` | 勘定科目マスタ（1xxx〜5xxx） |
| `src/shinkoku/tax_constants.py` | 税制定数の一元管理（税率・控除額・速算表等） |
| `src/shinkoku/tools/ledger.py` | 帳簿管理ツール（仕訳CRUD・財務諸表） |
| `src/shinkoku/tools/tax_calc.py` | 税額計算ツール（所得税・消費税・控除・減価償却） |
| `src/shinkoku/tools/import_data.py` | データ取り込みツール（CSV・レシート・請求書） |
| `src/shinkoku/tools/document.py` | PDF帳票生成ツール |
| `src/shinkoku/tools/pdf_utils.py` | PDF生成ユーティリティ |
| `src/shinkoku/tools/pdf_coordinates.py` | PDF帳票の座標定義 |
| `src/shinkoku/xtx/generator.py` | xtx（e-Tax XML）生成エンジン（XtxBuilder クラス） |
| `src/shinkoku/xtx/field_codes.py` | ABB コード定数辞書・名前空間・ネスト構造定義 |
| `src/shinkoku/xtx/income_tax.py` | 所得税申告書B 第一表・第二表 xtx ビルダー |
| `src/shinkoku/xtx/blue_return.py` | 青色申告決算書 PL・BS xtx ビルダー |
| `src/shinkoku/xtx/consumption_tax.py` | 消費税申告書 xtx ビルダー |
| `src/shinkoku/xtx/schedules.py` | 第三表（分離課税）xtx ビルダー |
| `src/shinkoku/xtx/attachments.py` | 医療費・住宅ローン控除明細書 xtx ビルダー |
| `src/shinkoku/xtx/generate_xtx.py` | xtx 生成オーケストレーション（DB→計算→XML出力） |
| `scripts/generate_xtx.py` | xtx 生成 CLI エントリーポイント |
| `skills/e-tax/SKILL.md` | e-Tax 電子申告スキル（xtx 生成→アップロード案内） |
| `skills/setup/SKILL.md` | セットアップウィザード（設定ファイル生成・DB初期化） |
| `agents/receipt-reader.md` | レシート画像OCRサブエージェント（Vision トークン分離） |

## 注意事項

- `output/` は `.gitignore` 対象 — 実行時に自動生成される
- `shinkoku.config.yaml` はコミットしない（テンプレートは `shinkoku.config.example.yaml`、`/setup` スキルで対話生成可能）
- 税法計算は令和7年分（2025年課税年度）の改正を反映済み
