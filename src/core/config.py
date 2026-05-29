# -*- coding: utf-8 -*-
"""配置管理器"""
import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """配置管理器 - 保存和加载应用设置"""

    DEFAULT_CONFIG = {
        "window_position": None,  # 搜索窗口位置 {"x": int, "y": int}
        "result_position": None,  # 结果窗口位置 {"x": int, "y": int}
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认配置文件路径
            self.config_path = Path.home() / ".fastdict_config.json"
        else:
            self.config_path = Path(config_path)

        self._config = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """加载配置"""
        if not self.config_path.exists():
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()
            return self._config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)

            # 合并默认配置，确保所有键都存在
            for key, value in self.DEFAULT_CONFIG.items():
                if key not in self._config:
                    self._config[key] = value

            return self._config

        except Exception as e:
            print(f"加载配置失败: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config

    def save(self) -> bool:
        """保存配置"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        self._config[key] = value
        return self.save()

    def get_window_position(self) -> Dict[str, int] or None:
        """获取窗口位置配置"""
        return self.get("window_position", None)

    def set_window_position(self, x: int, y: int) -> bool:
        """设置窗口位置"""
        return self.set("window_position", {"x": x, "y": y})

    def clear_window_position(self) -> bool:
        """清除窗口位置配置"""
        return self.set("window_position", None)

    def get_result_position(self) -> Dict[str, int] or None:
        """获取结果窗口位置配置"""
        return self.get("result_position", None)

    def set_result_position(self, x: int, y: int) -> bool:
        """设置结果窗口位置"""
        return self.set("result_position", {"x": x, "y": y})

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()
