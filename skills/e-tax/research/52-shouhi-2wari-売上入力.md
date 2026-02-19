# 52 - 事業所得（営業等）の売上（収入）金額等の入力（2割特例/一般課税共通）

## URL
https://www.keisan.nta.go.jp/syouhi/ai3600/inputEigyo.htmj#bsctrl

## 概要
事業所得（営業等）の売上金額を入力する画面。課税事業者となった日以降の取引分を入力。免税・非課税・不課税取引、軽減税率適用分、返還等対価・貸倒れの入力はアコーディオン内。

## フォーム要素

### 収入金額（メイン）

| ラベル | name | id | 備考 |
|---|---|---|---|
| 売上（収入）金額 | uriageWari | uriageWari | 必須。雑収入含む全額 |
| 課税取引金額 | kazeiTorihikiKingakuWari | kazeiTorihikiKingakuWari | 自動計算（disabled） |

### 免税・非課税・不課税取引（アコーディオン内）

| ラベル | name | id | 備考 |
|---|---|---|---|
| 免税売上 | menzeiUriageWari | menzeiUriageWari | |
| 非課税売上 | hikazeiUriageWari | hikazeiUriageWari | |
| 非課税資産の輸出等 | hikazeiSisanWari | hikazeiSisanWari | |
| 不課税取引 | jigyoFukazeiUriageWari | jigyoFukazeiUriageWari | |
| 課税売上 | jigyoKazeiUriageWari | jigyoKazeiUriageWari | 自動計算（disabled） |

### 軽減税率（6.24%）適用分

| ラベル | name | id | 備考 |
|---|---|---|---|
| 軽減税率適用分 | kazeiUriage624PercentWari | kazeiUriage624PercentWari | |
| 標準税率分 | kazeiUriage78PercentWari | kazeiUriage78PercentWari | 自動計算 |

### 返還等対価

| ラベル | name | id | 備考 |
|---|---|---|---|
| 返還等対価（軽減税率分） | uriageTaikaKeigen.uriageTaika624Percent | uriageTaika624Percent | |
| 返還等対価（標準税率分） | uriageTaikaKeigen.uriageTaika78Percent | uriageTaika78Percent | |
| 返還等対価合計 | uriageTaikaGoukeigaku | uriageTaikaGoukeigaku | 自動計算 |
| 免税返還 | uriageTaikaKeigen.menzeiHenkan | menzeiHenkan | |

### 貸倒れ

| ラベル | name | id | 備考 |
|---|---|---|---|
| 発生（軽減税率分） | kasidaoreKeigen.occurredKasidaore624Percent | occurredKasidaore624Percent | |
| 発生（標準税率分） | kasidaoreKeigen.occurredKasidaore78Percent | occurredKasidaore78Percent | |
| 発生合計 | occurredKasidaoreSum | occurredKasidaoreSum | 自動計算 |
| 回収（軽減税率分） | kasidaoreKeigen.recoveredKasidaore624Percent | recoveredKasidaore624Percent | |
| 回収（標準税率分） | kasidaoreKeigen.recoveredKasidaore78Percent | recoveredKasidaore78Percent | |
| 回収合計 | recoveredKasidaoreSum | recoveredKasidaoreSum | 自動計算 |

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 次へ | 売上一覧ハブ画面（ai0150） |
| 戻る | 売上一覧ハブ画面（ai0150） |

## スクリーンショット
- `50-shouhi-2wari-eigyo-input.png`
