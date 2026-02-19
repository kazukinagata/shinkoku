# 06 - 決算書（一般用）の入力

## URL
https://www.keisan.nta.go.jp/kessan/ac/aa0200#bsctrl

## 概要
青色申告決算書（一般用）の損益計算書入力画面。
営業等所得のP/L（損益計算書）を入力する。

## 到達方法（書面提出ルート）
CC-AA-010 → CC-AA-030 → CC-AA-090 → CC-AA-450 → /kessan/ac/r7/top → ac0300 → ac/pre/ac0300 → **ac/aa0200**

## フォーム要素

### 期間の入力

| フィールド名 | type | id / name | デフォルト値 |
|---|---|---|---|
| 開始月 | select | `sonekiKeisansyoFromMonth` | 1 |
| 開始日 | select | `from_date_day` / `sonekiKeisansyoFromDay` | 1 |
| 終了月 | select | `sonekiKeisansyoToMonth` | 12 |
| 終了日 | select | `to_date_day` / `sonekiKeisansyoToDay` | 31 |

### 金額の入力（アコーディオン展開型）

各セクションはクリックで展開し、内部に詳細入力フィールドがある。

#### 売上（収入）金額

| フィールド名 | name | 備考 |
|---|---|---|
| 売上金額合計 | `uriageKingakuGokei` | |

#### 売上原価

| フィールド名 | name | 備考 |
|---|---|---|
| 仕入金額合計 | `siireKingakuGokei` | |
| 製品製造原価 | `seihinSeizoGenka` | |
| 仕入金額/製品製造原価 | `disp_siireKingakuSeihinSeizoGenka` | 表示用 |
| 売上原価小計 | `disp_uriageGenkaSyokei` | 表示用 |
| 差引売上原価 | `disp_uriageGenkaSabikiGenka` | 表示用 |
| 差引金額 | `disp_uriageGenkaSabikiKingaku` | 表示用 |

#### 経費（アコーディオン展開 行8〜32）

##### 直接入力フィールド

| 行 | フィールド名 | name（直接入力） | 備考 |
|---|---|---|---|
| 8 | 租税公課 | `sozeiKoka` | |
| 9 | 荷造運賃 | `nidukuriUntin` | |
| 10 | 水道光熱費 | `suidoKonetuhi` | |
| 11 | 旅費交通費 | `ryohiKotuhi` | |
| 12 | 通信費 | `tusinhi` | |
| 13 | 広告宣伝費 | `kokokuSendenhi` | |
| 14 | 接待交際費 | `settaiKosaihi` | |
| 15 | 損害保険料 | `songaiHokenryo` | |
| 16 | 修繕費 | `syuzenhi` | |
| 17 | 消耗品費 | `syomohinhi` | |
| 18 | 減価償却費 | — | 「入力」ボタンで別画面遷移 |
| 19 | 福利厚生費 | `fukuriKoseihi` | |
| 20 | 給料賃金 | — | 「入力」ボタンで別画面遷移 |
| 21 | 外注工賃 | `gaichukotin` | |
| 22 | 利子割引料 | — | 「入力」ボタンで別画面遷移 |
| 23 | 地代家賃 | — | 「入力」ボタンで別画面遷移 |
| 24 | 貸倒金 | `kasidaorekin` | |
| 25 | 任意科目 + 税理士等の報酬 | `keihiNiniKingaku1` (id: `zeirishitou-no-housyu-ninnikamokumei-kingaku`) | 科目名: `keihiNiniKamoku1` |
| 26 | 任意科目 + 震災関連経費 | `keihiNiniKingaku2` (id: `shinsai-kannren-keihi-ninnikamokumei-kingaku`) | 科目名: `keihiNiniKamoku2` |
| 27 | 任意科目3 | `keihiNiniKingaku3` | 科目名: `keihiNiniKamoku3` |
| 28 | 任意科目4 | `keihiNiniKingaku4` | 科目名: `keihiNiniKamoku4` |
| 29 | 任意科目5 | `keihiNiniKingaku5` | 科目名: `keihiNiniKamoku5` |
| 30 | 任意科目6 | `keihiNiniKingaku6` | 科目名: `keihiNiniKamoku6` |
| 31 | 雑費 | `zappi` | |
| 32 | 経費合計 | `disp_keihiGokei` | 自動計算 |
| 33 | 差引金額（7-32） | `disp_keihiSabikiKingaku` | 自動計算 |

##### 集計フィールド（hidden / 表示用）

| フィールド名 | name | 備考 |
|---|---|---|
| 経費算入額合計 | `keihiSannyugakuGokei` | hidden |
| 給料賃金合計 | `kyuryoTinginTotalGokei` | hidden、「入力」ボタンで別画面 |
| 利子割引料合計 | `risiWaribikiryoGokei` | hidden、「入力」ボタンで別画面 |
| 地代家賃合計 | `tidaiYatinGokei` | hidden、「入力」ボタンで別画面 |
| 税理士等報酬科目名 | `keihiNiniKamoku1` (id: `zeirishitou-no-housyu-ninnikamokumei`) | placeholder: 任意科目名 |
| 税理士等報酬合計 | `zeirisiHosyuGokei` | hidden |
| 震災関連経費科目名 | `keihiNiniKamoku2` (id: `shinsai-kannren-keihi-ninnikamokumei`) | placeholder: 任意科目名 |
| 震災関連経費合計 | `sinsaiKanrenKeihiGokei` | hidden |
| 経費合計 | `disp_keihiGokei` | 自動計算・表示用 |
| 差引金額 | `disp_keihiSabikiKingaku` | 自動計算・表示用 |

##### 「入力」ボタン付きフィールド（別画面遷移）

以下の科目は直接入力ではなく「入力」ボタンクリックで別画面に遷移して詳細入力する:
- 行18: 減価償却費
- 行20: 給料賃金
- 行22: 利子割引料
- 行23: 地代家賃

##### 任意科目の追加

- 「追加」ボタンで任意科目を追加可能（あと3件入力可の表示あり）
- 任意科目25-30のうち、25は税理士等の報酬、26は震災関連経費が固定ラベル
- 27-30は自由入力（科目名 + 金額）

#### 繰戻額等

| フィールド名 | name（集計hidden） | name（直接入力） | 備考 |
|---|---|---|---|
| 本年貸倒繰戻し | `honnenKasidaoreKurimodosi` | — | hidden |
| 繰戻し任意科目1名 | `kurimodosiNiniKamoku1` | — | placeholder: 任意科目名 |
| 繰戻し任意科目1金額 | — | `kurimodosiNiniKingaku1` | |
| 繰戻し任意科目2名 | `kurimodosiNiniKamoku2` | — | placeholder: 任意科目名 |
| 繰戻し任意科目2金額 | — | `kurimodosiNiniKingaku2` | |
| 繰戻額等の合計 | `disp_kurimodosiGokei` | — | 自動計算・表示用 |

#### 専従者給与・繰入額等

| フィールド名 | name（集計hidden） | name（直接入力） | 備考 |
|---|---|---|---|
| 専従者給与合計 | `senjusyaKyuyoTotalGokei` | — | hidden、「入力」ボタンで別画面 |
| 貸倒繰入合計 | `kasidaoreKuriireGokei` | — | hidden |
| 繰入任意科目1名 | `kuriireNiniKamoku1` | — | placeholder: 任意科目名 |
| 繰入任意科目1金額 | — | `kuriireNiniKingaku1` | |
| 繰入任意科目2名 | `kuriireNiniKamoku2` | — | placeholder: 任意科目名 |
| 繰入任意科目2金額 | — | `kuriireNiniKingaku2` | |
| 繰入額等の合計 | `disp_kuriireGokei` | — | 自動計算・表示用 |

### 計算結果

| フィールド名 | name | 備考 |
|---|---|---|
| 青色申告特別控除前の所得金額（行43） | `disp_aoiroKojomaeSyotokuKingaku` | 自動計算 = 売上 - 売上原価 - 経費 + 繰戻額 - 専従者給与等 |

### その他

| フィールド名 | 操作 | 備考 |
|---|---|---|
| 本年中における特殊事情 | ボタン「入力」クリックでモーダル | テキスト入力 |

## ボタン

| ボタン名 | 遷移先 |
|---|---|
| 前に戻る | 青色申告決算書の種類選択 |
| 次へ進む | 貸借対照表の入力（推定） |
| ここまでの入力内容を保存する | .data ファイルダウンロード |
| この画面の入力内容をクリア | 入力値クリア |

## 計算式
青色申告特別控除前の所得金額 = 売上（収入）金額の合計 - 売上原価の合計 - 経費の合計 + 繰戻額等の合計 - 専従者給与・繰入額等の合計

## スクリーンショット
- `14-kessan-business-income-entry.png`
