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
