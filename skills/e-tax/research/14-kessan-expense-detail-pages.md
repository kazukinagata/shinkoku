# 14 - 決算書（一般用）経費 詳細入力ページ

## 概要
決算書（一般用）P/L入力ページ（aa0200）から「入力」ボタンで遷移する詳細入力サブページ。
P/Lの経費行のうち、以下の7項目に「入力」ボタン（`<input type="button">` 要素）がある。

### 入力ボタン一覧

| 行 | 科目 | ボタンID | 遷移先URL | 遷移先コード | 状態 |
|----|------|----------|-----------|-------------|------|
| - | 製造原価 | `input_seizogenka` | 未調査 | - | 有効 |
| 18 | 減価償却費 | `input_genkasyokyaku` | /kessan/ac/init/aa0203 | aa0203 | 有効 |
| 20 | 給料賃金 | `input_kyuryotingin` | /kessan/ac/aa0205 | aa0205 | 有効 |
| 22 | 利子割引料 | `input_rishiwaribiki` | /kessan/ac/aa0206 | aa0206 | 有効 |
| 23 | 地代家賃 | `input_tidaiyatin` | /kessan/ac/aa0207 | aa0207 | 有効 |
| 25 | 税理士等の報酬 | `input_kashidaore_kurimodoshi`? | 未確認 | - | disabled（任意科目入力後に有効化） |
| 26 | 震災関連経費 | - | 未確認 | - | disabled |
| - | 繰戻額等 | `input_kashidaore_kurimodoshi` | 未確認 | - | 有効 |
| - | 専従者給与 | `input_senjusyakyuyo` | 未確認 | - | 有効 |

### onclick パターン
```javascript
AA0200_doChangeSubmit(this.form, 'aa0203');  // 減価償却費
AA0200_doChangeSubmit(this.form, 'aa0205');  // 給料賃金
AA0200_doChangeSubmit(this.form, 'aa0206');  // 利子割引料
AA0200_doChangeSubmit(this.form, 'aa0207');  // 地代家賃
```

---

## 1. 減価償却費の入力 (/kessan/ac/init/aa0203)

### 概要
減価償却資産を個別に登録する2段構成のページ。
- **一覧ページ** (`/kessan/ac/init/aa0203`): 資産リストと合計表示
- **入力ページ** (`/kessan/ac/input/aa0203`): 個別資産の詳細入力

### 一覧ページ
- Q&A: 「減価償却費の計算はお済みですか？」→ はい/いいえ radio
- 「入力する」ボタンで個別資産入力ページへ
- 最大220件まで入力可
- 本年の減価償却費合計額を自動計算
- 特別償却（被災代替資産等、被災者向け優良賃貸住宅）は「震災関連経費」から入力

### 入力ページ フォーム要素

| フィールド名 | name | id | type | 備考 |
|---|---|---|---|---|
| 減価償却資産の種類等 | `sisanSyurui` | `sisanSyurui` | select | 建物定額法/定率法、無形固定資産、一括償却、中小特例、繰延資産、生物、果樹 |
| 減価償却資産の細目 | `sisanSaimoku` | `sisanData1` | select | 種類選択後に動的切替: 建物附属設備、構築物、機械装置、船舶、航空機、車両運搬具、工具器具備品 |
| 減価償却資産の名称 | `sisanMeisyo` | `sisanData2` | text | 16文字以内 |
| 任意償却の有無 | `niniSyokyakuUmu` | `niniSyokyakuUmu` | checkbox | |
| 面積又は数量 | `mensekiSuryo` | `sisanData3` | text | 12文字以内、面積は「平米」で入力 |
| 取得年月（元号） | `syutokuDateEra` | `gengo` | select | 明治/大正/昭和/平成/令和/西暦 |
| 取得年月（年） | `syutokuDateYear` | `sisanData4` | select | |
| 取得年月（月） | `syutokuDateMonth` | `sisanData5` | select | |
| 償却率変更の有無 | `syokyakurituHenkoUmu` | `syokyakurituHenkoUmu` | checkbox | |
| 償却率変更事業年度 | `syokyakurituHenkoJigyoNendo` | `syokyakurituHenkoJigyoNendoSelect` | select | |
| 取得価額（円） | `syutokuKagaku` | `sisanData6` | tel | |
| 前年末未償却残高（円） | `zennenmatuMisyokyakuZandaka` | `sisanData7` | tel | R6以前取得の場合のみ |
| 償却基礎額 | `syokyakuKisoGamen` | `sisanData8` | tel | |
| 耐用年数 | `taiyoNensu` | `sisanData9` | tel | 3桁以内 |
| 改定取得価額（円） | `kaiteiSyutokuKagaku` | `kaiteiSyutokuKagaku` | tel | |
| 本年中の償却期間 | `honnenchuSyokyakuKikan` | `sisanData10` | select | 0〜12月 |
| 除却・譲渡・廃棄 | `jokyaku` | `jokyaku` | checkbox | |
| 本年中の普通償却費 | `honnenchuFutuSyokyakuhi` | `honnenchuFutuSyokyakuhi` | tel | |
| 事業専用（貸付）割合 | `jigyoSenyoWariai` | `sisanData11` | text | 小数点第2位まで (%) |
| 摘要 | `tekiyo` | `sisanData12` | text | 8文字以内 |

### ボタン
| ボタン名 | 動作 |
|----------|------|
| 戻る | 一覧に戻る（confirm KS-W90011） |
| 続けてもう1件入力 | 入力保存して次の資産入力 |
| 入力内容の確認 | 入力内容を確認 |

---

## 2. 給料賃金の入力 (/kessan/ac/aa0205)

### 概要
従業員ごとの給料賃金・賞与・源泉徴収税額を入力するページ。
初期4人分の入力欄があり、「もう1人入力する」で追加可能。

### フォーム要素

#### 個別従業員（配列インデックス0-3、追加可能）

| フィールド名 | name パターン | type | 備考 |
|---|---|---|---|
| 氏名 | `kyuryoTinginDetailDataList[N].simei` | text | 12文字以内 |
| 年齢 | `kyuryoTinginDetailDataList[N].age` | tel | |
| 従事月数 | `kyuryoTinginDetailDataList[N].jujiTukisu` | select | 1-12月 |
| 給料賃金（円） | `kyuryoTinginDetailDataList[N].kyuryoTingin` | tel | |
| 賞与（円） | `kyuryoTinginDetailDataList[N].syoyo` | tel | |
| 支給額 | (自動計算: 給料賃金+賞与) | — | SPAN表示 |
| 源泉徴収税額（円） | `kyuryoTinginDetailDataList[N].gensenChosyuZeigaku` | tel | |

#### 合計欄（hidden）
- `kyuryoTinginDetailDataList[N].total` — 支給額自動計算値

#### その他（4人超の場合の合計入力）

| フィールド名 | name | type | 備考 |
|---|---|---|---|
| その他人数 | `otherNinzu` | tel | |
| その他従事月数 | `otherJujiTukisu` | tel | |
| その他給料賃金 | `otherKyuryoTingin` | tel | |
| その他賞与 | `otherSyoyo` | tel | |
| その他源泉徴収税額 | `otherGensenChosyuZeigaku` | tel | |

### 注意事項
- 源泉徴収税額は年末調整後の金額を入力
- 年の中途退職者は本年中に徴収した源泉徴収税額を入力

---

## 3. 利子割引料の入力 (/kessan/ac/aa0206)

### 概要
金融機関以外と金融機関への利子割引料の支払を入力するページ。

### フォーム要素

#### 金融機関以外への支払（最大2件、3件以上は合算）

| フィールド名 | name | type | 備考 |
|---|---|---|---|
| 支払先の住所 | `siharaisakiJusyo1`/`siharaisakiJusyo2` | text | 28文字以内 |
| 支払先の氏名 | `siharaisakiSimei1`/`siharaisakiSimei2` | text | 28文字以内 |
| 期末借入金等の金額（円） | `kimatuKariirekin1`/`kimatuKariirekin2` | tel | |
| 本年中の利子割引料（円） | `risiWaribikiryo1`/`risiWaribikiryo2` | tel | |
| 必要経費算入額（円） | `keihiSannyugaku1`/`keihiSannyugaku2` | tel | |

#### 金融機関への支払

| フィールド名 | name | type | 備考 |
|---|---|---|---|
| 金融機関分の利子割引料（必要経費算入額）の合計（円） | `kinyukikanRisiWaribikiryo` | tel | |

### 注意事項
- 3件以上の場合は2件目に「○○ほか」と記入し、金額は2件目以降の合計
- 本年中に支払うことの確定した金額を入力

---

## 4. 地代家賃の入力 (/kessan/ac/aa0207)

### 概要
店舗・工場・倉庫等の地代家賃の支払を入力するページ。

### フォーム要素

#### 支払先情報（最大2件、3件以上は合算）

| フィールド名 | name | type | 備考 |
|---|---|---|---|
| 支払先の住所 | `siharaisakiJusyo1`/`siharaisakiJusyo2` | text | 28文字以内 |
| 支払先の氏名 | `siharaisakiSimei1`/`siharaisakiSimei2` | text | 28文字以内 |
| 賃借物件 | `tinsyakuBukken1`/`tinsyakuBukken2` | text | 14文字以内 |
| 権利金（円） | `kenrikin1`/`kenrikin2` | tel | |
| 更新料（円） | `kosinryo1`/`kosinryo2` | tel | |
| 賃借料（円） | `tinsyakuryo1`/`tinsyakuryo2` | tel | |
| 必要経費算入額（円） | `keihiSannyugaku1`/`keihiSannyugaku2` | tel | |

### 注意事項
- 3件以上の場合は2件目に「○○ほか」と記入し、金額は2件目以降の合計
- 「地代家賃の合計」は自動計算表示

---

## 共通事項

### 戻る操作
全ての詳細ページから「前に戻る」を押すと、confirm ダイアログ KS-W90011 が表示される：
「この画面で入力したデータが反映されませんが、よろしいですか？」

### ボタン構成
- 前に戻る → P/L入力画面に戻る（confirm付き）
- 次へ進む → P/L入力画面に戻る（入力データ反映）

## スクリーンショット
- `24-kessan-depreciation-detail.png` — 減価償却費一覧ページ
- `25-kessan-depreciation-asset-entry.png` — 減価償却資産入力フォーム
- `26-kessan-wages-detail.png` — 給料賃金入力ページ
- `27-kessan-interest-detail.png` — 利子割引料入力ページ
- `28-kessan-rent-detail.png` — 地代家賃入力ページ
