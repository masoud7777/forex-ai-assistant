"""
کلاینت مدل آنلاین Gemini
"""

import json
from typing import Optional, List, Dict, Any
from src.models.base import BaseModelClient, ModelInfo
from src.key_store import KeyStore
from src.exceptions import ModelConnectionError, ModelTimeoutError, APIKeyMissingError
from src.logger import app_logger

class GeminiClient(BaseModelClient):
    """کلاینت برای مدل‌های Gemini گوگل"""
    
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
        self.model_name = model_info.model_name
        self.timeout = 30
        
        # دریافت کلید از key_store
        self.api_key = KeyStore.get_key(model_info.id)
        if not self.api_key and model_info.requires_key:
            raise APIKeyMissingError(model_info.id)
    
    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """ارسال تصویر به Gemini برای تحلیل"""
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            
            # ساخت محتوای درخواست
            contents = []
            
            # اضافه کردن context اگر وجود دارد
            if context:
                for msg in context:
                    contents.append({
                        "role": msg.get("role", "user"),
                        "parts": [{"text": msg.get("content", "")}]
                    })
            
            # اضافه کردن تصویر و پرامپت جدید
            contents.append({
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": "image/png",
                        "data": image_base64
                    }}
                ]
            })
            
            # ارسال درخواست
            response = model.generate_content(
                contents,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 512,
                }
            )
            
            if not response.text:
                raise ModelConnectionError(
                    self.model_id,
                    "پاسخ خالی از مدل دریافت شد"
                )
            
            # استخراج JSON از پاسخ
            return self._extract_json(response.text)
            
        except ImportError:
            raise ModelConnectionError(
                self.model_id,
                "کتابخانه google-generativeai نصب نیست. pip install google-generativeai"
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError(self.model_id, self.timeout)
            raise ModelConnectionError(self.model_id, str(e))
    
    def test_connection(self) -> bool:
        """تست اتصال به Gemini API"""
        try:
            import google.generativeai as genai
            
            if not self.api_key:
                return False
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            
            # یک درخواست ساده برای تست
            response = model.generate_content(
                "سلام",
                generation_config={"max_output_tokens": 10}
            )
            
            return bool(response.text)
            
        except Exception as e:
            app_logger.error(f"Gemini test connection failed: {e}")
            return False
    
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """استخراج JSON از پاسخ مدل"""
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                data = json.loads(json_str)
                
                required_fields = ["trend", "support", "resistance", "interpretation"]
                for field in required_fields:
                    if field not in data:
                        data[field] = "نامشخص"
                
                if "disclaimer" not in data:
                    data["disclaimer"] = "این تحلیل توصیه‌ی مالی نیست و صرفاً جنبه‌ی آموزشی دارد."
                
                return data
            else:
                return {
                    "trend": "neutral",
                    "support": [],
                    "resistance": [],
                    "candle_pattern": "نامشخص",
                    "interpretation": content[:200] if content else "تحلیل انجام نشد",
                    "disclaimer": "این تحلیل توصیه‌ی مالی نیست و صرفاً جنبه‌ی آموزشی دارد."
                }
        except json.JSONDecodeError:
            return {
                "trend": "neutral",
                "support": [],
                "resistance": [],
                "candle_pattern": "نامشخص",
                "interpretation": content[:200] if content else "خطا در پردازش پاسخ",
                "disclaimer": "این تحلیل توصیه‌ی مالی نیست و صرفاً جنبه‌ی آموزشی دارد."
            }
