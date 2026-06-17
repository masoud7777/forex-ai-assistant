"""
کلاینت مدل آنلاین Anthropic (Claude)
"""

import json
import base64
from typing import Optional, List, Dict, Any
from src.models.base import BaseModelClient, ModelInfo
from src.key_store import KeyStore
from src.exceptions import ModelConnectionError, ModelTimeoutError, APIKeyMissingError
from src.logger import app_logger

class AnthropicClient(BaseModelClient):
    """کلاینت برای مدل‌های Claude آنتروپیک"""
    
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
        """ارسال تصویر به Claude برای تحلیل"""
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # ساخت محتوای درخواست
            content = []
            
            # اضافه کردن context اگر وجود دارد
            if context:
                for msg in context:
                    role = msg.get("role", "user")
                    if role == "assistant":
                        role = "assistant"
                    else:
                        role = "user"
                    content.append({
                        "role": role,
                        "content": [{"type": "text", "text": msg.get("content", "")}]
                    })
            
            # اضافه کردن تصویر و پرامپت جدید
            content.append({
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64
                    }},
                    {"type": "text", "text": prompt}
                ]
            })
            
            # ارسال درخواست
            response = client.messages.create(
                model=self.model_name,
                max_tokens=512,
                temperature=0.1,
                messages=content
            )
            
            if not response.content:
                raise ModelConnectionError(
                    self.model_id,
                    "پاسخ خالی از مدل دریافت شد"
                )
            
            # استخراج JSON از پاسخ
            return self._extract_json(response.content[0].text)
            
        except ImportError:
            raise ModelConnectionError(
                self.model_id,
                "کتابخانه anthropic نصب نیست. pip install anthropic"
            )
        except Exception as e:
            if "timeout" in str(e).lower():
                raise ModelTimeoutError(self.model_id, self.timeout)
            raise ModelConnectionError(self.model_id, str(e))
    
    def test_connection(self) -> bool:
        """تست اتصال به Anthropic API"""
        try:
            import anthropic
            
            if not self.api_key:
                return False
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # یک درخواست ساده برای تست
            response = client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "سلام"}]
            )
            
            return bool(response.content)
            
        except Exception as e:
            app_logger.error(f"Anthropic test connection failed: {e}")
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
