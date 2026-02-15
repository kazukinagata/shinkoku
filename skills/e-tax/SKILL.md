---
name: e-tax
description: >
  This skill should be used when the user wants to generate xtx files for
  e-Tax electronic filing, submit their tax return electronically, or create
  XML data for upload to the e-Tax Web system. Trigger phrases include:
  "e-Tax提出", "xtx生成", "電子申告", "xtxファイル作成", "e-Taxで申告",
  "電子データ作成", "xtx出力", "e-Taxアップロード".
---

# e-Tax 電子申告用 xtx ファイル生成

shinkoku で計算した確定申告データから e-Tax 用の xtx ファイル（XML Tax Data）を生成し、
e-Tax Web にアップロードして電子申告するためのスキル。

## 前提条件

- `/income-tax` スキルで所得税の計算が完了していること
- `/settlement` スキルで決算書（PL/BS）の作成が完了していること
- `/consumption-tax` スキルで消費税の計算が完了していること（該当者のみ）
- `shinkoku.config.yaml` が設定済みであること

## CLI リファレンス

```bash
uv run python scripts/generate_xtx.py \
    --config <config_path>      # 必須: shinkoku.config.yaml のパス
    --output-dir <output_dir>   # 必須: xtx ファイルの出力先ディレクトリ
    --db-path <db_path>         # 任意: DB パス（省略時は config の db_path を使用）
    --type <type>               # 必須: income_tax / consumption_tax / all
```

## 設定の読み込み（最初に実行）

1. `shinkoku.config.yaml` を Read ツールで読み込む
2. ファイルが存在しない場合は `/setup` スキルの実行を案内して終了する
3. 設定値を把握し、相対パスは CWD を基準に絶対パスに変換する:
   - `db_path`: DB パス（`--db-path` CLI 引数に使用）
   - `output_dir`: xtx ファイルの出力先ディレクトリ（`--output-dir` CLI 引数に使用）

## 進捗情報の読み込み

設定の読み込み後、引継書ファイルを読み込んで前ステップの結果を把握する。

1. `.shinkoku/progress/progress-summary.md` を Read ツールで読み込む（存在する場合）
2. 以下の引継書を Read ツールで読み込む（存在する場合）:
   - `.shinkoku/progress/07-income-tax.md`
   - `.shinkoku/progress/08-consumption-tax.md`
   - `.shinkoku/progress/05-settlement.md`
3. 読み込んだ情報を以降のステップで活用する
4. ファイルが存在しない場合はスキップし、ユーザーに必要情報を直接確認する

## ステップ0: 必須データの検証

xtx 生成に必要なデータが揃っているか検証する。

### 検証項目

```
[1] 税額計算済み
    - .shinkoku/progress/07-income-tax.md が存在し、status: completed であること
    - または ledger_pl / tax_calc_income ツールで計算結果が取得可能であること

[2] プロファイル完備
    - profile_get_taxpayer ツールで以下を確認:
      - 氏名（姓・名）が登録されているか
      - マイナンバーが設定済みか（has_my_number: true）
      - 住所が登録されているか
      - 所轄税務署名が登録されているか

[3] 決算書データ
    - DB に仕訳データが存在すること
    - ledger_pl でPLが取得可能であること

[4] 消費税（該当者のみ）
    - .shinkoku/progress/08-consumption-tax.md が存在し、status: completed であること
```

不足している場合は、対応するスキルの実行を案内する:
- 税額未計算 → `/income-tax` スキル
- プロファイル未設定 → `/setup` スキル
- 決算書未作成 → `/settlement` スキル
- 消費税未計算 → `/consumption-tax` スキル

## ステップ1: 所得税 xtx の生成

以下の Bash コマンドで所得税の xtx ファイルを生成する:

```bash
uv run python scripts/generate_xtx.py \
    --config shinkoku.config.yaml \
    --db-path {db_path} \
    --output-dir {output_dir} \
    --type income_tax
```

`--db-path` は省略可能（省略時は config の `db_path` を使用）。

### 確認事項

- 出力ステータスが `Status: ok` であること
- 含まれる帳票を確認:
  - `KOA020`: 申告書B（第一表・第二表）
  - `KOA210`: 青色申告決算書（損益計算書・貸借対照表）
- Tax summary の数値が `/income-tax` スキルの計算結果と一致すること
- 警告（Warnings）がある場合はユーザーに報告する

## ステップ2: 消費税 xtx の生成（該当者のみ）

消費税の申告が必要な場合、以下のコマンドで消費税の xtx ファイルを生成する:

```bash
uv run python scripts/generate_xtx.py \
    --config shinkoku.config.yaml \
    --db-path {db_path} \
    --output-dir {output_dir} \
    --type consumption_tax
```

### 確認事項

- 出力ステータスが `Status: ok` であること
- `SHA010`: 消費税及び地方消費税申告書が含まれること
- 納付税額が `/consumption-tax` スキルの計算結果と一致すること

## ステップ3: 生成結果のレビュー

生成された xtx ファイルの内容をユーザーに報告する。

### 報告テンプレート

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
xtx ファイル生成結果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 所得税 xtx
  ファイル: {output_dir}/income_tax_r07.xtx
  含まれる帳票:
    - 申告書B 第一表
    - 申告書B 第二表
    - 青色申告決算書 損益計算書
    - 青色申告決算書 貸借対照表
  事業所得: {金額}円
  課税所得: {金額}円
  所得税額: {金額}円
  納付額/還付額: {金額}円

■ 消費税 xtx（該当者のみ）
  ファイル: {output_dir}/consumption_tax_r07.xtx
  含まれる帳票:
    - 消費税及び地方消費税申告書
  納付税額: {金額}円

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## ステップ4: e-Tax Web アップロード手順の案内

xtx ファイルの生成が完了したら、e-Tax Web でのアップロード手順を案内する。

### アップロード手順

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
e-Tax Web アップロード手順
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. e-Tax Web にアクセス
   https://login.e-tax.nta.go.jp/login/reception/loginIndividual

2. マイナンバーカードでログイン
   - ICカードリーダーまたはスマートフォンを使用
   - 初回の場合は利用者識別番号の取得が必要

3. メインメニューから「申告・申請・納税」を選択

4. 「作成済みデータの利用」を選択
   - 「作成済みデータを利用して申告書等を作成」

5. xtx ファイルをアップロード
   - 所得税: {output_dir}/income_tax_r07.xtx
   - 消費税: {output_dir}/consumption_tax_r07.xtx（該当者のみ）

6. 画面上で内容を確認
   - 帳票ごとに数値を確認する
   - 修正が必要な場合は画面上で編集可能

7. 電子署名を付与
   - マイナンバーカードで電子署名する
   - 署名用パスワード（6〜16桁の英数字）が必要

8. 送信
   - 送信完了後、受付番号を控える
   - メッセージボックスで受信通知を確認する

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 注意事項

- xtx ファイルには電子署名は含まれない（e-Tax Web 上でマイナンバーカードで署名する）
- アップロード後、e-Tax Web 上で内容を修正してから送信することも可能
- 複数の帳票（所得税・消費税）は別々にアップロード・送信する

## 引継書の出力

全ステップ完了後、以下のファイルを Write ツールで出力する。

### ステップ別ファイルの出力

`.shinkoku/progress/10-etax.md` に以下の形式で出力する:

```
---
step: 10
skill: e-tax
status: completed
completed_at: "{当日日付 YYYY-MM-DD}"
fiscal_year: {tax_year}
---

# e-Tax 電子申告の結果

## 生成した xtx ファイル

- 所得税: {output_dir}/income_tax_r07.xtx
- 消費税: {output_dir}/consumption_tax_r07.xtx（該当者のみ）

## 含まれる帳票

- 申告書B 第一表・第二表
- 青色申告決算書（損益計算書・貸借対照表）
- 消費税及び地方消費税申告書（該当者のみ）

## 税額サマリー

- 事業所得: {金額}円
- 課税所得: {金額}円
- 所得税額: {金額}円
- 消費税納付額: {金額}円（該当者のみ）

## 次のステップ

e-Tax Web にアクセスして xtx ファイルをアップロードし、電子署名・送信する。
```

### 進捗サマリーの更新

`.shinkoku/progress/progress-summary.md` を更新する（存在しない場合は新規作成）:

- YAML frontmatter: fiscal_year、last_updated（当日日付）、current_step: e-tax
- テーブル: 全ステップの状態を更新（e-tax を completed に）

### 出力後の案内

ファイルを出力したらユーザーに以下を伝える:
- 「引継書を `.shinkoku/progress/` に保存しました。」
- e-Tax Web でのアップロード手順を再度案内する
- 提出期限（所得税: 3月16日、消費税: 3月31日）を案内する
