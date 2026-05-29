# -*- coding: utf-8 -*-
"""FastDict - 快速单词查询工具入口"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from src.ui.main_window import MainWindow


def main():
    """程序入口"""
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 创建主窗口（不显示，仅作为控制器）
    window = MainWindow()

    print(f"FastDict 已启动，加载了 {len(window.dict_loader)} 个单词")
    print("输入框显示，回车查询单词，ESC返回输入框")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
