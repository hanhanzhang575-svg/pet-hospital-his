@echo off
setlocal enabledelayedexpansion
cd /d "C:\Users\zhangmohan\Desktop\信息系统"

echo.
echo ================================================
echo SQLite DLL 加载错误修复脚本
echo ================================================
echo.

REM 步骤1: 删除旧的虚拟环境
echo.
echo [步骤1] 删除旧的虚拟环境...
if exist .venv (
    echo 正在删除 .venv 目录...
    rmdir .venv /s /q
    echo ✓ 旧虚拟环境已删除
) else (
    echo ℹ 虚拟环境不存在，跳过
)
echo.

REM 步骤2: 创建新的虚拟环境
echo [步骤2] 创建新的虚拟环境...
python -m venv .venv
if %errorlevel% equ 0 (
    echo ✓ 虚拟环境创建成功
) else (
    echo ✗ 虚拟环境创建失败
    goto :error
)
echo.

REM 步骤3: 激活虚拟环境
echo [步骤3] 激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorlevel% equ 0 (
    echo ✓ 虚拟环境已激活
) else (
    echo ✗ 虚拟环境激活失败
    goto :error
)
echo.

REM 步骤4: 升级 pip
echo [步骤4] 升级 pip...
python -m pip install --upgrade pip
if %errorlevel% equ 0 (
    echo ✓ pip 升级成功
) else (
    echo ✗ pip 升级失败
    goto :error
)
echo.

REM 步骤5: 安装所有依赖
echo [步骤5] 安装所有依赖（从 backend/requirements.txt）...
if exist backend\requirements.txt (
    pip install -r backend\requirements.txt
    if %errorlevel% equ 0 (
        echo ✓ 依赖安装成功
    ) else (
        echo ✗ 依赖安装失败
        goto :error
    )
) else (
    echo ✗ backend\requirements.txt 文件不存在
    goto :error
)
echo.

REM 步骤6: 验证 sqlite3 是否可以加载
echo [步骤6] 验证 sqlite3 是否可以加载...
python -c "import sqlite3; print('SQLite3 加载成功 - OK')"
if %errorlevel% equ 0 (
    echo ✓ sqlite3 验证成功
) else (
    echo ✗ sqlite3 加载失败
    goto :error
)
echo.

REM 步骤7: 验证后端模块导入
echo [步骤7] 验证后端模块导入...
python -c "import backend.main; print('后端模块导入成功 - OK')"
if %errorlevel% equ 0 (
    echo ✓ 后端模块验证成功
) else (
    echo ✗ 后端模块导入失败
    goto :error
)
echo.

echo ================================================
echo 所有步骤执行成功！
echo ================================================
echo.
goto :end

:error
echo.
echo ================================================
echo 错误：执行过程中出现问题
echo ================================================
echo.
exit /b 1

:end
endlocal
