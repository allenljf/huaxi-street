# 陪葬! 華西街 — Glass UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立精美、有趣、手機友善的iOS玻璃風投資觀察介面，首頁精簡、詳情用popup展開。

**Architecture:** 靜態網站，頁面只讀批次產生的市場JSON。文案集中管理、分數方向與計算邏輯分離；對話框統一管理焦點與返回。此計畫只涵蓋介面，資料源、評分與部署依主設計另行規劃，不在此階段實作。

**Tech Stack:** 建議 React、TypeScript、Vite、CSS自訂屬性、原生dialog、SVG圖示與走勢、Playwright互動驗收；實作前核實依賴版本。

**Spec:** [每日投資觀察站設計](../specs/2026-11-06-market-dashboard-design.md)

## Global Constraints

- 網站名稱與主標題精確使用「陪葬! 華西街」。
- 產品文案「買進」改為「陪葬」、「賣出」改為「躲噴」，所有相關建議採一致趣味語氣。
- 名稱變更僅影響顯示：陪葬分仍代表買進支持，躲噴分仍代表賣出／減碼支持，不能交換方向或改變計算。
- 分數不是上漲機率；資料缺失不可填0、不可展示假行情；沒有資料時不能產生趣味交易建議。
- 尚未開始產品實作；此文件為後續實作與驗收依據。字型、色票與排版細節為設計者提案，可在視覺預覽時調整。

## Review Focus

- 玻璃背景明暗變化：卡片文字始終可讀，不能讓背景穿透干擾分數。（Task 1）
- 首頁與彈窗文案：陪葬／躲噴分數方向一致；缺資料不顯示建議。（Task 2）
- 手機窄螢幕與200%文字放大：內容不水平溢出，彈窗可完整捲動與關閉。（Task 3）
- 鍵盤及螢幕閱讀器：可開啟、關閉對話框，焦點不逸出且關閉後回到原按鈕。（Task 3）
- 不支援背景模糊或偏好減少動畫：仍有完整層次、資訊與操作。（Task 4）

## 檔案分工

`web/src/styles/tokens.css` 定義色彩、間距、玻璃與動畫；`web/src/styles/app.css` 排版與響應式。
`web/src/content/zh-TW.ts` 集中品牌與趣味文案；`web/src/types/market.ts` 定義介面資料契約；`web/src/components/MarketCard.tsx` 總覽卡片；`web/src/components/DetailDialog.tsx` 統一對話框；`web/src/App.tsx` 組合總覽與詳情。
`web/tests/dashboard.spec.ts` 驗收資訊與互動，`web/tests/fixtures/` 僅存明確標示的測試資料，不能發布為真實行情。

## 視覺方向

以「高級金融儀表板＋有點荒謬的招牌」為主調。主標使用醒目的繁中字重，旁有小型英文MARKET JOURNAL點綴；笑點集中在名稱和建議，數據排版保持精準。

預設深色：墨藍黑背景、低彩度青綠與淡紫光暈、柔和白字。玻璃卡片採半透明底色、20–28px模糊、1px淡色邊線、柔和陰影、20–24px圓角。文字區需有足夠底色；避免每張卡片多層模糊與持續移動光暈。數字採等寬數字，漲跌帶正負號和箭頭，不能只靠顏色。

桌面最寬1280px，寬螢幕3欄卡片、平板2欄、手機1欄。主要操作至少44px。介面動畫150–220ms，採opacity與transform；減少動畫偏好下停用位移。色彩與排版是本計畫建議，非使用者指定色票。

## 資訊層級與popup

首頁保留品牌、最近更新／資料異常摘要、市場篩選（全部／台股／美股／日韓／正二）、市場卡片與情緒摘要。每張卡片只顯示名稱代號、最近已收盤交易日、收盤與漲跌、微型走勢、陪葬／躲噴分、最多一句主要理由與「看陪葬攻略」按鈕。卡片不要整張變成多個巢狀點擊區。

「看陪葬攻略」打開標的詳情：較完整走勢、各指標數值／分數／理由、最近交叉事件、風險與來源。對話框內以「局勢／訊號／資料」分頁減少長文。另設「這分數怎麼來的？」顯示權重與陪葬／躲噴對照。資料過期、缺漏與正二標籤直接留在首頁，不能藏進彈窗。

桌面對話框寬度最多880px、高度最多85dvh，背景加暗與輕模糊。手機使用底部彈出樣式、最高92dvh，保留安全區與常駐關閉按鈕；不要求滑動手勢才能關閉。同一時間只有一個對話框，詳情不開巢狀popup；必須由使用者操作才開啟，不自動跳出。

## 文案對照（第一版固定）

| 原用途 | 顯示文案 |
|---|---|
| 網站標題 | 陪葬! 華西街 |
| 副標 | 今天陪葬，還是先躲噴？ |
| 買進／加碼支持度 | 陪葬指數 |
| 賣出／減碼支持度 | 躲噴指數 |
| 強加碼支持 | 陪葬訊號集結，分批入席 |
| 中度加碼支持 | 陪葬席可留，分批慢慢來 |
| 中性／觀望 | 先看戲，席位不急 |
| 買進支持弱 | 陪葬先緩緩，再看一輪 |
| 強減碼支持 | 躲噴警報，檢查減碼節奏 |
| 中度減碼支持 | 躲噴雷達亮起，留意部位 |
| 賣出支持弱 | 躲噴訊號偏淡，持續觀察 |
| 訊號矛盾 | 陪葬、躲噴各有說法，先別急 |
| 槓桿ETF | 正二刺激席・每日槓桿重設 |
| 指標詳情入口 | 看陪葬攻略 |

原始數值、指標原名、公式與科學結果不改成笑話。首次說明清楚寫「陪葬＝買進／加碼支持；躲噴＝賣出／減碼支持；分數不是獲利機率」。訊號卡須以實際計算狀態選文案，不從分數胡亂推導；未通過確認條件時標「訊號待確認」。資料不足用「資料不足，暫不評分」，抓取失敗用「更新未完成，顯示上次成功資料」；不以幽默掩蓋錯誤。

### Task 1: 品牌與玻璃視覺基礎

**Files:** 建立 `web/src/styles/tokens.css`、`web/src/styles/app.css`，建立或修改 `web/src/App.tsx`；建立本任務所需最小Vite與TypeScript設定。

**Interfaces:** 產出共用玻璃surface、文字／風險／互動色、間距與動畫tokens，後續元件只引用tokens，不各自發明玻璃參數。

- [ ] 建立主標、空總覽與玻璃卡片的視覺預覽；預覽資料明確標示範例。
- [ ] 實作上述色彩、層次、排版、圓角、陰影與字體，沒有裝飾性的持續動畫。
- [ ] 以明暗光暈位置檢查所有文字：一般文字對比至少4.5:1，大字至少3:1；逐個量測實際合成背景並修正底色。
- [ ] 在390px與1440px寬度渲染並保存畫面，檢查閱讀順序、留白與主標完整性；執行型別檢查與建置成功後提交本任務。

### Task 2: 精簡總覽與一致趣味文案

**Files:** 建立 `web/src/content/zh-TW.ts`、`web/src/types/market.ts`、`web/src/components/MarketCard.tsx`、`web/tests/dashboard.spec.ts` 與測試fixtures；修改 `web/src/App.tsx`。

**Interfaces:** `MarketView` 包含 `id, name, symbol, sessionDate, close, changePct, sparkline, buyScore, sellScore, status, confirmed, leveraged, reasons`；行情與分數可為null，`status`固定為 `fresh | holiday | stale | unavailable`。`MarketCard({market, onOpen})`傳回市場id；資料轉換由此邊界處理，計算模組仍使用buy/sell鍵。

- [ ] 先加互動驗收：強陪葬、強躲噴、訊號分歧、待確認、缺資料五個fixture各顯示對應固定文案；缺資料分數為「—」且無行動建議，正二有醒目標籤。
- [ ] 執行 `cd web && npx playwright test tests/dashboard.spec.ts`，確認在元件完成前案例失敗。
- [ ] 建立型別、統一文案與卡片，狀態先於分數決定是否可給建議；顯示資料日期，處理篩選與情緒摘要，保留明確的異常提示。
- [ ] 同一驗收全部通過，確認標題／分數／詳情方向一致後提交。測試無頭瀏覽器未安裝時先完成安裝，不以跳過代替驗收。

### Task 3: 詳情popup與手機底部視窗

**Files:** 建立 `web/src/components/DetailDialog.tsx`，修改 `web/src/App.tsx`、`web/src/styles/app.css`、`web/tests/dashboard.spec.ts`。

**Interfaces:** `DetailDialog({marketId: string | null, onClose: () => void})`以統一id讀取詳情，顯示局勢／訊號／資料分頁；計分說明同一對話框管理器呈現，禁止巢狀彈窗。以原生dialog的showModal提供模態語意。

- [ ] 先加驗收：按攻略打開正確標的、Escape關閉、關閉鈕關閉、焦點回原按鈕、Tab不逸出、具可讀標題；長內容與200%字體下可捲動且關閉鈕可達。
- [ ] 執行同一Playwright命令確認新增案例失敗，再實作對話框、分頁、焦點回復與安全區；遮罩可關閉，但從內容拖到遮罩不得誤關。
- [ ] 驗收390px底部樣式及1440px中央樣式；開啟時背景不捲動，關閉後回復原捲動位置。
- [ ] 全部互動測試通過、以鍵盤人工走完整條路徑後提交。

### Task 4: 視覺精修與降級驗收

**Files:** 修改上述樣式與元件，擴充 `web/tests/dashboard.spec.ts`；建立 `docs/qa/glass-ui-review.md` 記錄驗收證據。

**Interfaces:** 保持MarketView契約與固定文案；本任務完成可接上真實資料的UI，不改評分或來源權限。

- [ ] 加入並執行減少動畫與無backdrop-filter的互動案例：無位移動畫、卡片用較實底色、資訊與popup仍可讀可操作。
- [ ] 檢查320／390／768／1440px寬度、200%文字、空資料／部分過期／超長來源說明，修正溢出、裁切、不可達操作；SVG走勢提供文字摘要。
- [ ] 在Chromium與WebKit檢查玻璃、dialog、捲動與手機安全區，包含WebKit前綴；保存首頁與詳情畫面並逐張檢視。
- [ ] 執行 `cd web && npm run build` 與 `npx playwright test` 成功；記錄視覺與可及性驗收，再提交。預覽使用fixtures與正式行情清楚區隔。

## 完成條件

主標與趣味文案完整一致、首頁可快速閱讀、細節popup可存取、玻璃效果精緻且文字清楚；手機／鍵盤／減少動畫皆可用。完成UI不等於資料授權或策略驗證完成，正式站只發布主設計允許的行情與評分。這輪只寫計畫，待使用者確認後再進入實作。
