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
