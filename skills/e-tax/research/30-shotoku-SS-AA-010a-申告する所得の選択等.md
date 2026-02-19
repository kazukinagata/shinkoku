# 30 - 申告する所得の選択等

## 画面番号
SS-AA-010a

## URL
https://www.keisan.nta.go.jp/r7/syotoku/taM010a40_doInitialDisplay#bbctrl

## 概要
所得税申告の最初の画面。申告者の生年月日と、申告する所得の種類を選択する。
書面提出ルートで CC-AA-090 から「所得税」を選択するとこの画面に遷移する。

## ナビゲーションステップ
1. 申告準備 ← 現在
2. 収入等入力
3. 控除等入力
4. その他入力
5. 印刷
6. データ保存等

## フォーム要素

### 本人情報の確認

| フィールド名 | type | name/id | 備考 |
|---|---|---|---|
| 生年月日（年） | select | inOutDto.shnkkBirthymdYy | 明治23(1890)〜令和7(2025) |
| 生年月日（月） | select | inOutDto.shnkkBirthymdMm | 1〜12 |
| 生年月日（日） | select | inOutDto.shnkkBirthymdDd | 1〜31 |

### 申告する所得の選択（チェックボックス）

#### 給与収入がある方、年金収入がある方、退職金を受け取った方

| フィールド名 | type | name/id | value | 備考 |
|---|---|---|---|---|
| 給与 | checkbox | inOutDto.kyuy | 1 | ※確定申告をする場合には年末調整を受けた給与所得も含めて申告が必要 |
| 公的年金、企業年金など | checkbox | inOutDto.kotkNnknKgyoNnknEtc | 1 | 生命保険等の個人年金は「雑」を選択 |
| 退職金 | checkbox | inOutDto.tasyku | 1 | |

#### 個人事業の収入がある方、不動産等貸付けの収入がある方

| フィールド名 | type | name/id | value | 備考 |
|---|---|---|---|---|
| 事業（営業等） | checkbox | inOutDto.jgyoEgyoTo | 1 | |
| 事業（農業） | checkbox | inOutDto.jgyoNogyo | 1 | |
| 不動産 | checkbox | inOutDto.fdosn | 1 | |

#### 株式を売った方、配当等を受け取った方

| フィールド名 | type | name/id | value | 備考 |
|---|---|---|---|---|
| 株式等の譲渡（売却）、配当、利子 | checkbox | inOutDto.hatoKbshkJyotRsh | 1 | |

#### 土地や建物、金地金やゴルフ会員権などの資産を売った方

| フィールド名 | type | name/id | value | 備考 |
|---|---|---|---|---|
| 土地や建物等の譲渡（売却） | checkbox | inOutDto.tchYTtmnToJyotByk | 1 | |
| 総合譲渡（金地金の売却など） | checkbox | inOutDto.sogoJyot | 1 | |

#### その他の収入がある方

| フィールド名 | type | name/id | value | 備考 |
|---|---|---|---|---|
| 先物取引 | checkbox | inOutDto.skmnTrhk | 1 | FX・CFD・先物オプション |
| 一時 | checkbox | inOutDto.ichj | 1 | |
| 雑（業務・その他） | checkbox | inOutDto.ztsGyomSnt | 1 | 原稿料、講演料、副収入、暗号資産等 |

## ボタン・遷移

| ボタン名 | selector/ref | 遷移先 |
|---|---|---|
| 次へ | button ref=e148 | 収入金額・所得金額の入力（選択した所得に応じた画面） |
| 戻る | button ref=e149 | CC-AA-090 |

## shinkoku対象の典型的選択パターン

### 会社員＋副業（事業所得）
- 給与: checked
- 事業（営業等）: checked
- 雑（業務・その他）: checked（暗号資産等がある場合）

### 給与所得のみ（医療費控除等）
- 給与: checked

## スクリーンショット
- `31-shotoku-income-selection.png`
