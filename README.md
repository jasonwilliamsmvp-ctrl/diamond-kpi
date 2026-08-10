# Diamond KPI Enterprise — Render Edition

晶鑽生醫多人 KPI 與 CRM 管理平台，可透過 GitHub + Render 部署，不需在 Mac 安裝 Docker。

## 一鍵部署

本專案根目錄已包含 `render.yaml`，可建立 FastAPI Web Service 與 PostgreSQL。

詳細步驟請見：`RENDER_DEPLOY_GUIDE.md`

## 本機啟動（選用）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

開啟 `http://127.0.0.1:8000`。

## 主要環境變數

- `DATABASE_URL`
- `SECRET_KEY`
- `APP_ENV`
- `COMPANY_NAME`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SEED_DEMO_DATA`

## Health Check

`GET /health`

## 2026-08 update
- Product KPI adds **NovaBright** (`NVB`), unit **台**. Existing databases will add it automatically on application startup. Initial target/price are 0 so management can set the official values without affecting current KPI calculations.
- Sales records now have an **Edit** action. In the edit screen, **業務姓名** is a dropdown populated from active employees, so managers can select the salesperson directly instead of typing a name.


## Render runtime compatibility
This release pins Render to Python 3.13 to keep the PostgreSQL binary driver compatible with the deployed dependency set.


## Render v4 compatibility fix
Pinned `bcrypt==4.0.1` for compatibility with Passlib 1.7.4 on Render/Python 3.13. This prevents application startup failure caused by bcrypt 5.x enforcing the 72-byte limit during Passlib backend detection.
