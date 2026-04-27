@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动后端 API 服务...
echo.
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
pause
