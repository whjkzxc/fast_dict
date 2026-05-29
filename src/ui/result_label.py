# -*- coding: utf-8 -*-
"""单词释义展示标签"""
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QFrame, QScrollArea
from PyQt5.QtGui import QFont, QMouseEvent


class ResultLabel(QWidget):
    """词典释义展示窗口"""

    # 信号：窗口位置改变
    position_changed = pyqtSignal(int, int)
    # 信号：按下ESC键
    escape_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 拖动相关变量
        self._drag_position = QPoint()
        self._is_dragging = False
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)  # 允许接收键盘事件

        # 300x320 固定大小
        self.setFixedSize(300, 320)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主容器（包含拖动手柄和滚动区域）
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 拖动手柄（顶部区域）
        self.drag_handle = QWidget()
        self.drag_handle.setFixedHeight(12)
        self.drag_handle.setCursor(Qt.OpenHandCursor)
        self.drag_handle.setStyleSheet("""
            QWidget {
                background-color: #2ecc71;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QWidget:hover {
                background-color: #27ae60;
            }
        """)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea::verticalScrollBar {
                width: 10px;
                background: #ecf0f1;
                border-radius: 5px;
            }
            QScrollArea::verticalScrollBar::handle {
                background: #bdc3c7;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollArea::verticalScrollBar::handle:hover {
                background: #95a5a6;
            }
            QScrollArea::verticalScrollBar::add-line,
            QScrollArea::verticalScrollBar::sub-line {
                height: 0px;
            }
        """)

        # 内容标签
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setWordWrap(True)
        # 设置文本格式为自动识别（支持HTML）
        self.label.setTextFormat(Qt.AutoText)
        # 禁止打开外部链接
        self.label.setOpenExternalLinks(False)
        self.label.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 15px;
                padding-top: 10px;
                color: #2c3e50;
            }
        """)
        self.label.setFont(QFont("Arial", 11))

        # 将标签设置为滚动区域的widget
        self.scroll_area.setWidget(self.label)

        main_layout.addWidget(self.drag_handle)
        main_layout.addWidget(self.scroll_area)
        main_container.setLayout(main_layout)

        layout.addWidget(main_container)
        self.setLayout(layout)

    def show_definition(self, word: str, html: str):
        """显示单词释义"""
        self.label.setText(html)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.scroll_area.verticalScrollBar().setValue(0)

    def show_loading(self, word: str):
        """显示加载状态"""
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <p style="color: #7f8c8d;">正在查询 <b>{word}</b>...</p>
        </div>
        """
        self.label.setText(html)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def show_not_found(self, word: str):
        """显示未找到"""
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <h2 style="color: #e74c3c;">未找到</h2>
            <p style="color: #34495e;">词典中没有单词: <b>{word}</b></p>
        </div>
        """
        self.label.setText(html)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def clear(self):
        """清空内容并隐藏"""
        self.label.clear()
        self.hide()

    def position_near(self, x: int, y: int):
        """定位到指定位置附近"""
        # 显示在输入框右侧或下方
        self.move(x + 300, y)

    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() == Qt.Key_Escape:
            self.escape_pressed.emit()
        else:
            super().keyPressEvent(event)

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
            new_pos = event.globalPos() - self._drag_position
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件 - 结束拖动并发送位置信号"""
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.position_changed.emit(self.x(), self.y())
            event.accept()
        else:
            super().mouseReleaseEvent(event)
