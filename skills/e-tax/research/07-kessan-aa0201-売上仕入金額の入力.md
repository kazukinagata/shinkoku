# 07 - 売上（収入）金額・仕入金額の入力

## URL
https://www.keisan.nta.go.jp/kessan/ac/aa0201#bsctrl

## 概要
損益計算書の売上（収入）金額と仕入金額を月別に入力する詳細画面。
aa0200 の「売上（収入）金額」セクションの「入力」ボタン（`#input_uriagekingaku`）をクリックして遷移する。

## 到達方法（書面提出ルート）
ac/aa0200 → 「売上（収入）金額の合計」展開 → 行1「入力」ボタンクリック → **ac/aa0201**

## フォーム要素

### 月別の入力

| 行 | フィールド名 | 売上name | 仕入name |
|---|---|---|---|
| 1月 | 月別売上/仕入 | `uriageKingaku1` | `siireKingaku1` |
| 2月 | 月別売上/仕入 | `uriageKingaku2` | `siireKingaku2` |
| 3月 | 月別売上/仕入 | `uriageKingaku3` | `siireKingaku3` |
| 4月 | 月別売上/仕入 | `uriageKingaku4` | `siireKingaku4` |
| 5月 | 月別売上/仕入 | `uriageKingaku5` | `siireKingaku5` |
| 6月 | 月別売上/仕入 | `uriageKingaku6` | `siireKingaku6` |
| 7月 | 月別売上/仕入 | `uriageKingaku7` | `siireKingaku7` |
| 8月 | 月別売上/仕入 | `uriageKingaku8` | `siireKingaku8` |
| 9月 | 月別売上/仕入 | `uriageKingaku9` | `siireKingaku9` |
| 10月 | 月別売上/仕入 | `uriageKingaku10` | `siireKingaku10` |
| 11月 | 月別売上/仕入 | `uriageKingaku11` | `siireKingaku11` |
| 12月 | 月別売上/仕入 | `uriageKingaku12` | `siireKingaku12` |
| 家事消費等 | 売上のみ | `kajisyohi` | — |
| 雑収入 | 売上のみ | `zatusyunyu` | — |
| 合計 | 自動計算 | `dispUriageKingakuGokei`（表示用SPAN） | `dispSiireKingakuGokei`（表示用SPAN） |
| うち軽減税率対象 | 売上/仕入 | `uriageUtiKeigenZeiTuki` | `siireUtiKeigenZeiTuki` |

### 売上（収入）金額の合計を入力（年間合計入力方式）

月別入力の代わりに年間合計額を直接入力する方式。

| フィールド名 | name | 備考 |
|---|---|---|
| 合計金額（家事消費等・雑収入を含む） | `uriageKingakuKeisanZumiGokei` | 年間合計額 |
| うち軽減税率対象 | `uriageUtiKeigenZeiNen` | |

### hidden 集計フィールド

| フィールド名 | name | 備考 |
|---|---|---|
| 売上金額合計 | `uriageKingakuGokei` | hidden、aa0200 に戻る際に自動セット |
| 仕入金額合計 | `siireKingakuGokei` | hidden、aa0200 に戻る際に自動セット |

### 明細入力

| セクション | ボタン | 備考 |
|---|---|---|
| 売上（収入）金額の明細 | 「売上先を入力する」 | 取引先別の売上明細入力 |
| 仕入金額の明細 | 「仕入先を入力する」 | 取引先別の仕入明細入力 |

## ボタン

| ボタン名 | 遷移先 |
|---|---|
| 前に戻る | aa0200（確認ダイアログ「入力したデータが反映されません」KS-W90011） |
| 次へ進む | aa0200（入力データ反映） |
| この画面の入力内容をクリア | 入力値クリア |

## 注意事項
- 月別入力と年間合計入力は排他的（月別入力すると合計は自動計算、合計入力すると月別は無効）
- 「前に戻る」は confirm ダイアログが出る（KS-W90011: 入力データが反映されない警告）
- 「次へ進む」は入力データを aa0200 に反映して戻る
- pageId: `aa0201`

## スクリーンショット
- `15-kessan-revenue-detail-entry.png`
