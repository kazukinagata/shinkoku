# shinkoku

確定申告を自動化する AI コーディングエージェント向けプラグイン。個人事業主・会社員の所得税・消費税の確定申告を、帳簿の記帳から確定申告書等作成コーナーへの入力代行までエンドツーエンドで支援します。

**Claude Code Plugin** として動作するほか、**SKILL.md オープン標準** に準拠した Agent Skills パッケージとして、Claude Code / Cursor / Windsurf / GitHub Copilot / Gemini CLI / Codex / Cline / Roo Code / Antigravity など 40 以上の AI コーディングエージェントで利用できます。

## 想定ユーザー

| 対象 | 対応レベル | 備考 |
|------|-----------|------|
| 個人事業主（青色申告・一般用） | Full | メインターゲット。帳簿 → 決算書 → 税額計算 → 作成コーナー入力 |
| 会社員 + 副業（事業所得） | Full | 源泉徴収票 + 事業所得の税額計算 → 作成コーナー入力 |
| 給与所得のみ（会社員） | Full | 還付申告・医療費控除等 → 作成コーナー入力 |
| 消費税課税事業者 | Full | 2割特例・簡易課税・本則課税すべて対応 |
| ふるさと納税利用者 | Full | 寄附金 CRUD + 控除計算 + 限度額推定 |
| 住宅ローン控除（初年度） | Full | 控除額計算（添付書類は別途必要） |
| 医療費控除 | Full | 明細集計＋控除額計算 |
| 仮想通貨トレーダー | Full | 雑所得（総合課税）として申告書に自動反映 |

- **Full** = 計算＋確定申告書等作成コーナーへの入力代行
- **Out** = 対象外

## 非対応

以下のケースには対応していません。

| 対象 | 理由 |
|------|------|
| 株式投資家（分離課税） | 株式譲渡所得・配当の分離課税 |
| FX トレーダー | 先物取引に係る雑所得等 |
| 不動産所得 | 不動産所得用の決算書・申告 |
| 退職所得 | 退職所得控除の計算 |
| 譲渡所得（不動産売却） | 長期/短期税率、3,000万円特別控除 |
| 外国税額控除 | 外国税支払額の追跡・控除計算 |
| 農業所得・山林所得 | 専用所得区分 |
| 白色申告 | 青色申告のみ対応 |
| 非居住者 | 日本居住者専用 |

---

## ⚠️ 免責事項

**確定申告は自己責任で行ってください。**

- 本ツールが生成した申告書・計算結果は、提出前に**必ずご自身で内容を確認**してください
- 税法の解釈や申告内容に不安がある場合は、**税理士等の専門家に相談**することを強く推奨します
- 本ツールの利用によって生じた**いかなる損害についても、開発者は責任を負いません**
- 税制は毎年改正されます。本ツールは令和7年分（2025年課税年度）の税制に基づいています

---

## インストール

### 前提条件

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャ

### 方法 1: Claude Code プラグイン（フル機能）

プラグイン機能を使い、OCR 画像読取を含む全機能を利用できます。

```bash
# マーケットプレイスを追加
/plugin marketplace add kazukinagata/shinkoku

# プラグインをインストール
/plugin install shinkoku@shinkoku
```

開発・テスト用にローカルから直接読み込む場合:
```bash
claude --plugin-dir /path/to/shinkoku
```

### 方法 2: スキルのみインストール（40+ エージェント対応）

[skills](https://github.com/vercel-labs/skills) CLI でスキルをインストールできます。

```bash
# スキルのインストール（インストール先エージェントを対話的に選択）
npx skills add kazukinagata/shinkoku

# 特定のエージェントにグローバルインストール
npx skills add kazukinagata/shinkoku -g -a claude-code -a cursor

# インストール可能なスキル一覧を確認
npx skills add kazukinagata/shinkoku --list

```

その他の skills コマンド:

```bash
npx skills list              # インストール済みスキルの一覧
npx skills check             # アップデートの確認
npx skills update            # スキルの更新
npx skills remove -s e-tax   # 特定スキルの削除
```

### 環境別の補足

| 環境 | 設定方法 |
|------|---------|
| Claude Code | `/plugin marketplace add kazukinagata/shinkoku` → `/plugin install shinkoku@shinkoku` |
| Cowork | GUI でこのリポジトリの URL をマーケットプレイスに追加し、プラグインをインストール |
| Cursor | プロジェクトルートにスキルを配置。Rules で `SKILL.md` を参照 |
| Windsurf | プロジェクトルートにスキルを配置。Rules で `SKILL.md` を参照 |
| GitHub Copilot | `.github/copilot-instructions.md` からスキルを参照 |
| Gemini CLI | プロジェクトにスキルを追加。`GEMINI.md` から参照 |
| Antigravity | プロジェクトにスキルを配置。Browser Sub-Agent でブラウザ操作も可能 |
| その他（Cline, Roo Code, Codex 等） | 各エージェントのスキル読み込み機能を使用 |

### ブラウザ自動化（e-Tax に必要）

`/e-tax` スキルでは、確定申告書等作成コーナーへの入力にブラウザ自動化が必要です。以下の3方式に対応しています。

| 方式 | 対象環境 | 備考 |
|------|---------|------|
| Claude in Chrome（推奨） | Windows / macOS のネイティブ Chrome | Claude in Chrome 拡張機能が必要 |
| Antigravity Browser Sub-Agent | Windows / macOS / Linux | Antigravity IDE のブラウザ操作機能を利用 |
| Playwright CLI（フォールバック） | WSL / Linux 等 | `@playwright/cli` のインストールが必要 |

Claude in Chrome が利用できない環境では、Antigravity の Browser Sub-Agent または Playwright CLI を使用してください。

#### Playwright CLI のインストール

```bash
# パッケージインストール
npm install -g @playwright/cli@latest

# スキルインストール（エージェントがコマンドを認識するために必要）
playwright-cli install --skills

# Chromium インストール
npx playwright install chromium
```

WSL の場合、GUI 表示が必要です（headed モードで Chrome を操作するため）。Windows 11 では WSLg が標準搭載されており追加設定は不要です。Windows 10 では X Server（VcXsrv 等）が必要です。

## 使い方の流れ

確定申告の作業は、以下のステップを順番に進めていきます。AI エージェントに自然言語で依頼してください。

例: 「確定申告のセットアップをして」「所得税を計算して」「e-Taxで申告して」

### メインワークフロー

```
セットアップ        設定ファイル生成・DB 初期化（AI エージェントに `/setup` と入力）
  |
申告要否判定        申告要否・種類の判定
  |
書類収集            必要書類の収集ナビゲーション
  |
仕訳入力            帳簿管理（CSV / レシート / 請求書の取込）
  |
決算整理            決算書作成（減価償却・PL・BS）
  |
所得税計算          所得税計算
  |
消費税計算          消費税計算（課税事業者のみ）
  |
提出準備            最終チェックリスト
  |
e-Tax 電子申告      確定申告書等作成コーナーへの入力代行（e-Tax 利用者のみ）
```

### 補助スキル（必要に応じて）

- 税務相談 --- 税務に関する質問にいつでも回答
- ふるさと納税 --- 寄附金管理・控除計算
- 機能確認 --- shinkoku の対応範囲・機能の確認

## スキル一覧

### メインワークフロー

| スキル | 説明 |
|-------|------|
| `/setup` | 初回セットアップ。設定ファイル（`shinkoku.config.yaml`）の生成とデータベースの初期化 |
| `/assess` | 確定申告が必要かどうか、所得税・消費税の申告要否を判定 |
| `/gather` | 必要書類のチェックリストと取得先を案内 |
| `/journal` | CSV・レシート・請求書・源泉徴収票を取り込み、複式簿記の仕訳を登録 |
| `/settlement` | 減価償却・決算整理仕訳の登録、残高試算表・損益計算書・貸借対照表の生成 |
| `/income-tax` | 所得税額を計算（所得控除・税額控除・復興特別所得税） |
| `/consumption-tax` | 消費税額を計算（2割特例・簡易課税・本則課税） |
| `/submit` | 最終確認チェックリストと提出方法（e-Tax / 郵送 / 持参）の案内 |
| `/e-tax` | 確定申告書等作成コーナーへの入力代行（Claude in Chrome / Playwright / Antigravity） |

### 補助スキル

| スキル | 説明 |
|-------|------|
| `/tax-advisor` | 控除・節税・税制についての質問に回答する税務アドバイザー |
| `/furusato` | ふるさと納税の寄附金登録・一覧・削除・集計と控除限度額推定 |
| `/invoice-system` | インボイス制度関連の参照情報 |
| `/capabilities` | shinkoku の対応範囲・対応ペルソナ・既知の制限事項を表示 |
| `/incorporation` | 法人成り（個人事業主から法人への移行）の税額比較・設立手続き相談 |

### OCR 読取スキル

| スキル | 読取対象 |
|-------|---------|
| `/reading-receipt` | レシート・領収書・ふるさと納税受領証明書 |
| `/reading-withholding` | 源泉徴収票 |
| `/reading-invoice` | 請求書 |
| `/reading-deduction-cert` | 控除証明書（生命保険料・地震保険料等） |
| `/reading-payment-statement` | 支払調書 |

## 対応エージェント

### OCR 画像読取

レシート・源泉徴収票等の画像読取（`/reading-*` スキル）は、利用する LLM がマルチモーダル（画像認識）に対応している必要があります。これはエージェントプラットフォームではなく、接続先の LLM の能力に依存します。

- **マルチモーダル LLM**（Claude 3.5+, GPT-4o, Gemini 等）: OCR 読取可能
- **テキスト専用 LLM**: 手動入力が必要

### OCR デュアル検証（サブエージェント利用）

2つのサブエージェントが独立に画像を読み取り、結果をクロスチェックする機能です。サブエージェントの並列実行に対応したプラットフォームで利用できます。非対応のプラットフォームでは、単一読取 + ユーザー確認にフォールバックします。

| エージェント | デュアル検証 |
|-------------|:---:|
| Claude Code | ✓ |
| Cowork | ✓ |
| Cursor 2.5+ | ✓ |
| GitHub Copilot | ✓ |
| Cline | ✓ |
| Antigravity | ✓ |
| Windsurf | — |
| Gemini CLI | △ |
| Roo Code | △ |

- **△**: サブエージェント機能はあるが並列実行が制限的

## 開発者向け情報

### テスト

```bash
make test                              # 全テスト実行
uv run pytest tests/unit/ -v           # ユニットテスト
uv run pytest tests/scripts/ -v        # CLI テスト
uv run pytest tests/integration/ -v    # 統合テスト
uv run pytest tests/e2e/ -v           # E2E テスト
```

### Lint / 型チェック

```bash
make lint                                            # Ruff lint + format + mypy
uv run ruff format --check src/ tests/               # フォーマットチェック
uv run mypy src/shinkoku/ --ignore-missing-imports   # 型チェック
```

### プロジェクト構成

```
shinkoku/
├── .claude-plugin/
│   └── plugin.json              # Claude Code プラグインマニフェスト
├── .github/
│   └── workflows/
│       └── test.yml             # CI パイプライン
├── skills/                      # Agent Skills（SKILL.md オープン標準）
│   ├── setup/SKILL.md           #   初回セットアップ
│   ├── assess/SKILL.md          #   申告要否判定
│   ├── gather/SKILL.md          #   書類収集
│   ├── journal/SKILL.md         #   仕訳入力・帳簿管理
│   ├── settlement/SKILL.md      #   決算整理・決算書作成
│   ├── income-tax/SKILL.md      #   所得税計算
│   ├── consumption-tax/SKILL.md #   消費税計算
│   ├── submit/SKILL.md          #   提出準備
│   ├── tax-advisor/SKILL.md     #   税務アドバイザー
│   ├── furusato/SKILL.md        #   ふるさと納税
│   ├── e-tax/SKILL.md           #   e-Tax 電子申告（Claude in Chrome）
│   ├── capabilities/SKILL.md    #   機能確認
│   ├── incorporation/SKILL.md   #   法人成り相談
│   ├── reading-receipt/SKILL.md          # OCR: レシート
│   ├── reading-withholding/SKILL.md      # OCR: 源泉徴収票
│   ├── reading-invoice/SKILL.md          # OCR: 請求書
│   ├── reading-deduction-cert/SKILL.md   # OCR: 控除証明書
│   └── reading-payment-statement/SKILL.md # OCR: 支払調書
├── src/shinkoku/
│   ├── cli/                     # CLI エントリーポイント（shinkoku コマンド）
│   │   ├── __init__.py          #   main() + サブコマンド登録
│   │   ├── ledger.py            #   帳簿管理 CLI
│   │   ├── tax_calc.py          #   税額計算 CLI
│   │   ├── import_data.py       #   データ取込 CLI
│   │   ├── furusato.py          #   ふるさと納税 CLI
│   │   └── profile.py           #   プロファイル CLI
│   ├── tools/                   # ビジネスロジック（純粋関数）
│   │   ├── ledger.py            #   帳簿管理
│   │   ├── tax_calc.py          #   税額計算
│   │   ├── import_data.py       #   データ取り込み
│   │   ├── furusato.py          #   ふるさと納税
│   │   └── profile.py           #   プロファイル取得
│   ├── models.py                # Pydantic モデル定義
│   ├── db.py                    # SQLite DB 管理
│   ├── master_accounts.py       # 勘定科目マスタ
│   ├── tax_constants.py         # 税制定数
│   ├── config.py                # 設定ファイル読み込み
│   ├── hashing.py               # ハッシュユーティリティ
│   └── duplicate_detection.py   # 重複検出ロジック
├── tests/
│   ├── unit/                    # ユニットテスト
│   ├── scripts/                 # CLI テスト
│   ├── integration/             # 統合テスト
│   ├── e2e/                     # E2E テスト
│   ├── fixtures/                # テストフィクスチャ
│   └── helpers/                 # テストヘルパー
├── shinkoku.config.example.yaml # 設定ファイルテンプレート
├── pyproject.toml
├── Makefile
└── uv.lock
```

### 技術スタック

- Python 3.11+
- SQLite（WAL モード）
- Pydantic（モデル定義・バリデーション）
- pdfplumber（PDF 読取）
- Playwright（ブラウザ自動化フォールバック — Python `playwright` + npm `@playwright/cli`）
- PyYAML（設定ファイル読み込み）
- Ruff（lint / format）
- mypy（型チェック）
- pytest（テスト）

## ライセンス

MIT License -- 詳細は [LICENSE](./LICENSE) を参照してください。

## コントリビュート

Issue や Pull Request を歓迎します。日本語での報告・提案で構いません。

- バグ報告: Issue を作成してください。再現手順があると助かります
- 機能提案: Issue で議論した上で PR を作成してください
- PR: `main` ブランチに対して作成してください。CI（lint + テスト）が通ることを確認してください
