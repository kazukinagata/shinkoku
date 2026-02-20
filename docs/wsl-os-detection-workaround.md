# WSL/Linux 環境での確定申告書等作成コーナー OS 検出回避

## 問題

確定申告書等作成コーナー（https://www.keisan.nta.go.jp/）は、マイナンバーカード連携（QR コード認証）時に OS/ブラウザの環境チェックを行い、Linux 環境では QR コード認証画面への遷移をブロックする。

### 症状

- CC-AA-024（e-Tax を行う前の確認）から CC-AA-440（QR コード認証）への遷移がブロックされる
- 内部変数 `isTransition=false` が設定され、画面遷移が発生しない

### 原因

OS 検出は **2層** で行われる:

#### 層 1: クライアントサイド検出（navigator プロパティ）

サイト側の JavaScript 関数 `termnalInfomationCheckOS_myNumberLinkage()` が以下を検査する:

| 検査対象 | 判定方法 | 合格条件 |
|---------|---------|---------|
| `navigator.platform` | 文字列前方一致 | `Win32`, `MacIntel`, `iPhone`, `iPad`, `Linux armv` 等 |
| `navigator.userAgent` | 部分文字列検索 | `Windows`, `Macintosh`, `iPhone`, `iPad`, `Android` を含む |

WSL 上の Chrome/Chromium は `navigator.platform = 'Linux x86_64'` を返すため、非対応 OS として弾かれる。

#### 層 2: サーバーサイド OS ベイク（HTTP ヘッダ）

サーバーが HTTP リクエストの `User-Agent` / `sec-ch-ua-platform` ヘッダから OS を判定し、レスポンス内の `getClientOS()` 関数に `const os = "Linux"` のようにハードコードする（サーバーサイドレンダリング）。

- `addInitScript` による navigator プロパティ偽装ではこのベイク値は変わらない（`setExtraHTTPHeaders` では Chromium のネイティブ UA ヘッダを完全に上書きできないため）
- `getClientOS()` は複数箇所で呼ばれる:
  - CC-AA-010: `doSubmitCSW0100()` → `getClientOSVersionAsync()` → `getClientOS()` → `termnalInfomationCheckOS_myNumberLinkage()` で遷移判定
  - CC-AA-440: `displayQrcode()` → `getClientOS()` で `oStUseType` を決定（Win=`'3'`, Mac=`'4'`）。Linux だと `undefined` になり QR コードが描画されない

## 影響範囲

| 環境 | 影響 | 理由 |
|-----|------|------|
| Windows / macOS のネイティブ Chrome | なし | OS 検出を正常に通過 |
| Claude in Chrome（Windows / macOS） | なし | ネイティブ Chrome 上で動作 |
| WSL + Playwright（headed） | **ブロックされる** | Linux として検出 |
| WSL + Playwright（headless） | **使用不可** | QR コード認証に物理操作が必要 |
| Linux ネイティブ + Playwright | **ブロックされる** | Linux として検出 |

## 回避策

### 推奨: `etax-stealth.js` + `@playwright/mcp --init-script`

`skills/e-tax/scripts/etax-stealth.js` を `@playwright/mcp` の `--init-script` オプションで読み込むことで、ページ読み込み前に navigator プロパティを偽装する。

#### 偽装内容

**層 1: navigator プロパティ偽装**（`addInitScript` で実行、ページ読み込み前）

| プロパティ | 偽装値 | 目的 |
|-----------|--------|------|
| `navigator.platform` | `'Win32'` | OS 検出の回避 |
| `navigator.userAgent` | Windows Chrome UA | OS 検出の回避 |
| `navigator.userAgentData` | Windows Chrome Client Hints | Chrome 90+ の補助検出回避 |
| `navigator.webdriver` | `false` | Playwright 自動操作検出の回避 |
| Playwright グローバル変数 | 削除 | `__playwright__binding__` 等の検出回避 |
| `chrome.runtime` | スタブ化 | HeadlessChrome 判定の回避 |
| `navigator.plugins` | Chrome 標準値 | Headless 検出の回避 |
| `navigator.languages` | `['ja', 'en-US', 'en']` | 日本語環境の偽装 |

**層 2: サーバーベイク関数のパッチ**（`DOMContentLoaded` で実行、ページスクリプト後）

| パッチ対象 | 偽装値 | 目的 |
|-----------|--------|------|
| `getClientOS()` | `'Windows'` | サーバーベイク値の上書き |
| `getClientOSVersionAsync()` | `'Windows 11'` | OS バージョン判定の回避 |
| `isRecommendedOsAsEtaxAsync()` | `true` | 推奨 OS 判定の回避 |
| `isRecommendedBrowserAsEtaxAsync()` | `'OK'` | 推奨ブラウザ判定の回避 |

#### 設定方法

コマンドラインから起動する場合:

```bash
npx @playwright/mcp@latest \
  --init-script skills/e-tax/scripts/etax-stealth.js \
  --headed
```

`.mcp.json` で設定する場合:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--init-script",
        "skills/e-tax/scripts/etax-stealth.js",
        "--headed"
      ]
    }
  }
}
```

### 代替案 1: 検出関数の直接オーバーライド（非推奨）

ページ読み込み後に検出関数を上書きする方法。関数名がサイト更新で変更されると機能しなくなるため非推奨。

```javascript
window.termnalInfomationCheckOS_myNumberLinkage = function() {
  return true;
};
```

### 代替案 2: Windows 側の Chrome を WSL から起動（実験的）

WSL から Windows 側の Chrome バイナリを `--executable-path` で指定して起動する。OS 検出が Windows として通過するため偽装不要だが、Playwright が Windows バイナリを正しく制御できるかは環境依存。

```bash
npx @playwright/mcp@latest \
  --executable-path "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headed
```

## headed モードの必要性

確定申告書等作成コーナーの QR コード認証（CC-AA-440）では、ユーザーがスマートフォンで画面上の QR コードを読み取り、マイナンバーカードで物理的に認証する必要がある。このため headless モードでは認証を完了できず、**headed モードが必須**となる。

WSL 環境で headed モードを使用するには、以下のいずれかが必要:

- **WSLg**（Windows 11 標準）— 追加設定なしで GUI アプリを表示可能
- **X Server**（VcXsrv, X410 等）— `DISPLAY` 環境変数の設定が必要

## 書面提出ルートでの調査

OS 検出を回避できない場合でも、**書面提出ルート**（認証不要）を選択することで入力画面のフォーム構造を調査できる。フォーム構造（セレクタ・フィールド名）は e-Tax ルートと書面提出ルートで共通。

```
CC-AA-010 で「マイナンバーカードをお持ちですか」→「いいえ」
→ 書面提出を選択 → 認証なしで入力画面に到達
```

## 検証ステータス

| 項目 | ステータス | 備考 |
|-----|-----------|------|
| `navigator.platform` 偽装 | **確認済み** | `'Win32'` に偽装成功 |
| `navigator.userAgent` 偽装 | **確認済み** | Windows Chrome UA に偽装成功 |
| `navigator.webdriver` 偽装 | **確認済み** | `false` に偽装成功 |
| サーバーベイク関数パッチ | **確認済み** | `getClientOS()` 等のパッチで遷移・QR 描画が成功 |
| OS 検出通過（CC-AA-024 → CC-AA-440） | **確認済み** | 関数パッチにより遷移成功 |
| QR コード表示（CC-AA-440） | **確認済み** | canvas 要素で正常描画 |
| QR 認証完了 → 入力画面遷移 | 未検証 | マイナンバーカード認証が必要 |
| 書面提出ルートでのフォーム共通性 | 確認済み | Phase 2 調査で全入力画面のセレクタを取得 |
| 検出関数の直接オーバーライド | 未検証 | 非推奨のため優先度低 |
| Windows Chrome の WSL からの起動 | 未検証 | 環境依存のため優先度低 |

## TODO

- [x] `etax-stealth.js` 適用状態で e-Tax サイトにアクセスし、`navigator.platform` が `'Win32'` に偽装されているか確認
- [x] CC-AA-010 → CC-AE-090 → CC-AA-024 → CC-AA-440 の遷移が成功するか確認
- [x] 検証結果に基づき、検証ステータスを更新
- [ ] QR コード認証完了後、入力画面に正常遷移するか確認
- [ ] `DOMContentLoaded` パッチの自動適用がページ遷移ごとに機能するか確認
