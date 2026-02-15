# 確定申告書 第三表（分離課税用）フィールド定義

株式等の譲渡所得・FX取引（先物取引に係る雑所得等）の分離課税を申告する場合に使用。
座標は `src/shinkoku/tools/pdf_coordinates.py` に定義予定（Phase 3で追加）。

## 対象者

- 上場株式等の譲渡所得がある場合
- FX取引（先物取引に係る雑所得等）がある場合
- 配当所得を分離課税で申告する場合

## 収入金額・所得金額

### 株式等の譲渡所得

| 欄 | 項目名 | データソース |
|----|--------|-------------|
| — | 収入金額 | `StockTradingAccountRecord.gains` の合計 |
| — | 必要経費 | `StockTradingAccountRecord.losses` の合計 |
| — | 所得金額 | `SeparateTaxResult.stock_net_gain` |

### 先物取引に係る雑所得等（FX）

| 欄 | 項目名 | データソース |
|----|--------|-------------|
| — | 収入金額 | `FXTradingRecord.realized_gains + swap_income` の合計 |
| — | 必要経費 | `FXTradingRecord.expenses` の合計 |
| — | 所得金額 | `SeparateTaxResult.fx_net_income` |

## 税額の計算

### 株式等の譲渡所得

| 項目名 | 税率 | データソース |
|--------|------|-------------|
| 所得税 | 15% | `SeparateTaxResult.stock_income_tax` |
| 住民税 | 5% | `SeparateTaxResult.stock_residential_tax` |
| 復興特別所得税 | 0.315% | `SeparateTaxResult.stock_reconstruction_tax` |

### 先物取引に係る雑所得等（FX）

| 項目名 | 税率 | データソース |
|--------|------|-------------|
| 所得税 | 15% | `SeparateTaxResult.fx_income_tax` |
| 住民税 | 5% | `SeparateTaxResult.fx_residential_tax` |
| 復興特別所得税 | 0.315% | `SeparateTaxResult.fx_reconstruction_tax` |

## 損益通算・繰越控除

| 項目名 | データソース |
|--------|-------------|
| 株式の譲渡損失と配当の損益通算 | `SeparateTaxResult.stock_dividend_offset` |
| 株式の繰越損失適用額 | `SeparateTaxResult.stock_loss_carryforward_used` |
| FXの繰越損失適用額 | `SeparateTaxResult.fx_loss_carryforward_used` |

## 注意事項

- 株式とFXの損益通算は不可（別プール）
- 株式の損失は上場株式の配当とのみ通算可能
- 繰越控除は最大3年間
- 特定口座（源泉徴収あり）は原則申告不要だが、損益通算・繰越控除のために申告可能
