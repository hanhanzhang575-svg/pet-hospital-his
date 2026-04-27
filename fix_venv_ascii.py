#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated fix script - rebuild venv and install dependencies
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Set working directory
target_dir = Path(r"C:\Users\zhangmohan\Desktop\信息系统")
os.chdir(target_dir)

print("\n" + "="*70)
print("FastAPI SQLite DLL Fix Script")
print("="*70)
print(f"Working directory: {os.getcwd()}\n")

venv_dir = target_dir / ".venv"
venv_python = venv_dir / "Scripts" / "python.exe"
venv_pip = venv_dir / "Scripts" / "pip.exe"

# Step 1: Delete old venv
print("\n[Step 1] Removing old virtual environment...")
if venv_dir.exists():
    try:
        shutil.rmtree(venv_dir)
        print("[OK] Old venv deleted")
    except Exception as e:
        print(f"[ERROR] Deletion failed: {e}")
        sys.exit(1)
else:
    print("[INFO] venv does not exist, skipping")

# Step 2: Create new venv
print("\n[Step 2] Creating new virtual environment...")
try:
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, timeout=60)
    print("[OK] venv created successfully")
except Exception as e:
    print(f"[ERROR] Creation failed: {e}")
    sys.exit(1)

# Step 3: Upgrade pip
print("\n[Step 3] Upgrading pip...")
try:
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
        timeout=120
    )
    print("[OK] pip upgraded")
except Exception as e:
    print(f"[ERROR] pip upgrade failed: {e}")
    sys.exit(1)

# Step 4: Install requirements
print("\n[Step 4] Installing dependencies from backend/requirements.txt...")
requirements_file = target_dir / "backend" / "requirements.txt"
if not requirements_file.exists():
    print(f"[ERROR] File not found: {requirements_file}")
    sys.exit(1)

try:
    result = subprocess.run(
        [str(venv_pip), "install", "-r", str(requirements_file)],
        check=True,
        timeout=300,
        capture_output=True,
        text=True
    )
    print("[OK] Dependencies installed successfully")
    # Show last few lines
    lines = result.stdout.split('\n')
    for line in lines[-10:]:
        if line.strip():
            print("   ", line)
except subprocess.CalledProcessError as e:
    print("[ERROR] Dependency installation failed")
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Installation error: {e}")
    sys.exit(1)

# Step 5: Verify sqlite3
print("\n[Step 5] Verifying sqlite3...")
try:
    result = subprocess.run(
        [str(venv_python), "-c", "import sqlite3; print('SQLite3 version:', sqlite3.version)"],
        check=True,
        timeout=30,
        capture_output=True,
        text=True
    )
    print("[OK] sqlite3 loaded successfully")
    print("   ", result.stdout.strip())
except subprocess.CalledProcessError as e:
    print("[ERROR] sqlite3 loading failed")
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Verification error: {e}")
    sys.exit(1)

# Step 6: Verify backend import
print("\n[Step 6] Verifying backend.main import...")
try:
    result = subprocess.run(
        [str(venv_python), "-c", "import backend.main; print('Backend module imported successfully!')"],
        check=True,
        timeout=30,
        capture_output=True,
        text=True,
        cwd=str(target_dir)
    )
    print("[OK] Backend module imported successfully")
    print("   ", result.stdout.strip())
except subprocess.CalledProcessError as e:
    print("[ERROR] Backend import failed")
    print(e.stderr)
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Import verification error: {e}")
    sys.exit(1)

# Complete
print("\n" + "="*70)
print("[SUCCESS] All steps completed successfully!")
print("="*70)
print("\nNow you can start the FastAPI service:")
print(f"  python start_server.py")
print(f"\nOr using venv Python:")
print(f"  {venv_python} start_server.py")
print("\nAccess the API at: http://127.0.0.1:8000/docs")
print()
