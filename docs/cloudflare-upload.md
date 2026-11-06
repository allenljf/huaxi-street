# Cloudflare上傳與每日更新

本專案採Cloudflare Pages靜態網站；GitHub Actions負責抓資料、計算、建置，再將web/dist上傳。你不需要自購網域，使用Cloudflare回傳的.pages.dev網址即可。

## 方法一：先手動上傳試看

1. 執行 `./scripts/package-cloudflare.sh`，產生 `output/huaxi-street-cloudflare.zip`。
2. 登入 [Cloudflare控制台](https://dash.cloudflare.com/)，開啟 Workers & Pages。
3. 依官方Direct Upload流程選 Create application → Get started → Drag and drop your files（介面若出現Workers／Pages選擇，選Pages）。
4. 輸入專案名稱，例如huaxi-street，拖入上述ZIP或web/dist資料夾，按Deploy site。
5. 使用Cloudflare實際回傳的網址。名稱已被使用時，網址可能帶額外字元，不要猜測。

**上傳的是建置後ZIP或web/dist，不是整個專案原始碼資料夾。** ZIP根目錄含index.html、assets/與data/。手動上傳只是一份快照，不會自行抓股票資料。

[官方Direct Upload說明](https://developers.cloudflare.com/pages/get-started/direct-upload/)。Direct Upload專案後續可用Wrangler自動部署，但不能直接切換為Git整合專案；本計畫使用Actions＋Wrangler，與此相容。

## 方法二：推薦，自動更新與部署

在專案目錄執行：

```bash
./scripts/setup.sh --cloudflare
```

精靈會完成：

1. 檢查工具並透過GitHub CLI登入allenljf。
2. 選擇或建立GitHub專案，預設allenljf/huaxi-street。
3. 設定亞洲與美國的固定時段和資料源策略。
4. 引導取得Cloudflare帳號ID、輸入Pages專案名稱。
5. 引導建立限定帳號的 **Account / Cloudflare Pages / Edit** Token，隱藏輸入，寫入GitHub Actions Secrets；不將Token寫入.env或聊天。取得實際專案網址。
6. 測試並建置；確認後推送main及執行首次更新／部署。
7. 開啟Actions與實際網站網址檢查。

初次建立公開repo、Cloudflare專案、儲存憑證、推送與發布都會在具體目標顯示後確認。已有其他origin或未提交程式時會停止，無force push。

手動設定等價如下：

| 類別 | 名稱 | 值 |
|---|---|---|
| Actions Secret | CLOUDFLARE_ACCOUNT_ID | 你的Cloudflare帳號ID |
| Actions Secret | CLOUDFLARE_API_TOKEN | 限定該帳號的Pages Edit Token |
| Actions Variable | CLOUDFLARE_PROJECT_NAME | 控制台的實際Pages專案名稱 |
| Actions Variable | DEPLOY_TARGET | cloudflare |

來源選擇還有 ENABLE_RESEARCH_SOURCES / PUBLISH_RESEARCH_SOURCES 兩個變數，由精靈根據data/provider-settings.json同步。後者開啟只是操作者選擇發布，並不取得來源授權；使用者已於2026-11-06明確選擇啟用，目前兩者皆true。

既有Cloudflare專案若已連GitHub，請避免同時啟用Git整合自動建置和Actions部署，否則可能重複建置。可以另建本專案專用的Direct Upload Pages專案。

## 更新時段（台灣時間）

| 批次 | 時段 | 來源範圍 |
|---|---|---|
| 亞洲 | 週一至週五16:00 | 台灣加權、2330、0050、00631L、00685L、KOSPI、日經225 |
| 美國 | 週二至週六08:00 | S&P500、Nasdaq Composite、VIX、CNN恐慌貪婪（可取得時） |

GitHub UTC cron分別是 `0 8 * * 1-5`、`0 0 * * 2-6`。各市場以交易日曆判斷最近已完成交易時段；遇休市保留最近收盤日期。手動Run workflow可選all／asia／us。

網頁顯示「網站產生時間」、每個市場的「行情交易日」「最近成功抓取」與來源狀態；一個批次更新不會替另一批次刷新抓取時間。GitHub排程可能延遲，啟動時段不保證該分鐘已部署完成。

## 11/6資料檢查紀錄

2026-11-06台北18:44的實測：TWSE OpenAPI當時仍回11/5；官方一般報表已包含11/6。免費研究來源已取得台股／日韓11/6與美股11/5、VIX11/5。美股11/6收盤須等台北11/7清晨，因此11/7的08:00批次才會更新。CNN當時HTTP418，未冒充有值。

使用者已於2026-11-06選擇公開站顯示免費來源資料，最新ZIP已改為包含行情與指標；CNN缺漏仍如實保留。公開範圍受data/provider-settings.json與Actions變數控制。

[Cloudflare官方CI部署說明](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)、[尋找帳號ID](https://developers.cloudflare.com/fundamentals/account/find-account-and-zone-ids/)。
