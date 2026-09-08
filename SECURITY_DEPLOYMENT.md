# v31 正式上線資安部署清單

## 1. Render Environment Variables
正式環境至少設定：
- `APP_ENV=production`
- `SECRET_KEY`：64+ 字元隨機字串，禁止放 GitHub
- `ADMIN_PASSWORD`：強密碼，禁止使用 `Admin123!`
- `SEED_DEMO_DATA=false`
- `FORCE_PRIVILEGED_MFA=true`
- `LOGIN_MAX_FAILURES=5`
- `LOGIN_LOCK_MINUTES=15`
- `SESSION_MAX_AGE=28800`

`DATABASE_URL` 只由 Render Database connection string 注入，不寫入 repo。

## 2. 第一次部署 v31
1. 先備份 Production PostgreSQL。
2. 部署 v31 到 staging，確認登入、客戶、業績與 KPI 正常。
3. 再部署 production。
4. Admin 第一次登入會被導向 MFA setup。
5. 在 Google Authenticator / Microsoft Authenticator 手動新增帳號，輸入畫面顯示的 secret。
6. 輸入 6 位碼完成啟用。
7. 為每一位 Executive / Manager 建立個人帳號，禁止共用 admin。

## 3. Staging / Production 分離
- Production Web + Production PostgreSQL：正式資料。
- Staging Web + Staging PostgreSQL：測試資料。
- 兩邊使用不同 `SECRET_KEY`、不同資料庫、不同管理員密碼。
- 新版本先進 staging，再 promotion 到 production。

## 4. Backup / Restore
repo 內提供：
- `scripts/backup_postgres.sh`
- `scripts/restore_postgres.sh`

建議：每日備份、至少保留 30 天；每週把一份備份放到與 Production DB 不同的儲存位置。每季實際做一次 restore drill。

## 5. 權限規則
- Sales：自己的客戶 / daily performance / visit calendar。
- Manager：自己區域。
- Executive/Admin：全公司。
- Product master：Sales 唯讀；Executive/Admin 可修改。
- Audit Log：Admin / Executive 可讀；一般使用者不可刪除。

## 6. 上線前測試
- 嘗試以 Sales URL 修改其他 Sales 的 clinic_id / employee_id，應回 403。
- Manager 嘗試寫入其他區域，應回 403。
- 5 次錯誤密碼後確認暫鎖。
- 未完成 MFA 的主管無法進 Dashboard。
- POST 缺 CSRF token 應回 403。
- 作廢 Sale 後歷史紀錄仍存在，但 KPI 不再計入。
- Audit Log 應看到 username / IP / method / path。
