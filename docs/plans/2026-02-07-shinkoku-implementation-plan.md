# shinkoku v0.1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 確定申告を丸ごと自動化する Claude Code Plugin (shinkoku) の v0.1 を実装し、自分の令和7年分確定申告を完遂する。

**Architecture:** Python MCP Server (FastMCP, stdio) + Claude Code Skills (9つ) + SQLite。帳簿管理・税額計算・PDF生成を MCP ツールで提供し、Skills が対話的ワークフローとツール呼び出しをガイドする。

**Tech Stack:** Python 3.11+, mcp SDK, SQLite, ReportLab, pypdf, pdfplumber, pytest, uv

---

## Phase 1: プロジェクト基盤構築

### Task 1: プロジェクト初期化

**Files:**
- Create: `pyproject.toml`
- Create: `src/shinkoku/__init__.py`
- Create: `.gitignore`
- Create: `.claude-plugin/plugin.json`
- Create: `.mcp.json`

**Step 1: pyproject.toml を作成**

```toml
[project]
name = "shinkoku"
version = "0.1.0"
description = "確定申告自動化 Claude Code Plugin - MCP Server"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0",
    "reportlab>=4.0",
    "pypdf>=4.0",
    "pdfplumber>=0.10",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]

[project.scripts]
shinkoku = "shinkoku.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/shinkoku"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "slow: marks tests as slow",
    "visual_regression: PDF visual regression tests",
]

[tool.ruff]
line-length = 100
target-version = "py311"
```

**Step 2: .claude-plugin/plugin.json を作成**

```json
{
  "name": "shinkoku",
  "version": "0.1.0",
  "description": "確定申告を自動化する Claude Code Plugin。会社員＋副業（事業所得・青色申告）の所得税・消費税確定申告をエンドツーエンドで支援。",
  "author": {
    "name": "kazukinagata"
  },
  "license": "MIT",
  "keywords": ["確定申告", "tax-filing", "bookkeeping", "blue-return", "japan-tax"]
}
```

**Step 3: .mcp.json を作成**

```json
{
  "mcpServers": {
    "shinkoku": {
      "command": "uv",
      "args": ["run", "shinkoku"],
      "cwd": "${CLAUDE_PLUGIN_ROOT}"
    }
  }
}
```

**Step 4: .gitignore を作成**

```
data/
output/
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
```

**Step 5: ディレクトリ構造を作成**

```bash
mkdir -p .claude-plugin src/shinkoku/tools skills data/{receipts,statements,documents,templates} output tests/{unit,integration,e2e,fixtures/{csv,images,pdfs,expected_pdfs,scenarios},helpers}
touch src/shinkoku/__init__.py src/shinkoku/tools/__init__.py
```

**Step 6: 依存関係をインストール**

Run: `uv sync --all-extras`

**Step 7: Commit**

```bash
git add pyproject.toml .claude-plugin/ .mcp.json .gitignore src/ tests/
git commit -m "feat: initialize project structure and dependencies"
```

---

### Task 2: SQLite スキーマ + DB管理モジュール

**Files:**
- Create: `src/shinkoku/schema.sql`
- Create: `src/shinkoku/db.py`
- Test: `tests/unit/test_db.py`

**Step 1: テストを書く**

```python
# tests/unit/test_db.py
import sqlite3
import pytest
from shinkoku.db import init_db, get_connection, migrate

def test_init_db_creates_file(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    assert (tmp_path / "test.db").exists()
    conn.close()

def test_init_db_creates_all_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    expected = {"schema_version", "fiscal_years", "accounts", "journals",
                "journal_lines", "fixed_assets", "deductions", "withholding_slips"}
    assert expected.issubset(tables)
    conn.close()

def test_init_db_idempotent(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn1 = init_db(db_path)
    conn1.execute("INSERT INTO fiscal_years (year) VALUES (2025)")
    conn1.commit()
    conn1.close()
    conn2 = init_db(db_path)
    row = conn2.execute("SELECT year FROM fiscal_years").fetchone()
    assert row[0] == 2025
    conn2.close()

def test_foreign_keys_enabled(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1
    conn.close()
```

**Step 2: テスト実行（RED）**

Run: `uv run pytest tests/unit/test_db.py -v`
Expected: FAIL

**Step 3: schema.sql を作成**

7テーブル + 9インデックスの完全DDL。設計書のスキーマを拡張:
- `fiscal_years`: 年度管理
- `accounts`: 勘定科目マスタ（`sub_category`, `is_active`, `sort_order` 追加）
- `journals`: 仕訳ヘッダ（`fiscal_year`, `is_adjustment`, `updated_at` 追加）
- `journal_lines`: 仕訳明細（`tax_category` を詳細化: `taxable_10`/`taxable_8`/`taxable_8_reduced`、`tax_amount` 追加）
- `fixed_assets`: 固定資産台帳（`business_use_ratio`, `accumulated_depreciation` 追加）
- `deductions`: 控除情報（新規）
- `withholding_slips`: 源泉徴収票データ（新規）
- `schema_version`: マイグレーション管理

**Step 4: db.py を実装**

```python
# src/shinkoku/db.py
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def migrate(conn: sqlite3.Connection) -> int:
    # schema_version テーブルの存在確認 → なければ初期スキーマ適用
    ...

def init_db(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    migrate(conn)
    return conn
```

**Step 5: テスト実行（GREEN）**

Run: `uv run pytest tests/unit/test_db.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/shinkoku/schema.sql src/shinkoku/db.py tests/unit/test_db.py
git commit -m "feat: add SQLite schema and database management module"
```

---

### Task 3: Pydantic モデル定義

**Files:**
- Create: `src/shinkoku/models.py`

入出力の型定義。各ツールの引数・戻り値の Pydantic モデル。

- `JournalLine`, `JournalEntry`, `JournalSearchParams`, `JournalSearchResult`
- `TrialBalanceAccount`, `TrialBalanceResult`
- `PLResult`, `BSResult`
- `CSVImportCandidate`, `CSVImportResult`
- `IncomeTaxInput`, `IncomeTaxResult`
- `ConsumptionTaxResult`
- `DeductionItem`, `DeductionsResult`
- `DepreciationResult`

**Step 1: Commit**

```bash
git add src/shinkoku/models.py
git commit -m "feat: add Pydantic models for tool input/output types"
```

---

### Task 4: 勘定科目マスタデータ

**Files:**
- Create: `src/shinkoku/master_accounts.py`
- Test: `tests/unit/test_master_accounts.py`

個人事業・青色申告で使う勘定科目一覧（約60科目）。tax-domain-expert が設計した科目コード体系:
- 1xxx: 資産、2xxx: 負債、3xxx: 純資産、4xxx: 収益、5xxx: 費用
- 各科目に `code`, `name`, `category`, `sub_category`, `tax_category` を定義

**Step 1: テストを書く**

```python
def test_master_accounts_has_all_categories():
    categories = {a["category"] for a in MASTER_ACCOUNTS}
    assert categories == {"asset", "liability", "equity", "revenue", "expense"}

def test_master_accounts_codes_unique():
    codes = [a["code"] for a in MASTER_ACCOUNTS]
    assert len(codes) == len(set(codes))

def test_master_accounts_tax_categories_valid():
    valid = {"taxable", "non_taxable", "exempt", "out_of_scope", None}
    for a in MASTER_ACCOUNTS:
        assert a.get("tax_category") in valid
```

**Step 2-5: RED → GREEN → Commit**

---

### Task 5: MCP Server エントリポイント

**Files:**
- Create: `src/shinkoku/server.py`

```python
from mcp.server.fastmcp import FastMCP
from shinkoku.tools import ledger, import_data, tax_calc, document

mcp = FastMCP("shinkoku", json_response=True)

def register_tools():
    ledger.register(mcp)
    import_data.register(mcp)
    tax_calc.register(mcp)
    document.register(mcp)

def main():
    register_tools()
    mcp.run()
```

**Step 1: Commit**

```bash
git add src/shinkoku/server.py
git commit -m "feat: add MCP server entry point with FastMCP"
```

---

### Task 6: テスト基盤

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/unit/conftest.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/helpers/db_helpers.py`
- Create: `tests/helpers/assertion_helpers.py`

主要 fixtures:
- `in_memory_db`: インメモリSQLite（単体テスト用）
- `tmp_db`: テンポラリファイルDB（統合テスト用）
- `sample_journals`: サンプル仕訳投入済みDB
- `tax_params_2025`: 令和7年分の税額計算パラメータ
- `output_dir`: PDF出力先テンポラリ
- `assert_amount_is_integer_yen`: 金額が整数円であることのカスタムアサーション

**Step 1: Commit**

```bash
git add tests/
git commit -m "feat: add test infrastructure (fixtures, helpers)"
```

---

## Phase 2: 帳簿管理（ledger）— 9ツール

### Task 7: ledger_init + ledger_add_journal

**Files:**
- Create: `src/shinkoku/tools/ledger.py`
- Test: `tests/unit/test_ledger.py`

`ledger_init`: 年度の帳簿初期化（DB作成 + 勘定科目マスタ投入）
`ledger_add_journal`: 仕訳1件登録。**借方合計 == 貸方合計のバリデーション必須。**

テスト: `test_add_journal_debit_credit_must_balance`, `test_add_journal_zero_amount_rejected`, `test_add_journal_invalid_account_rejected` 等

---

### Task 8: ledger_add_journals_batch + ledger_search

バッチ登録（トランザクション内、1件でも不正なら全件ロールバック）と検索。

テスト: `test_add_journals_batch_all_or_nothing`, `test_search_by_date_range`, `test_search_by_account` 等

---

### Task 9: ledger_update_journal + ledger_delete_journal

仕訳の修正・削除。修正後も貸借一致を保証。

---

### Task 10: ledger_trial_balance + ledger_pl + ledger_bs

**最重要テスト:**
- `test_trial_balance_debit_equals_credit`: 残高試算表の借方合計 = 貸方合計
- `test_bs_assets_equal_liabilities_plus_equity`: 資産 = 負債 + 純資産
- `test_pl_revenue_minus_expense`: 当期利益 = 収益 - 費用

---

## Phase 3: データ取り込み（import）— 4ツール

Phase 2 と並行可能。

### Task 11: import_csv

**Files:**
- Create: `src/shinkoku/tools/import_data.py`
- Test: `tests/unit/test_import_data.py`
- Fixture: `tests/fixtures/csv/credit_card_simple.csv`

CSVパース + 構造化。勘定科目推定はSkill（Claude）側で行うため、ツールはパースのみ。
Shift_JIS/UTF-8 対応、不正行スキップ、重複検出。

---

### Task 12: import_receipt + import_invoice + import_withholding

- `import_receipt`: ファイル存在確認 + 空テンプレート返却（OCRはClaude Vision）
- `import_invoice`: pdfplumber でテキスト抽出
- `import_withholding`: pdfplumber でテキスト抽出 + 源泉徴収票テンプレート

---

## Phase 4: 税額計算（tax）— 4ツール

### Task 13: tax_calc_deductions

**Files:**
- Create: `src/shinkoku/tools/tax_calc.py`
- Test: `tests/unit/test_tax_calc.py`

適用可能な控除の計算。令和7年分改正を反映:
- **基礎控除**: 段階表（95万/88万/68万/63万/58万/48万/32万/16万/0円）
- 社会保険料控除、生命保険料控除、配偶者控除/配偶者特別控除
- ふるさと納税（寄附金控除）
- 住宅ローン控除（税額控除）

---

### Task 14: tax_depreciation

減価償却費の計算。定額法/定率法、月割計算、事業使用割合（家事按分）。

---

### Task 15: tax_calc_income

所得税額の計算。全フロー:
1. 各所得の計算（給与所得控除・事業所得）
2. 損益通算
3. 所得控除の適用
4. 速算表による税額計算（課税所得は1,000円未満切り捨て）
5. 税額控除（住宅ローン控除）
6. 復興特別所得税（2.1%）
7. 申告納税額（100円未満切り捨て）

**テストシナリオ（tax-domain-expert 設計の5パターン）:**

| パターン | 概要 | 期待納付額 |
|---------|------|-----------|
| 1 | 給与600万+副業300万 青色 ふるさと5万 | 277,400円 |
| 2 | 給与800万+副業200万 青色 住宅ローン3500万 ふるさと10万 配偶者あり | -162,900円（還付）|
| 3 | 給与180万+副業50万 青色 低収入（基礎控除95万適用）| -25,000円（全額還付）|
| 4 | 給与700万+副業1500万 青色 ふるさと15万 簡易課税 | 2,788,700円 |
| 5 | 給与500万+副業100万 青色 住宅ローン2500万 ふるさと3万 | -100,000円（全額還付）|

---

### Task 16: tax_calc_consumption

消費税額の計算。
- 2割特例（最もシンプル）
- 簡易課税（みなし仕入率）
- 本則課税（課税仕入控除）

---

## Phase 5: PDF生成（document）— 4ツール

### Task 17: PDF生成基盤（ユーティリティ + 座標定義）

**Files:**
- Create: `src/shinkoku/tools/pdf_utils.py`
- Create: `src/shinkoku/tools/pdf_coordinates.py`

- IPAexフォントの登録
- オーバーレイ描画の共通関数（テキスト描画、右寄せ数値、チェックボックス）
- 国税庁PDFテンプレートの座標解析（pdfplumber）
- 座標定義ファイル（各帳票の各欄の x, y, font_size, align）

---

### Task 18: doc_generate_bs_pl

**Files:**
- Create: `src/shinkoku/tools/document.py`
- Test: `tests/unit/test_document.py`

青色申告決算書PDF生成。帳簿データから損益計算書 + 貸借対照表を自動取得し、国税庁テンプレートにオーバーレイ。

---

### Task 19: doc_generate_income_tax + doc_generate_consumption_tax + doc_generate_deduction_detail

残りの3つのPDF生成ツール。Task 17-18 の仕組みを横展開。

---

## Phase 6: Skills — 対話系（MCP ツール不依存、Phase 2-5 と並行可能）

### Task 20: assess + gather + submit Skills

**Files:**
- Create: `skills/assess/SKILL.md`
- Create: `skills/gather/SKILL.md`
- Create: `skills/submit/SKILL.md`

MCP ツールを使わない対話系 Skills。各 SKILL.md にフロントマター（name, description）+ 本文（ワークフロー手順）を記述。

---

### Task 21: tax-advisor SKILL.md + reference 19ファイル

**Files:**
- Create: `skills/tax-advisor/SKILL.md`
- Create: `skills/tax-advisor/reference/glossary.md`
- Create: `skills/tax-advisor/reference/income-tax.md`
- ... (19ファイル)

令和7年分改正を反映した税務知識リファレンス。税額計算の速算表、控除の判定フロー、よくある間違い、免責事項。

---

## Phase 7: Skills — ツール連携（Phase 2-5 完了後）

### Task 22: journal SKILL.md

**Files:**
- Create: `skills/journal/SKILL.md`
- Create: `skills/journal/references/account-master.md`

CSV取り込み → ユーザー確認 → 仕訳登録のワークフロー。使用ツール: `ledger_init`, `ledger_add_journal`, `ledger_add_journals_batch`, `ledger_search`, `import_csv`, `import_receipt`, `import_invoice`

---

### Task 23: settlement + income-tax + consumption-tax Skills

**Files:**
- Create: `skills/settlement/SKILL.md` + `references/depreciation-rules.md`
- Create: `skills/income-tax/SKILL.md` + `references/form-b-fields.md`
- Create: `skills/consumption-tax/SKILL.md` + `references/tax-classification.md`

各 Skill が対応する MCP ツールの呼び出し手順をガイド。

---

## Phase 8: 統合テスト・E2Eテスト・検証

### Task 24: 統合テスト

**Files:**
- Create: `tests/integration/test_import_to_ledger.py`
- Create: `tests/integration/test_ledger_to_tax.py`
- Create: `tests/integration/test_tax_to_document.py`

モジュール間連携テスト（取り込み→仕訳登録→税額計算→PDF生成）。

---

### Task 25: E2Eテスト

**Files:**
- Create: `tests/e2e/test_income_tax_flow.py`
- Create: `tests/e2e/test_consumption_tax_flow.py`
- Create: `tests/fixtures/scenarios/*.yaml`

MCP Server 経由のフルフロー。テストシナリオ YAML でデータ定義。

---

### Task 26: CI/CD パイプライン

**Files:**
- Create: `.github/workflows/test.yml`

```
Push/PR → lint (ruff + mypy) → unit tests → integration tests → e2e tests → coverage report
```

---

### Task 27: Plugin ロード確認 + 自分の確定申告データで実行

- `claude --plugin-dir .` で Plugin をロード
- 各 Skill のトリガーテスト
- 自分の令和7年分の実際データでエンドツーエンド実行

---

## Skills ↔ MCP Tools 対応表

| Skill | 使用する MCP ツール |
|-------|-------------------|
| assess | なし（対話のみ） |
| gather | なし（情報提供のみ） |
| journal | `ledger_init`, `ledger_add_journal`, `ledger_add_journals_batch`, `ledger_search`, `ledger_update_journal`, `ledger_delete_journal`, `import_csv`, `import_receipt`, `import_invoice` |
| settlement | `ledger_trial_balance`, `ledger_pl`, `ledger_bs`, `ledger_add_journal`, `tax_depreciation`, `doc_generate_bs_pl` |
| income-tax | `tax_calc_income`, `tax_calc_deductions`, `import_withholding`, `doc_generate_income_tax`, `doc_generate_deduction_detail` |
| consumption-tax | `tax_calc_consumption`, `doc_generate_consumption_tax` |
| submit | なし（情報提供・確認のみ） |
| tax-advisor | なし（リファレンス参照のみ） |

## 端数処理ルール

| 対象 | ルール |
|------|--------|
| 課税所得金額 | 1,000円未満切り捨て |
| 所得税額（申告納税額） | 100円未満切り捨て |
| 復興特別所得税 | 1円未満切り捨て |
| 消費税額（国税分） | 100円未満切り捨て |
| 金額の内部表現 | 常に int（円単位整数）。float 禁止 |

## 令和7年分 税制改正の反映箇所

| 改正内容 | 影響するファイル |
|---------|---------------|
| 基礎控除の引き上げ（最大95万円の段階表） | `tax_calc.py`, `reference/income-deductions.md`, `reference/tax-reform/2025.md` |
| 給与所得控除の最低保障額引き上げ（55万→65万円） | `tax_calc.py`, `reference/income-tax.md` |
| 扶養親族等の所得要件変更（48万→58万円） | `tax_calc.py`, `reference/dependents.md`, `reference/spouse.md` |
| 特定親族特別控除の新設 | `tax_calc.py`, `reference/dependents.md` |
| 配偶者控除の所得要件変更 | `tax_calc.py`, `reference/spouse.md` |
| インボイス2割特例（〜令和8年9月30日） | `tax_calc.py`, `reference/consumption-tax.md`, `reference/tax-reform/transition.md` |
