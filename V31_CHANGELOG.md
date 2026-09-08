# Diamond KPI v31 — Production Security + Sales CRM

## v28 — Sales CRM Dashboard
- `/sales-portal`：業務每日輸入銷售 / 出貨 / 收款三種業績。
- A/B/C/D 客戶分級：A 每週、B 每月、C 每季、D 每半年。
- 紅黃綠燈拜訪提醒與自動拜訪月曆。
- 完成拜訪後自動建立 CRM Activity 與下一拜訪日。
- 產品唯讀並直接使用主管端共用 Product master。

## v29 — Role & Data Security
- 業務：只可存取綁定 Employee 的自己客戶、自己的 daily performance、自己的拜訪。
- 區域經理：只可讀寫自己區域。
- Executive/Admin：全公司。
- Sales / CRM / Clinic detail / CSV export / import confirm 皆做後端 scope 檢查，不只隱藏 UI。

## v30 — Production Security
- SameSite=Strict + Secure + HttpOnly session cookie（production）。
- Same-origin + double-submit CSRF 防護。
- Security headers：HSTS、CSP、X-Frame-Options、nosniff、Referrer-Policy、Permissions-Policy。
- 登入失敗 5 次暫鎖 15 分鐘（可由 env 調整）。
- Audit Log 擴充 IP、HTTP method、path；登入成功 / 失敗 / 封鎖也留紀錄。
- 業績刪除改為「已作廢」以保留歷史軌跡；KPI 計算只納入「已認列」。
- Admin 可停用帳號、重設密碼、重設 MFA。
- Production 新建環境禁止使用預設 Admin123!。

## v31 — MFA + Production Deployment
- 內建 RFC 6238 相容 TOTP，不依賴第三方 OTP 套件。
- Google Authenticator / Microsoft Authenticator 可使用手動 secret 設定。
- Production 預設強制 Admin / Executive / Manager MFA。
- 業務可自願啟用 MFA。
- 新增 `/security` 個人安全頁。
- 提供 staging / production 建議流程、PostgreSQL backup / restore scripts。

## Important
部署到既有 Render PostgreSQL 時會以 startup migration 自動新增 security 欄位，不會刪除現有正式資料。
