# 38 - 基本情報の入力

## 画面番号
SS-AC-030

## URL
https://www.keisan.nta.go.jp/r7/syotoku/taM060a10_doNext#bbctrl

## 概要
申告者の氏名・住所・電話番号・職業・提出先税務署等の基本情報を入力する画面。提出年月日は当日がデフォルトで入力済み。

## フォーム要素

### 氏名・電話番号の入力

| ラベル | type | name | 備考 |
|---|---|---|---|
| 氏名フリガナ（姓） | text | inOutDto.nameKnSe | 11文字以内 |
| 氏名フリガナ（名） | text | inOutDto.nameKnMe | 合計12文字以内 |
| 氏名漢字（姓） | text | inOutDto.nameKnjSe | 10文字以内 |
| 氏名漢字（名） | text | inOutDto.nameKnjMe | 10文字以内 |
| 電話番号（種別） | select | inOutDto.rnrkSkKbn | 自宅/勤務先/携帯 |
| 電話番号（市外局番） | tel | inOutDto.shgaKykbn | |
| 電話番号（市内局番） | tel | inOutDto.shnaKykbn | |
| 電話番号（加入者番号） | tel | inOutDto.knyusyBngo | |

### 住所の入力（現在の住所）

| ラベル | type | name | 備考 |
|---|---|---|---|
| 納税地の区分 | radio | inOutDto.nozeCh | 1=住所地, 2=事業所等 |
| 郵便番号 | tel | inOutDto.yubnBngoGnzaAddress | 7桁 |
| 都道府県 | select | inOutDto.tdofknGnzaAddress | 47都道府県 |
| 市区町村 | select | inOutDto.shkcyosnGnzaAddress | 都道府県連動 |
| 丁目番地等 | text | inOutDto.cyomBnchToGnzaAddress | 都道府県・市区町村と合計28文字以内 |
| 建物名・号室 | text | inOutDto.ttmnMeGoshtsGnzaAddress | 28文字以内 |
| 提出先税務署（都道府県） | select | inOutDto.tesytSkZemsyTdofkn | |
| 提出先税務署（税務署） | select | inOutDto.tesytSkZemsyZemsy | 都道府県連動 |

### 令和8年1月1日の住所

| ラベル | type | name | 備考 |
|---|---|---|---|
| 住所が上記と異なる | checkbox | — | チェックで追加フィールド表示 |
| 郵便番号 | tel | inOutDto.ybnBngWrkHyk1Yy1Mm1Ddddrss | 異なる場合のみ |
| 都道府県 | select | inOutDto.tdfknWrkHyk1Yy1Mm1Ddddrss | |
| 市区町村 | select | inOutDto.shkcysnWrkHyk1Yy1Mm1Ddddrss | |
| 丁目番地等 | text | inOutDto.cymBnchTWrkHyk1Yy1Mm1Ddddrss | |
| 建物名・号室 | text | inOutDto.ttmnMGshtsWrkHyk1Yy1Mm1Ddddrss | |

### その他の項目の入力

| ラベル | type | name | 備考 |
|---|---|---|---|
| 職業 | text | inOutDto.job | 11文字以内 |
| 屋号・雅号 | text | inOutDto.ygoGgo | 30文字以内 |
| 世帯主の氏名（漢字） | text | inOutDto.stanshNameKnj | 10文字以内 |
| 世帯主からみた続柄 | select | inOutDto.stanshKrTsdkgr | 本人/妻/夫/子/父/母/祖父/祖母/孫/その他 |
| 整理番号 | tel | inOutDto.serBngo | 数字8桁 |
| 提出年月日（年） | select | inOutDto.tesytYmdYy | 令和8〜令和13 |
| 提出年月日（月） | select | inOutDto.tesytYmdMm | 1〜12 |
| 提出年月日（日） | select | inOutDto.tesytYmdDd | 1〜28（月による） |

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 次へ | SS-AC-050（マイナンバーの入力） |
| 戻る | SS-AC-020a（財産債務調書、住民税等） |
| ここまでの入力内容を保存 | .dataファイルダウンロード |

## 備考
- 「郵便番号から住所入力」ボタンで住所自動入力可能
- 「ご自身が世帯主」ボタンで氏名自動コピー
- 市区町村・税務署のselect optionは都道府県選択後に動的に読み込まれる

## スクリーンショット
- `41-basic-info.png`
