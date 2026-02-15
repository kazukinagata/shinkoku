# 確定申告書 第二表（Form B Page 2）フィールド定義

国税庁公式様式の欄番号・項目名・データソースの対応表。
座標は `src/shinkoku/tools/pdf_coordinates.py` の `INCOME_TAX_P2` に定義。

## ヘッダー

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `name_kanji` | 氏名 | `config.taxpayer.last_name + first_name` |

## 所得の内訳（最大8行）

各行のフィールドキー: `income_{n}_type`, `income_{n}_payer`, `income_{n}_revenue`, `income_{n}_withheld` (n=1..8)

| 列 | 項目名 | データソース |
|----|--------|-------------|
| 所得の種類 | 給与/事業/雑 等 | `income_type` |
| 種目・所得の生ずる場所 | 勤務先名、取引先名等 | 源泉徴収票 / 支払調書 |
| 収入金額 | 各所得の収入金額 | 源泉徴収票 / 帳簿 |
| 源泉徴収税額 | 各所得の源泉徴収税額 | 源泉徴収票 / 支払調書 |

### 記載例

| 行 | 所得の種類 | 種目・所得の生ずる場所 | 収入金額 | 源泉徴収税額 |
|----|----------|---------------------|---------|-------------|
| 1 | 給与 | ○○株式会社 | 5,000,000 | 100,000 |
| 2 | 事業 | フリーランス収入 | 3,000,000 | 30,618 |
| 3 | 雑 | 暗号資産売却 | 500,000 | 0 |

## 社会保険料控除の内訳（最大4行）

各行のフィールドキー: `social_{n}_type`, `social_{n}_payer`, `social_{n}_amount` (n=1..4)

| 列 | 項目名 | データソース |
|----|--------|-------------|
| 社会保険の種類 | 国民年金/国民健康保険等 | `SocialInsuranceItemRecord.insurance_type` |
| 支払先の名称 | 保険者名 | `SocialInsuranceItemRecord.name` |
| 支払保険料 | 年間支払額 | `SocialInsuranceItemRecord.amount` |

## 生命保険料控除の内訳

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| — | 新生命保険料 | `InsurancePolicyRecord (life_general_new)` |
| — | 旧生命保険料 | `InsurancePolicyRecord (life_general_old)` |
| — | 介護医療保険料 | `InsurancePolicyRecord (life_medical_care)` |
| — | 新個人年金保険料 | `InsurancePolicyRecord (life_annuity_new)` |
| — | 旧個人年金保険料 | `InsurancePolicyRecord (life_annuity_old)` |

## 配偶者や親族に関する事項

### 配偶者
| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `spouse_name` | 氏名 | `SpouseRecord.name` |
| `spouse_income` | 所得金額 | `SpouseRecord.income` |

### 扶養親族（最大4人）
各人のフィールドキー: `dependent_{n}_name`, `dependent_{n}_relationship`, `dependent_{n}_birth_date` (n=1..4)

| 列 | 項目名 | データソース |
|----|--------|-------------|
| 氏名 | 扶養親族の氏名 | `DependentRecord.name` |
| 続柄 | 子/親/兄弟等 | `DependentRecord.relationship` |
| 生年月日 | 年齢判定に使用 | `DependentRecord.date_of_birth` |

## 住宅借入金等特別控除

| フィールドキー | 項目名 | データソース |
|--------------|--------|-------------|
| `housing_loan_move_in_date` | 居住開始年月日 | `HousingLoanDetailRecord.move_in_date` |

## 住民税に関する事項

| 項目名 | データソース |
|--------|-------------|
| 住民税の徴収方法 | 副業収入がある場合は「普通徴収」を推奨 |
| 16歳未満の扶養親族 | `DependentRecord` のうち16歳未満 |
