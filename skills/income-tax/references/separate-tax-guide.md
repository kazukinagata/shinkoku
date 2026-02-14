# 分離課税ガイド（株式・FX）

income-tax スキルのステップ1.11で使用する分離課税の詳細パラメータと手順。

## `tax_calc_separate` ツールのパラメータ

```
パラメータ:
  fiscal_year: int
  stock_gains: int                   — 株式譲渡益
  stock_losses: int                  — 株式譲渡損
  stock_dividend_separate: int       — 分離課税選択の配当
  stock_withheld_income_tax: int     — 源泉徴収済み所得税（株式）
  stock_withheld_residential_tax: int — 源泉徴収済み住民税（株式）
  stock_loss_carryforward: int       — 株式の繰越損失
  fx_gains: int                      — FX の実現益 + スワップ収入
  fx_expenses: int                   — FX の経費
  fx_loss_carryforward: int          — FX の繰越損失

戻り値:
  - stock_taxable_income: 株式の課税所得
  - stock_total_tax: 株式の税額（所得税 + 住民税 + 復興税）
  - stock_tax_due: 株式の納付額（源泉徴収差引後）
  - fx_taxable_income: FX の課税所得
  - fx_total_tax: FX の税額
  - fx_tax_due: FX の納付額
  - total_separate_tax: 分離課税の税額合計
```

## 株式取引の登録手順

1. `ledger_list_stock_trading_accounts` で登録済み口座を確認する
2. 未登録の場合は `ledger_add_stock_trading_account` で口座別に登録する
3. 繰越損失がある場合は `ledger_add_stock_loss_carryforward` で登録する

## FX 取引の登録手順

1. `ledger_list_fx_trading` で登録済み取引を確認する
2. 未登録の場合は `ledger_add_fx_trading` で証券会社別に登録する
3. 繰越損失がある場合は `ledger_add_fx_loss_carryforward` で登録する

## 注意事項

- 株式と FX の損益通算は不可（別プール）
- 配当の課税方式は事前にユーザーに確認する（総合課税 / 分離課税 / 申告不要）
- 税率: 所得税15% + 住民税5% + 復興特別所得税0.315% = 20.315%

## 引継書テンプレート（分離課税セクション）

```
## 分離課税（該当者のみ）

- 株式の課税所得: {金額}円
- 株式の税額: {金額}円（源泉徴収差引後: {金額}円）
- FXの課税所得: {金額}円
- FXの税額: {金額}円
- 分離課税合計: {金額}円
```
