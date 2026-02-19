# 54 - 簡易課税ルート サマリ

## 画面フロー
1. ac0100 条件判定等 → invoice=はい, kani=はい
2. ac0250 所得区分の選択 → ヘッダに「簡易課税」表示
3. ak0150 売上（収入）金額等の入力ハブ
4. ak0800/inputEigyo 事業所得（営業等）の売上入力（フォーム名は一般課税と同一）
5. ak0800/submit 中間納付税額等の入力
6. ac0300 計算結果の確認

## URL体系
- 簡易課税: `/syouhi/ak****` (kani の k)
- 一般課税: `/syouhi/ai****` (ippan の i)
- 共通: `/syouhi/ac****` (common)

## フォーム要素
売上入力フォームのフィールド名は一般課税/2割特例と**同一**（uriageWari等）。
簡易課税では仕入金額の入力は不要（みなし仕入率で自動計算）。

## 中間納付税額等の入力
| name | id | 備考 |
|---|---|---|
| chukanNofuZei | chukanNofuZei | 中間納付消費税額 |
| chukanNofuJotoWari | chukanNofuJotoWari | 中間納付譲渡割額 |

## 計算結果
簡易課税の計算結果表示は一般課税/2割特例と同じac0300画面。
ヘッダ部に「簡易課税」表示で区別。

## スクリーンショット
- `53-shouhi-kani-sales-hub.png`
- `54-shouhi-kani-eigyo-input.png`
- `55-shouhi-kani-result.png`
