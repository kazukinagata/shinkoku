# 04 - e-Taxを行う前の確認

## 画面番号
CC-AA-024

## URL
https://www.keisan.nta.go.jp/kyoutu/ky/sm/cmw6000#bsctrl

## 概要
推奨環境の確認、マイナポータルアプリのインストール案内、利用規約への同意画面。

## フォーム要素

なし（情報表示のみ）

## 表示内容
- 推奨環境テーブル（OS: Windows 11, ブラウザ: Edge/Chrome, PDF: Acrobat Reader DC）
- マイナポータルアプリインストール用QRコード（iPhone/Android）
- 利用規約リンク

## ボタン・遷移

| ボタン名 | id | onclick | 遷移先 |
|---|---|---|---|
| 戻る | - | `csw200back(document)` | CC-AE-600 |
| 利用規約に同意して次へ | `csw0200_next` | `csw0200Next()` | CC-AA-440 (QRコード認証) |

## スクリーンショット
- `06-etax-pre-confirmation.png`
