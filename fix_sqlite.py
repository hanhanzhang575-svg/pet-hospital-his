#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SQLite DLL 加载错误修复脚本
执行虚拟环境的重新创建和依赖安装
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """运行命令并报告结果"""
    print(f"\n{'='*50}")
    print(f"{description}")
    print(f"{'='*50}")
    print(f"执行: {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        # 输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # 检查结果
        if result.returncode == 0:
            print(f"✓ {description} - 成功")
            return True
        else:
            print(f"✗ {description} - 失败 (返回码: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - 超时")
        return False
    except Exception as e:
        print(f"✗ {description} - 错误: {e}")
        return False

def main():
    # 改变工作目录
    target_dir = r"C:\Users\zhangmohan\Desktop\信息系统"
    os.chdir(target_dir)
    print(f"工作目录: {os.getcwd()}\n")
    
    steps = [
        (
            'if exist .venv rmdir .venv /s /q',
            '【步骤1】删除旧的虚拟环境'
        ),
        (
            'python -m venv .venv',
            '【步骤2】创建新的虚拟环境'
        ),
        (
            '.venv\\Scripts\\activate.bat && python -m pip install --upgrade pip',
            '【步骤3和4】激活虚拟环境并升级 pip'
        ),
        (
            '.venv\\Scripts\\activate.bat && pip install -r backend\\requirements.txt',
            '【步骤5】安装所有依赖'
        ),
        (
            '.venv\\Scripts\\activate.bat && python -c "import sqlite3; print(\'SQLite3 OK\')"',
            '【步骤6】验证 sqlite3 是否可以加载'
        ),
        (
            '.venv\\Scripts\\activate.bat && python -c "import backend.main; print(\'IMPORT_OK\')"',
            '【步骤7】验证后端模块导入'
        ),
    ]
    
    print("\n" + "="*50)
    print("SQLite DLL 加载错误修复脚本")
    print("="*50)
    
    results = []
    for cmd, desc in steps:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    # 最终报告
    print("\n" + "="*70)
    print("执行结果总结")
    print("="*70)
    
    for desc, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{status} - {desc}")
    
    all_success = all(success for _, success in results)
    
    print("="*70)
    if all_success:
        print("\n✓ 所有步骤执行成功！")
        return 0
    else:
        print("\n✗ 某些步骤执行失败，请检查上面的错误信息。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
