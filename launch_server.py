#!/usr/bin/env python3
"""
Detached process launcher - launches FastAPI server in background
Run this to start the server without blocking
"""
import subprocess
import sys
import os
import time

os.chdir(r"C:\Users\zhangmohan\Desktop\信息系统")

print("""
================================================================================
FastAPI Server Launcher
================================================================================
This script will:
1. Check Python and install dependencies
2. Start FastAPI server on http://127.0.0.1:8000
3. Exit (server runs in background)
================================================================================
""")

# First, quickly install dependencies
print("Installing dependencies...")
subprocess.Popen(
    [sys.executable, "-m", "pip", "install", "-q", "fastapi", "uvicorn", "sqlalchemy"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
).wait()

# Start the server in a detached process
print("Starting FastAPI server...")
print()

# Use subprocess.Popen with CREATE_NEW_CONSOLE (Windows) or start (Windows batch)
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_SHOW

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    startupinfo=startupinfo,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Give it a moment to start
time.sleep(2)

# Check if it's still running
if proc.poll() is None:
    print("✓ Server started successfully (PID: {})".format(proc.pid))
    print()
    print("Access the API at:")
    print("  http://127.0.0.1:8000/docs (Swagger UI)")
    print("  http://127.0.0.1:8000/api/v1 (API root)")
    print()
    print("Note: Server is running in the background")
    print("To stop: Open Task Manager and kill python.exe process")
else:
    print("✗ Server failed to start")
    _, stderr = proc.communicate()
    if stderr:
        print("Error:", stderr.decode())
    sys.exit(1)
