"""
لایه‌ی انتزاعی اصلی AI Client
مدیریت مدل‌های فعال، fallback و انتخاب خودکار
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.exceptions import (
    ModelNotFoundError,
    ModelConnectionError,
    ConfigError,
    HardwareInsufficientError
)
from src.models import BaseModelClient, ModelInfo
from src.models import (
    OllamaClient,
    GeminiClient,
    OpenAIClient,
    AnthropicClient
)
from src.key_store import KeyStore
from src.logger import app_logger
from src.hardware_detector import HardwareDetector

class AIClient:
    """کلاینت اصلی هوش مصنوعی - مدیریت انتخاب مدل، fallback و کش"""
    
    MODEL_CLASSES = {
        "ollama": OllamaClient,
        "gemini": GeminiClient,
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
    }
    
    def __init__(self, config_path: Path, models_path: Path):
        self.config_path = config_path
        self.models_path = models_path
        self.config = {}
        self.models_config = {}
        self.models: Dict[str, BaseModelClient] = {}
        self.online_models: List[str] = []
        self.offline_models: List[str] = []
        
        self._load_config()
        self._load_models_config()
        self._initialize_models()
        
        app_logger.info(f"AI Client راه‌اندازی شد. حالت: {self.config.get('model_mode', 'auto')}")
    
    def _load_config(self) -> None:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise ConfigError("فایل config.json یافت نشد")
        except json.JSONDecodeError as e:
            raise ConfigError(f"خطا در parsing config.json: {e}")
    
    def _load_models_config(self) -> None:
        try:
            with open(self.models_path, 'r', encoding='utf-8') as f:
                self.models_config = json.load(f)
        except FileNotFoundError:
            self._create_default_models_config()
        except json.JSONDecodeError as e:
            raise ConfigError(f"خطا در parsing models.json: {e}")
    
    def _create_default_models_config(self) -> None:
        default_config = {
            "online_models": {
                "gemini": {
                    "display_name": "Gemini 3.5 Flash",
                    "model_name": "gemini-3.5-flash",
                    "type": "gemini",
                    "requires_key": True
                },
                "anthropic": {
                    "display_name": "Claude 4.6 Sonnet",
                    "model_name": "claude-4.6-sonnet",
                    "type": "anthropic",
                    "requires_key": True
                }
            },
            "offline_models": {
                "llama_vision": {
                    "display_name": "Llama 3.2 Vision",
                    "model_name": "llama3.2-vision",
                    "type": "ollama",
                    "url": "http://localhost:11434",
                    "requires_key": False
                }
            },
            "active_online": "gemini",
            "active_offline": "llama_vision"
        }
        
        self.models_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.models_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        self.models_config = default_config
        app_logger.info("فایل models.json پیش‌فرض ایجاد شد")
    
    def _initialize_models(self) -> None:
        for model_id, model_data in self.models_config.get("online_models", {}).items():
            model_info = ModelInfo(
                id=model_id,
                display_name=model_data.get("display_name", model_id),
                model_name=model_data.get("model_name", model_id),
                model_type="online",
                url=model_data.get("url"),
                requires_key=model_data.get("requires_key", True)
            )
            self._register_model(model_id, model_info, model_data.get("type"))
            self.online_models.append(model_id)
        
        for model_id, model_data in self.models_config.get("offline_models", {}).items():
            model_info = ModelInfo(
                id=model_id,
                display_name=model_data.get("display_name", model_id),
                model_name=model_data.get("model_name", model_id),
                model_type="offline",
                url=model_data.get("url"),
                file_path=model_data.get("file_path"),
                requires_key=model_data.get("requires_key", False)
            )
            self._register_model(model_id, model_info, model_data.get("type"))
            self.offline_models.append(model_id)
    
    def _register_model(self, model_id: str, model_info: ModelInfo, model_type: str) -> None:
        if model_type not in self.MODEL_CLASSES:
            app_logger.warning(f"نوع مدل ناشناخته: {model_type} برای {model_id}")
            return
        
        model_class = self.MODEL_CLASSES[model_type]
        
        try:
            self.models[model_id] = model_class(model_info)
            app_logger.info(f"مدل {model_id} با موفقیت ثبت شد")
        except Exception as e:
            app_logger.error(f"خطا در ثبت مدل {model_id}: {e}")
    
    def _get_active_models(self) -> List[str]:
        mode = self.config.get("model_mode", "auto")
        
        if mode == "always_online":
            active_id = self.models_config.get("active_online")
            if active_id and active_id in self.models:
                return [active_id]
            if self.online_models:
                return [self.online_models[0]]
            return []
        
        elif mode == "always_offline":
            active_id = self.models_config.get("active_offline")
            if active_id and active_id in self.models:
                return [active_id]
            if self.offline_models:
                return [self.offline_models[0]]
            return []
        
        else:  # "auto"
            hw_info = HardwareDetector.detect()
            
            if hw_info.get("can_run_offline", False):
                active_id = self.models_config.get("active_offline")
                if active_id and active_id in self.models:
                    return [active_id]
                if self.offline_models:
                    return [self.offline_models[0]]
            
            active_id = self.models_config.get("active_online")
            if active_id and active_id in self.models:
                return [active_id]
            if self.online_models:
                return [self.online_models[0]]
            
            return []
    
    def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """تحلیل تصویر با مدل فعال (با پشتیبانی از fallback)"""
        active_models = self._get_active_models()
        
        if not active_models:
            raise ModelNotFoundError("هیچ مدل فعالی یافت نشد")
        
        last_error = None
        
        for model_id in active_models:
            if model_id not in self.models:
                continue
            
            client = self.models[model_id]
            
            try:
                app_logger.info(f"تحلیل با مدل: {model_id}")
                result = client.analyze_image(image_base64, prompt, context)
                result["model_used"] = model_id
                result["model_type"] = client.model_type
                app_logger.info(f"تحلیل با مدل {model_id} با موفقیت انجام شد")
                return result
                
            except Exception as e:
                last_error = e
                app_logger.warning(f"خطا در مدل {model_id}: {e}")
                continue
        
        raise ModelConnectionError(
            model_name=", ".join(active_models),
            cause=str(last_error) if last_error else "همه‌ی مدل‌ها در دسترس نیستند"
        )
    
    def get_available_models(self) -> Dict[str, List[Dict]]:
        result = {"online": [], "offline": []}
        
        for model_id, client in self.models.items():
            info = {
                "id": model_id,
                "display_name": client.display_name,
                "is_available": client.is_available(),
                "is_active": model_id in self._get_active_models()
            }
            
            if client.model_type == "online":
                result["online"].append(info)
            else:
                result["offline"].append(info)
        
        return result
