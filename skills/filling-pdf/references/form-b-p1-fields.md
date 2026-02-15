# 確定申告書 第一表（Form B Page 1）フィールド定義

国税庁公式様式の欄番号・項目名・データソースの対応表。
座標は `src/shinkoku/tools/pdf_coordinates.py` の `INCOME_TAX_P1` に定義。

## ヘッダー（基本情報）

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `postal_code_upper` | 郵便番号（上3桁） | `config.address.postal_code[:3]` |
| `postal_code_lower` | 郵便番号（下4桁） | `config.address.postal_code[4:]` |
| `address` | 住所 | `config.address.prefecture + city + street + building` |
| `name_kana` | フリガナ | `config.taxpayer.last_name_kana + first_name_kana` |
| `name_kanji` | 氏名 | `config.taxpayer.last_name + first_name` |
| `birth_date` | 生年月日 | `config.taxpayer.date_of_birth` |
| `phone` | 電話番号 | `config.taxpayer.phone` |
| `fiscal_year_label` | 年分 | `令和{fiscal_year - 2018}年分` |
| `blue_return_checkbox` | 青色申告 | `config.filing.return_type == "blue"` |

## 収入金額等

| 欄番号 | フィールドキー | 項目名 | データソース |
|--------|--------------|--------|-------------|
| ア | `business_revenue` | 事業（営業等）収入 | 青色申告決算書の売上金額 |
| カ | `salary_revenue` | 給与収入 | 源泉徴収票の「支払金額」 |
| ク | `misc_revenue` | 雑（その他）収入 | 雑所得の収入合計 |

## 所得金額等

| 欄番号 | フィールドキー | 項目名 | データソース |
|--------|--------------|--------|-------------|
| ① | `business_income` | 事業（営業等）所得 | `IncomeTaxResult.business_income` |
| ⑥ | `salary_income` | 給与所得 | `IncomeTaxResult.salary_income_after_deduction` |
| ⑫ | `total_income` | 合計所得金額 | `IncomeTaxResult.total_income` |

## 所得から差し引かれる金額（所得控除）

| 欄番号 | フィールドキー | 項目名 | データソース |
|--------|--------------|--------|-------------|
| ⑬ | `social_insurance_deduction` | 社会保険料控除 | `deductions_detail.social_insurance` |
| ⑭ | `ideco_deduction` | 小規模企業共済等掛金控除 | `deductions_detail.ideco` |
| ⑮ | `life_insurance_deduction` | 生命保険料控除 | `deductions_detail.life_insurance` |
| ⑯ | `earthquake_insurance_deduction` | 地震保険料控除 | `deductions_detail.earthquake_insurance` |
| ⑲ | — | 障害者控除 | `deductions_detail.disability` |
| ⑳ | `spouse_deduction` | 配偶者控除・特別控除 | `deductions_detail.spouse` |
| ㉑ | `dependent_deduction` | 扶養控除 | `deductions_detail.dependent` |
| ㉒ | `basic_deduction` | 基礎控除 | `deductions_detail.basic` |
| ㉔ | `medical_deduction` | 医療費控除 | `deductions_detail.medical` |
| ㉕ | `furusato_deduction` | 寄附金控除 | `deductions_detail.furusato + donation` |
| ㉙ | `total_deductions` | 所得控除合計 | `IncomeTaxResult.total_income_deductions` |

## 税額の計算

| 欄番号 | フィールドキー | 項目名 | データソース |
|--------|--------------|--------|-------------|
| ㉚ | `taxable_income` | 課税される所得金額 | `IncomeTaxResult.taxable_income` |
| ㉛ | `income_tax_base` | 上の㉚に対する税額 | `IncomeTaxResult.income_tax_base` |
| ㉜ | `dividend_credit` | 配当控除 | `IncomeTaxResult.dividend_credit` |
| ㉝ | `housing_loan_credit` | 住宅借入金等特別控除 | `IncomeTaxResult.housing_loan_credit` |
| ㊱ | `income_tax_after_credits` | 差引所得税額 | `IncomeTaxResult.income_tax_after_credits` |
| ㊲ | `reconstruction_tax` | 復興特別所得税額 | `IncomeTaxResult.reconstruction_tax` |
| ㊳ | `total_tax` | 所得税及び復興特別所得税の額 | `IncomeTaxResult.total_tax` |
| ㊹ | `withheld_tax` | 源泉徴収税額 | `withheld_tax + business_withheld_tax` |
| — | `estimated_tax_payment` | 予定納税額 | `IncomeTaxResult.estimated_tax_payment` |
| ㊺ | `tax_due` | 申告納税額 | `IncomeTaxResult.tax_due` |

## 還付口座（還付の場合）

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| — | 銀行名 | `config.refund_account.bank_name` |
| — | 支店名 | `config.refund_account.branch_name` |
| — | 預金種類 | `config.refund_account.account_type` |
| — | 口座番号 | `config.refund_account.account_number` |

※ 還付口座の座標は `pdf_coordinates.py` に追加が必要（Phase 3で対応）

## 端数処理ルール

| 対象 | ルール |
|------|--------|
| 課税所得金額（㉚） | 1,000円未満切り捨て |
| 申告納税額（㊺） | 100円未満切り捨て |
| 復興特別所得税（㊲） | 1円未満切り捨て |
