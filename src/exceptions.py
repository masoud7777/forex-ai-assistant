"""
استثناهای سفارشی پروژه
همه از کلاس پایه AppError ارث‌بری می‌کنند
"""

class AppError(Exception):
    """کلاس پایه برای همه‌ی استثناهای پروژه"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ConfigError(AppError):
    """خطا در بارگذاری یا پردازش تنظیمات"""
    pass

class ModelNotFoundError(AppError):
    """مدل درخواستی در سیستم ثبت نشده است"""
    def __init__(self, model_name: str, details: dict = None):
        self.model_name = model_name
        super().__init__(
            message=f"مدل '{model_name}' یافت نشد",
            details=details
        )

class APIKeyMissingError(AppError):
    """کلید API برای مدل مورد نظر در سیستم ذخیره نشده است"""
    def __init__(self, model_name: str, details: dict = None):
        self.model_name = model_name
        super().__init__(
            message=f"کلید API برای مدل '{model_name}' تنظیم نشده است",
            details=details
        )

class HardwareInsufficientError(AppError):
    """سخت‌افزار برای اجرای مدل آفلاین کافی نیست"""
    def __init__(self, requirement: str, current: str, details: dict = None):
        self.requirement = requirement
        self.current = current
        super().__init__(
            message=f"سخت‌افزار کافی نیست. نیاز: {requirement} - موجود: {current}",
            details=details
        )

class ModelConnectionError(AppError):
    """خطا در اتصال به مدل (API یا سرور محلی)"""
    def __init__(self, model_name: str, cause: str = "", details: dict = None):
        self.model_name = model_name
        self.cause = cause
        super().__init__(
            message=f"خطا در اتصال به مدل '{model_name}': {cause}",
            details=details
        )

class ModelTimeoutError(ModelConnectionError):
    """زمان پاسخ‌دهی مدل بیش از حد مجاز شده است"""
    def __init__(self, model_name: str, timeout: int, details: dict = None):
        super().__init__(
            model_name=model_name,
            cause=f"زمان پاسخ‌دهی بیش از {timeout} ثانیه",
            details=details
        )

class ImageCaptureError(AppError):
    """خطا در گرفتن اسکرین‌شات یا پردازش تصویر"""
    pass

class HistoryError(AppError):
    """خطا در ذخیره یا بازیابی تاریخچه"""
    pass

class HardwareDetectionError(AppError):
    """خطا در تشخیص سخت‌افزار"""
    pass
