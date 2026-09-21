# v34 — Account & Access Security

## 帳號與權限
- Admin 可建立帳號、編輯姓名 / Email / 角色 / 區域 / 員工綁定。
- Sales 帳號強制綁定員工主檔，避免登入後跨人員資料。
- 同一員工只能綁定一個登入帳號。
- Admin / Executive 自動限制為全區；Manager 必須指定北 / 中 / 南區。
- 帳號可停用 / 重新啟用、解除登入鎖定、強制登出所有裝置。
- MFA 仍為選配，可由 Admin 清除綁定。

## 密碼與登入安全
- 初始密碼與 Admin 重設密碼後，使用者首次登入強制自行改密碼。
- 密碼至少 10 碼（可由 PASSWORD_MIN_LENGTH 調整），必須包含英文與數字，並封鎖常見弱密碼。
- 使用者可在「帳號安全」自行變更密碼。
- 密碼變更、角色變更、停用、MFA 重設與 Admin 強制登出都會提升 session_version，使舊工作階段立即失效。
- Admin 高風險帳號操作必須再次輸入自己的管理員密碼。
- 登入失敗鎖定、Secure/HttpOnly/SameSite Cookie、CSRF、Security Headers、Audit Log 延續 v31/v32。
- 記錄最後登入時間與最後登入 IP。

## 業務權限
- 業務：只能讀寫自己的客戶 / 銷售 / 出貨 / 收款 / 拜訪 / 行事曆。
- 區域經理：只限所屬區域。
- 高階主管 / Admin：全公司。
- 產品主檔：Sales / Manager 唯讀；Executive / Admin 可管理。
- 帳號管理：僅 Admin。

## 部署注意
- 不需刪除 PostgreSQL，startup migration 會自動新增 users 欄位。
- v34 部署後，舊的登入 cookie 因 session_version 升級可能需要重新登入一次，屬正常現象。
