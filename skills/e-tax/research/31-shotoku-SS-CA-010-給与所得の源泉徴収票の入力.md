# 31 - 給与所得の源泉徴収票の入力

## 画面番号
SS-CA-010（一覧）→ SS-CA-010（入力フォーム）

## URL
- 一覧: https://www.keisan.nta.go.jp/r7/syotoku/taM020a10_doKyuy#bbctrl (SS-CC-010)
- 入力（年末調整済み）: https://www.keisan.nta.go.jp/r7/syotoku/taS510a10_doAdd_nncyzm#bbctrl

## 画面遷移
SS-AA-050（収入・所得の入力ハブ）→ SS-CC-010（源泉徴収票の一覧）→ SS-CA-010（入力フォーム）

## 概要
給与所得の源泉徴収票に記載された内容を入力する画面。源泉徴収票の見本画像とともに、A〜Hラベルで各フィールドを対応付けている。
年末調整済みと年末調整未済で別フォーム。

## 全フォーム要素（name/id）

### 主要入力フィールド（常時表示）

| ラベル | type | name | 備考 |
|---|---|---|---|
| A: 支払金額（円） | tel | inOutDto.shhraKngk | 必須 |
| D: 源泉徴収税額（円） | tel | inOutDto.gnsnTyosyuZegk | 2段記載時は下段 |
| 社会保険料等の金額 | tel | inOutDto.sykaHknryoToKngk | |
| G: 支払者の住所 | text | inOutDto.shhrasyJysyKysyOrSyzach | 28文字以内 |
| H: 支払者の氏名又は名称 | text | inOutDto.shhrasyNameOrMesyo | 28文字以内 |

### 条件付きフィールド（ラジオ/チェック選択で表示）

| ラベル | type | name | 表示条件 |
|---|---|---|---|
| D': 源泉徴収税額（内書き） | tel | inOutDto.gnsnTyosyuZegkUchgk | gnsnTyosyuZegkUchgkUm チェック時 |
| 社会保険料等（内書き） | tel | inOutDto.sykaHknryoToUchgk | sykaHknryoToUchgkUm チェック時 |
| 生命保険料控除額 | tel | inOutDto.semeHknryoKojygk | semeHknryoKojygkKsaUm=1時 |
| 新生命保険料金額 | tel | inOutDto.shnSemeHknryoKngk | 生命保険料記載あり時 |
| 旧生命保険料金額 | tel | inOutDto.kyuSemeHknryoKngk | 生命保険料記載あり時 |
| 介護医療保険料金額 | tel | inOutDto.kagIryoHknryoKngk | 生命保険料記載あり時 |
| 新個人年金保険料金額 | tel | inOutDto.shnKjnNnknHknryoKngk | 生命保険料記載あり時 |
| 旧個人年金保険料金額 | tel | inOutDto.kyuKjnNnknHknryoKngk | 生命保険料記載あり時 |
| 地震保険料控除額 | tel | inOutDto.jshnHknryoKojygk | jshnHknryoKojygkKsaUm=1時 |
| 旧長期損害保険料金額 | tel | inOutDto.kyuCyokSngaHknryoKngk | 地震保険料記載あり時 |
| E: 住宅借入金等特別控除額 | tel | inOutDto.jyutkKrirknToTkbtsKojyGk | jyutkKrirknToTkbtsKojyGkKsaUm=1時 |
| E': 住宅借入金等特別控除可能額 | tel | inOutDto.jyutkKrirknToTkbtsKojyknoGk | 住宅借入金記載あり時 |
| E'': 住宅借入金年末残高1回目 | tel | inOutDto.jyutkKrirknToNnmtszndkIkkam | 住宅借入金記載あり時 |
| E''': 住宅借入金年末残高2回目 | tel | inOutDto.jyutkKrirknToNnmtszndkNkam | nkamJyutkKrirknKsaAr チェック時 |

### ラジオボタン

| フィールド名 | name | 値 | 備考 |
|---|---|---|---|
| 入力方法 | rsdamplex | on(カメラ)/on(直接入力) | id: nyrykHohoSntk_1/2 |
| 控除対象配偶者の記載 | inOutDto.kojyTashoHagsyKsaUm | 1(あり)/2(なし) | |
| 控除対象扶養親族の記載 | inOutDto.kojyTashoFyoShnzkKsaUm | 1(あり)/2(なし) | |
| 生命保険料控除額の記載 | inOutDto.semeHknryoKojygkKsaUm | 1(あり)/2(なし) | |
| 地震保険料控除額の記載 | inOutDto.jshnHknryoKojygkKsaUm | 1(あり)/2(なし) | |
| 住宅借入金等特別控除額の記載 | inOutDto.jyutkKrirknToTkbtsKojyGkKsaUm | 1(あり)/0(なし) | |
| 所得金額調整控除額の記載 | inOutDto.sytkKngkTyoseKojygkKsaUm | 1(あり)/0(なし) | |
| 本人が障害者・寡婦等 | inOutDto.hnninSygsyKfHtriyKnroGkseKsaUm | 1(あり)/2(なし) | |

### チェックボックス

| フィールド名 | name | 備考 |
|---|---|---|
| 源泉徴収税額が2段で記載 | inOutDto.gnsnTyosyuZegkUchgkUm | |
| 社会保険料等が2段で記載 | inOutDto.sykaHknryoToUchgkUm | |
| 2回目の住宅借入金の記載がある | inOutDto.nkamJyutkKrirknKsaAr | |
| 記載あり（寡婦） | inOutDto.ksaArKforkf | |
| 記載あり（勤労学生） | inOutDto.ksaArKnroGkse | |

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 入力終了 | SS-CC-010（源泉徴収票の一覧） |
| 戻る | SS-CC-010（源泉徴収票の一覧） |

## バリデーション
- 源泉徴収税額が支払金額と所得控除額から計算される理論値と大きく異なる場合、警告エラー（SSCA010-SUE023）
- 支払者の住所と氏名は必須

## スクリーンショット
- `32-kyuyo-gensen-input.png` - 初期表示
- `34-gensen-nenchou-input.png` - 年末調整済み入力
