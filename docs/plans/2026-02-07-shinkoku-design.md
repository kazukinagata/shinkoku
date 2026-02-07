# shinkoku - 確定申告自動化 Claude Code Plugin 設計書

## 概要

確定申告を丸ごと自動化するClaude Code Plugin（OSS）。

- 会社員＋副業（事業所得・青色申告）の所得税・消費税確定申告をエンドツーエンドで支援
- freee等の会計SaaSに依存せず、ローカルで完結
- データは手元に残る（プライバシー安全）
- OSSとして公開（コードの透明性が信頼の担保）

## 背景・ペイン

- 一年に一回しかやらない確定申告を毎回忘れてスムーズにいかない
- 仕訳入力（クレカ明細DL、レシート収集、請求書PDF→1つずつ入力）が苦痛
- ステップバイステップの質問対応で途中で必要書類が判明してDL作業が発生
- 住宅購入初年度の手続き、不明用語の調査など都度の調べ直しが負担
- 消費税の課税事業者判定基準など、税務知識の再学習コストが高い

## ターゲットユーザー

- v0.1: 自分自身（会社員＋副業・青色申告・住宅ローン控除初年度・ふるさと納税）
- 将来: フリーランス、小規模スタートアップ経営者

## アーキテクチャ

```
shinkoku/
├── .claude-plugin/
│   └── plugin.json               # Claude Code Plugin マニフェスト
├── .mcp.json                     # MCP Server 定義
├── skills/
│   ├── assess/SKILL.md           # 申告要否・種類の判定
│   ├── gather/SKILL.md           # 書類収集ナビゲーション
│   ├── journal/SKILL.md          # 仕訳入力
│   ├── settlement/SKILL.md       # 決算整理・決算書作成
│   ├── income-tax/SKILL.md       # 所得税 確定申告書作成
│   ├── consumption-tax/SKILL.md  # 消費税 確定申告書作成
│   ├── submit/SKILL.md           # 提出準備・チェックリスト
│   └── tax-advisor/
│       ├── SKILL.md              # 税務アドバイザー（専門家レベル）
│       └── reference/            # 税務知識リファレンス（19ファイル）
├── src/
│   └── mcp-server/               # Python MCP Server
│       ├── server.py
│       └── tools/
│           ├── ledger.py         # 帳簿管理
│           ├── import_data.py    # データ取り込み
│           ├── tax_calc.py       # 税額計算
│           └── document.py       # 申告書PDF生成
├── data/                         # ユーザーデータ（.gitignore対象）
│   ├── receipts/                 # レシート画像
│   ├── statements/               # クレカ明細CSV
│   ├── documents/                # 源泉徴収票等のPDF
│   └── ledger.db                 # 帳簿データ（SQLite）
└── output/                       # 生成された申告書類PDF
```

## 技術スタック

| 領域 | 技術 | 理由 |
|------|------|------|
| MCP Server | Python (mcp SDK) | PDF・数値計算のエコシステムが充実 |
| MCP通信 | stdio（ローカル） | センシティブデータをネットワークに流さない |
| データストア | SQLite (sqlite3) | 複式簿記に適したRDB。追加依存なし |
| PDF生成（v0.1） | ReportLab + pypdf | オーバーレイ方式の実装例が豊富 |
| PDF座標解析 | pdfplumber | テンプレートのフィールド位置特定 |
| OCR | Claude Vision（Skillから直接） | レシート・請求書の読み取り |
| テスト | pytest | Python標準 |

## Skills 設計

### ワークフロー系Skills

| Skill | 役割 | 主な操作 |
|-------|------|---------|
| `assess` | 申告要否・種類の判定 | 給与収入、副業売上、課税事業者判定、必要な申告の種類を対話で特定 |
| `gather` | 書類収集ナビゲーション | 判定結果に基づき必要書類を一覧化。取得先を案内 |
| `journal` | 仕訳入力 | クレカ明細CSV・レシート画像・請求書PDFを取り込み、勘定科目・課税区分を推定して仕訳登録 |
| `settlement` | 決算整理・決算書作成 | 減価償却、家事按分、棚卸、青色申告決算書の生成 |
| `income-tax` | 所得税 確定申告書作成 | 確定申告書Bの各欄を計算・入力、控除適用、PDF生成 |
| `consumption-tax` | 消費税 確定申告書作成 | 課税売上・仕入の集計、簡易課税/本則課税の選択、消費税申告書PDF生成 |
| `submit` | 提出準備・チェックリスト | 最終確認、提出方法の案内（e-Tax / 郵送 / 持参） |

### アドバイザー系Skills

| Skill | 役割 |
|-------|------|
| `tax-advisor` | 税務アドバイザー。税理士・ライフプランナー相当の専門知識で質問に回答 |

## tax-advisor リファレンス構成

税務エキスパートレビュー済み。

```
reference/
├── glossary.md              # 用語定義（収入vs所得、変換表）
├── income-tax.md            # 所得税（税率表、所得区分、損益通算）
├── resident-tax.md          # 住民税（税率、非課税、普通徴収/特別徴収）
├── consumption-tax.md       # 消費税（課税事業者判定、簡易課税、インボイス、2割特例）
├── income-deductions.md     # 所得控除一覧（基礎・社保・生保・寄附金等）
├── tax-credits.md           # 税額控除（配当控除、外国税額控除等）
├── medical-expenses.md      # 医療費控除・セルフメディケーション税制
├── spouse.md                # 配偶者控除・配偶者特別控除
├── dependents.md            # 扶養控除（税法上/住民税上/社保上の違い）
├── housing-loan.md          # 住宅ローン控除（初年度要件、ふるさと納税との相互影響）
├── blue-return.md           # 青色申告の特典・要件・65万控除の条件
├── business-expenses.md     # 事業所得の経費・家事按分・記帳実務
├── withholding-tax.md       # 源泉徴収・年末調整との関係
├── social-insurance.md      # 社会保険（扶養判定、130万/106万の壁）
├── filing-procedure.md      # 確定申告の手続き・期限・必要書類・e-Tax
├── life-planning.md         # ライフプラン（iDeCo、NISA、小規模企業共済、ふるさと納税最適額、法人成り判断）
├── common-mistakes.md       # よくある間違い・落とし穴集
├── tax-reform/
│   ├── 2025.md              # 令和7年分改正ポイント
│   ├── transition.md        # 経過措置一覧
│   └── upcoming.md          # 翌年以降の予定改正
└── disclaimer.md            # 免責事項テンプレート
```

### 設計方針

- referenceファイルに体系的な知識を持たせる（Claudeの一般知識に頼らない）
- 年度ファイルで税制改正に対応（翌年は新しい年度ファイルを追加するだけ）
- 回答には根拠条文・通達の参照を付ける
- 判定フローチャートを含める（Yes/Noで辿れる形式）
- ユーザーは「収入」で質問するため、自動的に「所得」に変換して判定する
- 免責を明示（最終判断は税理士への確認を推奨）

## MCP Server ツール設計

### 帳簿管理（ledger）

| ツール | 説明 |
|--------|------|
| `ledger_init` | 新しい年度の帳簿を初期化（SQLiteファイル作成、勘定科目マスタ設定） |
| `ledger_add_journal` | 仕訳を1件登録（日付、借方/貸方、金額、摘要、課税区分） |
| `ledger_add_journals_batch` | 仕訳を一括登録 |
| `ledger_search` | 仕訳の検索・一覧取得 |
| `ledger_update_journal` | 仕訳の修正 |
| `ledger_delete_journal` | 仕訳の削除 |
| `ledger_trial_balance` | 残高試算表の生成 |
| `ledger_pl` | 損益計算書の生成 |
| `ledger_bs` | 貸借対照表の生成 |

### データ取り込み（import）

| ツール | 説明 |
|--------|------|
| `import_csv` | クレカ明細CSVを読み込み、勘定科目・課税区分をAI推定した仕訳候補を返す |
| `import_receipt` | レシート画像をOCR（Claude Vision）で読み取り、仕訳候補を返す |
| `import_invoice` | 請求書PDFを読み取り、仕訳候補を返す |
| `import_withholding` | 源泉徴収票の読み取り（給与収入、社会保険料、源泉徴収額を構造化） |

### 税額計算（tax）

| ツール | 説明 |
|--------|------|
| `tax_calc_income` | 所得税額の計算（所得合算、控除適用、税率適用） |
| `tax_calc_consumption` | 消費税額の計算（本則課税/簡易課税） |
| `tax_calc_deductions` | 適用可能な控除の一覧と計算 |
| `tax_depreciation` | 減価償却費の計算（定額法/定率法、耐用年数判定） |

### 書類生成（document）

| ツール | 説明 |
|--------|------|
| `doc_generate_bs_pl` | 青色申告決算書PDF生成（損益計算書＋貸借対照表） |
| `doc_generate_income_tax` | 確定申告書B PDF生成 |
| `doc_generate_consumption_tax` | 消費税申告書PDF生成 |
| `doc_generate_deduction_detail` | 各種控除の明細書PDF生成 |

## データモデル（SQLite）

```sql
-- 勘定科目マスタ
CREATE TABLE accounts (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,    -- 'asset','liability','equity','revenue','expense'
  tax_category TEXT          -- 'taxable','non_taxable','exempt','out_of_scope'
);

-- 仕訳
CREATE TABLE journals (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,        -- 'YYYY-MM-DD'
  description TEXT,
  source TEXT,               -- 'csv_import','receipt_ocr','manual'
  source_file TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- 仕訳明細（借方・貸方）
CREATE TABLE journal_lines (
  id INTEGER PRIMARY KEY,
  journal_id INTEGER REFERENCES journals(id),
  side TEXT NOT NULL,        -- 'debit' or 'credit'
  account_code TEXT REFERENCES accounts(code),
  amount INTEGER NOT NULL,   -- 円単位（整数）
  tax_category TEXT,
  tax_rate INTEGER           -- 消費税率（10, 8）
);

-- 固定資産台帳
CREATE TABLE fixed_assets (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  acquisition_date TEXT,
  acquisition_cost INTEGER,
  useful_life INTEGER,
  method TEXT,               -- 'straight_line','declining_balance'
  memo TEXT
);
```

## 書類生成の技術的アプローチ

### v0.1: PDFオーバーレイ方式（書面提出）

- 国税庁が公式サイトで配布しているPDFテンプレートに、座標指定でデータを重ねて描画
- ReportLab でテキスト描画、pypdf でテンプレートとマージ
- 白黒印刷で受理可能。印刷して郵送または持参で提出

### v0.2: xtx（XML）生成方式（電子申告）

- 国税庁がXMLスキーマ（XSD）と仕様書を公式に一般公開している（https://www.e-tax.nta.go.jp/shiyo/shiyo3.htm）
- freee・マネーフォワード・弥生も同じ仕様に基づいてxtx出力を実装
- 対応範囲:
  - 所得税確定申告書のxtx生成
  - 消費税申告書のxtx生成
  - 青色申告決算書のxtx生成
  - 各種控除明細書のxtx生成
  - xtxバリデーション（XSDスキーマに対する検証）
  - e-Taxソフトへの読み込み・送信の手順ガイド（submit Skillの拡張）

## フェーズ計画

### v0.1 — 自分の確定申告を完遂する

- 会社員＋副業（事業所得・青色申告）の所得税確定申告
- 消費税確定申告（課税事業者判定〜申告書作成）
- 住宅ローン控除（初年度）、ふるさと納税
- 書類生成はPDFオーバーレイ方式（書面提出）
- Skills 全8種 + tax-advisor
- MCP Server ツール群

### v0.2 — e-Tax電子申告対応（xtx生成）

- e-Tax仕様書（XSD・XML構造設計書）の解析と実装
- 所得税・消費税・青色申告決算書・控除明細書のxtx生成
- xtxバリデーション
- submit Skillの拡張（e-Taxソフトへの読み込み手順ガイド）

### v0.3以降 — 拡張（構想）

- 対応する申告パターンの拡大（不動産所得、株式譲渡、退職所得など）
- 年末調整対応
- 住民税・事業税の試算
- コアロジックのライブラリ分離（ハイブリッド型への移行）
