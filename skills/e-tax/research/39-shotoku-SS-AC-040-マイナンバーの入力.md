# 39 - マイナンバーの入力

## 画面番号
SS-AC-040

## URL
https://www.keisan.nta.go.jp/r7/syotoku/taM070a10_doNext#bbctrl

## 概要
マイナンバー（個人番号）12桁を入力する画面。本人および扶養親族等がいる場合はその分も表示される。

## フォーム要素

マイナンバーは3分割（各4桁）で入力。

| ラベル | type | name | maxlength |
|---|---|---|---|
| マイナンバー1（本人） | text | inOutDto.mynmbrNyrykList[0].mynmbr1 | 4 |
| マイナンバー2（本人） | text | inOutDto.mynmbrNyrykList[0].mynmbr2 | 4 |
| マイナンバー3（本人） | text | inOutDto.mynmbrNyrykList[0].mynmbr3 | 4 |

配偶者・扶養親族がいる場合は `mynmbrNyrykList[1]`, `[2]`, ... と追加される。

## 表示情報
- 氏名
- 生年月日
- 関係（本人、配偶者、扶養親族等）

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 次へ | SS-AC-050（申告書印刷/帳票表示） |
| 戻る | SS-AC-030（基本情報の入力） |
| ここまでの入力内容を保存 | .dataファイルダウンロード |

## スクリーンショット
- `42-mynumber.png`
