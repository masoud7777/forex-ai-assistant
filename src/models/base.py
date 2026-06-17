"""
کلاس پایه برای همه‌ی مدل‌های هوش مصنوعی (آنلاین و آفلاین)
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from src.exceptions import ModelConnectionError, ModelTimeoutError

@dataclass
class ModelInfo:
    """اطلاعات یک مدل"""
    id: str
    display_name: str
    model_name: str
    model_type: str  # "online" یا "offline"
    url: Optional[str] = None
    file_path: Optional[str] = None
    requires_key: bool = True
    
class BaseModelClient(ABC):
    """کلاس پایه‌ی انتزاعی برای همه‌ی کلاینت‌های مدل"""
    
    def __init__(self, model_info: ModelInfo):
        self.model_info = model_info
        self._is_available = None
    
    @abstractmethod
    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        تحلیل یک تصویر با مدل
        
        Returns:
            دیکشنری با فیلدهای:
            - trend: "bullish" | "bearish" | "neutral"
            - support: لیست قیمت‌های حمایت
            - resistance: لیست قیمت‌های مقاومت
            - candle_pattern: نام الگوی کندلی
            - interpretation: تفسیر متنی
            - disclaimer: متن هشدار حقوقی
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """تست اتصال به مدل"""
        pass
    
    def is_available(self) -> bool:
        if self._is_available is None:
            self._is_available = self.test_connection()
        return self._is_available
    
    def reset_availability(self) -> None:
        self._is_available = None
    
    @property
    def display_name(self) -> str:
        return self.model_info.display_name
    
    @property
    def model_id(self) -> str:
        return self.model_info.id
    
    @property
    def model_type(self) -> str:
        return self.model_info.model_type
