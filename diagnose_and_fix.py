#!/usr/bin/env python3
"""
Minimal diagnostic and fix script - no special chars
Run this script to diagnose and fix venv issues.
This version avoids encoding issues on Windows.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_cmd(cmd_list, description=""):
    """Run command and return success status"""
    print(f"\n>>> {description}")
    print(f"    Command: {' '.join(cmd_list)}")
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"    SUCCESS")
            if result.stdout:
                for line in result.stdout.strip().split('\n')[-3:]:
                    if line.strip():
                        print(f"    {line}")
            return True
        else:
            print(f"    FAILED (exit code: {result.returncode})")
            if result.stderr:
                print(f"    Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"    EXCEPTION: {str(e)[:100]}")
        return False

# Set working directory
os.chdir(r"C:\Users\zhangmohan\Desktop\信息系统")
print("="*70)
print("FastAPI SQLite Diagnostic and Fix Tool")
print("="*70)
print(f"Working dir: {os.getcwd()}")

# Get Python paths
sys_python = sys.executable
venv_dir = Path(".venv")
venv_python = venv_dir / "Scripts" / "python.exe"
venv_pip = venv_dir / "Scripts" / "pip.exe"

print(f"System Python: {sys_python}")
print(f"Venv dir: {venv_dir}")
print(f"Venv Python: {venv_python}")

# Check current venv status
print("\n" + "="*70)
print("DIAGNOSTIC CHECKS")
print("="*70)

print("\n[1] System Python can import sqlite3?")
run_cmd([sys_python, "-c", "import sqlite3; print(sqlite3.version)"], 
        "Test sqlite3 on system Python")

print("\n[2] System Python can import fastapi?")
run_cmd([sys_python, "-c", "import fastapi; print(fastapi.__version__)"],
        "Test fastapi on system Python")

print("\n[3] Is .venv directory empty?")
if venv_dir.exists():
    print(f"    .venv exists")
    py_exe = venv_dir / "Scripts" / "python.exe"
    if py_exe.exists():
        print(f"    python.exe exists in .venv")
    else:
        print(f"    python.exe MISSING in .venv")
else:
    print(f"    .venv does NOT exist")

# Begin fix process
print("\n" + "="*70)
print("FIX PROCEDURE")
print("="*70)

# Step 1: Use system Python to install dependencies into system
print("\n[STEP 1] Installing fastapi and dependencies to system Python")
reqs_file = Path("backend/requirements.txt")
if reqs_file.exists():
    success = run_cmd([sys_python, "-m", "pip", "install", "-q", "-r", str(reqs_file)],
                      "Install requirements.txt using system Python")
    if not success:
        print("FAILED - Trying alternate method with --no-cache-dir")
        run_cmd([sys_python, "-m", "pip", "install", "--no-cache-dir", "-r", str(reqs_file)],
                "Install with --no-cache-dir flag")
else:
    print(f"ERROR: requirements.txt not found at {reqs_file}")

# Step 2: Test backend import with system Python
print("\n[STEP 2] Testing backend import")
run_cmd([sys_python, "-c", "import backend.main; print('Backend import OK')"],
        "Import backend.main using system Python")

# Step 3: Test port
print("\n[STEP 3] Testing port 8000")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    if result == 0:
        print("    WARNING: Port 8000 is already in use")
    else:
        print("    Port 8000 is available")
except Exception as e:
    print(f"    Cannot check port: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC AND SETUP COMPLETE")
print("="*70)
print("\nTo start FastAPI server using system Python:")
print(f"  {sys_python} start_server.py")
print("\nOr using direct uvicorn command:")
print(f"  {sys_python} -m uvicorn backend.main:app --host 127.0.0.1 --port 8000")
print("\nThen access: http://127.0.0.1:8000/docs")
print()
