# 51 - 所得区分の選択

## URL
https://www.keisan.nta.go.jp/syouhi/ac0250/submit.htmj#bsctrl

## 概要
消費税申告における所得区分の選択画面。該当する所得区分を全て選択する。

## フォーム要素

| ラベル | type | name/id | 備考 |
|---|---|---|---|
| 事業所得（営業等）がある | checkbox | jigyoSyotokuEigyo | |
| 事業所得（農業）がある | checkbox | jigyoSyotokuNogyo | |
| 不動産所得がある | checkbox | fudosanSyotoku | |
| 雑所得（原稿料等）がある | checkbox | zatuSyotoku | |
| 業務用固定資産等の譲渡所得がある | checkbox | jotoSyotoku | |

## ヘッダ表示
- 課税方式（一般課税/簡易課税）
- 経理方式（税込/税抜）

## ボタン・遷移

| ボタン名 | 遷移先 |
|---|---|
| 次へ | 売上（収入）金額・仕入金額等の入力 |
| 戻る | 条件判定等画面 |
| ここまでの入力内容を保存 | .dataファイルダウンロード |

## スクリーンショット
- `48-shouhi-income-type.png`
