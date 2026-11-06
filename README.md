# 陪葬! 華西街

一份給自己與朋友的每日市場筆記。iOS毛玻璃介面、手機底部詳情視窗、固定公式運算，無LLM、無登入。

## 目前實際可用範圍

- 台灣加權、2330、0050、00631L、00685L最新已收盤行情：TWSE官方OpenAPI。
- RSI14、台式KD9、SMA50/200與交叉、MACD、布林、ADX/DMI、ATR與252日高點回落的計算與測試已提供。
- **首次啟動歷史不夠，完整評分尚未啟用。** OpenAPI加權僅當月，股票僅最新日。每天累積快照；需400筆且公司行動已覆核才產生完整分數。不能把等候時間誤認為兩週即可備齊。
- 海外四個指數、VIX、CNN目前顯示來源待確認及官方連結，**沒有冒充接上即時數值或歷史回測**。免費可下載不等同可公開再散布。
- 可匯入已取得公開使用權的歷史資料；引擎支援分割／配息一致調整。回測工具已實作，但真實歷史未齊時拒絕產生績效。
- 分數是研究規則的支持度，尚無真實樣本外績效結論。陪葬代表買進／加碼支持；躲噴代表賣出／減碼支持。

## 本機預覽

需Node.js 24+、Python 3.11+。Python使用標準函式庫，不需API金鑰。

```bash
npm --prefix web ci
python3 -m market.pipeline
npm --prefix web run dev
```

終端機會顯示本機網址。離線重建用 `python3 -m market.pipeline --offline`；不會產生假行情。過期快照保留價格、停用行動評分。

## GitHub Pages部署精靈

預設帳號 `allenljf`，建議專案 `huaxi-street`。不需要Cloudflare帳號、朋友名單或PAT。

```bash
./scripts/setup.sh --check
./scripts/setup.sh
```

精靈會檢查工具、透過GitHub CLI登入、選擇repo與週六更新選項。**建立公開repo、推送與發布前會顯示目標並確認。** 既有origin不同或存在未提交程式時會停止，不會強制推送或自動加入所有檔案。

主分支 `main` 推送後會觸發更新與部署；設定Pages來源為GitHub Actions由精靈完成。預設週一至週五台灣08:00啟動；選配週六需repo variable `INCLUDE_SATURDAY=true`。啟動時間不等於完成時間；GitHub排程可能延遲或在60天無活動後停用。

網址預設為 `https://allenljf.github.io/huaxi-street/`；必須實際完成精靈並等Actions部署成功後才可使用。知道網址即可查看。

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
python3 -m market.pipeline --import-bundle .private/history-bundle.json --offline
python3 -m market.backtest --id 0050
```

`publicPermission`是操作者對資料用途的確認，不是程式能替你取得的授權。events須涵蓋整段分割／配息，不要只複製0050分割一筆就宣告完整。合併歷史後會寫入可公開的 `data/history.json`。匯入資料最晚覆核日期須涵蓋最後交易日；後續超過該日則暫停股票評分，避免默默漏算新公司行動。

海外匯入目前僅供單次快照，尚未提供自動來源或各國交易日曆，不應用於正式海外評分。請勿在未擴充來源與日曆前當成完整支援。

## 測試

```bash
python3 -m unittest discover -s tests -v
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
