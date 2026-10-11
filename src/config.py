import os
import shutil
from pathlib import Path
import pytesseract

def get_tesseract_path() -> str:
    """Resolve the Tesseract OCR executable path with robust fallbacks."""
    # 1. Check explicit environment variable
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. Check system PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # 3. Known default installation paths
    default_candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    for candidate in default_candidates:
        if Path(candidate).is_file():
            return str(candidate)

    return "tesseract"

TESSERACT_CMD = get_tesseract_path()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
