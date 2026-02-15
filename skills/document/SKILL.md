---
name: document
description: >
  This skill should be used when the user needs to generate tax filing PDF
  documents (確定申告書類PDF). It orchestrates the creation of all required
  forms by spawning pdf-form-filler sub-agents. Trigger phrases include:
  "書類を作成", "PDFを生成", "申告書を出力", "帳票を作成", "/document",
  "確定申告書類", "書類一式", "PDF一式".
---

# 確定申告書類PDF作成（Document Generation Orchestration）

確定申告に必要なPDF帳票の生成をオーケストレーションするスキル。
各帳票の生成は `pdf-form-filler` サブエージェントに委任し、メインコンテキストの消費を最小化する。

## 設定の読み込み（最初に実行）

1. `shinkoku.config.yaml` を Read ツールで読み込む
2. ファイルが存在しない場合は `/setup` スキルの実行を案内して終了する
3. 納税者プロフィール・住所・事業情報・申告方法・還付口座を把握する

## 進捗情報の読み込み

1. `.shinkoku/progress/progress-summary.md` を Read ツールで読み込む（存在する場合）
2. 以下の引継書を Read ツールで読み込む（存在する場合）:
   - `.shinkoku/progress/06-settlement.md` — 決算結果（PL/BS データ）
   - `.shinkoku/progress/07-income-tax.md` — 所得税計算結果
   - `.shinkoku/progress/08-consumption-tax.md` — 消費税計算結果
   - `.shinkoku/progress/02-assess.md` — 課税判定結果
3. 計算結果がまだ存在しない場合は、先に `/income-tax` や `/settlement` の実行を案内する

## 必要帳票の判定

進捗情報と config に基づいて生成する帳票を判定する:

### 全員必須
| 帳票 | テンプレート | 条件 |
|------|------------|------|
| 確定申告書 第一表 | `templates/r07/01.pdf` | 常に |
| 確定申告書 第二表 | `templates/r07/02.pdf` | 常に |

### 青色申告の場合
| 帳票 | テンプレート | 条件 |
|------|------------|------|
| 青色申告決算書 損益計算書 (P1-P3) | `templates/r07/10.pdf` (p1-p3) | `filing.return_type == "blue"` |
| 青色申告決算書 貸借対照表 | `templates/r07/10.pdf` (p4) | `filing.return_type == "blue"` |

### 白色申告の場合
| 帳票 | テンプレート | 条件 |
|------|------------|------|
| 収支内訳書 | `templates/r07/05.pdf` | `filing.return_type == "white"` |

### 該当者のみ
| 帳票 | テンプレート | 条件 |
|------|------------|------|
| 第三表（分離課税） | `templates/r07/02.pdf` | 株式・FX の分離課税あり |
| 第四表（損失申告） | `templates/r07/03.pdf` | 純損失の繰越あり |
| 消費税申告書 | `templates/consumption_tax.pdf` | 課税事業者の場合 |
| 医療費控除明細書 | `templates/medical_expense.pdf` | 医療費控除適用者 |
| 住宅ローン控除明細書 | `templates/r07/14.pdf` | 住宅ローン控除初年度 |

## 帳票生成の実行

各帳票について `pdf-form-filler` サブエージェントを Task ツールで spawn する。

### spawn 時に渡す情報

1. **帳票種類**: 生成する帳票の名称
2. **テンプレートPDFのパス**: `templates/r07/` 内のファイル
3. **入力データ**: 進捗情報から取得した計算結果 + config のプロフィール情報
4. **出力先**: `{output_dir}/{帳票名}_{fiscal_year}.pdf`

### spawn の例

```
Task tool:
  subagent_type: general-purpose
  prompt: |
    pdf-form-filler エージェントとして動作してください。
    skills/filling-pdf/SKILL.md を読んで手順に従ってください。

    帳票種類: 確定申告書 第一表
    テンプレート: templates/r07/01.pdf
    出力先: output/income_tax_p1_2025.pdf

    入力データ:
    [計算結果・プロフィール情報をここに記載]
```

## 生成後の確認

1. 全サブエージェント完了後、生成されたPDFの一覧を表示する
2. `doc_preview_pdf` ツールでPDFをPNG画像に変換してプレビューする
3. ユーザーに目視確認を促す
4. 修正が必要な場合は該当帳票のサブエージェントを再 spawn する

## 出力サマリー

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
確定申告書類PDF生成結果（令和○年分）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 生成した帳票:
  ✓ 確定申告書 第一表: output/income_tax_p1_2025.pdf
  ✓ 確定申告書 第二表: output/income_tax_p2_2025.pdf
  ✓ 青色申告決算書 損益計算書: output/blue_return_pl_2025.pdf
  ✓ 青色申告決算書 貸借対照表: output/blue_return_bs_2025.pdf
  [該当する帳票のみ表示]

■ プレビュー画像:
  output/ ディレクトリ内のPNG画像を確認してください。

■ 次のステップ:
  → /submit で提出準備を行う
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## NTA公式様式について

テンプレートPDFは国税庁公式サイトからダウンロードする。
URL一覧は `skills/filling-pdf/references/nta-form-urls.md` を参照。
