# 介面與行為驗收 — 2026-11-06

- 正式建置成功：TypeScript＋Vite，靜態產物不含原始資料下載程式、測試fixtures或秘密。
- Python 22案例通過：OHLC合法性、RSI/KD無波動、均線交叉、分割＋配息事件順序、未到期事件、暖機、交易日、同日合併、過期抑制、現金流、滑價與XIRR。
- Playwright 18案例通過（Chromium與WebKit各9）：買賣方向、資料缺漏、篩選、彈窗焦點、Escape與回復、320px＋200%文字、無模糊／減少動畫、訊號分歧、連線失敗、過期快照與格式異常。
- 已逐張檢視1440px桌面、390px手機與手機彈窗；長頁面中段實際捲動檢查，卡片正常渲染。320px＋200%文字的內容元素未超出螢幕左右。
- 模糊24px、邊框與柔和光暈；降級使用不透明surface。muted文字#A1AFBD配深色surface #131E2B，對比大於7:1；最亮玻璃底色#273B3B仍大於5:1。正負號與文字並存，不只用色彩判讀。
- Safari原生dialog Tab可移至body，已補明確焦點循環；Safari按鈕點擊不一定focus，開啟前顯式聚焦以確保關閉後正確返回。
- 精靈：bash語法及 --check 通過，尚未以真人登入／發布流程完整執行；本機未安裝shellcheck。
- GitHub runner的網路、Pages權限與實際部署尚未驗證，需精靈完成首次部署後確認。

## 真實資料狀態

本機直接請求TWSE三個OpenAPI端點成功，5個台股標的有最新行情，加權有當月4筆。當日資料未更新到應有交易日時標過期。0個完整評分，不製造展示數字。海外、VIX、CNN只顯示官方入口與尚未接入原因。尚無真實回測結果，來源限制詳見README與data/sources.json。

## 畫面

- [桌面](screenshots/desktop.png)
- [手機](screenshots/mobile.png)
- [手機詳情](screenshots/mobile-dialog.png)


## 兩段更新與Cloudflare追加驗收

- Python40案例通過（包含原22），新增NYSE感恩節／夏令時間、日本／韓國／台灣收盤判斷、週六美股、區域batch隔離、調整後OHLC與未收盤排除、VIX/CNN資料驗證、Cloudflare GET/404/403安全流程、實際執行workflow selector檢查GITHUB_ENV換行與美股提早收盤的CNN檢查。
- 瀏覽器20案例通過（兩引擎各10），新增美國batch不能替過期亞洲資料刷新有效期。
- 本機研究實抓9個市場5年歷史、每個約1,200筆；亞洲11/6、美股11/5均有值與公式分數；VIX11/5=28.18，CNN418無值。真實樣本外回測仍未執行，不宣稱投資績效。
- 研究預覽已透過Vite開發模式接到忽略的.private/，公開建置仍只讀web/public；研究截圖也存.private/screenshots，不提交。
- Cloudflare ZIP已實際產生並檢查根目錄index.html，無原始碼、測試資料、.env或.private。Wrangler4.158.0本機可執行；尚未以Cloudflare帳號登入／上傳，需使用者執行精靈。
- 獨立review代理完成部分閱讀與22測試後因服務額度停止，未產出完整審查結論；後續由主實作者自行檢查，不能稱完整獨立審閱。

## 免費來源公開設定確認後

使用者已明確選擇公開站顯示免費來源資料。重新線上抓取後，公開JSON與Cloudflare ZIP均驗證為9標的行情、9組陪葬／躲噴分數，亞洲11/6、美股11/5；VIX有值，CNN缺漏。已移除本機私人研究預覽模式，瀏覽器實測公開資料與指標詳情可讀。Python40案例再次通過。此確認不等於Cloudflare已實際上傳，首次發布仍由精靈完成。


## macOS部署精靈變數邊界修正

使用者第二步遇到TARGET_REPO全形問號被誤解析為變數名稱。已在macOS內建Bash與UTF-8 locale重現；新增4個實際執行精靈片段的回歸案例（新repo確認、既有repo說明、origin不符、Cloudflare確認），修正前4例皆失敗，修正後皆通過。只正規化STAGES之後的變數為${NAME}，保持wizard共用library不變。完整Python44案例、bash語法與--check通過；測試替換服務邊界，未建立repo、未推送或發布。
