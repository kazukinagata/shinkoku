# コントリビューションガイド

shinkoku への貢献に興味を持っていただきありがとうございます。

## バグ報告

[Issue](https://github.com/kazukinagata/shinkoku/issues/new?template=bug_report.yml) から報告してください。

- 再現手順を具体的に記載してください
- 実行環境（OS, Python バージョン, エージェント名）を明記してください
- エラーメッセージやログがあれば貼り付けてください

## 機能提案

[Issue](https://github.com/kazukinagata/shinkoku/issues/new?template=feature_request.yml) から提案してください。

大きな変更の場合は、先に Issue で方針を議論してから実装に入ることを推奨します。

## Pull Request

### 基本方針

- `main` ブランチに対して作成してください
- CI（lint + テスト + 型チェック）が通ることを確認してください
- 1つの PR には 1つの論理的な変更をまとめてください

### 開発環境のセットアップ

```bash
git clone https://github.com/kazukinagata/shinkoku.git
cd shinkoku
uv sync --all-extras
uv run pre-commit install
```

### テスト・Lint の実行

```bash
# テスト
uv run pytest tests/unit/ -v
uv run pytest tests/scripts/ -v
uv run pytest tests/integration/ -v

# Lint + フォーマット
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# 型チェック
uv run mypy src/shinkoku/ --ignore-missing-imports
```

### コーディング規約

- **金額は `int`（円単位の整数）** — `float` は使わない
- **型ヒント必須** — 全関数に型ヒントを付与。`from __future__ import annotations` をファイル先頭に記述
- **Ruff** — `line-length: 100`, `target-version: py311`
- **ドメインロジックのコメントは日本語** — 税法の計算根拠など
- **自明なコードにはコメントを付けない**

### コミットメッセージ

```
[type]: [description]
```

- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `ci`: CI/CD

### Pydantic モデル命名規則

| サフィックス | 用途 | 例 |
|------------|------|-----|
| `*Input` | ツールへの入力 | `IncomeTaxInput` |
| `*Result` | ツールからの出力 | `IncomeTaxResult` |
| `*Params` | 検索条件 | `JournalSearchParams` |
| `*Record` | DB レコード | `JournalRecord` |

## 対応範囲

コントリビューションは以下の範囲を対象としています。

- 既存の対応ペルソナ（個人事業主・会社員＋副業・給与所得のみ等）の機能改善
- 税制改正への対応
- テストの追加・改善
- ドキュメントの改善
- バグ修正

「非対応」に記載されている機能（株式分離課税、不動産所得等）を新たに対応する場合は、先に Issue で議論してください。

## 日本語でOK

Issue・PR・コミットメッセージ、すべて日本語で構いません。
