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
class SummaryPage(QFrame):
    def __init__(self, wizard, parent=None):
        super().__init__(parent)
        self.wizard = wizard
        self.setObjectName("PageCard")
        self.setStyleSheet(STYLE_PAGE_CARD)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(28, 24, 28, 28)
        self.layout.setSpacing(12)

        title = QLabel("确认设置")
        title.setObjectName("PageTitle")
        self.layout.addWidget(title)

        description = QLabel("请检查即将保存的配置。API Key 仅显示首尾字符。")
        description.setObjectName("PageDescription")
        description.setWordWrap(True)
        self.layout.addWidget(description)

        self.summary = QTextEdit()
        self.summary.setObjectName("SummaryOutput")
        self.summary.setReadOnly(True)
        self.summary.setAccessibleName("配置摘要")
        self.summary.setMinimumHeight(200)
        self.layout.addWidget(self.summary)
        self.layout.addStretch()

    def refresh(self):
        cfg = self.wizard.collect_config()
        lines = []
        b = cfg["llm"]["backend"]
        if b == "ollama":
            lines.append("AI 大脑  ·  Ollama（本地免费）")
        elif b == "deepseek":
            k = cfg["llm"].get("api_key", "")
            lines.append("AI 大脑  ·  DeepSeek API")
            lines.append(f"API Key  ·  {k[:8]}…{k[-4:]}" if len(k) > 12 else "需要处理  ·  Key 未设置")
        elif b == "mimo":
            k = cfg["llm"].get("api_key", "")
            lines.append("AI 大脑  ·  MiMo V2.5 API（在线多模态）")
            lines.append(f"API Key  ·  {k[:8]}…{k[-4:]}" if len(k) > 12 else "需要处理  ·  Key 未设置")

        t = cfg["tts"]
        if t["enabled"]:
            eng = t.get("engine", "gpt_sovits")
            if eng == "mimo":
                mk = t.get("api_key", "")
                lines.append(f"语音  ·  MiMo 云端 TTS（音色：{t.get('voice', '冰糖')}）")
                if mk:
                    lines.append(
                        f"TTS Key  ·  {mk[:8]}…{mk[-4:]}" if len(mk) > 12 else "TTS Key  ·  已填写"
                    )
                else:
                    lines.append("需要处理  ·  TTS Key 未设置（语音将无法合成）")
            elif eng == "vits":
                lines.append("语音  ·  VITS 本地（日语）")
            else:
                lines.append("语音  ·  GPT-SoVITS 本地（日语）")
        else:
            lines.append("语音  ·  关闭")

        lines.append("")
        lines.append(f"平台  ·  {PLATFORM['display']}")
        lines.append("模型目录  ·  ./models/")
        lines.append("立绘目录  ·  ./sprites/")
        lines.append("Live2D  ·  ./live2d/model/mea_live2d/")
        if PLATFORM["is_linux"]:
            lines.append("Linux 启动  ·  QT_QPA_PLATFORM=xcb python pet.py")
        elif PLATFORM["is_windows"]:
            lines.append("Windows 启动  ·  双击 启动桌宠.bat 或 python pet.py")
        elif PLATFORM["is_macos"]:
            lines.append("macOS 启动  ·  python pet.py")
        # 识图 / 屏幕观察
        w = cfg.get("watcher") or {}
        v = cfg.get("vision") or {}
        lines.append("")
        if w.get("enabled"):
            vb = (v.get("backend") or "跟随对话") or "跟随对话"
            lines.append(f"屏幕观察  ·  开启（后端 {vb}）")
            if (v.get("backend") == "mimo" or (not v.get("backend") and b == "mimo")):
                if w.get("allow_cloud"):
                    lines.append("云端识图  ·  已允许（截图会上传）")
                else:
                    lines.append("需要处理  ·  云端识图未允许（MiMo 识图不会工作）")
            else:
                lines.append(f"视觉模型  ·  {v.get('model') or 'qwen3.5:4b'}")
            iv = w.get("interval") or {}
            if iv:
                lines.append(
                    f"观察间隔  ·  约 {int(iv.get('min_ms', 180000))/60000:.0f}~"
                    f"{int(iv.get('max_ms', 360000))/60000:.0f} 分钟"
                )
        else:
            lines.append("屏幕观察  ·  关闭（可在向导或右键菜单开启）")
        if b not in ("ollama", "mimo") and not (v.get("backend") in ("ollama", "mimo")):
            lines.append("   DeepSeek 对话时，识图建议单独选 Ollama/MiMo")
        self.summary.setText("\n".join(lines))


# ═══════════════════════════════════════
# 主向导窗口
# ═══════════════════════════════════════
