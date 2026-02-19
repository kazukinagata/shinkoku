# 09 - 貸借対照表（一般用）の入力

## URL
https://www.keisan.nta.go.jp/kessan/ac/preAoiroCalc#bsctrl
（preAoiroCalc から遷移、URL は変わらない場合あり）

## 概要
青色申告決算書の貸借対照表（B/S）を入力する画面。
資産の部と負債・資本の部をそれぞれアコーディオン展開で入力する。
期首・期末の各部合計が一致する必要がある。

## 到達方法（書面提出ルート）
ac/submit/aa0100（青色申告特別控除）→ preAoiroCalc → **貸借対照表入力**

## フォーム要素

### 期間

| フィールド名 | 備考 |
|---|---|
| 期首: 月/日 | テキストボックス（P/Lの期間から自動セット） |
| 期末: 月/日 | テキストボックス（P/Lの期間から自動セット） |
| 年号テキスト | `令和` |
| 年 | `7` |
| 月/日 | `12月31日現在` |

### 資産の部（sisannobuTaisyohyoDetailDataList）

配列形式: `sisannobuTaisyohyoDetailDataList[N].kisyuKingaku` / `sisannobuTaisyohyoDetailDataList[N].kimatuKingaku`

| index | 勘定科目 | 期首name | 期末name |
|---|---|---|---|
| 0 | 現金 | `sisannobuTaisyohyoDetailDataList[0].kisyuKingaku` | `sisannobuTaisyohyoDetailDataList[0].kimatuKingaku` |
| 1 | 当座預金 | `...[1].kisyuKingaku` | `...[1].kimatuKingaku` |
| 2 | 定期預金 | `...[2].kisyuKingaku` | `...[2].kimatuKingaku` |
| 3 | その他の預金 | `...[3].kisyuKingaku` | `...[3].kimatuKingaku` |
| 4 | 受取手形 | `...[4].kisyuKingaku` | `...[4].kimatuKingaku` |
| 5 | 売掛金 | `...[5].kisyuKingaku` | `...[5].kimatuKingaku` |
| 6 | 有価証券 | `...[6].kisyuKingaku` | `...[6].kimatuKingaku` |
| 7 | 棚卸資産 | `...[7].kisyuKingaku` | `...[7].kimatuKingaku` |
| 8 | 前払金 | `...[8].kisyuKingaku` | `...[8].kimatuKingaku` |
| 9 | 貸付金 | `...[9].kisyuKingaku` | `...[9].kimatuKingaku` |
| 10 | 建物 | `...[10].kisyuKingaku` | `...[10].kimatuKingaku` |
| 11 | 建物附属設備 | `...[11].kisyuKingaku` | `...[11].kimatuKingaku` |
| 12 | 機械装置 | `...[12].kisyuKingaku` | `...[12].kimatuKingaku` |
| 13 | 車両運搬具 | `...[13].kisyuKingaku` | `...[13].kimatuKingaku` |
| 14 | 工具器具備品 | `...[14].kisyuKingaku` | `...[14].kimatuKingaku` |
| 15 | 土地 | `...[15].kisyuKingaku` | `...[15].kimatuKingaku` |
| 16-23 | 任意科目（追加可能） | `...[16-23].kisyuKingaku` | `...[16-23].kimatuKingaku` |

### 負債・資本の部（fusainobuTaisyohyoDetailDataList）

配列形式: `fusainobuTaisyohyoDetailDataList[N].kisyuKingaku` / `fusainobuTaisyohyoDetailDataList[N].kimatuKingaku`

| index | 勘定科目 | 期首name | 期末name |
|---|---|---|---|
| 0 | 支払手形 | `fusainobuTaisyohyoDetailDataList[0].kisyuKingaku` | `...[0].kimatuKingaku` |
| 1 | 買掛金 | `...[1].kisyuKingaku` | `...[1].kimatuKingaku` |
| 2 | 借入金 | `...[2].kisyuKingaku` | `...[2].kimatuKingaku` |
| 3 | 未払金 | `...[3].kisyuKingaku` | `...[3].kimatuKingaku` |
| 4 | 前受金 | `...[4].kisyuKingaku` | `...[4].kimatuKingaku` |
| 5 | 預り金 | `...[5].kisyuKingaku` | `...[5].kimatuKingaku` |
| 6 | 貸倒引当金 | `...[6].kisyuKingaku` | `...[6].kimatuKingaku` |
| 7-15 | 任意科目（追加可能） | `...[7-15].kisyuKingaku` | `...[7-15].kimatuKingaku` |
| 16 | 元入金 | `...[16].kisyuKingaku` | `...[16].kimatuKingaku` |
| 17 | 事業主借 | `...[17].kisyuKingaku` | `...[17].kimatuKingaku` |
| 18 | 事業主貸 | `...[18].kisyuKingaku` | `...[18].kimatuKingaku` |
| 19 | 青色申告特別控除前の所得金額 | `...[19].kisyuKingaku` | `...[19].kimatuKingaku` |
| 20-23 | 予備 | — | — |

### 各部の合計金額（自動計算・検証）

| フィールド名 | 備考 |
|---|---|
| 資産の部 期首合計 | 自動計算 |
| 資産の部 期末合計 | 自動計算 |
| 負債・資本の部 期首合計 | 自動計算 |
| 負債・資本の部 期末合計 | 自動計算（P/Lの所得金額が自動反映） |
| 結果: 一致/不一致 | 期首・期末ごとに資産=負債+資本を検証 |

## ジャンプリンク

| リンクテキスト | href | 備考 |
|---|---|---|
| 資産の部 | `JavaScript:jumpassets();` | 資産の部にスクロール |
| 負債・資本の部 | `JavaScript:jumpdebcap();` | 負債・資本の部にスクロール |

## ボタン

| ボタン名 | 遷移先 |
|---|---|
| 前に戻る | 青色申告特別控除の入力 |
| 次へ進む | 住所等入力（推定） |
| ここまでの入力内容を保存する | .data ファイルダウンロード |
| この画面の入力内容をクリア | 入力値クリア |

## 注意事項
- P/L の青色申告特別控除前の所得金額が自動的に負債・資本の部の期末に反映される
- 期首・期末の各部合計が一致しないと「不一致」表示（送信は可能かは未確認）
- 資産の部と負債・資本の部はそれぞれアコーディオン展開型
- 任意科目の追加ボタンがある

## スクリーンショット
- `19-kessan-balance-sheet.png`
