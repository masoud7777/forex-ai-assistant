"""
شنودگر هات‌کی سراسری با pynput
"""

from pynput import keyboard
from threading import Thread
from src.logger import app_logger

class HotkeyListener:
    """مدیریت هات‌کی‌های سراسری"""
    
    def __init__(self, hotkey: str = "ctrl+shift+s"):
        self.hotkey = hotkey
        self.keys_pressed = set()
        self.listener = None
        self.callback = None
        self._running = False
    
    def start(self, callback=None):
        """شروع شنود هات‌کی"""
        self.callback = callback
        
        def on_press(key):
            try:
                # ذخیره کلیدهای فشرده شده
                if hasattr(key, 'char') and key.char:
                    self.keys_pressed.add(key.char.lower())
                elif hasattr(key, 'name'):
                    self.keys_pressed.add(key.name)
                else:
                    self.keys_pressed.add(str(key))
                
                # بررسی ترکیب هات‌کی
                if self._check_hotkey():
                    app_logger.info(f"هات‌کی {self.hotkey} فعال شد")
                    if self.callback:
                        self.callback()
                    self.keys_pressed.clear()
                    
            except Exception as e:
                app_logger.error(f"خطا در پردازش کلید: {e}")
        
        def on_release(key):
            try:
                # حذف کلیدهای رها شده
                if hasattr(key, 'char') and key.char:
                    self.keys_pressed.discard(key.char.lower())
                elif hasattr(key, 'name'):
                    self.keys_pressed.discard(key.name)
                else:
                    self.keys_pressed.discard(str(key))
            except Exception:
                pass
        
        # اجرای شنودگر در یک ترد جداگانه
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._running = True
        self.listener.start()
        app_logger.info(f"شنودگر هات‌کی {self.hotkey} شروع شد")
    
    def _check_hotkey(self) -> bool:
        """بررسی اینکه ترکیب هات‌کی فعال شده است"""
        if not self.hotkey:
            return False
        
        expected = set(self.hotkey.lower().replace('+', ' ').split())
        
        # همه‌ی کلیدهای مورد انتظار باید فشرده شده باشند
        return expected.issubset(self.keys_pressed)
    
    def stop(self):
        """توقف شنودگر"""
        self._running = False
        if self.listener:
            self.listener.stop()
            app_logger.info("شنودگر هات‌کی متوقف شد")
