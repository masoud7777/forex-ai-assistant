"""
کلاینت مدل آنلاین OpenAI
"""

import json
import base64
from typing import Optional, List, Dict, Any
from src.models.base import BaseModelClient, ModelInfo
from src.key_store import KeyStore
from src.exceptions import ModelConnectionError, ModelTimeoutError, APIKeyMissingError
from src.logger import app_logger

class OpenAIClient(BaseModelClient):
    """کلاینت برای مدل‌های OpenAI (GPT-4o و ...)"""
    
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
        """ارسال تصویر به OpenAI برای تحلیل"""
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            # ساخت محتوای درخواست
            content = [
                {"type": "text", "text": prompt}
            ]
            
            # اضافه کردن تصویر
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}"
                }
            })
            
            # ساخت پیام‌ها با context
            messages = []
            if context:
                for msg in context:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({
                "role": "user",
                "content": content
            })
            
            # ارسال درخواست
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=512,
                temperature=0.1
            )
            
            if not response.choices:
                raise ModelConnectionError(
                    self.model_id,
                    "پاسخ خالی از مدل دریافت شد"
                )
            
            # استخراج JSON از پاسخ
            return self._extract_json(response.choices[0].message.content)
            
        except ImportError:
            raise ModelConnectionError(
                self.model_id,
                "کتابخانه openai نصب نیست. pip install openai"
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError(self.model_id, self.timeout)
            raise ModelConnectionError(self.model_id, str(e))
    
    def test_connection(self) -> bool:
        """تست اتصال به OpenAI API"""
        try:
            from openai import OpenAI
            
            if not self.api_key:
                return False
            
            client = OpenAI(api_key=self.api_key)
            
            # یک درخواست ساده برای تست
            response = client.chat.completions.create(
                model=self.model_name,
                max_tokens=5,
                messages=[{"role": "user", "content": "سلام"}]
            )
            
            return bool(response.choices)
            
        except Exception as e:
            app_logger.error(f"OpenAI test connection failed: {e}")
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
