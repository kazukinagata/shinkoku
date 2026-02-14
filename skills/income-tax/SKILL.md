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
5. **予定納税額**: assess で確認済みの予定納税額を取得する
   - 未確認の場合は、前年の確定申告書（㊺欄）から判定する
   - 予定納税額は源泉徴収税額とは別に管理する

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

## ステップ1.5: 扶養親族・配偶者情報の確認

所得控除の計算前に、扶養親族の情報を収集する。

### 確認項目

1. **配偶者**: 配偶者の有無と年間所得金額を確認する
   - 所得48万円以下 → 配偶者控除（38万円）
   - 所得48万円超133万円以下 → 配偶者特別控除（段階的）
   - 納税者の所得が1,000万円超 → 配偶者控除なし

2. **扶養親族**: 以下の情報を収集する
   - 氏名、続柄、生年月日、年間所得、障害の有無、同居の有無
   - 16歳未満: 扶養控除なし（児童手当対象）
   - 16歳以上: 一般扶養38万円
   - 19歳以上23歳未満: 特定扶養63万円
   - 70歳以上: 老人扶養48万円（同居58万円）

3. **障害者控除**: 扶養親族に障害がある場合
   - 一般障害者: 27万円、特別障害者: 40万円、同居特別障害者: 75万円

## ステップ1.6: iDeCo・小規模企業共済の確認

1. iDeCo（個人型確定拠出年金）の年間掛金を確認する
   - 小規模企業共済等掛金払込証明書から金額を確認
   - 全額が所得控除（上限: 自営業者は年額81.6万円）
2. 小規模企業共済の掛金がある場合も同様に確認する

## ステップ1.7: 医療費明細の集計

医療費控除を適用する場合、明細を集計する。

### 医療費の登録・集計

1. `ledger_list_medical_expenses` で登録済み医療費明細を取得する
2. 未登録の医療費がある場合は `ledger_add_medical_expense` で登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       date: str               — 診療日 (YYYY-MM-DD)
       patient_name: str        — 患者名
       medical_institution: str — 医療機関名
       amount: int              — 医療費（円）
       insurance_reimbursement: int — 保険金等の補填額（円）
       description: str | None  — 備考
   ```
3. 集計結果（total_amount - total_reimbursement）を医療費控除の計算に使用する

## ステップ1.8: 事業所得の源泉徴収（支払調書）

取引先から受け取った支払調書の情報を登録する。

### 支払調書の取り込み

1. `import_payment_statement` で支払調書PDF/画像からデータを抽出する
2. `ledger_add_business_withholding` で取引先別の源泉徴収情報を登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       client_name: str     — 取引先名
       gross_amount: int    — 支払金額
       withholding_tax: int — 源泉徴収税額
   ```
3. `ledger_list_business_withholding` で登録済み情報を確認する
4. 源泉徴収税額の合計を `business_withheld_tax` として所得税計算に使用する

## ステップ1.9: 損失繰越の確認

前年以前に事業で損失が発生し、青色申告している場合、繰越控除を適用できる。

1. `ledger_list_loss_carryforward` で登録済みの繰越損失を確認する
2. 未登録の場合は `ledger_add_loss_carryforward` で登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       loss_year: int  — 損失が発生した年（3年以内）
       amount: int     — 繰越損失額（円）
   ```
3. 繰越損失の合計を `loss_carryforward_amount` として所得税計算に使用する

## ステップ2: 所得控除の計算

### `calc_deductions` の呼び出し

```
パラメータ:
  total_income: int              — 合計所得金額
  social_insurance: int          — 社会保険料の年間支払額
  life_insurance_premium: int    — 生命保険料
  earthquake_insurance_premium: int — 地震保険料
  medical_expenses: int          — 医療費合計（保険金差引後）
  furusato_nozei: int            — ふるさと納税寄附金合計
  housing_loan_balance: int      — 住宅ローン年末残高
  spouse_income: int | None      — 配偶者の所得金額
  ideco_contribution: int        — iDeCo/小規模企業共済掛金
  dependents: list[DependentInfo] — 扶養親族のリスト
  fiscal_year: int               — 会計年度
  housing_loan_detail: HousingLoanDetail | None — 住宅ローン控除の詳細

戻り値: DeductionsResult
  - income_deductions: 所得控除の一覧
    - basic_deduction: 基礎控除（Reiwa 7 改正対応）
    - social_insurance_deduction: 社会保険料控除
    - life_insurance_deduction: 生命保険料控除
    - earthquake_insurance_deduction: 地震保険料控除
    - ideco_deduction: 小規模企業共済等掛金控除
    - medical_deduction: 医療費控除
    - furusato_deduction: 寄附金控除
    - spouse_deduction: 配偶者控除/配偶者特別控除
    - dependent_deduction: 扶養控除
    - disability_deduction: 障害者控除
  - tax_credits: 税額控除の一覧
    - housing_loan_credit: 住宅ローン控除
  - total_income_deductions: 所得控除合計
  - total_tax_credits: 税額控除合計
```

**各控除の確認事項:**

- 基礎控除: 合計所得金額に応じた段階的控除（令和7年分の改正を反映、132万以下=95万）
- 社会保険料控除: 国民年金・国民健康保険・その他の年間支払額
- 生命保険料控除: 新旧制度の区分を確認する
- 地震保険料控除: 年間支払額（上限5万円）
- 小規模企業共済等掛金控除: iDeCo掛金は全額所得控除
- 医療費控除: 支払額から保険金等の補填額を差し引き、10万円（または所得の5%）を超える部分
- 配偶者控除/特別控除: 配偶者の所得に応じて段階的に控除額が変動
- 扶養控除: 年齢区分に応じた控除額（一般38万/特定63万/老人48万or58万）
- 障害者控除: 障害の程度に応じた控除額
- ふるさと納税: 寄附金 − 2,000円（確定申告ではワンストップ特例分も含める）
- 住宅ローン控除: 住宅区分別の年末残高上限と控除率0.7%（令和4年以降入居）

## ステップ3: 所得税額の計算

### `calc_income_tax` の呼び出し

```
パラメータ: IncomeTaxInput
  - fiscal_year: int                — 会計年度
  - salary_income: int              — 給与収入（収入金額）
  - business_revenue: int           — 事業収入
  - business_expenses: int          — 事業経費
  - blue_return_deduction: int      — 青色申告特別控除額（65万/10万/0）
  - social_insurance: int           — 社会保険料
  - life_insurance_premium: int     — 生命保険料
  - earthquake_insurance_premium: int — 地震保険料
  - medical_expenses: int           — 医療費（保険金差引後）
  - furusato_nozei: int             — ふるさと納税寄附金合計
  - housing_loan_balance: int       — 住宅ローン年末残高
  - spouse_income: int | None       — 配偶者の所得
  - ideco_contribution: int         — iDeCo掛金
  - withheld_tax: int               — 源泉徴収税額（給与分のみ）
  - business_withheld_tax: int      — 事業所得の源泉徴収税額（取引先別合計）
  - estimated_tax_payment: int      — 予定納税額（第1期 + 第2期の合計）
  - loss_carryforward_amount: int   — 繰越損失額

戻り値: IncomeTaxResult
  - salary_income_after_deduction: 給与所得控除後の金額
  - business_income: 事業所得
  - total_income: 合計所得金額（繰越損失適用後）
  - total_income_deductions: 所得控除合計
  - taxable_income: 課税所得金額（1,000円未満切り捨て）
  - income_tax_base: 算出税額
  - total_tax_credits: 税額控除合計
  - income_tax_after_credits: 税額控除後
  - reconstruction_tax: 復興特別所得税（基準所得税額 × 2.1%）
  - total_tax: 所得税及び復興特別所得税の額（100円未満切り捨て）
  - withheld_tax: 源泉徴収税額（給与分）
  - business_withheld_tax: 事業所得の源泉徴収税額
  - estimated_tax_payment: 予定納税額
  - loss_carryforward_applied: 適用した繰越損失額
  - tax_due: 申告納税額（= total_tax - withheld_tax - business_withheld_tax - estimated_tax_payment）
```

**計算結果の確認:**

1. 合計所得金額の内訳を表示する
2. 繰越損失が適用されている場合はその額を明示する
3. 所得税の速算表の適用が正しいか確認する
4. 復興特別所得税が正しく加算されているか確認する
5. 源泉徴収税額（給与分 + 事業分）が正しく控除されているか確認する
6. 予定納税額が正しく控除されているか確認する
7. 最終的な納付額（または還付額）を明示する

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

## ステップ3.5: 医療費控除の明細書PDF生成（該当者のみ）

医療費控除を適用する場合、明細書PDFを生成する。

### `doc_generate_medical_expense_detail` の呼び出し

```
パラメータ:
  fiscal_year: int              — 会計年度
  expenses: list[dict]          — 医療費明細リスト（ledger_list_medical_expenses の結果）
  total_income: int             — 合計所得金額（控除額の計算に使用）
  output_path: str              — 出力先ファイルパス
  taxpayer_name: str            — 氏名
```

## ステップ3.7: 住宅ローン控除の計算明細書PDF生成（該当者のみ）

住宅ローン控除（初年度）を適用する場合、計算明細書PDFを生成する。

### `doc_generate_housing_loan_detail` の呼び出し

```
パラメータ:
  fiscal_year: int              — 会計年度
  housing_detail: dict          — 住宅ローン控除の詳細情報
    housing_type: str            — 住宅区分（new_custom/new_subdivision/resale/used/renovation）
    housing_category: str        — 住宅性能区分（general/certified/zeh/energy_efficient）
    move_in_date: str            — 入居年月日（YYYY-MM-DD）
    year_end_balance: int        — 年末残高
    is_new_construction: bool    — 新築かどうか
  credit_amount: int            — 計算された控除額
  output_path: str              — 出力先ファイルパス
  taxpayer_name: str            — 氏名
```

**住宅区分別の年末残高上限（令和4〜7年入居）:**

| 住宅区分 | 新築 | 中古 |
|---------|------|------|
| 認定住宅（長期優良/低炭素） | 5,000万円 | 3,000万円 |
| ZEH水準省エネ住宅 | 4,500万円 | 3,000万円 |
| 省エネ基準適合住宅 | 4,000万円 | 3,000万円 |
| 一般住宅 | 3,000万円 | 2,000万円 |

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
  予定納税額:          ○○,○○○円
  ---------------------------------
  申告納税額:          ○○,○○○円（納付 / 還付）

■ 出力ファイル:
  → [出力パス]/income_tax_2025.pdf
  → [出力パス]/deduction_detail_2025.pdf
  → [出力パス]/medical_expense_detail_2025.pdf（該当者のみ）
  → [出力パス]/housing_loan_detail_2025.pdf（住宅ローン控除初年度のみ）

■ 次のステップ:
  → consumption-tax スキルで消費税の計算を行う
  → submit スキルで提出準備を行う
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 免責事項

- この計算は一般的な所得税の計算ロジックに基づく
- 分離課税の所得（株式譲渡益・不動産譲渡益等）は本スキルの対象外
- 雑所得（仮想通貨等）、譲渡所得、配当所得、不動産所得は現時点で未対応
- 最終的な申告内容は税理士等の専門家に確認することを推奨する
