# 控除シミュレーションガイド（Deduction Simulation Guide）

令和7年分（2025年課税年度）対応。

`calc-deductions` コマンドを使った控除のシミュレーション手順と、
よくある相談パターン別の操作手順をまとめたガイド。

## calc-deductions コマンドの概要

### 基本的な使い方

```bash
shinkoku tax calc-deductions --input deductions.json
```

入力は JSON ファイルで指定する。出力は控除項目の一覧と合計額が JSON で返る。

### 主要な入力パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `total_income` | int | 合計所得金額（必須） |
| `social_insurance` | int | 社会保険料の支払額 |
| `life_insurance_premium` | int | 生命保険料（簡易入力。詳細は `life_insurance_detail` を使用） |
| `life_insurance_detail` | object | 生命保険料の詳細（新旧・区分別に入力） |
| `earthquake_insurance_premium` | int | 地震保険料の支払額 |
| `old_long_term_insurance_premium` | int | 旧長期損害保険料の支払額 |
| `medical_expenses` | int | 医療費の支払額 |
| `self_medication_expenses` | int | セルフメディケーション対象医薬品の購入額 |
| `self_medication_eligible` | bool | セルフメディケーション税制の適格性（健診等の取組あり） |
| `furusato_nozei` | int | ふるさと納税の合計寄附額 |
| `housing_loan_balance` | int | 住宅ローンの年末残高 |
| `housing_loan_detail` | object | 住宅ローンの詳細（住宅区分等） |
| `spouse_income` | int | 配偶者の合計所得金額 |
| `ideco_contribution` | int | iDeCoの年間掛金 |
| `small_business_mutual_aid` | int | 小規模企業共済の年間掛金 |
| `dependents` | array | 扶養親族の情報（年齢、障害者区分等） |
| `fiscal_year` | int | 課税年度（デフォルト: 2025） |
| `widow_status` | string | 寡婦/ひとり親の区分（"none", "widow", "single_parent"） |
| `disability_status` | string | 障害者区分（"none", "general", "special", "special_cohabit"） |
| `working_student` | bool | 勤労学生かどうか |
| `donations` | array | 寄附金の詳細（ふるさと納税以外の寄附を含む場合） |

### 出力の構造

```json
{
  "income_deductions": [
    {"type": "basic", "name": "基礎控除", "amount": 580000},
    {"type": "social_insurance", "name": "社会保険料控除", "amount": 1000000},
    ...
  ],
  "tax_credits": [
    {"type": "housing_loan", "name": "住宅ローン控除", "amount": 245000},
    ...
  ],
  "total_income_deductions": 2380000,
  "total_tax_credits": 245000
}
```

## 段階的な控除追加シミュレーション手順

控除の効果を段階的に確認するための手順。

### ステップ1: 基本的な所得情報のみ

まず最低限の情報（所得と社会保険料）だけで計算する。

```json
{
  "total_income": 5200000,
  "social_insurance": 1000000
}
```

```bash
shinkoku tax calc-deductions --input step1.json
```

→ 基礎控除 + 社会保険料控除の基本控除額を確認。

### ステップ2: iDeCo・小規模企業共済を追加

```json
{
  "total_income": 5200000,
  "social_insurance": 1000000,
  "ideco_contribution": 276000,
  "small_business_mutual_aid": 840000
}
```

→ 所得控除の増加分と、課税所得の変化を確認。

### ステップ3: 家族構成を反映

```json
{
  "total_income": 5200000,
  "social_insurance": 1000000,
  "ideco_contribution": 276000,
  "small_business_mutual_aid": 840000,
  "spouse_income": 500000,
  "dependents": [
    {"age": 20, "disability": "none"},
    {"age": 15, "disability": "none"}
  ]
}
```

→ 配偶者控除、扶養控除（特定扶養親族等）の適用を確認。

### ステップ4: ふるさと納税・医療費控除を追加

```json
{
  "total_income": 5200000,
  "social_insurance": 1000000,
  "ideco_contribution": 276000,
  "small_business_mutual_aid": 840000,
  "spouse_income": 500000,
  "dependents": [
    {"age": 20, "disability": "none"},
    {"age": 15, "disability": "none"}
  ],
  "furusato_nozei": 80000,
  "medical_expenses": 250000
}
```

→ 全控除を反映した最終的な控除合計額を確認。

### ステップ5: 所得税の計算

控除額が確定したら、`calc-income` コマンドで所得税を計算する。

```bash
shinkoku tax calc-income --input income_params.json
```

## よくある相談パターン別の操作手順

### パターン1: ふるさと納税の上限額を知りたい

```bash
# 1. まず控除額を計算
shinkoku tax calc-deductions --input my_deductions.json

# 2. 上限額を計算（total_income_deductions の値を使用）
shinkoku tax calc-furusato-limit --input furusato_params.json
```

`calc-furusato-limit` の入力:

```json
{
  "total_income": 5200000,
  "total_income_deductions": 2380000
}
```

**ポイント**: iDeCo や住宅ローン控除がある場合、それらを反映した `total_income_deductions` を使って上限額を計算する。控除を反映しないと上限額が過大になる。

### パターン2: iDeCoを始めた場合の効果を知りたい

```bash
# iDeCoなしで計算
shinkoku tax calc-deductions --input without_ideco.json
shinkoku tax calc-income --input income_without_ideco.json

# iDeCoありで計算
shinkoku tax calc-deductions --input with_ideco.json
shinkoku tax calc-income --input income_with_ideco.json

# 2つの結果を比較して節税効果を算出
```

```json
// without_ideco.json
{
  "total_income": 5200000,
  "social_insurance": 1000000
}

// with_ideco.json（iDeCoを追加）
{
  "total_income": 5200000,
  "social_insurance": 1000000,
  "ideco_contribution": 276000
}
```

比較結果:
- 所得控除の増加: 276,000円
- 所得税の節税（税率20%の場合）: 55,200円
- 住民税の節税: 27,600円
- **年間節税効果: 82,800円**

### パターン3: 医療費控除の損益分岐を知りたい

医療費控除の適用判定:

```
Q1. 年間の医療費合計（家族分含む）はいくらか？
Q2. 保険金等で補填された金額はいくらか？
Q3. 差引後の金額が10万円（or 所得の5%）を超えるか？

損益分岐点:
  所得200万円以上: 医療費 > 10万円 + 保険金等
  所得200万円未満: 医療費 > 所得 × 5% + 保険金等
```

セルフメディケーション税制との比較:

```json
// 通常の医療費控除で計算
{
  "total_income": 3000000,
  "social_insurance": 450000,
  "medical_expenses": 120000
}

// セルフメディケーション税制で計算
{
  "total_income": 3000000,
  "social_insurance": 450000,
  "self_medication_expenses": 80000,
  "self_medication_eligible": true
}
```

→ 通常の医療費控除: (120,000 − 100,000) = 20,000円の控除
→ セルフメディケーション: (80,000 − 12,000) = 68,000円の控除
→ この場合はセルフメディケーション税制が有利

### パターン4: 副業を始めた場合の影響を知りたい

```bash
# 副業なし（給与所得のみ）
shinkoku tax calc-income --input salary_only.json

# 副業あり（給与所得 + 事業所得）
shinkoku tax calc-income --input salary_plus_business.json
```

副業開始時に追加で検討すべき項目:
1. **事業所得 vs 雑所得の判定**: reference/side-business-classification.md 参照
2. **青色申告の検討**: 65万円控除の恩恵が大きい
3. **消費税の課税判定**: 売上が1,000万円超なら2年後に課税事業者
4. **ふるさと納税上限の変動**: 事業所得の追加で上限額が変わる
5. **住民税の普通徴収**: 副業バレ対策（reference/startup-guide.md 参照）

### パターン5: 住宅ローン控除と他の控除の最適化

住宅ローン控除がある場合の全体最適化:

```json
{
  "total_income": 6000000,
  "social_insurance": 900000,
  "ideco_contribution": 276000,
  "furusato_nozei": 100000,
  "housing_loan_balance": 35000000,
  "housing_loan_detail": {
    "housing_type": "zeh",
    "move_in_year": 2025,
    "is_new_construction": true
  }
}
```

確認ポイント:
- 住宅ローン控除で所得税が0になる場合、ふるさと納税の所得税控除分が無効化
- 住民税からの控除上限（課税所得×5%、最大97,500円）を確認
- iDeCoは所得控除なので住宅ローン控除（税額控除）とは別の段階で効果がある

## シミュレーション時の注意事項

### 金額はすべて int（円単位の整数）

```json
// 正しい
{"total_income": 5200000, "social_insurance": 1000000}

// 誤り（float は使わない）
{"total_income": 5200000.0, "social_insurance": 1000000.0}
```

### 合計所得金額の計算

`total_income` には合計所得金額を入力する。収入金額ではない。

```
給与所得者の場合:
  給与収入 → 給与所得控除を差し引く → 給与所得（= total_income）

事業所得者の場合:
  事業収入 − 必要経費（− 青色申告特別控除） = 事業所得

複数所得がある場合:
  給与所得 + 事業所得 + 雑所得 + ... = 合計所得金額
```

### fiscal_year パラメータ

令和7年分の計算には `"fiscal_year": 2025` を指定する（デフォルト値）。
年度が異なると基礎控除額や給与所得控除額の計算が変わる。

## 参照条文

- 所得税法第72条〜第86条（各種所得控除）
- 所得税法第78条（寄附金控除 — ふるさと納税の上限計算）
- 所得税法第89条（税率 — 速算表）
- 租税特別措置法第41条（住宅ローン控除）
- 地方税法附則第5条の5（ふるさと納税の住民税特例控除）
