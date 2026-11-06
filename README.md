# 陪葬! 華西街

一份給自己與朋友的每日市場筆記。iOS毛玻璃介面、手機底部詳情視窗、固定公式運算，無LLM、無登入。

## 目前實際可用範圍

- 台灣加權、2330、0050、00631L、00685L最新已收盤行情：TWSE官方OpenAPI。
- RSI14、台式KD9、SMA50/200與交叉、MACD、布林、ADX/DMI、ATR與252日高點回落的計算與測試已提供。
- TWSE開放資料版首次歷史不足，因此暫不完整評分。另已實作Yahoo免費研究來源，可一次取得各標的5年調整OHLC；本機研究版9個標的已實際算出分數。
- 免費研究版已實測接上海外四個指數與VIX；CNN仍回HTTP418，顯示無資料，不冒充成功。預設研究資料只存.private/，與公開輸出分開；公開使用仍受來源條款限制。
- 可匯入已取得公開使用權的歷史資料；引擎支援分割／配息一致調整。回測工具已實作，但真實歷史未齊時拒絕產生績效。
- 分數是研究規則的支持度，尚無真實樣本外績效結論。陪葬代表買進／加碼支持；躲噴代表賣出／減碼支持。

## 本機預覽

需Node.js 24+、Python 3.11+。安裝exchange-calendars以處理各國交易日、收盤時刻與美國夏令時間；資料抓取不需API金鑰。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix web ci
.venv/bin/python -m market.pipeline
npm --prefix web run dev
```

終端機會顯示本機網址。離線重建用 `.venv/bin/python -m market.pipeline --offline`；不會產生假行情。過期快照保留價格、停用行動評分。

## GitHub Pages部署精靈

預設帳號 `allenljf`，建議專案 `huaxi-street`。不需要Cloudflare帳號、朋友名單或PAT。

```bash
./scripts/setup.sh --check
./scripts/setup.sh
```

精靈會檢查工具、透過GitHub CLI登入、選擇repo與週六更新選項。**建立公開repo、推送與發布前會顯示目標並確認。** 既有origin不同或存在未提交程式時會停止，不會強制推送或自動加入所有檔案。

主分支main推送後會更新與部署。亞洲在台灣週一至週五16:00，美國在週二至週六08:00；UTC cron分別0 8 * * 1-5與0 0 * * 2-6。手動更新可選all／asia／us。各市場依自己的交易日曆判斷收盤，每個市場保留獨立抓取時間。啟動不等於完成時間；GitHub排程仍可能延遲或在60天無活動後停用。

網址預設為 `https://allenljf.github.io/huaxi-street/`；必須實際完成精靈並等Actions部署成功後才可使用。知道網址即可查看。

## 免費研究來源與本機預覽

```bash
.venv/bin/python -m market.pipeline --research --batch all
RESEARCH_PREVIEW=true npm --prefix web run dev
```

研究快照寫入被忽略的.private/，Vite僅在開發模式提供此快照；正式build不會自動帶入。來源為Yahoo調整後OHLC、Cboe VIX；CNN失敗保留缺漏。台灣11/6下午可取得亞洲11/6，當時美股最新完整收盤為11/5。

如果操作者另外選擇公開使用研究資料，可在data/provider-settings.json將enableResearch／publishResearch設為true，精靈會同步Actions變數。這是發布開關，不是授權證明。來源使用條款記錄於data/sources.json。`--publish-research`必須搭配`--research`，不可默默將私人研究輸出放到公開站。

## 上傳Cloudflare

最快試看：`./scripts/package-cloudflare.sh`，再將output/huaxi-street-cloudflare.zip拖到Cloudflare Pages Direct Upload。只上傳web/dist的產物，不上傳整個原始碼目錄。

自動更新：`./scripts/setup.sh --cloudflare`；精靈建立／使用Pages專案，將限定權限的Cloudflare Token存入GitHub Secrets，以兩段排程自動部署。

完整操作、所需Secrets與首次上傳說明見[Cloudflare上傳指南](docs/cloudflare-upload.md)。

## 匯入有公開使用權的歷史

不要把無分享權的資料、帳戶資料或機密放在公開repo。以下bundle請自行放在被忽略的 `.private/`，以真實OHLC取代示意，至少400筆才能評分。

```json
{
  "id": "0050",
  "publicPermission": true,
  "sourceName": "你已確認可公開使用的資料源",
  "sourceUrl": "https://來源的實際網址",
  "licenseNote": "實際授權名稱或許可範圍",
  "eventsReviewedThrough": "2026-11-05",
  "events": [{"date":"2025-06-18","split":4,"dividend":0}],
  "bars": [{"date":"2026-11-05","open":99.4,"high":99.75,"low":96.9,"close":97.15}]
}
```

```bash
.venv/bin/python -m market.pipeline --import-bundle .private/history-bundle.json --offline
.venv/bin/python -m market.backtest --id 0050
```

`publicPermission`是操作者對資料用途的確認，不是程式能替你取得的授權。events須涵蓋整段分割／配息，不要只複製0050分割一筆就宣告完整。合併歷史後會寫入可公開的 `data/history.json`。匯入資料最晚覆核日期須涵蓋最後交易日；後續超過該日則暫停股票評分，避免默默漏算新公司行動。

海外免費研究來源與美日韓交易日曆已接入；公開發布選擇由data/provider-settings.json與Actions variables控制。不是僅因網站免費或只有朋友使用就自動取得來源授權。

## 測試

```bash
.venv/bin/python -m unittest discover -s tests -v
npm --prefix web run build
npm --prefix web exec -- playwright install chromium webkit
npm --prefix web test
bash -n scripts/setup.sh
```

瀏覽器測試使用明確的獨立fixtures，不發布為行情；包含Chromium與WebKit、手機／文字放大、對話框焦點與錯誤狀態。

## 專案結構

- `market/`：純計算、受控公開資料管線、相同現金流研究回測。
- `data/`：允許公開的歷史快照、交易日曆與來源檢視記錄。
- `web/`：React／TypeScript靜態網站與端對端測試。
- `scripts/setup.sh`：可重複部署精靈。
- `.github/workflows/`：驗證、每日資料更新、GitHub Pages部署。
- `docs/`：研究、設計、實作計畫、規則與驗收。

資料來源：臺灣證券交易所OpenAPI；依[政府資料開放授權條款第1版](https://data.gov.tw/license)顯名使用。來源權利狀態詳見 `data/sources.json`。本專案與證交所、CNN、Cboe及任何券商無隸屬關係。
