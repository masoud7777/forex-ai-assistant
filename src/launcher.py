"""
آیکون شناور کنار صفحه برای فعال‌سازی ابزار
"""

from PyQt5.QtWidgets import QWidget, QApplication, QLabel
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from src.overlay import OverlayWidget
from src.logger import app_logger

class LauncherWidget(QWidget):
    """آیکون شناور دایره‌ای کنار صفحه"""
    
    activated = pyqtSignal()  # سیگنال فعال‌سازی
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(48, 48)
        
        # موقعیت پیش‌فرض (کنار راست صفحه)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 70, screen.height() // 2 - 24)
        
        # رنگ‌ها
        self.bg_color = QColor(30, 144, 255)  # آبی
        self.hover_color = QColor(70, 184, 255)  # آبی روشن‌تر
        
        self.is_hovered = False
        self.is_dragging = False
        self.drag_position = None
        
        # ایجاد آیکون (می‌توانید از یک تصویر استفاده کنید)
        self.setToolTip("Forex AI Assistant (Ctrl+Shift+S)")
        
        app_logger.info("Launcher ایجاد شد")
    
    def paintEvent(self, event):
        """رسم آیکون دایره‌ای"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # دایره
        color = self.hover_color if self.is_hovered else self.bg_color
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(2, 2, 44, 44)
        
        # متن یا آیکون داخلی
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignCenter, "AI")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            # اگر درگ نبود، فعال‌سازی
            if self.drag_position and (event.globalPos() - self.drag_position).manhattanLength() < 10:
                self.activate()
    
    def mouseDoubleClickEvent(self, event):
        """کلیک دوبل برای فعال‌سازی"""
        if event.button() == Qt.LeftButton:
            self.activate()
    
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
    
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
    
    def activate(self):
        """فعال‌سازی ابزار (نمایش overlay)"""
        app_logger.info("Launcher فعال شد")
        self.activated.emit()
    
    def show_overlay(self):
        """نمایش overlay برای انتخاب کادر"""
        self.overlay = OverlayWidget()
        self.overlay.show()
        # اتصال رویدادهای overlay
        self.overlay.on_selection_done = self.on_selection_done
        self.overlay.on_cancel = self.on_cancel
    
    def on_selection_done(self, x, y, width, height):
        """پس از انتخاب کادر"""
        app_logger.info(f"ناحیه انتخاب شد: ({x}, {y}) {width}x{height}")
        # اینجا باید Screenshot گرفته شود و به AI ارسال شود
        # توسط main.py مدیریت می‌شود
        pass
    
    def on_cancel(self):
        """لغو انتخاب"""
        app_logger.info("انتخاب لغو شد")
