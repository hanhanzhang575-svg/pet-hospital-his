#!/usr/bin/env python
"""
Quick FastAPI startup script - Uses system Python to run uvicorn
"""
import subprocess
import sys
import os
from pathlib import Path

os.chdir(r"C:\Users\zhangmohan\Desktop\信息系统")

print("\n" + "="*70)
print("FastAPI Server Quick Start")
print("="*70)
print(f"Python: {sys.executable}")
print(f"Working dir: {os.getcwd()}")

print("\nStep 1: Verify fastapi is installed...")
try:
    import fastapi
    print(f"  OK - fastapi {fastapi.__version__}")
except ImportError:
    print("  ERROR - fastapi not installed")
    print("  Installing fastapi and uvicorn...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastapi", "uvicorn"], check=False)

print("\nStep 2: Verify backend can be imported...")
try:
    import backend.main
    print("  OK - backend.main imported")
except ImportError as e:
    print(f"  ERROR - {e}")
    sys.exit(1)

print("\nStep 3: Starting uvicorn server...")
print("  Access: http://127.0.0.1:8000/docs")
print("  Press Ctrl+C to stop\n")

try:
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ], cwd=os.getcwd())
except KeyboardInterrupt:
    print("\nServer stopped.")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
