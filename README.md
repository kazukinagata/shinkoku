# shinkoku

確定申告を自動化する Claude Code Plugin。会社員＋副業（事業所得・青色申告）の所得税・消費税確定申告をエンドツーエンドで支援。

## 概要

shinkoku は Claude Code Plugin（MCP Server）として動作し、会社員で副業を行う個人事業主（事業所得・青色申告）を対象とした確定申告の自動化ツールです。帳簿の記帳から税額計算、PDF帳票の生成まで、確定申告ワークフローの全体を8つの対話型スキルでカバーします。複式簿記に準拠した仕訳管理、令和7年分の税制改正を反映した所得税・消費税の自動計算、確定申告書B・青色申告決算書・消費税申告書のPDF生成に対応しています。

## 特徴

**帳簿管理**
- 複式簿記に準拠した仕訳入力・管理
- CSV・レシート・請求書・源泉徴収票の取り込み
- 残高試算表・損益計算書・貸借対照表の自動生成

**税額計算**
- 所得税（給与所得控除、各種所得控除、税額控除、復興特別所得税）
- 消費税（2割特例・簡易課税・本則課税）
- 控除の自動計算（基礎控除、社会保険料、生命保険料、配偶者控除 等）
- 減価償却（定額法・定率法）

**帳票生成**
- 確定申告書B（第一表・第二表）のPDF生成
- 青色申告決算書のPDF生成
- 消費税申告書のPDF生成

**スキル**
- 8つの対話型ワークフローによる段階的なガイド

## 前提条件

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャ
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

## インストール

```bash
git clone https://github.com/kazukinagata/shinkoku.git
cd shinkoku
uv sync --all-extras
```

## 設定

`shinkoku.config.example.yaml` を `shinkoku.config.yaml` にコピーして編集します。

```bash
cp shinkoku.config.example.yaml shinkoku.config.yaml
```

| フィールド | 説明 |
|-----------|------|
| `tax_year` | 対象年度（例: `2025`） |
| `invoices_dir` | 売上データ（請求書PDF等）が格納されたディレクトリ |
| `withholding_slips_dir` | 源泉徴収票が格納されたディレクトリ |
| `past_returns_dir` | 過去の確定申告データ（参考用） |

`shinkoku.config.yaml` は `.gitignore` に含まれるため、リポジトリにはコミットされません。

## 使い方

プラグインとして Claude Code を起動します。

```bash
make dev
```

起動後、以下の順序でスキルを利用して確定申告を進めます。

1. `/assess` — 申告の種類を判定
2. `/gather` — 必要書類を収集
3. `/journal` — 仕訳を入力・帳簿管理
4. `/settlement` — 決算整理・決算書作成
5. `/income-tax` — 所得税計算・確定申告書PDF生成
6. `/consumption-tax` — 消費税計算・申告書PDF生成（課税事業者のみ）
7. `/submit` — 提出準備・チェックリスト

税務に関する質問は `/tax-advisor` でいつでも相談できます。

## スキル一覧

| スキル | 説明 | 使うタイミング |
|-------|------|---------------|
| `/assess` | 申告要否・種類の判定 | 最初に実行。確定申告が必要かどうか、所得税・消費税・住民税の申告要否を判定 |
| `/gather` | 書類収集ナビゲーション | assess の後。必要書類のチェックリストと取得先を案内 |
| `/journal` | 仕訳入力・帳簿管理 | 書類が揃った後。CSV/レシート/請求書を取り込み、仕訳を登録 |
| `/settlement` | 決算整理・決算書作成 | 日常仕訳の入力完了後。減価償却・決算整理仕訳の登録、試算表・PL・BSの生成 |
| `/income-tax` | 所得税計算・確定申告書作成 | 決算書の完成後。所得税額を計算し、確定申告書BのPDFを生成 |
| `/consumption-tax` | 消費税計算・申告書作成 | 課税事業者のみ。消費税額を計算し、消費税申告書PDFを生成 |
| `/submit` | 提出準備・チェックリスト | 申告書の完成後。最終確認と提出方法（e-Tax/郵送/持参）の案内 |
| `/tax-advisor` | 税務アドバイザー | いつでも。控除・節税・税制についての質問に回答 |

## 開発

```bash
# テスト
make test
uv run pytest tests/unit/ -v       # ユニットテスト
uv run pytest tests/integration/ -v # 統合テスト
uv run pytest tests/e2e/ -v         # E2Eテスト

# Lint
make lint
uv run ruff format --check src/ tests/

# 型チェック
uv run mypy src/shinkoku/ --ignore-missing-imports
```

テスト構成:
- `tests/unit/` — 個別関数・モジュールの単体テスト
- `tests/integration/` — モジュール間連携のテスト
- `tests/e2e/` — YAMLシナリオデータによるエンドツーエンドテスト

## プロジェクト構成

```
shinkoku/
├── .claude-plugin/
│   └── plugin.json          # プラグインマニフェスト
├── .github/
│   └── workflows/
│       └── test.yml         # CI パイプライン
├── skills/                  # 対話型ワークフロー定義
│   ├── assess/SKILL.md      # 申告要否判定
│   ├── gather/SKILL.md      # 書類収集
│   ├── journal/SKILL.md     # 仕訳入力
│   ├── settlement/SKILL.md  # 決算整理
│   ├── income-tax/SKILL.md  # 所得税計算
│   ├── consumption-tax/SKILL.md  # 消費税計算
│   ├── submit/SKILL.md      # 提出準備
│   └── tax-advisor/SKILL.md # 税務アドバイザー
├── src/shinkoku/
│   ├── server.py            # MCP Server エントリーポイント
│   ├── models.py            # Pydantic モデル定義
│   ├── db.py                # SQLite DB 管理
│   ├── master_accounts.py   # 勘定科目マスタ
│   └── tools/               # MCP ツール
│       ├── ledger.py        # 帳簿管理（仕訳CRUD・財務諸表）
│       ├── tax_calc.py      # 税額計算（所得税・消費税・控除・減価償却）
│       ├── import_data.py   # データ取り込み（CSV・レシート・請求書）
│       ├── document.py      # PDF帳票生成
│       ├── pdf_utils.py     # PDF生成ユーティリティ
│       └── pdf_coordinates.py  # PDF座標定義
├── tests/
│   ├── unit/                # ユニットテスト
│   ├── integration/         # 統合テスト
│   └── e2e/                 # E2Eテスト
├── shinkoku.config.example.yaml  # 設定ファイルテンプレート
├── pyproject.toml           # プロジェクト設定
├── Makefile                 # 開発コマンド
└── uv.lock                  # 依存関係ロックファイル
```

## ライセンス

MIT

## 免責事項

本ツールは確定申告の作業を支援する目的で提供されています。生成された申告書の内容については、提出前に必ず税理士等の専門家に確認を取ることを推奨します。本ツールの利用によって生じたいかなる損害についても、開発者は責任を負いません。
