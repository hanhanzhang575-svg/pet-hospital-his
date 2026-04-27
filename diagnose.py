#!/usr/bin/env python
"""FastAPI 服务诊断脚本"""
import sys
import os
import subprocess
import socket
from pathlib import Path

print("=" * 60)
print("FastAPI 服务启动诊断")
print("=" * 60)

# 1. 检查 Python 环境
print("\n1. 环境检查")
print(f"   Python 版本: {sys.version}")
print(f"   Python 执行路径: {sys.executable}")

# 检查 venv
venv_python = Path(r"C:\Users\zhangmohan\Desktop\信息系统\.venv\Scripts\python.exe")
if venv_python.exists():
    print(f"   ✓ venv Python 存在: {venv_python}")
else:
    print(f"   ✗ venv Python 不存在")

# 2. 检查 8000 端口占用
print("\n2. 端口检查")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    if result == 0:
        print("   ✗ 端口 8000 已被占用")
    else:
        print("   ✓ 端口 8000 未被占用")
except Exception as e:
    print(f"   ⚠ 检查端口时出错: {e}")

# 3. 检查代理环境变量
print("\n3. 代理环境变量检查")
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy', 'ALL_PROXY', 'all_proxy']
for var in proxy_vars:
    val = os.environ.get(var)
    if val:
        print(f"   {var}={val}")
if not any(os.environ.get(var) for var in proxy_vars):
    print("   ✓ 未检测到代理设置")

# 4. 检查依赖
print("\n4. 依赖检查")
deps = ['fastapi', 'uvicorn', 'sqlalchemy']
for dep in deps:
    try:
        __import__(dep)
        print(f"   ✓ {dep} 已安装")
    except ImportError:
        print(f"   ✗ {dep} 未安装")

# 5. 尝试导入 backend.main
print("\n5. 项目导入检查")
try:
    # 添加项目根目录到 Python 路径
    project_root = Path(r"C:\Users\zhangmohan\Desktop\信息系统")
    sys.path.insert(0, str(project_root))
    
    import backend.main
    print("   ✓ backend.main 导入成功")
except Exception as e:
    print(f"   ✗ backend.main 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
