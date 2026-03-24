---
name: tax-legal-context
description: "Provides the standard legal disclaimer text, cites Tax Accountant Act (税理士法) scope limitations, and clarifies the boundary between tax information and regulated tax advisory. Adds enhanced warnings for gray-zone scenarios such as specific tax optimization schemes or inheritance tax calculations. Use when generating tax-related responses that require a disclaimer or legal context. This skill is not user-invocable — Claude loads it automatically."
user-invocable: false
---

# 税務法的コンテキスト（Tax Legal Context）

このスキルは shinkoku の税務関連回答における法的・免責コンテキストを提供する。

## 免責事項の提示

免責事項が必要な回答を行う際は、`references/disclaimer.md` を読み込んで以下を実行する:

1. `references/disclaimer.md` の「標準免責文」を回答末尾に付記する
2. 免責を強調すべきケース（グレーゾーン・高額案件等）に該当する場合は追加注意喚起を行う
3. 税理士法第52条の観点から、個別具体的な税務代理行為に該当しないよう留意する

## 参照ファイル

| ファイル | 内容 |
|---------|------|
| `references/disclaimer.md` | 標準免責文・税理士法との関係・ツール制限事項・情報の正確性 |
