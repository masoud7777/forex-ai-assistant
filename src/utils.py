"""
توابع کمکی عمومی
"""

import ctypes
import sys
from pathlib import Path
from src.logger import app_logger

def set_process_dpi_aware() -> bool:
    """
    تنظیم DPI-Aware بودن فرآیند برای نمایش صحیح در مانیتورهای با مقیاس بالا
    بازگشت True در صورت موفقیت
    """
    try:
        if sys.platform == "win32":
            # Windows 10/11 DPI awareness
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            app_logger.info("DPI-Awareness تنظیم شد")
            return True
        return False
    except Exception as e:
        app_logger.warning(f"تنظیم DPI-Awareness ناموفق: {e}")
        return False

def get_project_root() -> Path:
    """دریافت مسیر ریشه‌ی پروژه"""
    return Path(__file__).parent.parent

def ensure_directories() -> None:
    """ایجاد پوشه‌های مورد نیاز پروژه"""
    root = get_project_root()
    dirs = [
        root / "data" / "history",
        root / "data" / "cache",
        root / "logs",
        root / "config",
        root / "assets" / "icons"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    app_logger.info("پوشه‌های مورد نیاز ایجاد شدند")

def get_platform() -> str:
    """دریافت نام پلتفرم فعلی"""
    import platform
    return platform.system()
