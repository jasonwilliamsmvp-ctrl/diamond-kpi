# Diamond KPI v34 正式環境資安部署

## 必做
1. Render 設定 `APP_ENV=production`。
2. `SECRET_KEY` 使用 Render Secret / generateValue，不可提交 GitHub。
3. `ADMIN_PASSWORD` 使用強密碼並放在 Render Secret，不可提交 GitHub。
4. `SEED_DEMO_DATA=false`。
5. `FORCE_PRIVILEGED_MFA=false`（目前 MFA 為選配；如公司政策要強制主管 MFA 才改 true）。
6. PostgreSQL 不對公網開放；`DATABASE_URL` 只由 Render Database 注入。
7. 正式網域全程 HTTPS，Production 保留 HSTS / CSP / Secure Cookie。
8. 正式資料庫使用具備自動備份 / PITR 能力的 PostgreSQL 方案；不要把 Free DB 當作正式營運的唯一資料副本。
9. 至少每月做一次還原演練，確認 backup 不是只有「有檔案」而是真的能 restore。
10. Production 與 Staging 使用不同資料庫、不同 SECRET_KEY、不同 Admin 密碼。

## 帳號管理標準流程
- 到職：Admin 建立帳號 → 綁定員工 → 指定角色 / 區域 → 發一次性初始密碼 → 使用者首次登入強制改密碼。
- 調職：Admin 修改角色 / 區域 → v34 立即使該帳號舊 session 失效。
- 密碼遺失：Admin 重設臨時密碼 → 舊 session 全部失效 → 使用者下次登入強制改密碼。
- 異常登入：Admin 可解除鎖定；若懷疑帳號外洩，先停用 + 強制登出，再重設密碼。
- 離職：停用帳號，不刪除歷史員工 / 業績 / CRM 資料。

## 權限原則
- Sales：只限本人 employee_id。
- Manager：只限 user.region。
- Executive：全公司營運資料，不可管理帳號。
- Admin：全公司 + 帳號權限管理。
- 所有資料範圍在 FastAPI 後端檢查，不只靠 UI 隱藏。

## 建議上線前再做
- 使用公司 Google Workspace / Microsoft Entra ID SSO，可進一步降低自行管理密碼的風險。
- 對外公開服務若流量變大，可在 Render 前增加 Cloudflare WAF / rate limiting。
- 定期進行 OWASP ASVS / Top 10 檢查與第三方弱點掃描。
