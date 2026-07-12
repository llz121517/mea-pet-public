"""配置文件健康检查模块。"""

import json
import os

def check_config_lines(config_path: str) -> bool:
    """兼容旧函数名：验证文件是可读取的 JSON 对象。"""
    if not os.path.exists(config_path):
        return False
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return isinstance(data, dict)
    except (OSError, json.JSONDecodeError, UnicodeError):
        return False
