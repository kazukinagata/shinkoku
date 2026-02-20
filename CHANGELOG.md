# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2025-02-20

### Added
- 複式簿記の帳簿管理（仕訳 CRUD・残高試算表・損益計算書・貸借対照表）
- 所得税計算（所得控除・税額控除・復興特別所得税・住宅ローン控除）
- 消費税計算（2割特例・簡易課税・本則課税）
- ふるさと納税 CRUD・控除計算・限度額推定
- データ取込（CSV・レシート・請求書・源泉徴収票・控除証明書）
- OCR 画像読取スキル（レシート・源泉徴収票・請求書・控除証明書・支払調書）
- e-Tax 電子申告スキル（Claude in Chrome による確定申告書等作成コーナー入力代行）
- Playwright フォールバック（WSL / Linux 環境向け）
- Agent Skills（SKILL.md オープン標準）による 35+ エージェント対応
- Claude Code Plugin マニフェスト
- CI パイプライン（Ruff lint + mypy + pytest + coverage）
