# v32 — Optional MFA / Simplified Login

- 所有角色預設使用「帳號＋密碼」直接登入。
- Production 不再強制 Admin / Executive / Manager 設定 MFA。
- MFA/TOTP 功能完整保留，使用者可在「帳號安全」自行啟用。
- 已啟用 MFA 的帳號仍會在登入時要求 6 位驗證碼。
- 已啟用 MFA 的使用者可在「帳號安全」關閉 MFA；關閉後立即登出。
- 保留 v31 的登入錯誤鎖定、Secure/HttpOnly/SameSite Cookie、CSRF、防護 Header、Audit Log、角色與資料範圍隔離。
- Render production/staging 預設 FORCE_PRIVILEGED_MFA=false。
- 不刪除或重建既有 PostgreSQL 資料。
