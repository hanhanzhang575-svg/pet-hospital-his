#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化修复脚本 - 使用 subprocess 和 sys 路径操作来避免激活 venv
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

# 设置工作目录
target_dir = Path(r"C:\Users\zhangmohan\Desktop\信息系统")
os.chdir(target_dir)

print("\n" + "="*70)
print("FastAPI SQLite DLL 修复脚本 - 自动化版本")
print("="*70)
print(f"工作目录: {os.getcwd()}\n")

venv_dir = target_dir / ".venv"
venv_python = venv_dir / "Scripts" / "python.exe"
venv_pip = venv_dir / "Scripts" / "pip.exe"

# 步骤 1: 删除旧虚拟环境
print("\n【步骤 1】删除旧的虚拟环境...")
if venv_dir.exists():
    try:
        shutil.rmtree(venv_dir)
        print("✓ 旧虚拟环境已删除")
    except Exception as e:
        print(f"✗ 删除失败: {e}")
        sys.exit(1)
else:
    print("ℹ 虚拟环境不存在，跳过删除")

# 步骤 2: 创建新虚拟环境
print("\n【步骤 2】创建新的虚拟环境...")
try:
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, timeout=60)
    print("✓ 虚拟环境创建成功")
except Exception as e:
    print(f"✗ 创建失败: {e}")
    sys.exit(1)

# 步骤 3: 升级 pip
print("\n【步骤 3】升级 pip...")
try:
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
        timeout=120
    )
    print("✓ pip 升级成功")
except Exception as e:
    print(f"✗ pip 升级失败: {e}")
    sys.exit(1)

# 步骤 4: 安装依赖
print("\n【步骤 4】安装 backend/requirements.txt 中的依赖...")
requirements_file = target_dir / "backend" / "requirements.txt"
if not requirements_file.exists():
    print(f"✗ 文件不存在: {requirements_file}")
    sys.exit(1)

try:
    result = subprocess.run(
        [str(venv_pip), "install", "-r", str(requirements_file)],
        check=True,
        timeout=300,
        capture_output=True,
        text=True
    )
    print("✓ 依赖安装成功")
    if result.stdout:
        print(result.stdout[-500:])  # 仅显示最后 500 字符
except subprocess.CalledProcessError as e:
    print(f"✗ 依赖安装失败")
    print(e.stdout)
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"✗ 安装出错: {e}")
    sys.exit(1)

# 步骤 5: 验证 sqlite3
print("\n【步骤 5】验证 sqlite3 加载...")
try:
    result = subprocess.run(
        [str(venv_python), "-c", "import sqlite3; print('SQLite3 版本:', sqlite3.version)"],
        check=True,
        timeout=30,
        capture_output=True,
        text=True
    )
    print("✓ sqlite3 加载成功")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"✗ sqlite3 加载失败")
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"✗ 验证出错: {e}")
    sys.exit(1)

# 步骤 6: 验证后端导入
print("\n【步骤 6】验证后端模块导入...")
try:
    result = subprocess.run(
        [str(venv_python), "-c", "import backend.main; print('Backend 模块导入成功！')"],
        check=True,
        timeout=30,
        capture_output=True,
        text=True,
        cwd=str(target_dir)
    )
    print("✓ 后端模块导入成功")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"✗ 后端模块导入失败")
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"✗ 导入验证出错: {e}")
    sys.exit(1)

# 完成
print("\n" + "="*70)
print("✓✓✓ 所有步骤执行成功！✓✓✓")
print("="*70)
print("\n现在可以启动 FastAPI 服务了：")
print(f"  python start_server.py")
print(f"\n或使用虚拟环境中的 Python：")
print(f"  {venv_python} start_server.py")
print("\n访问地址: http://127.0.0.1:8000/docs")
print()
