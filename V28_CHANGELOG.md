# Diamond KPI v28 — Sales CRM Dashboard

## 新增功能
1. 業務專屬 Customer Dashboard `/sales-portal`
2. 每日三種業績：銷售、出貨、收款
3. 客戶 A/B/C/D 分級與固定拜訪頻率
4. 紅黃綠燈拜訪提醒
5. 自動下一拜訪日與月曆行程
6. 一鍵完成拜訪並寫入 CRM Activity
7. 業務端產品唯讀，直接連動 Product master
8. 業務可新增自己的客戶
9. 帳號可綁定 Employee，資料以 owner_employee_id 做範圍隔離

## 拜訪規則
- A：7 天
- B：1 個月
- C：3 個月
- D：6 個月
- 紅：已逾期
- 黃：3 天內到期
- 綠：尚未到期

## 注意
本版是初版工作流。每日三種業績暫存在 `daily_performance`，不直接重寫既有主管 KPI 的 Sale 計算，避免造成既有 Dashboard 歷史數據重複計算。確認管理口徑後再做 v29 串接。
