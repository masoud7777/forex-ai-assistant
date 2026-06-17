"""
سیستم لاگ‌نویسی یکپارچه
لاگ‌ها در پوشه‌ی logs/ ریشه‌ی پروژه ذخیره می‌شوند
"""

import logging
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"

def setup_logger(name: str = "forex_ai") -> logging.Logger:
    """تنظیم و بازگرداندن یک logger پیکربندی‌شده"""
    LOG_DIR.mkdir(exist_ok=True)
    
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

app_logger = setup_logger("forex_ai")

def get_logger(name: str) -> logging.Logger:
    """دریافت logger با نام دلخواه"""
    return setup_logger(name)
