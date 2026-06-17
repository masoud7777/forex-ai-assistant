"""
پنل نمایش پاسخ با پشتیبانی از Markdown و سؤال تکمیلی
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLineEdit, QScrollArea, QFrame,
    QLabel, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

class ResponsePanel(QWidget):
    """پنل نمایش تحلیل و پاسخ‌های تکمیلی"""
    
    send_query = pyqtSignal(str)  # سیگنال ارسال سؤال تکمیلی
    save_requested = pyqtSignal()  # سیگنال ذخیره‌سازی
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint
        )
        self.setWindowTitle("Forex AI - تحلیل")
        self.resize(450, 550)
        
        self.init_ui()
        self.history = []  # تاریخچه‌ی مکالمه
        
        self.show()
    
    def init_ui(self):
        """رابط کاربری پنل"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # عنوان
        title = QLabel("🤖 تحلیل هوشمند فارکس")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        layout.addWidget(title)
        
        # ناحیه‌ی نمایش پاسخ (با Markdown)
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
        """)
        layout.addWidget(self.text_display, 1)
        
        # دکمه‌های پایین
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 ذخیره")
        self.save_btn.clicked.connect(self.save_requested.emit)
        btn_layout.addWidget(self.save_btn)
        
        self.copy_btn = QPushButton("📋 کپی")
        self.copy_btn.clicked.connect(self.copy_text)
        btn_layout.addWidget(self.copy_btn)
        
        self.close_btn = QPushButton("✕ بستن")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # خط جداکننده
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #3c3c3c; max-height: 1px;")
        layout.addWidget(line)
        
        # بخش سؤال تکمیلی
        query_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("سؤال تکمیلی بنویسید...")
        self.query_input.returnPressed.connect(self.send_query_clicked)
        query_layout.addWidget(self.query_input)
        
        self.send_btn = QPushButton("ارسال")
        self.send_btn.clicked.connect(self.send_query_clicked)
        query_layout.addWidget(self.send_btn)
        
        layout.addLayout(query_layout)
        
        # برچسب وضعیت
        self.status_label = QLabel("آماده")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_label)
    
    def display_analysis(self, data: dict):
        """نمایش تحلیل دریافتی"""
        # ساخت متن با فرمت Markdown
        text = self._format_analysis(data)
        self.text_display.setMarkdown(text)
        
        # اضافه کردن به تاریخچه
        self.history.append({
            "role": "assistant",
            "content": text
        })
        
        self.status_label.setText(f"تحلیل با مدل: {data.get('model_used', 'نامشخص')}")
    
    def _format_analysis(self, data: dict) -> str:
        """فرمت‌سازی تحلیل به Markdown"""
        trend_emoji = {
            "bullish": "📈",
            "bearish": "📉",
            "neutral": "➡️"
        }
        
        trend = data.get("trend", "neutral")
        emoji = trend_emoji.get(trend, "➡️")
        
        text = f"""
## {emoji} تحلیل چارت فارکس

**روند:** {trend.capitalize()}

**سطوح حمایت:**
{self._format_levels(data.get("support", []))}

**سطوح مقاومت:**
{self._format_levels(data.get("resistance", []))}

**الگوی کندلی:** {data.get("candle_pattern", "تشخیص داده نشد")}

**تفسیر:**
{data.get("interpretation", "تحلیل در دسترس نیست")}

---
⚠️ {data.get("disclaimer", "این تحلیل توصیه‌ی مالی نیست و صرفاً جنبه‌ی آموزشی دارد.")}
"""
        return text
    
    def _format_levels(self, levels: list) -> str:
        """فرمت‌سازی لیست سطوح"""
        if not levels:
            return "تشخیص داده نشد"
        return "\n".join([f"- {level}" for level in levels])
    
    def send_query_clicked(self):
        """ارسال سؤال تکمیلی"""
        query = self.query_input.text().strip()
        if not query:
            return
        
        # نمایش سؤال در متن
        self.text_display.append(f"\n\n**شما:** {query}")
        
        # افزودن به تاریخچه
        self.history.append({
            "role": "user",
            "content": query
        })
        
        # سیگنال به main
        self.send_query.emit(query)
        self.query_input.clear()
        self.status_label.setText("در حال پردازش...")
    
    def display_followup(self, response: str):
        """نمایش پاسخ به سؤال تکمیلی"""
        self.text_display.append(f"\n\n**دستیار:** {response}")
        self.history.append({
            "role": "assistant",
            "content": response
        })
        self.status_label.setText("آماده")
    
    def copy_text(self):
        """کپی متن به کلیپ‌بورد"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_display.toPlainText())
        self.status_label.setText("📋 کپی شد!")
    
    def get_history(self) -> list:
        """دریافت تاریخچه‌ی مکالمه"""
        return self.history.copy()
