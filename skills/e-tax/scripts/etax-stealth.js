// etax-stealth.js
// @playwright/mcp の --init-script オプションで読み込むステルススクリプト。
// ページ読み込み前に実行され、確定申告書等作成コーナーの OS 検出・bot 検出を回避する。
//
// 使用方法:
//   npx @playwright/mcp@latest --init-script skills/e-tax/scripts/etax-stealth.js
//
// 回避対象:
//   1. termnalInfomationCheckOS_myNumberLinkage() による OS 検出
//      - navigator.platform / navigator.userAgent で Linux を非対応 OS として弾く
//   2. Playwright の自動操作検出（navigator.webdriver, グローバル変数）
//   3. HeadlessChrome 判定（chrome.runtime の有無）

(() => {
  "use strict";

  // ── 1. navigator.platform の偽装 ──
  // 確定申告書等作成コーナーの termnalInfomationCheckOS_myNumberLinkage() は
  // navigator.platform を検査し、'Win32' / 'MacIntel' 等でなければ isTransition=false にする
  Object.defineProperty(navigator, "platform", {
    get: () => "Win32",
    configurable: true,
  });

  // ── 2. navigator.userAgent の偽装 ──
  // Windows 11 + Chrome 131 の UA 文字列に偽装
  const WINDOWS_CHROME_UA =
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

  Object.defineProperty(navigator, "userAgent", {
    get: () => WINDOWS_CHROME_UA,
    configurable: true,
  });

  // ── 3. navigator.userAgentData の偽装（Chrome 90+ Client Hints） ──
  // 一部のサイトは userAgentData.platform も検査する
  if (navigator.userAgentData) {
    Object.defineProperty(navigator, "userAgentData", {
      get: () => ({
        brands: [
          { brand: "Google Chrome", version: "131" },
          { brand: "Chromium", version: "131" },
          { brand: "Not_A Brand", version: "24" },
        ],
        mobile: false,
        platform: "Windows",
        getHighEntropyValues: () =>
          Promise.resolve({
            architecture: "x86",
            bitness: "64",
            brands: [
              { brand: "Google Chrome", version: "131.0.0.0" },
              { brand: "Chromium", version: "131.0.0.0" },
              { brand: "Not_A Brand", version: "24.0.0.0" },
            ],
            fullVersionList: [
              { brand: "Google Chrome", version: "131.0.0.0" },
              { brand: "Chromium", version: "131.0.0.0" },
              { brand: "Not_A Brand", version: "24.0.0.0" },
            ],
            mobile: false,
            model: "",
            platform: "Windows",
            platformVersion: "15.0.0",
            uaFullVersion: "131.0.0.0",
          }),
        toJSON: () => ({
          brands: [
            { brand: "Google Chrome", version: "131" },
            { brand: "Chromium", version: "131" },
            { brand: "Not_A Brand", version: "24" },
          ],
          mobile: false,
          platform: "Windows",
        }),
      }),
      configurable: true,
    });
  }

  // ── 4. navigator.webdriver の偽装 ──
  // Playwright は navigator.webdriver = true を設定する。
  // 確定申告書等作成コーナーが直接検査するかは不明だが、安全のため false に偽装する。
  Object.defineProperty(navigator, "webdriver", {
    get: () => false,
    configurable: true,
  });

  // ── 5. Playwright グローバル変数の削除 ──
  // Playwright が注入するグローバル変数を削除して検出を回避する
  const playwrightGlobals = [
    "__playwright",
    "__pw_manual",
    "__PW_inspect",
    "__playwright__binding__",
  ];
  for (const key of playwrightGlobals) {
    try {
      delete window[key];
    } catch {
      // configurable でない場合は無視
    }
  }

  // ── 6. chrome.runtime のスタブ化 ──
  // HeadlessChrome では chrome.runtime が存在しない場合がある。
  // 通常の Chrome 拡張環境をシミュレートする。
  if (!window.chrome) {
    window.chrome = {};
  }
  if (!window.chrome.runtime) {
    window.chrome.runtime = {
      connect: () => {},
      sendMessage: () => {},
      id: undefined,
    };
  }

  // ── 7. navigator.plugins の偽装 ──
  // Headless Chrome は plugins が空になる場合がある
  Object.defineProperty(navigator, "plugins", {
    get: () => {
      const plugins = [
        { name: "PDF Viewer", filename: "internal-pdf-viewer" },
        {
          name: "Chrome PDF Viewer",
          filename: "internal-pdf-viewer",
        },
        {
          name: "Chromium PDF Viewer",
          filename: "internal-pdf-viewer",
        },
        {
          name: "Microsoft Edge PDF Viewer",
          filename: "internal-pdf-viewer",
        },
        {
          name: "WebKit built-in PDF",
          filename: "internal-pdf-viewer",
        },
      ];
      plugins.length = plugins.length;
      return plugins;
    },
    configurable: true,
  });

  // ── 8. navigator.languages の偽装 ──
  // 日本語環境の Chrome に合わせる
  Object.defineProperty(navigator, "languages", {
    get: () => ["ja", "en-US", "en"],
    configurable: true,
  });

  // ── 9. サーバーベイク関数のパッチ ──
  // 確定申告書等作成コーナーのサーバーは HTTP リクエストの User-Agent / sec-ch-ua-platform
  // ヘッダから OS を判定し、レスポンス内の getClientOS() 関数に
  // const os = "Linux" のようにハードコードする（サーバーサイドレンダリング）。
  // addInitScript による navigator プロパティ偽装ではこのベイク値は変わらないため、
  // ページスクリプト読み込み後に関数そのものを上書きする。
  //
  // パッチ対象:
  //   getClientOS()               — OS 文字列を返す（"Linux" → "Windows" に変更）
  //   getClientOSVersionAsync()   — OS バージョンを返す（→ "Windows 11"）
  //   isRecommendedOsAsEtaxAsync() — 推奨 OS 判定（→ true）
  //   isRecommendedBrowserAsEtaxAsync() — 推奨ブラウザ判定（→ "OK"）
  //
  // 影響箇所:
  //   CC-AA-010: doSubmitCSW0100() → getClientOSVersionAsync() → termnalInfomationCheckOS_myNumberLinkage()
  //   CC-AA-440: displayQrcode() → getClientOS() で oStUseType を決定（Win='3', Mac='4'）

  const _patchServerFunctions = () => {
    if (typeof window.getClientOS === "function") {
      window.getClientOS = function () {
        return "Windows";
      };
    }
    if (typeof window.getClientOSVersionAsync === "function") {
      window.getClientOSVersionAsync = async function () {
        return "Windows 11";
      };
    }
    if (typeof window.isRecommendedOsAsEtaxAsync === "function") {
      window.isRecommendedOsAsEtaxAsync = async function () {
        return true;
      };
    }
    if (typeof window.isRecommendedBrowserAsEtaxAsync === "function") {
      window.isRecommendedBrowserAsEtaxAsync = async function () {
        return "OK";
      };
    }
  };

  // DOMContentLoaded: インラインスクリプトが実行された後、ユーザー操作の前
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _patchServerFunctions);
  } else {
    // すでに DOM 構築済みの場合（reload 等）
    _patchServerFunctions();
  }

  // load イベントでの再パッチ（安全策）
  window.addEventListener("load", _patchServerFunctions);
})();
