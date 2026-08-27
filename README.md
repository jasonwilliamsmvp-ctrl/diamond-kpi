# 中國線材市場綁定 Dashboard V2

多人連線 Web 版，包含：
- 帳號登入與角色：Admin / Manager / Sales
- 醫師新增、修改、搜尋
- 機構新增、修改、搜尋
- 綁定狀態：未接觸 / 接觸中 / 試用 / 合作 / 核心綁定 / 流失
- 醫師與機構分級：S >= 1000、A >= 500、B >= 300、C >= 100、其餘未分級
- 月目標 vs 實際、達成率
- 紅黃綠燈：綠 >= 85%；黃 60–84.9% 或尚未設定目標；紅 < 60%；流失直接紅燈
- 最後拜訪、下次拜訪、下次行動
- 省份 / 城市 / 業務排行榜
- 醫師 / 機構 Top 10
- 本月新增綁定、本月流失
- PostgreSQL 多人共用資料庫
- Audit log 基礎稽核紀錄

## GitHub

1. 在 GitHub 建立一個空白 repository，例如 `china-thread-dashboard`。
2. 將本專案所有檔案上傳到 repo 根目錄。
3. 不要上傳 `.env`。

## Render 一鍵 Blueprint 部署

本專案根目錄已包含 `render.yaml`。

1. 登入 Render。
2. 建立 Blueprint，連接剛才的 GitHub repository。
3. Render 讀取 `render.yaml` 後，會建立：
   - Node.js Web Service
   - PostgreSQL Database
   - DATABASE_URL 自動連結
   - SESSION_SECRET 自動產生
4. Render 會要求輸入 `ADMIN_PASSWORD`。請設定至少 12 碼的強密碼。
5. 部署完成後，以：
   - 帳號：`admin`
   - 密碼：你在 Render 輸入的 `ADMIN_PASSWORD`
   登入。
6. 登入後到「帳號管理」新增其他同事帳號。

## 本機開發

需要 Node.js 20+ 與 PostgreSQL。

```bash
cp .env.example .env
npm install
npm start
```

開啟 `http://localhost:3000`。

## 安全注意事項

- 正式環境請勿把密碼或 `.env` commit 到 GitHub。
- Render 上的 `SESSION_SECRET` 使用自動生成。
- 正式環境 cookie 設定為 Secure + HttpOnly + SameSite=Lax。
- 管理員帳號建立後，建議另外新增個人 Admin 帳號，不要多人共用 admin。
