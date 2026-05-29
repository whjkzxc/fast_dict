# -*- coding: utf-8 -*-
"""主窗口 - 控制器"""
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QLinearGradient
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QSystemTrayIcon, QMenu, QAction

from src.ui.search_widget import SearchWidget
from src.ui.result_label import ResultLabel
from src.core.dictionary import DictionaryLoader, DictionaryQuery
from src.core.fuzzy_match import FuzzyMatcher
from src.core.llm_query import query_llm


class LLMWorker(QThread):
    """后台线程调用大模型"""
    finished = pyqtSignal(str, str)  # word, result
    error = pyqtSignal(str, str)     # word, error_msg

    def __init__(self, word: str):
        super().__init__()
        self.word = word

    def run(self):
        try:
            result = query_llm(self.word)
            self.finished.emit(self.word, result)
        except Exception as e:
            self.error.emit(self.word, str(e))


class MainWindow(QWidget):
    """主窗口 - 控制器（不显示）"""

    def __init__(self):
        super().__init__()

        # 加载词典
        self.dict_loader = DictionaryLoader()
        self.dict_loader.load_all()
        self.dict_query = DictionaryQuery(self.dict_loader)
        self.fuzzy_matcher = FuzzyMatcher(self.dict_loader.word_list)

        # UI组件
        self.search_widget = SearchWidget(self.fuzzy_matcher)
        self.result_label = ResultLabel()

        # 连接信号
        self.search_widget.search_confirmed.connect(self.on_search_confirmed)
        self.search_widget.position_changed.connect(self.on_search_position_changed)
        self.result_label.position_changed.connect(self.on_result_position_changed)
        self.result_label.escape_pressed.connect(self.on_result_escape)

        # 设置主窗口属性（不显示）
        self.setWindowFlags(Qt.Widget)
        self.setLayout(QVBoxLayout())

        # 系统托盘
        self.setup_tray_icon()

        # 显示搜索框
        self.show_search()

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        # 创建图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建渐变背景（从深蓝到浅蓝）
        gradient = QLinearGradient(0, 0, 32, 32)
        gradient.setColorAt(0, QColor("#2c3e50"))   # 深蓝
        gradient.setColorAt(1, QColor("#3498db"))   # 浅蓝

        # 绘制书本主体（带渐变的圆角矩形）
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(3, 5, 26, 22, 3, 3)

        # 绘制书脊（左侧深色条）
        painter.setBrush(QColor("#1a252f"))
        painter.drawRoundedRect(3, 5, 5, 22, 2, 2)

        # 绘制页面效果（右侧细线）
        painter.setPen(QColor(255, 255, 255, 80))
        for i in range(3):
            x = 22 + i * 2
            painter.drawLine(x, 9, x, 23)

        # 绘制字母F（带轻微阴影）
        # 阴影
        painter.setPen(QColor(0, 0, 0, 100))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(pixmap.rect().adjusted(1, 1, 1, 1), Qt.AlignCenter, "F")

        # 主文字
        painter.setPen(QColor("white"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "F")

        painter.end()

        icon = QIcon(pixmap)

        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("FastDict - 快速单词查询")

        # 托盘菜单
        menu = QMenu()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def show_search(self):
        """显示搜索框"""
        self.result_label.hide()
        self.search_widget.show()
        self.search_widget.activateWindow()
        self.search_widget.input_field.setFocus()

    def show_result(self, word: str, html: str):
        """显示结果卡片"""
        # 定位结果标签到搜索框位置
        search_geo = self.search_widget.geometry()
        self.result_label.move(search_geo.x(), search_geo.y())

        self.result_label.show_definition(word, html)
        self.search_widget.hide()

    def on_search_position_changed(self, x: int, y: int):
        """搜索窗口位置改变"""
        print(f"[DEBUG] 搜索窗口位置: ({x}, {y})")

    def on_result_position_changed(self, x: int, y: int):
        """结果窗口位置改变"""
        print(f"[DEBUG] 结果窗口位置: ({x}, {y})")

    def on_search_confirmed(self, word: str):
        """搜索确认"""
        # 显示加载状态
        self.result_label.show_loading(word)

        # 定位结果标签到搜索框位置
        search_geo = self.search_widget.geometry()
        self.result_label.move(search_geo.x(), search_geo.y())

        # 查询单词
        entry = self.dict_query.lookup(word)
        if entry:
            html = self.dict_query.get_definition_html(word)
            self.show_result(word, html)
        else:
            # 词典未找到，调用大模型获取解释
            self.search_widget.hide()
            self.result_label.show_loading(word)
            self.result_label.show()
            self.result_label.raise_()
            self.result_label.activateWindow()
            self.result_label.setFocus()

            self._llm_worker = LLMWorker(word)
            self._llm_worker.finished.connect(self.on_llm_finished)
            self._llm_worker.error.connect(self.on_llm_error)
            self._llm_worker.start()

    def on_llm_finished(self, word: str, result: str):
        """大模型返回结果"""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px;">
            <h1 style="margin: 0 0 5px 0; color: #2c3e50; font-size: 24px;">
                {word}
            </h1>
            <p style="margin: 0 0 8px 0; color: #95a5a6; font-size: 11px;">
                AI 生成
            </p>
            <div style="border-top: 1px solid #ecf0f1; padding-top: 10px;">
                <p style="margin: 0; color: #34495e; font-size: 13px; line-height: 1.6;">
                    {result}
                </p>
            </div>
        </div>
        """
        self.result_label.show_definition(word, html)

    def on_llm_error(self, word: str, error_msg: str):
        """大模型调用失败"""
        self.result_label.show_not_found(word)

    def on_result_escape(self):
        """结果卡片按下ESC"""
        self.show_search()

    def quit_app(self):
        """退出应用"""
        self.tray_icon.hide()
        self.search_widget.close()
        self.result_label.close()
        self.close()
        QApplication.instance().quit()

    def closeEvent(self, event):
        """关闭事件"""
        self.quit_app()
        event.accept()
