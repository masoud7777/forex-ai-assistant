"""
پنل تنظیمات عمومی برنامه
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QGroupBox,
    QCheckBox, QSpinBox, QTabWidget, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.logger import app_logger

class SettingsPanel(QWidget):
    """پنل تنظیمات عمومی (فاز سه تکمیل می‌شود)"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # پیام موقت
        label = QLabel("⚙️ پنل تنظیمات - در حال توسعه")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; padding: 50px;")
        layout.addWidget(label)
        
        app_logger.info("SettingsPanel ایجاد شد (نسخه‌ی موقت)")
