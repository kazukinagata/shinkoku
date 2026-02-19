# 11 - 住所・氏名等の入力

## URL
https://www.keisan.nta.go.jp/kessan/ac/ac0500#bsctrl

## 概要
納税地、提出先税務署、氏名等の基本情報を入力する画面。
ステップ3「住所等入力」に該当。

## 到達方法（書面提出ルート）
所得金額の確認 → **ac/ac0500**

## フォーム要素

### 納税地情報

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 納税地区分（住所） | `nozeitiKubunRadio` | `jusyo` | radio | value=1 |
| 納税地区分（事業所等） | `nozeitiKubunRadio` | `jigyosyo` | radio | value=2 |
| 納税地区分hidden | `nozeitiKubun` | `nozeitiKubunValue` | hidden | |

### 住所（自宅）

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 郵便番号 | `jitakuZip` | `jitakuZip` | tel | 7桁数字、郵便番号検索で住所候補を取得 |
| 都道府県 | `jitakuPrefectureId` | `jitakuPrefectureId` | select | 47都道府県 |
| 市区町村 | `jitakuMunicipalityCode` | `jitakuMunicipalityCode` | select | 都道府県選択後に動的ロード |
| 丁目番地等 | `jitakuAddress1` | `jitakuAddress1` | text | ※都道府県市区町村と合計28文字以内 |
| 建物名・号室 | `jitakuAddress2` | `jitakuAddress2` | text | ※28文字以内 |
| 電話番号1 | `jitakuTelNumber1` | `jitakuTelNumber1` | tel | 市外局番 |
| 電話番号2 | `jitakuTelNumber2` | `jitakuTelNumber2` | tel | 局番 |
| 電話番号3 | `jitakuTelNumber3` | `jitakuTelNumber3` | tel | 加入者番号 |

### 事業所等

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 郵便番号 | `jigyosyoZip` | `jigyosyoZip` | tel | |
| 都道府県 | `jigyosyoPrefectureId` | `jigyosyoPrefectureId` | select | |
| 市区町村 | `jigyosyoMunicipalityCode` | `jigyosyoMunicipalityCode` | select | |
| 丁目番地等 | `jigyosyoAddress1` | `jigyosyoAddress1` | text | |
| 建物名・号室 | `jigyosyoAddress2` | `jigyosyoAddress2` | text | |
| 電話番号1 | `jigyosyoTelNumber1` | `jigyosyoTelNumber1` | tel | |
| 電話番号2 | `jigyosyoTelNumber2` | `jigyosyoTelNumber2` | tel | |
| 電話番号3 | `jigyosyoTelNumber3` | `jigyosyoTelNumber3` | tel | |
| 「住所と同じ」ボタン | — | — | button | 住所をコピー（納税地=事業所等選択時のみ有効） |

### 提出する税務署等

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 都道府県 | `zeimusyoPrefectureId` | `zeimusyoPrefecture` | select | |
| 税務署名 | `zeimusyo` | `zeimusyo` | select | 都道府県選択後に動的ロード |
| 整理番号 | `seiriNumber` | `seiriNumber` | tel | 数字8桁 |

### 提出年月日

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 元号 | `teisyutuEra` | `gengo0` | select | 令和 |
| 年 | `teisyutuYear` | `teisyutuYear` | select | |
| 月 | `teisyutuMonth` | `teisyutuMonth` | select | |
| 日 | `teisyutuDay` | `teisyutuDay` | select | |

### 氏名等

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 氏名（漢字）姓 | `nameKanjiSei` | `nameKanjiSei` | text | ※10文字以内 |
| 氏名（漢字）名 | `nameKanjiMei` | `nameKanjiMei` | text | ※10文字以内 |
| 氏名（カナ）セイ | `nameKanaSei` | `nameKanaSei` | text | ※11文字以内 |
| 氏名（カナ）メイ | `nameKanaMei` | `nameKanaMei` | text | ※11文字以内 |
| 業種名又は職業 | `gyosyuSyokugyoMei` | `gyosyuSyokugyoMei` | text | ※11文字以内 |
| 屋号 | `yago` | `yago` | text | ※30文字以内 |
| 加入団体名 | `kanyuDantaimei` | `kanyuDantaimei` | text | ※15文字以内 |

## ボタン

| ボタン名 | 遷移先 |
|---|---|
| 前に戻る | 所得金額の確認 |
| 次へ進む | 印刷画面 |
| ここまでの入力内容を保存する | .data ファイルダウンロード |
| この画面の入力内容をクリア | 入力値クリア |

## 注意事項
- 郵便番号入力で住所自動入力される
- 市区町村セレクトは都道府県選択後にAjaxで動的ロードされる
- 税務署名セレクトも都道府県選択後に動的ロード
- プレースホルダーにサンプル値が入っている（例: 国税太郎、コクゼイタロウ）

## スクリーンショット
- `21-kessan-address-entry.png`
