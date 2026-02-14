---
name: income-tax
description: >
  This skill should be used when the user needs to calculate their income tax
  (所得税), generate the tax return form (確定申告書), compute deductions, or
  import withholding slips. Trigger phrases include: "所得税を計算",
  "確定申告書を作成", "控除を計算", "源泉徴収票を取り込む", "所得税額",
  "納付額を計算", "還付額を計算", "確定申告書PDF", "第一表", "第二表",
  "申告書B", "所得控除", "税額控除".
---

# 所得税計算・確定申告書作成（Income Tax Calculation）

事業所得・各種控除から所得税額を計算し、確定申告書（申告書B様式）のPDFを生成するスキル。
settlement スキルで決算書の作成が完了していることを前提とする。

## 設定の読み込み（最初に実行）

1. `shinkoku.config.yaml` を Read ツールで読み込む
2. ファイルが存在しない場合は `/setup` スキルの実行を案内して終了する
3. 設定値を把握し、相対パスは CWD を基準に絶対パスに変換する:
   - `db_path`: MCP ツールの `db_path` 引数に使用
   - `output_dir`: PDF 生成時の `output_path` 引数のベースディレクトリに使用
   - 各ディレクトリ: ファイル参照時に使用

### パス解決の例

config の `output_dir` が `./output` で CWD が `/home/user/tax-2025/` の場合:
- `generate_income_tax_pdf(output_path="/home/user/tax-2025/output/income_tax_2025.pdf", ...)`
- `generate_deduction_detail_pdf(output_path="/home/user/tax-2025/output/deduction_detail_2025.pdf", ...)`

## 基本方針

- settlement スキルで青色申告決算書が完成しているか確認してから開始する
- 所得の計算 → 控除の計算 → 税額の計算 → PDF生成 の順序で進める
- 各ステップの計算結果をユーザーに提示し、確認を得る
- references/form-b-fields.md の各欄に正しく値を設定する
- 端数処理ルール（課税所得: 1,000円未満切り捨て、税額: 100円未満切り捨て）を厳守する

## 前提条件の確認

所得税計算を開始する前に以下を確認する:

1. **青色申告決算書が完成しているか**: settlement スキルの出力を確認する
2. **事業所得以外の所得**: 給与所得・雑所得等がある場合は情報を収集する
3. **源泉徴収票**: 給与所得がある場合は取り込みを案内する
4. **各種控除の適用状況**: 適用可能な控除を網羅的に確認する

## ステップ1: 源泉徴収票の取り込み

給与所得がある場合、源泉徴収票からデータを取り込む。

### `import_withholding` の呼び出し

```
パラメータ:
  file_path: str — 源泉徴収票の画像またはPDFファイルのパス

戻り値:
  - payer_name: 支払者名
  - payment_amount: 支払金額（給与収入）
  - deduction_amount: 給与所得控除後の金額
  - income_tax_withheld: 源泉徴収税額
  - social_insurance: 社会保険料等の金額
  - life_insurance: 生命保険料の控除額
  - spouse_deduction: 配偶者控除の額
```

**取り込み後の処理:**

1. 抽出された各金額が正しいか確認する
2. 複数の勤務先がある場合は各社分を取り込む
3. 年末調整済みの控除を確認し、追加控除の有無を判定する

## ステップ2: 所得控除の計算

### `calc_deductions` の呼び出し

```
パラメータ:
  fiscal_year: int           — 会計年度
  social_insurance: int      — 社会保険料の年間支払額
  life_insurance_premium: int — 生命保険料
  medical_expenses: int      — 医療費（保険金差引後）
  spouse_income: int | None  — 配偶者の所得金額
  dependents: int            — 扶養親族の数
  ideco: int                 — iDeCo掛金
  donation: int              — ふるさと納税等の寄附金
  ... その他控除項目

戻り値: DeductionsResult
  - basic_deduction: 基礎控除
  - social_insurance_deduction: 社会保険料控除
  - life_insurance_deduction: 生命保険料控除
  - medical_deduction: 医療費控除
  - spouse_deduction: 配偶者控除
  - dependent_deduction: 扶養控除
  - small_enterprise_deduction: 小規模企業共済等掛金控除
  - donation_deduction: 寄附金控除
  - total_deductions: 所得控除合計
```

**各控除の確認事項:**

- 基礎控除: 合計所得金額に応じた段階的控除（令和7年分の改正を反映）
- 社会保険料控除: 国民年金・国民健康保険・その他の年間支払額
- 生命保険料控除: 新旧制度の区分を確認する
- 医療費控除: 支払額から保険金等の補填額を差し引き、10万円（または所得の5%）を超える部分
- 配偶者控除/特別控除: 配偶者の所得に応じて段階的に控除額が変動
- ふるさと納税: 寄附金 − 2,000円（確定申告ではワンストップ特例分も含める）

## ステップ3: 所得税額の計算

### `calc_income_tax` の呼び出し

```
パラメータ: IncomeTaxInput
  - fiscal_year: int             — 会計年度
  - business_income: int         — 事業所得
  - salary_income: int           — 給与収入（収入金額）
  - other_income: int            — その他の所得
  - blue_return_deduction: int   — 青色申告特別控除額（65万/10万/0）
  - deductions: DeductionsResult — 所得控除の計算結果
  - withholding_tax: int         — 源泉徴収税額（予定納税含む）
  - housing_loan_credit: int     — 住宅ローン控除額

戻り値: IncomeTaxResult
  - total_income: 合計所得金額
  - taxable_income: 課税所得金額（1,000円未満切り捨て）
  - income_tax: 算出税額
  - tax_credits: 税額控除合計
  - reconstruction_tax: 復興特別所得税（基準所得税額 × 2.1%）
  - total_tax: 所得税及び復興特別所得税の額
  - withholding_tax: 源泉徴収税額
  - tax_due: 申告納税額（プラスなら納付、マイナスなら還付）
```

**計算結果の確認:**

1. 合計所得金額の内訳を表示する
2. 所得税の速算表の適用が正しいか確認する
3. 復興特別所得税が正しく加算されているか確認する
4. 源泉徴収税額が正しく控除されているか確認する
5. 最終的な納付額（または還付額）を明示する

### 所得税の速算表（参考）

| 課税所得金額 | 税率 | 控除額 |
|-------------|------|--------|
| 〜195万円 | 5% | 0円 |
| 195万超〜330万円 | 10% | 97,500円 |
| 330万超〜695万円 | 20% | 427,500円 |
| 695万超〜900万円 | 23% | 636,000円 |
| 900万超〜1,800万円 | 33% | 1,536,000円 |
| 1,800万超〜4,000万円 | 40% | 2,796,000円 |
| 4,000万超 | 45% | 4,796,000円 |

## ステップ4: 控除明細PDFの生成

### `generate_deduction_detail_pdf` の呼び出し

```
パラメータ:
  deductions: DeductionsResult — 控除の計算結果
  output_path: str             — 出力先ファイルパス
```

- 各控除の明細と計算根拠を記載したPDFを生成する
- 確定申告書の第二表「所得から差し引かれる金額に関する事項」の根拠資料となる

## ステップ5: 確定申告書PDFの生成

### `generate_income_tax_pdf` の呼び出し

```
パラメータ:
  result: IncomeTaxResult — 所得税の計算結果
  output_path: str        — 出力先ファイルパス
```

- 確定申告書B様式（第一表・第二表）のPDFを生成する
- references/form-b-fields.md の各欄に計算結果を設定する
- 出力後、主要な記載内容をサマリーとして表示する

## ステップ6: 計算結果サマリーの提示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
所得税の計算結果（令和○年分）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 所得金額
  事業所得:           ○○○,○○○円
  給与所得:           ○○○,○○○円
  合計所得金額:       ○○○,○○○円

■ 所得控除
  社会保険料控除:     ○○○,○○○円
  生命保険料控除:      ○○,○○○円
  基礎控除:           480,000円
  [その他の控除...]
  所得控除合計:       ○○○,○○○円

■ 税額計算
  課税所得金額:       ○○○,○○○円
  算出税額:           ○○○,○○○円
  税額控除:            ○○,○○○円
  復興特別所得税:       ○,○○○円
  所得税及び復興特別所得税: ○○○,○○○円
  源泉徴収税額:       ○○○,○○○円
  ---------------------------------
  申告納税額:          ○○,○○○円（納付 / 還付）

■ 出力ファイル:
  → [出力パス]/income_tax_2025.pdf
  → [出力パス]/deduction_detail_2025.pdf

■ 次のステップ:
  → consumption-tax スキルで消費税の計算を行う
  → submit スキルで提出準備を行う
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 免責事項

- この計算は一般的な所得税の計算ロジックに基づく
- 分離課税の所得（株式譲渡益・不動産譲渡益等）は本スキルの対象外
- 最終的な申告内容は税理士等の専門家に確認することを推奨する
