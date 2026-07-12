"""配置向导各页面"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import urllib.request
from typing import Optional, Dict, Any, List

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject, QSize, QUrl
from PyQt5.QtGui import *

from wizard.styles import (
    STYLE_INPUT, STYLE_BTN_PRIMARY, STYLE_BTN_SECONDARY,
    COLOR_BG, COLOR_CARD, COLOR_ACCENT, COLOR_TEXT, COLOR_OK, COLOR_WARN, COLOR_ERR,
    STYLE_PAGE_CARD,
)
from wizard.platform_info import PLATFORM, CONFIG_PATH, platform_checklist, ollama_install_hint, detect_platform
from wizard.env_utils import (
    WorkerSignals, pip_install, check_installed, download_file,
    check_ollama_running, check_ollama_installed, pull_ollama_model,
)

# 兼容页面内可能使用的短名
class ApiKeyPage(QFrame):
    def __init__(self, parent=None, backend="deepseek"):
        super().__init__(parent)
        self.backend = backend
        self.setObjectName("PageCard")
        self.setStyleSheet(STYLE_PAGE_CARD)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(14)

        if backend == "deepseek":
            title_text = "连接 DeepSeek"
            desc_text = "在 platform.deepseek.com 注册获取API Key，要先充点额度，不过能用很久。"
            key_label = "DeepSeek API Key："
            key_placeholder = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            api_base_default = "https://api.deepseek.com/v1"
        else:
            title_text = "连接 MiMo V2.5"
            desc_text = "在 xiaomimimo 平台注册获取 MiMo V2.5 的 API Key。"
            key_label = "MiMo API Key："
            key_placeholder = "输入你的 API Key"
            api_base_default = "https://api.xiaomimimo.com/v1"

        title = QLabel(title_text)
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        description = QLabel(desc_text)
        description.setObjectName("PageDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        key_caption = QLabel(key_label)
        key_caption.setObjectName("FieldLabel")
        layout.addWidget(key_caption)
        self.key_input = QLineEdit()
        self.key_input.setObjectName(f"{backend}ApiKey")
        self.key_input.setPlaceholderText(key_placeholder)
        self.key_input.setStyleSheet(STYLE_INPUT)
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setAccessibleName(f"{backend} API Key")
        self.key_input.setAccessibleDescription("凭据只会保存到本机配置文件")
        layout.addWidget(self.key_input)

        self.show_btn = QPushButton("显示 Key")
        self.show_btn.setStyleSheet(STYLE_BTN_SECONDARY)
        self.show_btn.setMinimumSize(112, 44)
        self.show_btn.setAccessibleName("显示 API Key")
        self.show_btn.setCheckable(True)
        self.show_btn.toggled.connect(self._toggle_key_visibility)
        layout.addWidget(self.show_btn, 0, Qt.AlignLeft)

        api_base_caption = QLabel("API 地址（可选）：")
        api_base_caption.setObjectName("FieldLabel")
        layout.addWidget(api_base_caption)
        self.api_base = QLineEdit(api_base_default)
        self.api_base.setObjectName(f"{backend}ApiBase")
        self.api_base.setStyleSheet(STYLE_INPUT)
        self.api_base.setAccessibleName(f"{backend} API 地址")
        layout.addWidget(self.api_base)

        layout.addStretch()

    def set_backend(self, backend: str):
        """切换后端类型，更新界面标签"""
        self.backend = backend

    def _toggle_key_visibility(self, visible: bool) -> None:
        self.key_input.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        self.show_btn.setText("隐藏 Key" if visible else "显示 Key")
        self.show_btn.setAccessibleName("隐藏 API Key" if visible else "显示 API Key")


# ═══════════════════════════════════════
# 页面：TTS 设置
# ═══════════════════════════════════════
