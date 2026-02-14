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

## 進捗情報の読み込み

設定の読み込み後、引継書ファイルを読み込んで前ステップの結果を把握する。

1. `.shinkoku/progress/progress-summary.md` を Read ツールで読み込む（存在する場合）
2. 以下の引継書を Read ツールで読み込む（存在する場合）:
   - `.shinkoku/progress/06-settlement.md`
   - `.shinkoku/progress/02-assess.md`
   - `.shinkoku/progress/05-furusato.md`
3. 読み込んだ情報を以降のステップで活用する（ユーザーへの再質問を避ける）
4. ファイルが存在しない場合はスキップし、ユーザーに必要情報を直接確認する

## 基本方針

- settlement スキルで青色申告決算書が完成しているか確認してから開始する
- 所得の計算 → 控除の計算 → 税額の計算 → PDF生成 の順序で進める
- 各ステップの計算結果をユーザーに提示し、確認を得る
- references/form-b-fields.md の各欄に正しく値を設定する
- 端数処理ルール（課税所得: 1,000円未満切り捨て、税額: 100円未満切り捨て）を厳守する

## 前提条件の確認

所得税計算を開始する前に以下を確認する:

1. **青色申告決算書が完成しているか**: settlement スキルの出力を確認する
2. **納税者プロファイルの読み込み**: `profile_get_taxpayer` ツールで config から納税者情報を取得する
   - 氏名・住所・税務署名 → PDF 帳票の自動記入に使用
   - 寡婦/ひとり親・障害者・勤労学生の状態 → 人的控除の計算に使用
3. **事業所得以外の所得**: 給与所得・雑所得・配当所得・一時所得等がある場合は情報を収集する
4. **源泉徴収票**: 給与所得がある場合は取り込みを案内する
5. **各種控除の適用状況**: 適用可能な控除を網羅的に確認する
6. **予定納税額**: assess で確認済みの予定納税額を取得する
   - 未確認の場合は、前年の確定申告書（㊺欄）から判定する
   - 予定納税額は源泉徴収税額とは別に管理する
7. **分離課税の確認**: 株式取引・FX取引がある場合は別途 `tax_calc_separate` で計算する

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
まず DB に登録済みのデータを確認し、不足があれば追加入力する。

### DB からの読み込み

1. `ledger_get_spouse` で配偶者情報を取得する（登録済みの場合）
2. `ledger_list_dependents` で扶養親族のリストを取得する（登録済みの場合）

### 未登録の場合の確認項目

1. **配偶者**: 配偶者の有無と年間所得金額を確認する
   - 所得48万円以下 → 配偶者控除（38万円）
   - 所得48万円超133万円以下 → 配偶者特別控除（段階的）
   - 納税者の所得が1,000万円超 → 配偶者控除なし
   - 確認後 `ledger_set_spouse` で DB に登録する

2. **扶養親族**: 以下の情報を収集する
   - 氏名、続柄、生年月日、年間所得、障害の有無、同居の有無
   - 16歳未満: 扶養控除なし（児童手当対象）
   - 16歳以上: 一般扶養38万円
   - 19歳以上23歳未満: 特定扶養63万円
   - 70歳以上: 老人扶養48万円（同居58万円）
   - 確認後 `ledger_add_dependent` で各人を DB に登録する

3. **障害者控除**: 扶養親族に障害がある場合
   - 一般障害者: 27万円、特別障害者: 40万円、同居特別障害者: 75万円

## ステップ1.6: iDeCo・小規模企業共済の確認

掛金払込証明書がある場合は `import_deduction_certificate` で取り込むことができる。

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

## ステップ1.8.5: 税理士等報酬の登録

税理士・弁護士等に報酬を支払っている場合、報酬明細を登録する。

1. `ledger_list_professional_fees` で登録済みの税理士等報酬を確認する
2. 未登録の場合は `ledger_add_professional_fee` で登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       payer_address: str    — 支払者住所
       payer_name: str       — 支払者名（税理士・弁護士名）
       fee_amount: int       — 報酬金額（円）
       expense_deduction: int — 必要経費（円）
       withheld_tax: int     — 源泉徴収税額（円）
   ```
3. 源泉徴収税額は `business_withheld_tax` に合算する

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

## ステップ1.10: その他の所得の確認（雑所得・配当所得・一時所得・年金所得・退職所得）

事業所得・給与所得以外の総合課税の所得を確認・登録する。

### 公的年金等の雑所得

公的年金等の収入がある場合、年金控除を計算して雑所得を求める。

1. 年金収入の有無を確認する
2. `tax_calc_pension_deduction` で公的年金等控除を計算する:
   ```
   パラメータ:
     pension_income: int   — 公的年金等の収入金額（円）
     is_over_65: bool      — 65歳以上かどうか（年度末12/31時点）
     other_income: int     — 公的年金等以外の合計所得金額（0の場合は省略可）

   戻り値:
     pension_income: int              — 入力の年金収入
     deduction_amount: int            — 公的年金等控除額
     taxable_pension_income: int      — 雑所得（年金） = 収入 - 控除
     other_income_adjustment: int     — 所得金額調整額
   ```
3. `taxable_pension_income` を雑所得として `misc_income` に加算する
4. 令和7年改正: 65歳未満の最低保障額60万→70万、65歳以上の最低保障額110万→130万

### 退職所得

退職金を受け取った場合、退職所得を計算する。

1. 退職金の有無を確認する
2. `tax_calc_retirement_income` で退職所得を計算する:
   ```
   パラメータ:
     severance_pay: int              — 退職手当等の収入金額（円）
     years_of_service: int           — 勤続年数（1年未満切上げ）
     is_officer: bool                — 役員等かどうか（デフォルト: false）
     is_disability_retirement: bool  — 障害退職かどうか（デフォルト: false）

   戻り値:
     severance_pay: int                — 入力の退職金
     retirement_income_deduction: int  — 退職所得控除額
     taxable_retirement_income: int    — 退職所得（1/2適用後）
     half_taxation_applied: bool       — 1/2課税が適用されたか
   ```
3. 退職所得は原則分離課税（退職時に源泉徴収済み）だが、確定申告で精算する場合もある
4. 役員等の短期退職（勤続5年以下）は1/2課税が適用されない

### 雑所得（miscellaneous）

副業の原稿料、暗号資産の売却益、その他の雑収入。

1. `ledger_list_other_income` で登録済み雑所得を確認する
2. 未登録の収入がある場合は `ledger_add_other_income` で登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       income_type: "miscellaneous"
       description: str       — 収入の内容
       revenue: int           — 収入金額
       expenses: int          — 必要経費
       withheld_tax: int      — 源泉徴収税額
       payer_name: str | None — 支払者名
   ```
3. 雑所得 = 収入 - 経費（特別控除なし）

### 仮想通貨（暗号資産）

暗号資産の売却益は雑所得（総合課税）として申告する。

1. `ledger_list_crypto_income` で登録済み仮想通貨所得を確認する
2. 未登録の場合は `ledger_add_crypto_income` で取引所別に登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       exchange_name: str — 取引所名
       gains: int         — 売却益
       expenses: int      — 取引手数料等
   ```
3. 合計を雑所得として total_income に加算する

### 配当所得（総合課税選択分）

総合課税を選択した配当は配当控除（税額控除）の対象となる。

1. `ledger_list_other_income` で `income_type: "dividend_comprehensive"` を確認する
2. 未登録の場合は `ledger_add_other_income` で登録する
3. 配当控除: 課税所得1,000万以下の部分 → 配当の10%、超える部分 → 5%

### 一時所得

保険満期金、懸賞金等の一時的な所得。

1. `ledger_list_other_income` で `income_type: "one_time"` を確認する
2. 未登録の場合は `ledger_add_other_income` で登録する
3. 一時所得 = max(0, (収入 - 経費 - 特別控除50万円)) × 1/2

### `calc_income_tax` への反映

上記のその他所得は以下のパラメータで `calc_income_tax` に渡す:
- `misc_income`: 雑所得合計（仮想通貨含む）
- `dividend_income_comprehensive`: 配当所得（総合課税選択分）
- `one_time_income`: 一時所得の収入金額（1/2 計算は内部で実施）
- `other_income_withheld_tax`: その他所得の源泉徴収税額合計

## ステップ1.11: 分離課税の確認（株式・FX）

株式取引や FX 取引がある場合、分離課税として別途計算する。
総合課税の所得税とは別に `tax_calc_separate` ツールで計算する。

詳細なパラメータ・登録手順・引継書テンプレートは `references/separate-tax-guide.md` を参照。

**注意**: 株式と FX の損益通算は不可（別プール）。配当の課税方式は事前にユーザーに確認する（総合課税 / 分離課税 / 申告不要）。

## ステップ1.12: 社会保険料の種別別内訳の登録

所得控除の内訳書に種別ごとの記載が必要なため、社会保険料を種別別に登録する。

社会保険料の控除証明書がある場合は `import_deduction_certificate` で取り込むことができる。

1. `ledger_list_social_insurance_items` で登録済み項目を確認する
2. 未登録の場合は `ledger_add_social_insurance_item` で種別ごとに登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       insurance_type: str  — 種別（national_health / national_pension / national_pension_fund / nursing_care / labor_insurance / other）
       name: str | None     — 保険者名等
       amount: int          — 年間支払額（円）
   ```
3. 合計額を `social_insurance` として控除計算に使用する

## ステップ1.13: 保険契約の保険会社名の登録

所得控除の内訳書に保険会社名の記載が必要なため、保険契約を登録する。

控除証明書の画像・PDFがある場合は `import_deduction_certificate` で取り込むことができる。
取り込み後、抽出データに基づいて `ledger_add_insurance_policy` で登録する。

1. `ledger_list_insurance_policies` で登録済み項目を確認する
2. 未登録の場合は `ledger_add_insurance_policy` で登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       policy_type: str   — 種別（life_general_new / life_general_old / life_medical_care / life_annuity_new / life_annuity_old / earthquake / old_long_term）
       company_name: str  — 保険会社名
       premium: int       — 年間保険料（円）
   ```
3. 生命保険料は `life_insurance_detail` パラメータに、地震保険料は `earthquake_insurance_premium` に反映する

## ステップ1.14: ふるさと納税以外の寄附金の確認

政治活動寄附金、認定NPO法人、公益社団法人等への寄附金を確認する。

1. `ledger_list_donations` で登録済み寄附金を確認する
2. 未登録の場合は `ledger_add_donation` で登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail:
       donation_type: str      — 種別（political / npo / public_interest / specified / other）
       recipient_name: str     — 寄附先名
       amount: int             — 寄附金額（円）
       date: str               — 寄附日（YYYY-MM-DD）
       receipt_number: str | None — 領収書番号
   ```
3. 寄附金控除の計算:
   - **所得控除**: 全寄附金 - 2,000円（総所得金額の40%上限）
   - **税額控除（政治活動寄附金）**: (寄附金 - 2,000円) × 30%（所得税額の25%上限）
   - **税額控除（認定NPO等）**: (寄附金 - 2,000円) × 40%（所得税額の25%上限）
4. `calc_deductions` の `donations` パラメータに寄附金レコードのリストを渡す

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
  donations: list[DonationRecordRecord] | None — ふるさと納税以外の寄附金

戻り値: DeductionsResult
  - income_deductions: 所得控除の一覧
    - basic_deduction: 基礎控除（Reiwa 7 改正対応）
    - social_insurance_deduction: 社会保険料控除
    - life_insurance_deduction: 生命保険料控除
    - earthquake_insurance_deduction: 地震保険料控除
    - ideco_deduction: 小規模企業共済等掛金控除
    - medical_deduction: 医療費控除
    - furusato_deduction: 寄附金控除（ふるさと納税）
    - donation_deduction: 寄附金控除（その他）
    - spouse_deduction: 配偶者控除/配偶者特別控除
    - dependent_deduction: 扶養控除
    - disability_deduction: 障害者控除
  - tax_credits: 税額控除の一覧
    - housing_loan_credit: 住宅ローン控除
    - political_donation_credit: 政治活動寄附金控除
    - npo_donation_credit: 認定NPO等寄附金控除
  - total_income_deductions: 所得控除合計
  - total_tax_credits: 税額控除合計
```

**各控除の確認事項:**

- 基礎控除: 合計所得金額に応じた段階的控除（令和7年分の改正を反映、132万以下=95万）
- 社会保険料控除: 国民年金・国民健康保険・その他の年間支払額
- 生命保険料控除: 新旧制度 × 3区分（一般/介護医療/個人年金）で計算する
  - `life_insurance_detail` パラメータで5区分の保険料を指定:
    - `general_new`: 一般（新制度）、`general_old`: 一般（旧制度）
    - `medical_care`: 介護医療（新制度のみ）
    - `annuity_new`: 個人年金（新制度）、`annuity_old`: 個人年金（旧制度）
  - 各区分の上限: 新制度 40,000円 / 旧制度 50,000円 / 合算上限 40,000円
  - 3区分合計の上限: 120,000円
  - 源泉徴収票に生命保険料5区分の記載がある場合はそのまま使用する
- 地震保険料控除: 地震保険（上限5万円）+ 旧長期損害保険（上限1.5万円）、合算上限5万円
  - `old_long_term_insurance_premium` パラメータで旧長期損害保険料を指定可能
- 小規模企業共済等掛金控除: 3サブタイプ個別追跡
  - iDeCo（個人型確定拠出年金）
  - 小規模企業共済
  - 心身障害者扶養共済
  - `small_business_mutual_aid` パラメータで小規模企業共済掛金を指定
- 医療費控除: 支払額から保険金等の補填額を差し引き、10万円（または所得の5%）を超える部分
  - **セルフメディケーション税制との選択適用**: OTC医薬品の購入額 - 12,000円（上限 88,000円）
  - 医療費控除とセルフメディケーションは併用不可。有利な方を選択する
- 配偶者控除/特別控除: 配偶者の所得に応じて段階的に控除額が変動
- 扶養控除: 年齢区分に応じた控除額（一般38万/特定63万/老人48万or58万）
- 障害者控除: 障害の程度に応じた控除額
- **人的控除**（config の納税者情報から自動判定）:
  - 寡婦控除: 27万円（所得500万以下）
  - ひとり親控除: 35万円（所得500万以下）
  - 障害者控除（本人）: 一般 27万円 / 特別 40万円
  - 勤労学生控除: 27万円（所得75万以下）
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

**寄附金控除の反映:**

ふるさと納税以外の寄附金控除（ステップ1.14で登録）は、`calc_deductions` の結果に含まれている。
`calc_income_tax` は内部で `calc_deductions` を呼び出すため、以下のパラメータが正しく渡されていれば自動的に反映される:
- `furusato_nozei`: ふるさと納税の寄附金合計
- 政治活動寄附金・認定NPO等の税額控除は `calc_deductions` の `donations` パラメータ経由で計算される

所得税計算前に `calc_deductions` を個別に呼び出す場合は、`donations` パラメータにステップ1.14で登録した寄附金レコードのリストを必ず渡すこと。

**計算結果の確認:**

1. 合計所得金額の内訳を表示する
2. 繰越損失が適用されている場合はその額を明示する
3. 所得税の速算表の適用が正しいか確認する
4. 復興特別所得税が正しく加算されているか確認する
5. 源泉徴収税額（給与分 + 事業分）が正しく控除されているか確認する
6. 予定納税額が正しく控除されているか確認する
7. 最終的な納付額（または還付額）を明示する

所得税の速算表・配偶者控除テーブル・住宅ローン限度額等は `references/deduction-tables.md` を参照。

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

### 住宅ローン控除明細の DB 登録

PDF 生成前に、住宅ローン控除の詳細情報を DB に登録する。

1. `ledger_add_housing_loan_detail` で住宅ローン控除の明細を登録する:
   ```
   パラメータ:
     db_path: str
     fiscal_year: int
     detail: HousingLoanDetailInput
       housing_type: str            — 住宅区分
       housing_category: str        — 住宅性能区分
       move_in_date: str            — 入居年月日
       year_end_balance: int        — 年末残高
       is_new_construction: bool    — 新築かどうか
       is_childcare_household: bool — 子育て世帯
       has_pre_r6_building_permit: bool — R5以前の建築確認済み
       purchase_date: str | None    — 住宅購入日
       purchase_price: int          — 住宅の価格
       total_floor_area: int        — 総床面積（㎡×100）
       residential_floor_area: int  — 居住用部分の面積（㎡×100）
       property_number: str | None  — 不動産番号
       application_submitted: bool  — 適用申請書提出有無
   ```
2. 登録後、DB の情報を使って PDF を生成する

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

住宅区分別の年末残高上限テーブルは `references/deduction-tables.md` を参照。

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

■ 所得金額（総合課税）
  事業所得:           ○○○,○○○円
  給与所得:           ○○○,○○○円
  雑所得:             ○○○,○○○円（該当者のみ）
  配当所得:           ○○○,○○○円（総合課税分、該当者のみ）
  一時所得:           ○○○,○○○円（該当者のみ）
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

■ 分離課税（該当者のみ）
  株式の課税所得:     ○○○,○○○円
  株式の税額:         ○○○,○○○円
  FXの課税所得:       ○○○,○○○円
  FXの税額:           ○○○,○○○円
  分離課税合計:       ○○○,○○○円

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

## 引継書の出力

サマリー提示後、以下のファイルを Write ツールで出力する。
これにより、セッションの中断や Compact が発生しても次のステップで結果を引き継げる。

### ステップ別ファイルの出力

`.shinkoku/progress/07-income-tax.md` に以下の形式で出力する:

```
---
step: 7
skill: income-tax
status: completed
completed_at: "{当日日付 YYYY-MM-DD}"
fiscal_year: {tax_year}
---

# 所得税計算・確定申告書作成の結果

## 所得金額の内訳

- 事業所得: {金額}円
- 給与所得: {金額}円
- 雑所得: {金額}円（該当者のみ、仮想通貨含む）
- 配当所得（総合課税）: {金額}円（該当者のみ）
- 一時所得: {金額}円（該当者のみ）
- 合計所得金額: {金額}円

## 扶養親族・配偶者

- 配偶者控除/特別控除: {適用あり（控除額）/適用なし}
- 扶養控除: {適用あり（控除額、人数）/適用なし}

## iDeCo・小規模企業共済

- 小規模企業共済等掛金控除: {金額}円（{iDeCo/小規模企業共済/なし}）

## 医療費控除

- 適用: {あり/なし}
- 医療費控除額: {金額}円

## 事業所得の源泉徴収

- 源泉徴収税額（事業分）: {金額}円

## 損失繰越控除

- 適用: {あり/なし}
- 繰越損失控除額: {金額}円

## 所得控除の内訳

| 控除項目 | 金額 |
|---------|------|
| 基礎控除 | {金額}円 |
| 社会保険料控除 | {金額}円 |
| 生命保険料控除 | {金額}円 |
| 地震保険料控除 | {金額}円 |
| 小規模企業共済等掛金控除 | {金額}円 |
| 医療費控除 | {金額}円 |
| 寄附金控除 | {金額}円 |
| 配偶者控除/特別控除 | {金額}円 |
| 扶養控除 | {金額}円 |
| 障害者控除 | {金額}円 |
| **所得控除合計** | **{金額}円** |

## 税額計算

- 課税所得金額: {金額}円
- 算出税額: {金額}円
- 税額控除（住宅ローン控除等）: {金額}円
- 復興特別所得税: {金額}円
- 所得税及び復興特別所得税: {金額}円
- 源泉徴収税額（給与分）: {金額}円
- 源泉徴収税額（事業分）: {金額}円
- 予定納税額: {金額}円
- **申告納税額: {金額}円（{納付/還付}）**

## 分離課税（該当者のみ）

- 株式の課税所得: {金額}円
- 株式の税額: {金額}円（源泉徴収差引後: {金額}円）
- FXの課税所得: {金額}円
- FXの税額: {金額}円
- 分離課税合計: {金額}円

## 出力ファイル

- 確定申告書PDF: {ファイルパス}
- 控除明細PDF: {ファイルパス}
- 医療費控除明細書PDF: {ファイルパス}（該当者のみ）
- 住宅ローン控除明細書PDF: {ファイルパス}（該当者のみ）

## 次のステップ

/consumption-tax で消費税の計算を行う
/submit で提出準備を行う
```

### 進捗サマリーの更新

`.shinkoku/progress/progress-summary.md` を更新する（存在しない場合は新規作成）:

- YAML frontmatter: fiscal_year、last_updated（当日日付）、current_step: income-tax
- テーブル: 全ステップの状態を更新（income-tax を completed に）
- 次のステップの案内を記載

### 出力後の案内

ファイルを出力したらユーザーに以下を伝える:
- 「引継書を `.shinkoku/progress/` に保存しました。セッションが中断しても次のスキルで結果を引き継げます。」
- 次のステップの案内

## Additional Resources

### Reference Files

詳細なテーブル・パラメータは以下を参照:
- **`references/form-b-fields.md`** — 確定申告書B様式の各欄の対応
- **`references/deduction-tables.md`** — 所得税速算表、配偶者控除テーブル、基礎控除テーブル、住宅ローン限度額、生命保険料控除等
- **`references/separate-tax-guide.md`** — 分離課税（株式・FX）の詳細パラメータ、登録手順、引継書テンプレート

## 免責事項

- この計算は一般的な所得税の計算ロジックに基づく
- 分離課税（株式・FX）は `tax_calc_separate` で計算する（第三表の生成含む）
- 不動産所得、譲渡所得（不動産売却等）、退職所得は現時点で未対応
- 最終的な申告内容は税理士等の専門家に確認することを推奨する
