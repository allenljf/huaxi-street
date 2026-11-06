# 每日市場儀表板：免費資料來源調研

調研日期：2026-11-06（台北）。僅研究，未實作網站。使用者偏向數月到數年的分批投入。下列「建議」為設計提案，並非資料商保證。

## 結論

免費取得並在私人研究中計算，多數需求可以做到；完整跨國指數、CNN 指標的「免費公開再散布」不能一併保證。建議台股用 TWSE OpenAPI、VIX 用 Cboe、海外研究用 yfinance，CNN 當可缺省的輔助欄位。公開上線前依資料來源確認展示及衍生資料權利；換成自算分數不能自動消除授權問題。

## 標的與來源

| 標的 | 建議資料來源 | 欄位／限制 |
|---|---|---|
| 加權 TAIEX | TWSE `/indicesReport/MI_5MINS_HIST` | OHLC；實測 OpenAPI 只回當月4筆，長期初始化另用歷史查詢 |
| 台積電 2330 | TWSE `/exchangeReport/STOCK_DAY_ALL` | 最新日 OHLC、成交股數、成交額；另補月歷史 |
| 0050、00631L、00685L | 同上 | 實測三者均有資料；須管理分割與配息調整 |
| S&P 500 | Yahoo `^GSPC`，FRED `SP500` 可交叉檢查 | yfinance 個人研究候選；FRED 僅收盤、10年日資料、更新不保證08:00前 |
| Nasdaq Composite | Yahoo `^IXIC`，FRED `NASDAQCOM` 可交叉檢查 | 此為綜合指數，不是 Nasdaq-100；需在設計中明訂 |
| 韓國 KOSPI | Yahoo `^KS11`；韓國官方金融委員會 API 為備選 | 官方 API 應另核實申請資格、發布延遲及授權；尚未完成實測 |
| 日本 Nikkei 225 | Yahoo `^N225`，Nikkei 官方 CSV | 官方提供最近3年日資料及10年月資料；公開再散布需授權 |
| VIX | Cboe 官方歷史 CSV | 1990起、每日更新；實測 CSV 有 DATE/OPEN/HIGH/LOW/CLOSE；不把可下載解讀為無條件公開授權 |
| CNN Fear & Greed | CNN 網站所用 graphdata | 非已確認的正式開發者 API；本次普通 HTTP 請求回418；保留最近成功值並顯示日期，失敗不阻斷其餘資料 |

第一方來源：[TWSE Swagger](https://openapi.twse.com.tw/)、[TWSE API schema](https://openapi.twse.com.tw/v1/swagger.json)、[TAIEX 歷史頁](https://www.twse.com.tw/en/indices/taiex/mi-5min-hist.html)、[Yahoo 國際指數代號](https://tw.stock.yahoo.com/world-indices/)、[FRED S&P500](https://fred.stlouisfed.org/series/SP500)、[FRED Nasdaq](https://fred.stlouisfed.org/series/NASDAQCOM)、[韓國官方 API](https://www.data.go.kr/data/15094807/openapi.do)、[Nikkei 資料提供說明](https://indexes.nikkei.co.jp/nkave/data/index.en.html)、[Cboe 歷史頁](https://www.cboe.com/tradable_products/vix/vix_historical_data)、[CNN 指標頁](https://www.cnn.com/markets/fear-and-greed)。

## 已實測與尚未實測

- 直接讀取 TWSE Swagger：`STOCK_DAY_ALL` 明列日 OHLCV；`MI_5MINS_HIST` 明列 OHLC；`MI_INDEX` 僅收盤和漲跌，不能單獨拿來計算標準 KD。
- `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` 本次回 1,389 筆，2330、0050、00631L、00685L 都存在，日期1151105（2026-11-05）。
- `https://openapi.twse.com.tw/v1/indicesReport/MI_5MINS_HIST` 本次回4筆，起始1151102。不能誤以為 API 名稱含歷史就提供足夠200日均線歷史。
- `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv` 本次可讀，首列1990-01-02。官方目前歷史頁連結已使用 `cdn-api.cboe.com` 主機；實作時應跟隨官方實際連結，避免只硬編舊主機。
- CNN `https://production.dataviz.cnn.io/index/fearandgreed/graphdata` 在網頁擷取工具可識別 JSON，但本機普通請求回418。未證實 GitHub Actions 可穩定取用，不建議使用繞過封鎖手段。
- 未安裝 yfinance、未批次下載全部歷史、未在 GitHub runner 驗證。月歷史回補端點及限流應在實作前的小型資料驗證中確認。

## 免費與授權要分開

TWSE Swagger 的 `info.description` 直接連到[政府資料開放授權條款](https://data.gov.tw/license)。該條款允許重製、散布與衍生利用，要求顯名。適用範圍是按此授權釋出的資料，不能因此推論所有 TWSE 網頁、第三方指數或歷史查詢都同樣授權。

[yfinance 原始碼倉庫 README](https://github.com/ranaroussi/yfinance) 說明它非 Yahoo 官方，主要供研究教育，且 Yahoo Finance API 為個人用途。套件本身的 Apache 授權不等於行情資料授權。多國資料整合方便，但無服務穩定性承諾；適合私人版候選，不宜直接宣告公開版已獲授權。

[FRED SP500](https://fred.stlouisfed.org/series/SP500) 說明資料為日收盤、僅10年，且再製需 S&P 事前書面許可；[NASDAQCOM](https://fred.stlouisfed.org/series/NASDAQCOM) 亦標示 copyrighted / pre-approval required。[FRED 日經](https://fred.stlouisfed.org/data/NIKKEI225) 允許研究下載，但向第三人散布資料或含該資料的研究報告須向日經取得許可。FRED 不是免授權轉售／公開展示的捷徑。

[Nikkei 官方](https://indexes.nikkei.co.jp/nkave/data/index.en.html) 明示超出私人使用或法定引用需取得授權。Cboe 歷史頁提供每日下載，但本次未取得允許網站再散布的明確授權。CNN 同樣未找到可引用的公開開發者 SLA 與免費再散布許可。

## 長期分批投入特別注意

- 0050 追蹤臺灣50；00631L 追蹤臺灣50「單日」正向兩倍。兩者不等同加權指數。[元大00631L基本資料](https://www.yuantaetfs.com/product/detail/00631L/Basic_information)
- 00685L 是群益臺灣加權正2，追蹤「臺指日報酬兩倍指數」，來源為加權指數單日兩倍。[群益官方產品頁](https://www.capitalfund.com.tw/etf/product/detail/094)
- 每日槓桿重設造成路徑相依，跨多日報酬不等於原指數累積報酬乘2。元大官方也明示此點及不適合長期持有；群益官方分割文件同樣提醒槓桿、複利及長期持有特性。[元大產品說明](https://www.yuantafunds.com/active/ETF00631L/index.html)、[群益官方文件](https://www.capitalfund.com.tw/ECStorge/fund/ec/event/00685L/00685L_Lazybag.pdf)
- 設計建議：正2保留可比較的技術數據，但獨立顯示槓桿風險，不把普通指數高分直接翻譯成長期加碼正2。
- 0050 2025-06-18以1拆4恢復交易；舊 OHLC 若直接拼接新資料，會產生假的大跌與超賣訊號。[TWSE 官方公告](https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d696b406fc0196ce27c2e90063.pdf)
- 群益產品頁也明示00685L於2026-07-01至07-06分割。不能只特判0050，所有標的應使用事件表與一致價格口徑。
- 建議儲存原始 OHLC、分割事件、配息事件及調整 OHLC；指標以同一調整口徑計算，行情展示保留實際收盤。yfinance目前預設 `auto_adjust=True`，應明確指定選項，避免套件版本或預設改動悄悄改變指標。[yfinance README](https://github.com/ranaroussi/yfinance)

## 資料品質設計提案

每個標的保留來源、交易日、取得時間、最新完整交易日、是否過期、價格調整方式。外國「日收盤」不代表台北當天日期；應按市場交易日判定。不同來源更換時先比對重疊歷史，不直接拼接；只有收盤價的備援不應虛構最高最低來算 KD。抓取失敗保留上次成功資料並標示，核心資料缺少時停止當日新評分，輔助情緒資料缺少時顯示缺失及採用版本，避免把缺失當中性。
