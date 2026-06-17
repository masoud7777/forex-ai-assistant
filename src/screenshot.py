"""
گرفتن اسکرین‌شات از ناحیه‌ی انتخاب شده با mss
"""

import mss
import mss.tools
import base64
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple
from src.exceptions import ImageCaptureError
from src.logger import app_logger

class ScreenshotCapture:
    """گرفتن اسکرین‌شات از ناحیه‌ی انتخاب شده"""
    
    def __init__(self):
        self.sct = mss.mss()
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[bytes]:
        """
        گرفتن اسکرین‌شات از یک ناحیه‌ی مشخص
        
        Args:
            x, y: مختصات گوشه‌ی بالا-چپ
            width, height: ابعاد ناحیه
        
        Returns:
            داده‌های تصویر به‌صورت bytes یا None در صورت خطا
        """
        try:
            # اطمینان از معتبر بودن ابعاد
            if width <= 0 or height <= 0:
                raise ImageCaptureError("ابعاد ناحیه نامعتبر است")
            
            # گرفتن اسکرین‌شات
            monitor = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            screenshot = self.sct.grab(monitor)
            
            # تبدیل به bytes
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # ذخیره در حافظه
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            app_logger.info(f"اسکرین‌شات گرفته شد: {width}x{height} در ({x}, {y})")
            return buffer.getvalue()
            
        except Exception as e:
            app_logger.error(f"خطا در گرفتن اسکرین‌شات: {e}")
            raise ImageCaptureError(f"خطا در گرفتن اسکرین‌شات: {e}")
    
    def capture_to_base64(self, x: int, y: int, width: int, height: int) -> str:
        """
        گرفتن اسکرین‌شات و تبدیل به base64
        """
        image_data = self.capture_region(x, y, width, height)
        if image_data is None:
            raise ImageCaptureError("تصویر گرفته نشد")
        
        return base64.b64encode(image_data).decode('utf-8')
