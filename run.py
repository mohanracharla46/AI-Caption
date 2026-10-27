import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

import uvicorn
from app.config import FFMPEG_EXE, UPLOADS_DIR, EXPORTS_DIR, FRONTEND_DIR

def main():
    print("=" * 65)
    print("  [*] Tenglish Auto Caption Generator (Telugu -> English Script)")
    print("=" * 65)
    print(f"[*] Project Root    : {BASE_DIR}")
    print(f"[*] FFmpeg Binary   : {FFMPEG_EXE}")
    print(f"[*] Uploads Dir     : {UPLOADS_DIR}")
    print(f"[*] Exports Dir     : {EXPORTS_DIR}")
    print(f"[*] Frontend Static : {FRONTEND_DIR}")
    print("-" * 65)
    print("[+] Starting server at http://127.0.0.1:8000")
    print("    Open http://127.0.0.1:8000 in your web browser.")
    print("=" * 65)

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
