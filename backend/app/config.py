import os
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
TEMP_DIR = BASE_DIR / "temp"
BIN_DIR = BASE_DIR / "bin"

# Ensure directories exist
for folder in [UPLOADS_DIR, EXPORTS_DIR, TEMP_DIR, BIN_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# File settings
MAX_UPLOAD_SIZE_MB = 500
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}

# Whisper settings
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
SUPPORTED_MODELS = ["tiny", "base", "small", "medium"]

# Gemini AI settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# FFmpeg detection & setup
def setup_ffmpeg() -> str:
    """Ensure ffmpeg is in PATH and return its absolute path."""
    bin_ffmpeg = BIN_DIR / "ffmpeg.exe" if os.name == "nt" else BIN_DIR / "ffmpeg"
    
    # Check if already present in system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # If bin_ffmpeg exists, add to PATH and return
    if bin_ffmpeg.exists():
        os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"
        return str(bin_ffmpeg)

    # Copy from imageio_ffmpeg if available
    try:
        import imageio_ffmpeg
        img_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if img_exe and os.path.exists(img_exe):
            shutil.copy2(img_exe, bin_ffmpeg)
            os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"
            return str(bin_ffmpeg)
    except Exception as e:
        print(f"Warning copying imageio-ffmpeg: {e}")

    return "ffmpeg"

FFMPEG_EXE = setup_ffmpeg()
# Ensure PATH is updated
if os.path.exists(FFMPEG_EXE):
    exe_dir = str(Path(FFMPEG_EXE).parent)
    if exe_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{exe_dir}{os.pathsep}{os.environ.get('PATH', '')}"
