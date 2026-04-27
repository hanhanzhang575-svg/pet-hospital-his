@echo off
REM SQLite DLL 加载错误修复脚本
REM 此脚本将重建虚拟环境并安装所有依赖

setlocal enabledelayedexpansion
cd /d "C:\Users\zhangmohan\Desktop\信息系统"

echo.
echo ============================================================
echo            SQLite DLL 加载错误修复脚本
echo ============================================================
echo.
echo 当前工作目录: %cd%
echo.

REM 设置变量
set "PYTHON_EXE=python"
set "VENV_DIR=.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

echo ============================================================
echo 步骤 1: 删除旧的虚拟环境
echo ============================================================
if exist %VENV_DIR% (
    echo 正在删除旧的虚拟环境目录...
    rmdir %VENV_DIR% /s /q >nul 2>&1
    timeout /t 2 /nobreak >nul
    if exist %VENV_DIR% (
        echo ✗ 失败: 无法删除旧虚拟环境
        goto :error
    ) else (
        echo ✓ 成功: 旧虚拟环境已删除
    )
) else (
    echo ℹ 信息: 虚拟环境不存在，无需删除
)
echo.

echo ============================================================
echo 步骤 2: 创建新的虚拟环境
echo ============================================================
echo 执行: %PYTHON_EXE% -m venv %VENV_DIR%
%PYTHON_EXE% -m venv %VENV_DIR%
if !errorlevel! neq 0 (
    echo ✗ 失败: 虚拟环境创建失败
    goto :error
)
echo ✓ 成功: 虚拟环境创建完成
echo.

echo ============================================================
echo 步骤 3: 激活虚拟环境
echo ============================================================
echo 执行: %VENV_ACTIVATE%
call %VENV_ACTIVATE%
if !errorlevel! neq 0 (
    echo ✗ 失败: 虚拟环境激活失败
    goto :error
)
echo ✓ 成功: 虚拟环境已激活
echo.

echo ============================================================
echo 步骤 4: 升级 pip
echo ============================================================
echo 执行: %VENV_PYTHON% -m pip install --upgrade pip
%VENV_PYTHON% -m pip install --upgrade pip
if !errorlevel! neq 0 (
    echo ✗ 失败: pip 升级失败
    goto :error
)
echo ✓ 成功: pip 升级完成
echo.

echo ============================================================
echo 步骤 5: 安装所有依赖
echo ============================================================
if not exist backend\requirements.txt (
    echo ✗ 失败: backend\requirements.txt 文件不存在
    goto :error
)
echo 执行: %VENV_PIP% install -r backend\requirements.txt
%VENV_PIP% install -r backend\requirements.txt
if !errorlevel! neq 0 (
    echo ✗ 失败: 依赖安装失败
    goto :error
)
echo ✓ 成功: 所有依赖安装完成
echo.

echo ============================================================
echo 步骤 6: 验证 sqlite3 是否可以加载
echo ============================================================
echo 执行: %VENV_PYTHON% -c "import sqlite3; print('SQLite3 OK')"
%VENV_PYTHON% -c "import sqlite3; print('SQLite3 OK')"
if !errorlevel! neq 0 (
    echo ✗ 失败: sqlite3 加载失败
    goto :error
)
echo ✓ 成功: sqlite3 加载正常
echo.

echo ============================================================
echo 步骤 7: 验证后端模块导入
echo ============================================================
echo 执行: %VENV_PYTHON% -c "import backend.main; print('IMPORT_OK')"
%VENV_PYTHON% -c "import backend.main; print('IMPORT_OK')"
if !errorlevel! neq 0 (
    echo ✗ 失败: 后端模块导入失败
    goto :error
)
echo ✓ 成功: 后端模块导入正常
echo.

echo ============================================================
echo 所有步骤执行成功！
echo ============================================================
echo.
goto :end

:error
echo.
echo ============================================================
echo 执行失败: 请查看上面的错误信息
echo ============================================================
echo.
exit /b 1

:end
endlocal
