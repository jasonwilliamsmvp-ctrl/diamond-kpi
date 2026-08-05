@echo off
where docker >nul 2>nul
if %errorlevel%==0 (
  docker compose up -d --build
  start http://localhost:8000
) else (
  echo Please install Docker Desktop first.
  pause
)
