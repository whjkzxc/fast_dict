# -*- coding: utf-8 -*-
"""搜索输入框组件"""
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QMouseEvent, QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QPushButton
)


class SearchWidget(QWidget):
    """搜索输入框组件"""

    # 信号：用户确认查询（回车）
    search_confirmed = pyqtSignal(str)
    # 信号：窗口位置改变
    position_changed = pyqtSignal(int, int)

    def __init__(self, fuzzy_matcher=None):
        super().__init__()
        self.fuzzy_matcher = fuzzy_matcher
        self.word_list = set(fuzzy_matcher.word_list) if fuzzy_matcher else set()

        # 拖动相关变量
        self._drag_position = QPoint()
        self._is_dragging = False

        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主容器（包含拖动手柄和输入框）
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 2px solid #3498db;
            }
        """)

        # 给主容器添加阴影效果
        main_shadow = QGraphicsDropShadowEffect()
        main_shadow.setBlurRadius(16)
        main_shadow.setColor(QColor(0, 0, 0, 60))
        main_shadow.setOffset(0, 4)
        main_container.setGraphicsEffect(main_shadow)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 拖动手柄（顶部区域）
        self.drag_handle = QWidget()
        self.drag_handle.setFixedHeight(12)
        self.drag_handle.setCursor(Qt.OpenHandCursor)
        self.drag_handle.setStyleSheet("""
            QWidget {
                background-color: #3498db;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QWidget:hover {
                background-color: #2980b9;
            }
        """)

        # 输入框容器（包含输入框和清除按钮）
        input_container = QWidget()
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 6, 10, 6)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setMaxLength(50)
        self.input_field.setPlaceholderText("输入单词...")
        self.input_field.setFont(QFont("Arial", 13))
        self.input_field.setTextMargins(8, 0, 8, 0)
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #2c3e50;
                selection-background-color: #3498db;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.input_field.setCursor(Qt.IBeamCursor)

        self.input_field.setFixedWidth(240)
        self.input_field.setFixedHeight(28)  # 刚好容纳一个单词的高度

        self.input_field.textChanged.connect(self.on_text_changed)
        self.input_field.returnPressed.connect(self.on_return_pressed)

        # 清除按钮
        self.clear_button = ClearButton()
        self.clear_button.setFixedSize(22, 22)
        self.clear_button.clicked.connect(self.clear_input)
        self.clear_button.setVisible(False)  # 有内容时才显示

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.clear_button)

        input_container.setLayout(input_layout)

        main_layout.addWidget(self.drag_handle)
        main_layout.addWidget(input_container)
        main_container.setLayout(main_layout)

        layout.addWidget(main_container)
        self.setLayout(layout)

    def on_text_changed(self, text: str):
        """输入文本变化 - 控制清除按钮显示"""
        self.clear_button.setVisible(bool(text.strip()))

    def on_return_pressed(self):
        """回车键"""
        text = self.input_field.text().strip()
        if text:
            self.search_confirmed.emit(text.lower())

    def clear_input(self):
        """清除输入框内容"""
        self.input_field.clear()
        self.input_field.setFocus()

    def keyPressEvent(self, event):
        """按键事件 - ESC清除输入框内容"""
        if event.key() == Qt.Key_Escape:
            if self.input_field.text().strip():
                # 有内容时清除内容
                self.clear_input()
                event.accept()
            # 无内容时不做处理（父类会正常处理）
        else:
            super().keyPressEvent(event)

    def popup(self, screen_pos=None):
        """弹出搜索框"""
        print(f"[DEBUG] SearchWidget.popup 被调用, screen_pos={screen_pos}")
        self.input_field.clear()
        self.clear_button.setVisible(False)

        if screen_pos:
            self.move(screen_pos)
            print(f"[DEBUG] 移动到: ({screen_pos.x()}, {screen_pos.y()})")
        else:
            # 默认屏幕中心
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                x = (geo.width() - self.width()) // 2
                y = (geo.height() - self.height()) // 3
                self.move(x, y)

        self.show()
        self.activateWindow()
        self.input_field.setFocus()
        print(f"[DEBUG] popup 完成, visible={self.isVisible()}")

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 开始拖动"""
        if event.button() == Qt.LeftButton:
            # 检查是否在拖动手柄区域
            handle_pos = self.drag_handle.mapFromGlobal(event.globalPos())
            if self.drag_handle.rect().contains(handle_pos):
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self._is_dragging = True
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 执行拖动"""
        if event.buttons() == Qt.LeftButton and self._is_dragging:
            # 移动窗口
            new_pos = event.globalPos() - self._drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件 - 结束拖动并发送位置信号"""
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            # 发送位置变化信号
            self.position_changed.emit(self.x(), self.y())
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class ClearButton(QWidget):
    """清除按钮 - X图标"""

    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        """绘制X图标"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆形背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#e0e0e0"))
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)

        # 绘制X
        painter.setPen(QPen(QColor("#757575"), 2))
        center = self.width() // 2
        offset = 4
        painter.drawLine(center - offset, center - offset, center + offset, center + offset)
        painter.drawLine(center + offset, center - offset, center - offset, center + offset)

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        """鼠标悬停"""
        self.update()

    def leaveEvent(self, event):
        """鼠标离开"""
        self.update()
