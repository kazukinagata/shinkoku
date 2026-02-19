# 50 - 一般課税・簡易課税の条件判定等

## 画面番号
（フッタなし、URL: ac0100）

## URL
https://www.keisan.nta.go.jp/syouhi/ac0100/submit.htmj#bsctrl

## 概要
消費税の課税方式を決定するための条件判定画面。基準期間の課税売上高、インボイス発行事業者かどうか、簡易課税制度選択の有無、経理方式を入力。回答内容に応じて2割特例・簡易課税・一般課税のいずれかの入力フローに分岐する。

## フォーム要素

| ラベル | type | name | id | 備考 |
|---|---|---|---|---|
| 基準期間の課税売上高 | text | kijunKazeiUriage | kijunKazeiUriage | 必須。R5年分 |
| インボイス発行事業者ですか？ | radio | invoice | invoiceTrue/invoiceFalse | true/false |
| 簡易課税制度を選択していますか？ | radio | kani | kazeiSeidoKaniTrue/kazeiSeidoKaniFalse | true/false |
| 経理方式 | radio | zeikomi | keiriZeikomi/keiriZeinuki | 税込/税抜 |

### 条件付きフィールド（インボイス=はい の場合に表示）

| ラベル | type | name | id | 備考 |
|---|---|---|---|---|
| 新たに課税事業者になった方ですか？ | radio | newKazeiJigyosya | newKazeiJigyosyaTrue/False | |
| 2割特例を適用しますか？ | radio | niwariTokurei | niwariTokureiTrue/False | |
| 免税期間の課税売上高 | text | menzeiKikanKazeiUriage | menzeiKikanKazeiUriage | |

### 一般課税の場合に表示

| ラベル | type | name | id | 備考 |
|---|---|---|---|---|
| 仕入税額の計算方法 | radio | siireKeisanHouhou | siire-warimodosi/siire-tumiage | 割戻し/積上げ |

### 特別な売上基準（アコーディオン）

| ラベル | type | name | id | 備考 |
|---|---|---|---|---|
| 割賦基準 | checkbox | kappu | kappu | |
| 延払基準 | checkbox | nobebarai | nobebarai | |
| 工事進行基準 | checkbox | kojisinko | kojisinko | |
| 現金主義会計 | checkbox | genkin | genkin | |

## 分岐ロジック

| 条件 | 遷移先 |
|---|---|
| インボイス=はい & 新課税事業者=はい & 2割特例=はい | 2割特例入力画面 |
| 簡易課税=はい（& 基準期間5000万円以下） | 簡易課税入力画面 |
| 上記以外 | 一般課税入力画面 |

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 次へ | 条件に応じた入力画面 |
| 戻る | 作成開始画面 |

## スクリーンショット
- `47-shouhi-condition.png`
