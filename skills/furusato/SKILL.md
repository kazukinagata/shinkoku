---
name: furusato
description: >
  This skill manages furusato nozei (hometown tax) donations. Use when the user
  wants to register donation data, read donation receipts, check deduction limits,
  or manage their furusato nozei records. Trigger phrases: "ふるさと納税",
  "furusato", "寄附金", "寄付金", "ふるさと納税の控除", "寄附金受領証明書",
  "ワンストップ特例".
---

# ふるさと納税管理（Furusato Nozei Management）

ふるさと納税の寄附金受領証明書を読み取り、寄附データを管理し、控除額を計算するスキル。

## 設定の読み込み（最初に実行）

1. `shinkoku.config.yaml` を Read ツールで読み込む
2. ファイルが存在しない場合は `/setup` スキルの実行を案内して終了する
3. 設定値を把握する:
   - `db_path`: MCP ツールの `db_path` 引数に使用（CWD基準で絶対パスに変換）
   - `tax_year`: 対象年度
   - `furusato_receipts_dir`: 受領証明書の格納ディレクトリ（任意）

## 進捗情報の読み込み

設定の読み込み後、引継書ファイルを読み込んで前ステップの結果を把握する。

1. `.shinkoku/progress/progress-summary.md` を Read ツールで読み込む（存在する場合）
2. 以下の引継書を Read ツールで読み込む（存在する場合）:
   - `.shinkoku/progress/01-setup.md`
3. 読み込んだ情報を以降のステップで活用する（ユーザーへの再質問を避ける）
4. ファイルが存在しない場合はスキップし、ユーザーに必要情報を直接確認する

## ステップ1: 受領証明書の画像読み取り

### 1-1. ファイルの確認

`import_furusato_receipt` でファイルの存在を確認する。

### 1-2. receipt-reader サブエージェントで読み取り

**重要: 画像の読み取りは receipt-reader サブエージェントに委任する。** メインコンテキストで直接 Read ツールによる画像読み取りを行わないこと（Vision トークンでコンテキストが圧迫されるため）。

#### 単一の受領証明書の場合

**Task ツールで receipt-reader サブエージェントに画像読み取りを委任する:**
```
Task(
  subagent_type="receipt-reader",
  prompt="以下のふるさと納税受領証明書の画像を読み取り、構造化データを返してください: {ファイルパス}"
)
```

サブエージェントから返された `---FURUSATO_RECEIPT_DATA---` ブロックから以下の情報を取得する:

- **自治体名**: 寄附先の市区町村名
- **都道府県名**: 寄附先の都道府県
- **寄附金額**: 円単位の整数
- **寄附日**: YYYY-MM-DD 形式
- **受領証明書番号**: 記載があれば

#### 複数の受領証明書を一括処理する場合

1. Glob ツールで受領証明書画像の一覧を取得する（例: `furusato_receipts/*.jpg`, `furusato_receipts/*.png`）
2. `import_furusato_receipt` で各ファイルの存在を確認する
3. **全ファイルパスをまとめて receipt-reader サブエージェントに渡す:**
   ```
   Task(
     subagent_type="receipt-reader",
     prompt="以下のふるさと納税受領証明書の画像をすべて読み取り、各ファイルの構造化データを返してください:\n- {パス1}\n- {パス2}\n- ..."
   )
   ```
4. サブエージェントから返された各証明書の結果をまとめてユーザーに提示する

### 1-3. ユーザーに確認

抽出した情報を一覧表示し、正しいか確認する。修正があればユーザーの入力を反映する。

## ステップ2: 寄附データの登録

確認が完了したら `furusato_add_donation` で登録する。

```
パラメータ:
  db_path: str
  fiscal_year: int
  municipality_name: str   -- 自治体名
  amount: int              -- 寄附金額（円）
  date: str                -- 寄附日（YYYY-MM-DD）
  municipality_prefecture: str | None -- 都道府県
  receipt_number: str | None -- 受領証明書番号
  one_stop_applied: bool   -- ワンストップ特例申請済みか
```

### ワンストップ特例の確認

登録時に「ワンストップ特例を申請しましたか？」と確認する。

**重要な注意**: 副業で確定申告する場合、ワンストップ特例は**無効化**される。
確定申告時に全額を寄附金控除として申告する必要がある。

## ステップ3: 複数の証明書を繰り返し処理

「他に受領証明書はありますか？」と確認し、あればステップ1~2を繰り返す。

## ステップ4: 集計と控除上限チェック

すべての寄附データを登録したら `furusato_summary` で集計する。

表示する情報:
- 寄附先自治体数と合計金額
- 所得控除額（合計 - 2,000円）
- ワンストップ特例申請数
- 控除上限の推定（所得情報がある場合）

### 控除上限の推定

所得情報が把握できている場合は `tax_calc_furusato_limit` で上限を推定する。

上限超過の場合は警告を表示:
「寄附合計額が推定上限を超えています。超過分は自己負担となります。」

## ステップ5: 確定申告との関係

以下を説明する:
- 副業で確定申告する場合、ワンストップ特例は使えない
- 確定申告で寄附金控除（所得控除）として申告する
- 所得税からの控除 = (寄附合計 - 2,000) x 所得税率
- 住民税からの控除は別途計算される（特例分含む）

## 次のステップの案内

- `income-tax` スキルで所得税の計算に進む（寄附金控除が自動反映される）
- 他の控除（医療費控除等）がある場合は先にそちらを処理する

## 引継書の出力

サマリー提示後、以下のファイルを Write ツールで出力する。
これにより、セッションの中断や Compact が発生しても次のステップで結果を引き継げる。

### ステップ別ファイルの出力

`.shinkoku/progress/05-furusato.md` に以下の形式で出力する:

```
---
step: 5
skill: furusato
status: completed
completed_at: "{当日日付 YYYY-MM-DD}"
fiscal_year: {tax_year}
---

# ふるさと納税管理の結果

## 登録済み寄附一覧

| 自治体名 | 都道府県 | 金額 | 寄附日 | ワンストップ |
|---------|---------|------|--------|------------|
| {自治体名} | {都道府県} | {金額}円 | {日付} | {申請済み/未申請} |

## 集計

- 寄附先自治体数: {件数}
- 寄附合計額: {合計金額}円
- 控除額（合計 - 2,000円）: {控除額}円

## 控除上限との比較

- 推定控除上限: {上限額}円（所得情報がある場合）
- 上限超過: {なし/あり（超過額: {金額}円）}

## 次のステップ

/income-tax で所得税の計算に進む
```

寄附がない場合（スキップ）は status を `skipped` とし、内容は「該当なし」と記載する。

### 進捗サマリーの更新

`.shinkoku/progress/progress-summary.md` を更新する（存在しない場合は新規作成）:

- YAML frontmatter: fiscal_year、last_updated（当日日付）、current_step: furusato
- テーブル: 全ステップの状態を更新（furusato を completed または skipped に）
- 次のステップの案内を記載

### 出力後の案内

ファイルを出力したらユーザーに以下を伝える:
- 「引継書を `.shinkoku/progress/` に保存しました。セッションが中断しても次のスキルで結果を引き継げます。」
- 次のステップの案内
