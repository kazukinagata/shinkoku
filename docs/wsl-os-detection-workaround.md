# WSL 環境での確定申告書等作成コーナー OS 検出ブロック問題

## 問題

確定申告書等作成コーナー（https://www.keisan.nta.go.jp/）は、マイナンバーカード連携時に
OS/ブラウザの環境チェックを行い、Linux 環境ではQRコード認証画面への遷移をブロックする。

### 症状

- QRコード認証画面（CC-AA-440）に到達しても QR コードが表示されない
- `isTransition=false` が設定され、画面遷移が完全にブロックされる

### 原因

サイト側の JavaScript 関数 `termnalInfomationCheckOS_myNumberLinkage()` が
`navigator.platform` や `navigator.userAgent` を検査し、
Windows / macOS / iOS / Android 以外の OS を非対応として弾いている。

WSL 上の Chrome は Linux として検出されるため、対象外と判定される。

## 影響範囲

- **Playwright での調査時のみ発生** — WSL 上の Chrome で確定申告書等作成コーナーにアクセスした場合
- **本番運用には影響なし** — Claude in Chrome は Windows/macOS のネイティブ Chrome 上で動作するため

## 回避策（仮説・未検証）

### 案1: User-Agent / platform 偽装（推奨）

Playwright の `addInitScript` で `navigator.platform` と `navigator.userAgent` を Windows に偽装する。

```javascript
// Playwright の run-code で実行
await page.context().addInitScript(() => {
  Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
  });
  Object.defineProperty(navigator, 'userAgent', {
    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
  });
});
```

playwright-cli での実行例:

```bash
playwright-cli run-code "async page => {
  await page.context().addInitScript(() => {
    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
    Object.defineProperty(navigator, 'userAgent', { get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36' });
  });
}"
# 偽装適用後にページをリロード
playwright-cli reload
```

注意: `addInitScript` はページ読み込み前に実行される必要があるため、goto の前に設定するか、設定後に reload する。

### 案2: 検出関数の直接オーバーライド

ページ読み込み後に検出関数を上書きする。

```javascript
// ページ読み込み後に eval で実行
window.termnalInfomationCheckOS_myNumberLinkage = function() {
  return true; // 常に対応OSと判定
};
```

案1より脆弱（関数名変更で壊れる）だが、即座に適用できる利点がある。

### 案3: Windows 側の Chrome を使う

WSL から Windows 側の Chrome を Playwright で起動する。

```bash
playwright-cli open --browser="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
```

OS 検出が素直に Windows と判定されるため、最も確実。
ただし Playwright が Windows バイナリを正しく制御できるか未検証。

## 調査時の代替アプローチ

OS 検出を回避できない場合でも、**書面提出ルート**（認証不要）を選択することで
認証後の入力画面を調査できる。フォーム構造（セレクタ・フィールド名）は
e-Tax ルートと書面提出ルートで共通。

```
CC-AA-010 で「マイナンバーカードをお持ちですか」→「いいえ」
→ 書面提出を選択 → 認証なしで入力画面に到達
```

今回の Phase 2 調査ではこの方法で全入力画面のセレクタを取得した。

## TODO

- [ ] 案1（User-Agent 偽装）の動作検証
- [ ] 案2（関数オーバーライド）の動作検証
- [ ] 偽装状態で QR コード表示 → 認証完了まで通るか確認
