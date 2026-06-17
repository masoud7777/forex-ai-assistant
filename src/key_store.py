"""
مدیریت امن کلیدهای API با استفاده از keyring
کلیدها در فضای امن ویندوز (Credential Manager) ذخیره می‌شوند
"""

import keyring
from typing import Optional
from src.exceptions import APIKeyMissingError

SERVICE_NAME = "forex_ai_assistant"

class KeyStore:
    """wrapper روی keyring برای ذخیره و بازیابی امن کلیدهای API"""
    
    @staticmethod
    def save_key(model_name: str, api_key: str) -> None:
        """ذخیره‌ی کلید API برای یک مدل خاص"""
        keyring.set_password(SERVICE_NAME, model_name, api_key)
    
    @staticmethod
    def get_key(model_name: str) -> Optional[str]:
        """بازیابی کلید API برای یک مدل خاص"""
        try:
            return keyring.get_password(SERVICE_NAME, model_name)
        except Exception:
            return None
    
    @staticmethod
    def get_key_or_raise(model_name: str) -> str:
        """بازیابی کلید API و در صورت نبود، استثنا پرتاب می‌کند"""
        key = KeyStore.get_key(model_name)
        if key is None:
            raise APIKeyMissingError(model_name)
        return key
    
    @staticmethod
    def delete_key(model_name: str) -> bool:
        """حذف کلید API برای یک مدل خاص"""
        try:
            keyring.delete_password(SERVICE_NAME, model_name)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
    
    @staticmethod
    def list_keys() -> list:
        """لیست تمام مدل‌هایی که کلید برای آنها ذخیره شده"""
        try:
            import win32cred
            credentials = win32cred.CredEnumerate(None, 0)
            keys = []
            for cred in credentials:
                if cred["TargetName"].startswith(SERVICE_NAME):
                    model_name = cred["TargetName"].replace(f"{SERVICE_NAME}/", "")
                    keys.append(model_name)
            return keys
        except Exception:
            return []
