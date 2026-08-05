# 晶鑽生醫 KPI Dashboard：GitHub + Render 部署指南

## 1. 建立 GitHub Repository

1. 登入 GitHub，點 **New repository**。
2. Repository name 建議填 `diamond-kpi`。
3. 選擇 **Private**，不要勾選建立 README。
4. 建立後，點 **uploading an existing file**。
5. 將本資料夾內所有檔案拖曳上傳，包含 `app` 資料夾、`render.yaml`、`requirements.txt`。
6. Commit message 填 `Initial Render deployment`，按 **Commit changes**。

> GitHub 網頁不接受直接上傳壓縮檔後自動解壓；請先在 Mac 解壓，再上傳裡面的檔案。

## 2. 使用 Render Blueprint 一鍵部署

1. 登入 Render，使用 GitHub 帳號授權。
2. 點 **New +** → **Blueprint**。
3. 選擇剛建立的 `diamond-kpi` Repository。
4. Render 會讀取根目錄的 `render.yaml`，建立：
   - `diamond-kpi` Web Service
   - `diamond-kpi-db` PostgreSQL
5. 畫面要求輸入 `ADMIN_PASSWORD` 時，設定至少 12 碼、含大小寫、數字與符號的密碼。
6. 點 **Apply**，等待約 5–10 分鐘。
7. 部署完成後，點 Web Service 顯示的 `onrender.com` 網址。

## 3. 登入

- 帳號：`admin`
- 密碼：部署時設定的 `ADMIN_PASSWORD`

如 `SEED_DEMO_DATA=true`，另有示範帳號：

- `ceo / Ceo123!`
- `manager / Manager123!`
- `sales / Sales123!`

正式上線後，請在 Render 的 Environment 將 `SEED_DEMO_DATA` 改為 `false`，並刪除示範帳號或修改密碼。

## 4. 日後更新

每次在 GitHub 修改並 Commit，Render 會自動重新部署。資料存放於 PostgreSQL，不會因重新部署而消失。

## 5. 自訂網域

在 Render Web Service → **Settings** → **Custom Domains** 新增：

`kpi.diamond-biotechnology.com`

再到網域 DNS 管理平台依 Render 顯示的紀錄新增 CNAME。Render 會自動配置 HTTPS。

## 正式營運前建議

免費方案適合驗收。正式多人營運時，請將 Web Service 與 PostgreSQL 升級為付費方案，以避免休眠並取得更穩定的資源、備份與支援。
