"""
کلاینت مدل آفلاین Ollama
"""

import base64
import json
import requests
from typing import Optional, List, Dict, Any
from src.models.base import BaseModelClient, ModelInfo
from src.exceptions import ModelConnectionError, ModelTimeoutError
from src.logger import app_logger

class OllamaClient(BaseModelClient):
    """کلاینت برای مدل‌های Ollama (آفلاین)"""
    
    def __init__(self, model_info: ModelInfo):
        super().__init__(model_info)
        self.url = model_info.url or "http://localhost:11434"
        self.model_name = model_info.model_name
        self.timeout = 60  # ثانیه
    
    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """ارسال تصویر به Ollama برای تحلیل"""
        
        # ساخت پیام با context
        messages = []
        if context:
            messages.extend(context)
        
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_base64]
        })
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 512
            }
        }
        
        try:
            response = requests.post(
                f"{self.url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            # استخراج JSON از پاسخ
            return self._extract_json(content)
            
        except requests.exceptions.Timeout:
            raise ModelTimeoutError(self.model_id, self.timeout)
        except requests.exceptions.ConnectionError:
            raise ModelConnectionError(
                self.model_id,
                "سرور Ollama در دسترس نیست. آیا Ollama در حال اجراست؟"
            )
        except requests.exceptions.RequestException as e:
            raise ModelConnectionError(self.model_id, str(e))
    
    def test_connection(self) -> bool:
        """تست اتصال به سرور Ollama"""
        try:
            response = requests.get(
                f"{self.url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                # بررسی اینکه مدل مورد نظر وجود دارد
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == self.model_name:
                        return True
                app_logger.warning(f"مدل {self.model_name} در Ollama یافت نشد")
                return False
            return False
        except Exception:
            return False
    
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """استخراج JSON از پاسخ مدل"""
        try:
            # پیدا کردن JSON در متن
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                data = json.loads(json_str)
                
                # اطمینان از وجود فیلدهای مورد نیاز
                required_fields = ["trend", "support", "resistance", "interpretation"]
                for field in required_fields:
                    if field not in data:
                        data[field] = "نامشخص"
                
                # اضافه کردن disclaimer اگر نبود
                if "disclaimer" not in data:
                    data["disclaimer"] = "این تحلیل توصیه‌ی مالی نیست و صرفاً جنبه‌ی آموزشی دارد."
                
                return data
            else:
                # اگر JSON پیدا نشد، یک پاسخ پیش‌فرض برگردان
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
