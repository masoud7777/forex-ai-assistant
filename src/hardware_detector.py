"""
تشخیص سخت‌افزار برای تعیین قابلیت اجرای مدل‌های آفلاین
"""

import subprocess
import re
from typing import Dict, Any
from src.logger import app_logger

class HardwareDetector:
    """تشخیص GPU، VRAM و قابلیت سیستم برای اجرای مدل‌های محلی"""
    
    @staticmethod
    def detect() -> Dict[str, Any]:
        """تشخیص اطلاعات سخت‌افزاری سیستم"""
        result = {
            "has_gpu": False,
            "gpu_name": "نامشخص",
            "vram_gb": 0,
            "system_ram_gb": 0,
            "can_run_offline": False,
            "recommendation": "online"
        }
        
        try:
            import psutil
            # RAM سیستم
            mem = psutil.virtual_memory()
            result["system_ram_gb"] = round(mem.total / (1024**3), 1)
        except ImportError:
            app_logger.warning("psutil نصب نیست، RAM قابل تشخیص نیست")
        
        # تشخیص GPU با nvidia-smi
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                text=True,
                timeout=5
            )
            lines = output.strip().split('\n')
            if lines:
                parts = lines[0].split(',')
                if len(parts) >= 2:
                    result["has_gpu"] = True
                    result["gpu_name"] = parts[0].strip()
                    # استخراج VRAM
                    mem_match = re.search(r'(\d+)', parts[1])
                    if mem_match:
                        result["vram_gb"] = round(int(mem_match.group(1)) / 1024, 1)
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            app_logger.debug("nvidia-smi در دسترس نیست، احتمالاً GPU انویدیا وجود ندارد")
        
        # تشخیص با GPUtil (جایگزین)
        if not result["has_gpu"]:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    result["has_gpu"] = True
                    result["gpu_name"] = gpu.name
                    result["vram_gb"] = round(gpu.memoryTotal / 1024, 1)
            except ImportError:
                app_logger.debug("GPUtil نصب نیست")
            except Exception:
                pass
        
        # تعیین قابلیت اجرای مدل آفلاین
        if result["has_gpu"] and result["vram_gb"] >= 4:
            result["can_run_offline"] = True
            result["recommendation"] = "offline"
        elif result["system_ram_gb"] >= 16:
            result["can_run_offline"] = True
            result["recommendation"] = "offline (CPU mode)"
        else:
            result["recommendation"] = "online"
        
        app_logger.info(f"سخت‌افزار شناسایی شد: GPU={result['has_gpu']}, VRAM={result['vram_gb']}GB, RAM={result['system_ram_gb']}GB")
        app_logger.info(f"توصیه: {result['recommendation']}")
        
        return result
