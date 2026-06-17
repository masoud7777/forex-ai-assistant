"""
Overlay شفاف برای انتخاب کادر
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from typing import Optional, Tuple

class OverlayWidget(QWidget):
    """پنجره‌ی شفاف برای انتخاب کادر با ماوس"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # حالت انتخاب
        self.is_selecting = False
        self.start_point = None
        self.end_point = None
        self.selection_rect = None
        
        # رنگ‌ها
        self.overlay_color = QColor(0, 0, 0, 100)  # نیمه‌شفاف
        self.selection_color = QColor(0, 150, 255, 50)
        self.border_color = QColor(0, 150, 255, 255)
        
        # حالت تمام‌صفحه
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selecting = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point)
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            
            # اگر ناحیه انتخاب شده معتبر است
            if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
                self.close()
                # سیگنال یا callback برای گرفتن اسکرین‌شات
                if hasattr(self, 'on_selection_done'):
                    self.on_selection_done(
                        self.selection_rect.x(),
                        self.selection_rect.y(),
                        self.selection_rect.width(),
                        self.selection_rect.height()
                    )
            else:
                # ناحیه خیلی کوچک است، لغو
                self.cancel_selection()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel_selection()
    
    def cancel_selection(self):
        """لغو انتخاب و بستن overlay"""
        self.is_selecting = False
        self.selection_rect = None
        if hasattr(self, 'on_cancel'):
            self.on_cancel()
        self.close()
    
    def paintEvent(self, event):
        """رسم overlay و کادر انتخاب"""
        painter = QPainter(self)
        
        # پس‌زمینه‌ی شفاف
        painter.fillRect(self.rect(), self.overlay_color)
        
        if self.selection_rect:
            # رسم ناحیه‌ی انتخاب
            painter.fillRect(self.selection_rect, self.selection_color)
            
            # رسم کادر
            pen = QPen(self.border_color, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)
            
            # نمایش ابعاد
            size_text = f"{self.selection_rect.width()} × {self.selection_rect.height()}"
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawText(
                self.selection_rect.x() + 8,
                self.selection_rect.y() + 20,
                size_text
            )
    
    def get_selection(self) -> Optional[Tuple[int, int, int, int]]:
        """دریافت مختصات ناحیه‌ی انتخاب شده"""
        if self.selection_rect:
            return (
                self.selection_rect.x(),
                self.selection_rect.y(),
                self.selection_rect.width(),
                self.selection_rect.height()
            )
        return None
