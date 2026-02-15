# 確定申告書 第四表（損失申告用）フィールド定義

純損失の繰越控除を適用する場合に使用。
座標は `src/shinkoku/tools/pdf_coordinates.py` に定義予定（Phase 3で追加）。

## 対象者

- 青色申告者で事業所得が赤字（純損失）の場合
- 前年以前の純損失を繰り越して控除する場合

## 第四表（一）: 損失額の計算

| 欄 | 項目名 | データソース |
|----|--------|-------------|
| — | 事業所得の損失額 | `IncomeTaxResult.business_income`（マイナスの場合） |
| — | 給与所得 | `IncomeTaxResult.salary_income_after_deduction` |
| — | その他所得 | 雑所得・配当所得等 |
| — | 通算後の損失額 | 各所得との損益通算後 |

## 第四表（二）: 繰越損失の控除

### 前年以前の繰越損失

| 行 | 項目名 | データソース |
|----|--------|-------------|
| 1 | 前々々年の損失額 | `LossCarryforwardRecord (loss_year=fiscal_year-3)` |
| 2 | 前々年の損失額 | `LossCarryforwardRecord (loss_year=fiscal_year-2)` |
| 3 | 前年の損失額 | `LossCarryforwardRecord (loss_year=fiscal_year-1)` |

### 控除額の計算

| 項目名 | データソース |
|--------|-------------|
| 繰越損失の控除額 | `IncomeTaxResult.loss_carryforward_applied` |
| 控除後の所得金額 | `IncomeTaxResult.total_income` |
| 翌年以降に繰り越す損失額 | 残余の繰越損失額 |

## 注意事項

- 純損失の繰越控除は青色申告者のみ適用可能
- 繰越期間は最大3年
- 古い年度の損失から先に控除する（FIFO）
- 白色申告者は変動所得・被災事業用資産の損失のみ繰越可能
