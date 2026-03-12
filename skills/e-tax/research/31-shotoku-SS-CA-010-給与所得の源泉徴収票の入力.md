# 31 - 給与所得の源泉徴収票の入力

## 画面番号
SS-CA-010（一覧）→ SS-CA-010（入力フォーム）

## URL
- 一覧: https://www.keisan.nta.go.jp/r7/syotoku/taM020a10_doKyuy#bbctrl (SS-CC-010)
- 入力（年末調整済み）: https://www.keisan.nta.go.jp/r7/syotoku/taS510a10_doAdd_nncyzm#bbctrl
- 入力（年末調整未済）: 要確認（スクリーンショット 32 に表示あるが未記録）

## 画面遷移
SS-AA-050（収入・所得の入力ハブ）→ SS-CC-010（源泉徴収票の一覧）→ SS-CA-010（入力フォーム）

## 概要
給与所得の源泉徴収票に記載された内容を入力する画面。源泉徴収票の見本画像とともに、ラベルで各フィールドを対応付けている。

**年末調整済みと年末調整未済で別フォーム・別ラベル体系**になっている:
- 年末調整済み: A〜L ラベル（12項目）
- 年末調整未済: A〜E ラベル（5項目）

### 物理的な源泉徴収票との対応

物理的な源泉徴収票（紙）に印字される項目と、作成コーナーのフォームラベルの対応:

| 源泉徴収票の欄 | 年末調整済みフォーム | 年末調整未済フォーム |
|---------------|-------------------|-------------------|
| 支払金額 | A | A |
| 給与所得控除後の金額 | （入力不要・自動計算） | B（自動計算・入力不可） |
| 所得控除の額の合計額 | （入力不要） | C（入力欄あり） |
| 源泉徴収税額 | B | D |
| 社会保険料等の金額 | E | （ラベルなし） |
| 生命保険料の控除額 | F（ラジオ） | — |
| 地震保険料の控除額 | G（ラジオ） | — |
| 住宅借入金等特別控除の額 | H（ラジオ） | E |
| 支払者の住所 | K | — |
| 支払者の氏名 | L | — |

---

## 年末調整済みフォーム

URL: `https://www.keisan.nta.go.jp/r7/syotoku/taS510a10_doAdd_nncyzm#bbctrl`

### 主要入力フィールド（常時表示）

| ラベル | type | name | 備考 |
|---|---|---|---|
| A: 支払金額（円） | tel | inOutDto.shhraKngk | 必須 |
| B: 源泉徴収税額（円） | tel | inOutDto.gnsnTyosyuZegk | 2段記載時は下段 |
| E: 社会保険料等の金額 | tel | inOutDto.sykaHknryoToKngk | |
| K: 支払者の住所 | text | inOutDto.shhrasyJysyKysyOrSyzach | 28文字以内 |
| L: 支払者の氏名又は名称 | text | inOutDto.shhrasyNameOrMesyo | 28文字以内 |

### ラジオボタン

| フィールド名 | ラベル | name | 値 | 備考 |
|---|---|---|---|---|
| 入力方法 | — | rsdamplex | on(カメラ)/on(直接入力) | id: nyrykHohoSntk_1/2 |
| 控除対象配偶者の記載 | C | inOutDto.kojyTashoHagsyKsaUm | 1(あり)/2(なし) | |
| 控除対象扶養親族の記載 | D | inOutDto.kojyTashoFyoShnzkKsaUm | 1(あり)/2(なし) | |
| 生命保険料控除額の記載 | F | inOutDto.semeHknryoKojygkKsaUm | 1(あり)/2(なし) | ※ラベル推定 |
| 地震保険料控除額の記載 | G | inOutDto.jshnHknryoKojygkKsaUm | 1(あり)/2(なし) | ※ラベル推定 |
| 住宅借入金等特別控除額の記載 | H | inOutDto.jyutkKrirknToTkbtsKojyGkKsaUm | 1(あり)/0(なし) | ※ラベル推定 |
| 所得金額調整控除額の記載 | I | inOutDto.sytkKngkTyoseKojygkKsaUm | 1(あり)/0(なし) | ※ラベル推定 |
| 本人が障害者・寡婦等 | J | inOutDto.hnninSygsyKfHtriyKnroGkseKsaUm | 1(あり)/2(なし) | ※ラベル推定 |

> ※ F〜J のラベルはスクリーンショット未確認。フォーム上の並び順からの推定。

### 条件付きフィールド（ラジオ/チェック選択で表示）

| ラベル | type | name | 表示条件 |
|---|---|---|---|
| B': 源泉徴収税額（内書き） | tel | inOutDto.gnsnTyosyuZegkUchgk | gnsnTyosyuZegkUchgkUm チェック時 |
| 社会保険料等（内書き） | tel | inOutDto.sykaHknryoToUchgk | sykaHknryoToUchgkUm チェック時 |
| 生命保険料控除額 | tel | inOutDto.semeHknryoKojygk | F ラジオ「記載あり」時 |
| 新生命保険料金額 | tel | inOutDto.shnSemeHknryoKngk | F ラジオ「記載あり」時 |
| 旧生命保険料金額 | tel | inOutDto.kyuSemeHknryoKngk | F ラジオ「記載あり」時 |
| 介護医療保険料金額 | tel | inOutDto.kagIryoHknryoKngk | F ラジオ「記載あり」時 |
| 新個人年金保険料金額 | tel | inOutDto.shnKjnNnknHknryoKngk | F ラジオ「記載あり」時 |
| 旧個人年金保険料金額 | tel | inOutDto.kyuKjnNnknHknryoKngk | F ラジオ「記載あり」時 |
| 地震保険料控除額 | tel | inOutDto.jshnHknryoKojygk | G ラジオ「記載あり」時 |
| 旧長期損害保険料金額 | tel | inOutDto.kyuCyokSngaHknryoKngk | G ラジオ「記載あり」時 |
| H: 住宅借入金等特別控除額 | tel | inOutDto.jyutkKrirknToTkbtsKojyGk | H ラジオ「記載あり」時 |
| H': 住宅借入金等特別控除可能額 | tel | inOutDto.jyutkKrirknToTkbtsKojyknoGk | H ラジオ「記載あり」時 |
| H'': 住宅借入金年末残高1回目 | tel | inOutDto.jyutkKrirknToNnmtszndkIkkam | H ラジオ「記載あり」時 |
| H''': 住宅借入金年末残高2回目 | tel | inOutDto.jyutkKrirknToNnmtszndkNkam | nkamJyutkKrirknKsaAr チェック時 |

### チェックボックス

| フィールド名 | name | 備考 |
|---|---|---|
| 源泉徴収税額が2段で記載 | inOutDto.gnsnTyosyuZegkUchgkUm | |
| 社会保険料等が2段で記載 | inOutDto.sykaHknryoToUchgkUm | |
| 2回目の住宅借入金の記載がある | inOutDto.nkamJyutkKrirknKsaAr | |
| 記載あり（寡婦） | inOutDto.ksaArKforkf | J ラジオ「記載あり」時に表示 |
| 記載あり（勤労学生） | inOutDto.ksaArKnroGkse | J ラジオ「記載あり」時に表示 |

---

## 年末調整未済フォーム

URL: 要確認

### 入力フィールド

| ラベル | type | name | 備考 |
|---|---|---|---|
| A: 支払金額（円） | tel | inOutDto.shhraKngk | 必須 |
| B: 給与所得控除後の金額 | — | （自動計算） | 入力不可。A から自動算出 |
| C: 所得控除の額の合計額 | tel | 要確認 | **入力欄あり。源泉徴収票に記載があれば入力** |
| D: 源泉徴収税額（円） | tel | inOutDto.gnsnTyosyuZegk | |
| E: 住宅借入金等特別控除額 | tel | inOutDto.jyutkKrirknToTkbtsKojyGk | |

> フィールド C の `name` 属性は DevTools での確認が必要。

---

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 入力終了 | SS-CC-010（源泉徴収票の一覧） |
| 戻る | SS-CC-010（源泉徴収票の一覧） |

## バリデーション
- 源泉徴収税額が支払金額と所得控除額から計算される理論値と大きく異なる場合、警告エラー（SSCA010-SUE023）
- 支払者の住所と氏名は必須（年末調整済みフォーム）

## スクリーンショット
- `32-kyuyo-gensen-input.png` - 年末調整未済フォーム
- `34-gensen-nenchou-input.png` - 年末調整済み入力（上部）
- `34c-gensen-bottom.png` - 年末調整済み入力（下部）
