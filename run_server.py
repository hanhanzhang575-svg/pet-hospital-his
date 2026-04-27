
import sys
import os
from pathlib import Path

project_root = Path(r"C:\Users\zhangmohan\Desktop\信息系统")
sys.path.insert(0, str(project_root))
os.chdir(project_root)

print("\n[Server Starting]")
print(f"Python: {sys.version.split()[0]}")
print(f"Working Directory: {project_root}")

try:
    from backend.main import app
    print("[OK] App imported successfully")
    
    import uvicorn
    print("[OK] Starting uvicorn server...")
    print("[INFO] Server running at http://127.0.0.1:8000")
    print("[INFO] API Docs at http://127.0.0.1:8000/docs")
    print("[INFO] Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
