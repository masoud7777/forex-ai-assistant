"""
مدیریت تاریخچه‌ی تحلیل‌ها با ذخیره‌سازی لوکال
"""

import json
import base64
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from src.logger import app_logger
from src.exceptions import HistoryError

class HistoryManager:
    """مدیریت ذخیره، بازیابی و گزارش تاریخچه"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.history_dir = data_dir / "history"
        self.cache_dir = data_dir / "cache"
        self.index_file = self.history_dir / "index.json"
        
        # ایجاد پوشه‌ها
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # بارگذاری ایندکس
        self.index = self._load_index()
        app_logger.info(f"HistoryManager راه‌اندازی شد. تعداد تحلیل‌ها: {len(self.index)}")
    
    def _load_index(self) -> Dict[str, Any]:
        """بارگذاری فایل ایندکس"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                app_logger.warning("فایل ایندکس خراب است، ایندکس جدید ایجاد می‌شود")
                return {"entries": [], "last_cleanup": None}
        return {"entries": [], "last_cleanup": None}
    
    def _save_index(self) -> None:
        """ذخیره‌سازی فایل ایندکس"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"خطا در ذخیره‌سازی ایندکس: {e}")
    
    def add_entry(
        self,
        image_base64: str,
        result: Dict[str, Any],
        prompt_version: str,
        model_used: str
    ) -> str:
        """افزودن یک تحلیل جدید به تاریخچه"""
        try:
            # ایجاد شناسه‌ی یکتا
            entry_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # ذخیره‌سازی تصویر (تامبنیل)
            thumbnail_path = self.history_dir / f"{entry_id}_thumb.png"
            image_data = base64.b64decode(image_base64)
            with open(thumbnail_path, 'wb') as f:
                f.write(image_data)
            
            # ذخیره‌سازی نتیجه
            result_path = self.history_dir / f"{entry_id}_result.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # افزودن به ایندکس
            entry = {
                "id": entry_id,
                "timestamp": datetime.now().isoformat(),
                "thumbnail": str(thumbnail_path.name),
                "result_file": str(result_path.name),
                "prompt_version": prompt_version,
                "model_used": model_used,
                "trend": result.get("trend", "unknown"),
                "summary": result.get("interpretation", "")[:100]
            }
            
            self.index["entries"].append(entry)
            self._save_index()
            
            # پاک‌سازی خودکار (در صورت نیاز)
            self._auto_cleanup()
            
            app_logger.info(f"تحلیل جدید ذخیره شد: {entry_id}")
            return entry_id
            
        except Exception as e:
            app_logger.error(f"خطا در ذخیره‌سازی تاریخچه: {e}")
            raise HistoryError(f"خطا در ذخیره‌سازی تاریخچه: {e}")
    
    def get_entries(self, limit: Optional[int] = None) -> List[Dict]:
        """دریافت لیست تحلیل‌ها (با محدودیت اختیاری)"""
        entries = self.index.get("entries", [])
        # مرتب‌سازی بر اساس زمان (جدیدترین اول)
        entries = sorted(entries, key=lambda x: x["timestamp"], reverse=True)
        
        if limit and limit > 0:
            return entries[:limit]
        return entries
    
    def get_entry(self, entry_id: str) -> Optional[Dict]:
        """دریافت یک تحلیل خاص با شناسه"""
        for entry in self.index.get("entries", []):
            if entry["id"] == entry_id:
                # بارگذاری نتیجه کامل
                result_path = self.history_dir / entry["result_file"]
                if result_path.exists():
                    with open(result_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    entry["full_result"] = result
                return entry
        return None
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        """
        دریافت خلاصه‌ی روزانه
        Args:
            date: تاریخ به فرمت YYYY-MM-DD (اگر None باشد، امروز)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        entries = self.index.get("entries", [])
        daily_entries = []
        
        for entry in entries:
            entry_date = entry["timestamp"][:10]  # YYYY-MM-DD
            if entry_date == date:
                daily_entries.append(entry)
        
        # آمارگیری
        trends = {}
        for entry in daily_entries:
            trend = entry.get("trend", "unknown")
            trends[trend] = trends.get(trend, 0) + 1
        
        summary = {
            "date": date,
            "total_analyses": len(daily_entries),
            "trends": trends,
            "entries": daily_entries[:10]  # حداکثر 10 مورد
        }
        
        return summary
    
    def _auto_cleanup(self) -> None:
        """پاک‌سازی خودکار تاریخچه‌های قدیمی"""
        # هر 24 ساعت یک بار پاک‌سازی
        last_cleanup = self.index.get("last_cleanup")
        if last_cleanup:
            last_time = datetime.fromisoformat(last_cleanup)
            if datetime.now() - last_time < timedelta(hours=24):
                return
        
        # حذف تحلیل‌های قدیمی‌تر از 7 روز
        cutoff = datetime.now() - timedelta(days=7)
        entries_to_keep = []
        
        for entry in self.index.get("entries", []):
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time > cutoff:
                entries_to_keep.append(entry)
            else:
                # حذف فایل‌های مربوطه
                try:
                    thumb_path = self.history_dir / entry["thumbnail"]
                    if thumb_path.exists():
                        thumb_path.unlink()
                    result_path = self.history_dir / entry["result_file"]
                    if result_path.exists():
                        result_path.unlink()
                except Exception as e:
                    app_logger.warning(f"خطا در حذف فایل‌های قدیمی: {e}")
        
        self.index["entries"] = entries_to_keep
        self.index["last_cleanup"] = datetime.now().isoformat()
        self._save_index()
        
        app_logger.info(f"پاک‌سازی خودکار انجام شد. {len(entries_to_keep)} تحلیل باقی ماند.")
    
    def clear_cache(self, older_than_hours: int = 24) -> None:
        """پاک‌سازی کش قدیمی"""
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mod_time < cutoff:
                    cache_file.unlink()
                    app_logger.debug(f"کش حذف شد: {cache_file.name}")
            except Exception as e:
                app_logger.warning(f"خطا در حذف کش {cache_file}: {e}")
    
    def generate_report(self, start_date: str, end_date: str) -> Dict:
        """تولید گزارش بین دو تاریخ"""
        entries = self.index.get("entries", [])
        filtered = []
        
        for entry in entries:
            entry_date = entry["timestamp"][:10]
            if start_date <= entry_date <= end_date:
                filtered.append(entry)
        
        # تحلیل آماری
        total = len(filtered)
        if total == 0:
            return {"message": "هیچ تحلیلی در این بازه وجود ندارد"}
        
        trend_counts = {}
        model_counts = {}
        
        for entry in filtered:
            trend = entry.get("trend", "unknown")
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
            
            model = entry.get("model_used", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_analyses": total,
            "trend_distribution": trend_counts,
            "model_distribution": model_counts,
            "most_common_trend": max(trend_counts, key=trend_counts.get) if trend_counts else "none"
        }
