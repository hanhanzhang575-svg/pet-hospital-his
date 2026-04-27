@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd frontend
echo 启动前端开发服务器...
echo.
npm run dev
pause
