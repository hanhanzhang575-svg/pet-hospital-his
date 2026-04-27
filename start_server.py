#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Direct FastAPI server startup with Miniconda SQLite DLL fix"""
import sys
import os
from pathlib import Path

# CRITICAL FIX: Handle Miniconda SQLite DLL conflict
# By forcing Python to use venv's sqlite3 instead of Miniconda's
if 'miniconda' in sys.executable.lower():
    # We're in a Miniconda-based venv
    # Miniconda puts conflicting DLLs in the lib folder
    venv_lib = Path(sys.executable).parent.parent / "lib"
    miniconda_lib = Path(sys.executable).parent.parent.parent / "lib"
    
    # Temporarily modify PATH to prioritize venv over Miniconda
    pathvar = os.environ.get('PATH', '')
    venv_bin = str(Path(sys.executable).parent)
    os.environ['PATH'] = venv_bin + os.pathsep + pathvar

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 60)
print("FastAPI Server Startup")
print("=" * 60)
print(f"Project Root: {project_root}")
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")

# 1. Check dependencies
print("\nChecking dependencies...")
required_modules = ['fastapi', 'uvicorn', 'sqlalchemy']
optional_modules = ['apscheduler', 'networkx', 'chromadb', 'httpx']
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
        print(f"  [OK] {module}")
    except ImportError as e:
        print(f"  [FAIL] {module}: {e}")
        missing_modules.append(module)

if missing_modules:
    print(f"\n[ERROR] Missing required dependencies: {', '.join(missing_modules)}")
    print("Please run: pip install -r backend/requirements.txt")
    sys.exit(1)

print("\nOptional dependencies:")
for module in optional_modules:
    try:
        __import__(module)
        print(f"  [OK] {module}")
    except ImportError:
        print(f"  [SKIP] {module} (optional, some features may not work)")

# 2. Try importing main app
print("\nImporting application...")
try:
    from backend.main import app
    print("  [OK] backend.main imported successfully")
except Exception as e:
    print(f"  [FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Start service
print("\nStarting Uvicorn server...")
print("Access: http://127.0.0.1:8000/docs")
print("Press Ctrl+C to stop\n")

try:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
except Exception as e:
    print(f"[ERROR] Startup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
