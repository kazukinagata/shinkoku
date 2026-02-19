# 37 - 財産債務調書、住民税等に関する事項

## 画面番号
SS-AC-020a

## URL
https://www.keisan.nta.go.jp/r7/syotoku/taM050a20_doNext#bbctrl

## 概要
財産債務調書の提出要件確認と住民税に関する事項の入力画面。確定申告書を提出する場合は住民税の申告書は不要だが、所得税と住民税で取扱いが異なる事項について入力が必要。

## フォーム要素

### 財産債務調書の提出要件

| フォーム要素 | type | name | 備考 |
|---|---|---|---|
| 10億円以上の財産を保有 | checkbox | inOutDto.snOkNIjyoZisnEtc | |

### 住民税に関する事項

| フォーム要素 | type | name | 備考 |
|---|---|---|---|
| 16歳未満の扶養親族に関する入力を行う | checkbox | inOutDto.jyrkmmnFyoShnzk | |
| 退職所得のある配偶者・親族等に関する入力を行う | checkbox | inOutDto.tasykuSytkHagsyShnzkTo | |
| 別居の配偶者・親族に関する入力を行う | checkbox | inOutDto.bkyoHagsyShnzk | |
| 非上場株式の少額配当等の入力を行う | checkbox | inOutDto.hjojoKbshkSyogkHatoKngkUm | |
| 住民税の徴収方法 | select | inOutDto.jyumnzeCyosyuHoho | |

住民税の徴収方法の選択肢:

| value | テキスト |
|---|---|
| （空） | 必要な方のみ選択してください |
| 1 | 特別徴収（給与から天引き） |
| 2 | 自分で納付 |

### 隠しチェックボックス（DOM上に存在）

| name | 備考 |
|---|---|
| inOutDto.duitssekeHagsy | 同一生計配偶者? |
| inOutDto.jyumnzeToJgyoSytkFdosnSytk | 住民税等事業所得不動産所得? |

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 次へ | SS-AA-100（住所・氏名等の入力） |
| 戻る | SS-AC-010a（納付方法等の入力） |
| ここまでの入力内容を保存 | .dataファイルダウンロード |

## スクリーンショット
- `40-zaimu-juminzei.png`
