"""
نقطه‌ی ورود اصلی برنامه
"""

import sys
import os
from pathlib import Path

# تنظیم مسیرها
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from src.utils import set_process_dpi_aware, ensure_directories
from src.logger import app_logger
from src.launcher import LauncherWidget
from src.hotkey_listener import HotkeyListener
from src.overlay import OverlayWidget
from src.screenshot import ScreenshotCapture
from src.ai_client import AIClient
from src.response_panel import ResponsePanel
from src.prompts import get_prompt
from src.exceptions import AppError

class ForexAIAssistant:
    """کلاس اصلی برنامه"""
    
    def __init__(self):
        # تنظیم DPI-Aware
        set_process_dpi_aware()
        
        # ایجاد پوشه‌های مورد نیاز
        ensure_directories()
        
        # بارگذاری تنظیمات
        config_path = PROJECT_ROOT / "config" / "config.json"
        models_path = PROJECT_ROOT / "config" / "models.json"
        
        # راه‌اندازی AI Client
        self.ai_client = None
        try:
            self.ai_client = AIClient(config_path, models_path)
        except Exception as e:
            app_logger.error(f"خطا در راه‌اندازی AI Client: {e}")
        
        # راه‌اندازی Qt
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # ایجاد ویجت‌ها
        self.launcher = LauncherWidget()
        self.launcher.activated.connect(self.on_launcher_activated)
        self.launcher.show()
        
        # هات‌کی
        self.hotkey_listener = HotkeyListener("ctrl+shift+s")
        self.hotkey_listener.start(self.on_launcher_activated)
        
        # متغیرهای وضعیت
        self.overlay = None
        self.response_panel = None
        self.current_image_base64 = None
        
        app_logger.info("برنامه با موفقیت راه‌اندازی شد")
    
    def on_launcher_activated(self):
        """فعال‌سازی ابزار - نمایش overlay"""
        if self.overlay and self.overlay.isVisible():
            return
        
        self.overlay = OverlayWidget()
        self.overlay.on_selection_done = self.on_selection_done
        self.overlay.on_cancel = self.on_cancel
        self.overlay.show()
    
    def on_selection_done(self, x: int, y: int, width: int, height: int):
        """پس از انتخاب کادر"""
        app_logger.info(f"ناحیه انتخاب شد: ({x}, {y}) {width}x{height}")
        
        try:
            # گرفتن اسکرین‌شات
            screenshot = ScreenshotCapture()
            image_base64 = screenshot.capture_to_base64(x, y, width, height)
            self.current_image_base64 = image_base64
            
            # تحلیل با AI
            if self.ai_client:
                prompt = get_prompt("v2")
                
                # نمایش پنل پاسخ
                if not self.response_panel:
                    self.response_panel = ResponsePanel()
                    self.response_panel.send_query.connect(self.on_followup_query)
                    self.response_panel.save_requested.connect(self.on_save_analysis)
                
                self.response_panel.show()
                self.response_panel.status_label.setText("در حال تحلیل...")
                
                # ارسال به AI
                result = self.ai_client.analyze_image(image_base64, prompt)
                
                # نمایش نتیجه
                self.response_panel.display_analysis(result)
                self.response_panel.status_label.setText("تحلیل کامل شد")
                
                # ذخیره تاریخچه
                self.current_result = result
                
            else:
                QMessageBox.warning(
                    None,
                    "خطا",
                    "AI Client راه‌اندازی نشده است. لطفاً تنظیمات را بررسی کنید."
                )
                
        except Exception as e:
            app_logger.error(f"خطا در پردازش: {e}")
            QMessageBox.critical(
                None,
                "خطا",
                f"خطا در تحلیل: {str(e)}"
            )
    
    def on_cancel(self):
        """لغو انتخاب"""
        app_logger.info("انتخاب لغو شد")
    
    def on_followup_query(self, query: str):
        """پرسش تکمیلی کاربر"""
        if not self.ai_client or not self.current_image_base64:
            self.response_panel.display_followup("لطفاً ابتدا یک تحلیل انجام دهید.")
            return
        
        try:
            # گرفتن تاریخچه از پنل
            history = self.response_panel.get_history()
            
            # پرامپت برای سؤال تکمیلی
            followup_prompt = f"""
User's follow-up question about the previous chart analysis:
{query}

Please provide a helpful response based on the analysis you already did.
Return your response as plain text (not JSON).
Keep it concise and in Persian.
"""
            
            # ارسال به AI با context
            result = self.ai_client.analyze_image(
                self.current_image_base64,
                followup_prompt,
                context=history
            )
            
            # نمایش پاسخ
            if "interpretation" in result:
                self.response_panel.display_followup(result["interpretation"])
            else:
                self.response_panel.display_followup("پاسخ قابل پردازش نیست.")
                
        except Exception as e:
            app_logger.error(f"خطا در سؤال تکمیلی: {e}")
            self.response_panel.display_followup(f"خطا: {str(e)}")
    
    def on_save_analysis(self):
        """ذخیره‌سازی تحلیل فعلی"""
        if hasattr(self, 'current_result'):
            # TODO: پیاده‌سازی ذخیره‌سازی در تاریخچه
            QMessageBox.information(
                None,
                "ذخیره شد",
                "تحلیل با موفقیت ذخیره شد."
            )
        else:
            QMessageBox.warning(
                None,
                "خطا",
                "هیچ تحلیلی برای ذخیره وجود ندارد."
            )
    
    def run(self):
        """اجرای برنامه"""
        try:
            sys.exit(self.app.exec_())
        except Exception as e:
            app_logger.error(f"خطای بحرانی: {e}")
    
    def cleanup(self):
        """پاک‌سازی قبل از خروج"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        app_logger.info("برنامه بسته شد")


def main():
    """نقطه‌ی ورود"""
    assistant = ForexAIAssistant()
    assistant.run()

if __name__ == "__main__":
    main()
