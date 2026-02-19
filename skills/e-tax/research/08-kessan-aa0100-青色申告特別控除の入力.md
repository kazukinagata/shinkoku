# 08 - 青色申告特別控除の入力

## URL
https://www.keisan.nta.go.jp/kessan/ac/submit/aa0100#bsctrl
https://www.keisan.nta.go.jp/kessan/ac/preAoiroCalc#bsctrl （計算処理後）

## 概要
青色申告特別控除額の選択と関連質問に回答する画面。
Q&A形式で順次質問が展開される。

## 到達方法（書面提出ルート）
ac/pre/ac0300（種類選択）→ ac/aa0200（P&L入力）→ ac0300（種類選択ハブ）→ **ac/submit/aa0100**

## フォーム要素

### 質問1: 青色申告特別控除額の選択

| フィールド名 | name | id | value | 備考 |
|---|---|---|---|---|
| 10万円 | `aoiroTokubetuKojoSentakugaku` | `aoiroKojogaku` | `2` | |
| 55万円 | `aoiroTokubetuKojoSentakugaku` | `aoiroKojogaku2` | `3` | 書面提出の場合の上限 |
| 65万円 | `aoiroTokubetuKojoSentakugaku` | `aoiroKojogaku3` | `1` | e-Tax送信が必要（書面提出ではエラー KS-E10089） |

### 質問2: 電子帳簿保存の要件（65万円選択時のみ表示）

| フィールド名 | name | id | value | 備考 |
|---|---|---|---|---|
| はい | `densiChoboHozonSelect` | `densichouboTrue` | `true` | 優良な電子帳簿保存の届出済み |
| いいえ | `densiChoboHozonSelect` | `densichouboFalse` | `false` | |

### 質問3: 貸借対照表の作成

| フィールド名 | name | id | value | 備考 |
|---|---|---|---|---|
| はい | `taisyohyoCreateSelect` | `taisyakuTaisyohyoTrue` | `true` | 貸借対照表入力画面へ進む |
| いいえ | `taisyohyoCreateSelect` | `taisyakuTaisyohyoFalse` | `false` | 貸借対照表をスキップ |

### 不動産貸付事業判定（不動産所得がある場合のみ）

| フィールド名 | name | id | value | 備考 |
|---|---|---|---|---|
| はい | `fudosanKasitukeKubun` | `fudosanAsZigyoTrue` | `true` | |
| いいえ | `fudosanKasitukeKubun` | `fudosanAsZigyoFalse` | `false` | |

## 重要な制約

### 書面提出ルートでの65万円控除
- 65万円の青色申告特別控除はe-Tax送信が必須
- 書面提出ルートで65万円を選択すると、エラー KS-E10089 が表示される
- エラー内容: 「65万円の青色申告特別控除の適用を受けるためには、貸借対照表を作成の上、青色申告決算書と確定申告書を法定申告期限までにe-Taxで送信（提出）する必要があります。」
- 書面提出では最大55万円まで

### 55万円控除の要件
1. 正規の簿記の原則により記帳
2. 青色申告決算書（貸借対照表を含む）を添付
3. 法定申告期限までに提出

### 65万円控除の追加要件（55万円の要件 + 以下のいずれか）
1. 優良な電子帳簿の要件を満たして電子データで保存 + 届出書提出
2. 確定申告書と青色申告決算書をe-Taxで送信

## ボタン

| ボタン名 | 遷移先 | 備考 |
|---|---|---|
| 前に戻る | 青色申告決算書の種類選択 | |
| 次へ進む | 貸借対照表の入力（「はい」選択時）/ 住所等入力 | 質問完了後に有効化 |
| ここまでの入力内容を保存する | .data ファイルダウンロード | |

## 画面遷移フロー
```
65万円選択
  → 電子帳簿保存の質問
    → はい/いいえ
      → 貸借対照表作成の質問
        → はい → preAoiroCalc → 貸借対照表入力
        → いいえ → 次の画面へ
  ※ 書面提出の場合、preAoiroCalc で KS-E10089 エラー

55万円選択
  → 電子帳簿保存の質問（非表示）
  → 貸借対照表作成の質問
    → はい → preAoiroCalc → 貸借対照表入力
    → いいえ → 次の画面へ

10万円選択
  → 貸借対照表作成の質問（非表示？）
  → 次の画面へ
```

## スクリーンショット
- `17-kessan-aoiro-deduction.png`（初期表示 + 要件説明モーダル）
- `18-kessan-aoiro-deduction-answered.png`（回答後）
