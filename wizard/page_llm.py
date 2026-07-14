"""配置向导各页面"""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from wizard.styles import (
    STYLE_INPUT,
    STYLE_PAGE_CARD,
    set_status,
)
from wizard.env_utils import (
    check_ollama_installed,
    check_ollama_running,
)

# 兼容页面内可能使用的短名
class LLMPage(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._provider_drafts = {}
        self._active_provider = None
        self._suspend_provider_switch = False
        self.setObjectName("PageCard")
        self.setStyleSheet(STYLE_PAGE_CARD)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(14)

        title = QLabel("选择 AI 大脑")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        desc = QLabel("桌宠要靠一个 AI 来对话，选一个你有的：")
        desc.setObjectName("PageDescription")
        layout.addWidget(desc)

        # Ollama
        self.radio_ollama = QRadioButton("Ollama（推荐 · 免费、本地运行）")
        self.radio_ollama.setAccessibleDescription("本地运行，不需要 API Key")
        self.radio_ollama.setChecked(True)
        layout.addWidget(self.radio_ollama)
        ollama_detail = QLabel(
            "    • 完全免费，不需要 API Key\n"
            "    • 需要先装 Ollama 并下载模型\n"
            "    • 推荐模型：qwen3.5:4b（多模态，对话+识图一体）"
        )
        ollama_detail.setObjectName("HelperText")
        ollama_detail.setWordWrap(True)
        layout.addWidget(ollama_detail)

        # DeepSeek
        self.radio_ds = QRadioButton("DeepSeek API（在线、速度快）")
        self.radio_ds.setAccessibleDescription("在线服务，按量付费，需要 API Key")
        layout.addWidget(self.radio_ds)
        deepseek_detail = QLabel(
            "    • 需要注册 DeepSeek 获取 API Key\n"
            "    • 按量付费，不需要本地显卡\n"
            "    • 注：屏幕识图仍需要 Ollama（装 qwen3.5:4b 即可，多模态对话+识图一体）"
        )
        deepseek_detail.setObjectName("HelperText")
        deepseek_detail.setWordWrap(True)
        layout.addWidget(deepseek_detail)

        # MiMo V2.5
        self.radio_mimo = QRadioButton("MiMo V2.5（小米多模态 API，在线、可识图）")
        self.radio_mimo.setAccessibleDescription("在线多模态服务，支持对话和识图，需要 API Key")
        layout.addWidget(self.radio_mimo)
        mimo_detail = QLabel(
            "    • 需要注册 xiaomimimo 平台获取 API Key\n"
            "    • 按量付费，不需要本地显卡\n"
            "    • 支持识图（不需要额外装 Ollama）"
        )
        mimo_detail.setObjectName("HelperText")
        mimo_detail.setWordWrap(True)
        layout.addWidget(mimo_detail)

        # 自定义模型服务商仍属于 direct，不把 OpenAI-compatible 端点伪装成 Agent。
        self.radio_custom = QRadioButton("自定义模型接口（直连）")
        self.radio_custom.setAccessibleDescription(
            "填写实际协议、地址、模型和鉴权信息"
        )
        layout.addWidget(self.radio_custom)

        self.direct_settings = QFrame()
        self.direct_settings.setObjectName("SectionCard")
        direct_layout = QVBoxLayout(self.direct_settings)
        direct_layout.setContentsMargins(16, 14, 16, 16)
        direct_layout.setSpacing(10)

        protocol_label = QLabel("接口协议：")
        protocol_label.setObjectName("FieldLabel")
        direct_layout.addWidget(protocol_label)
        self.protocol_combo = QComboBox()
        self.protocol_combo.setObjectName("DirectProtocol")
        self.protocol_combo.setAccessibleName("直连接口协议")
        self.protocol_combo.addItem("Ollama Chat", "ollama_chat")
        self.protocol_combo.addItem("OpenAI Chat Completions", "openai_chat")
        self.protocol_combo.addItem("OpenAI Responses", "openai_responses")
        self.protocol_combo.addItem("Anthropic Messages", "anthropic_messages")
        direct_layout.addWidget(self.protocol_combo)

        endpoint_label = QLabel("实际 API 地址：")
        endpoint_label.setObjectName("FieldLabel")
        direct_layout.addWidget(endpoint_label)
        self.endpoint_input = QLineEdit("http://127.0.0.1:11434")
        self.endpoint_input.setObjectName("DirectApiEndpoint")
        self.endpoint_input.setStyleSheet(STYLE_INPUT)
        self.endpoint_input.setAccessibleName("直连 API 地址")
        direct_layout.addWidget(self.endpoint_input)

        model_label = QLabel("实际模型 ID：")
        model_label.setObjectName("FieldLabel")
        direct_layout.addWidget(model_label)
        self.model_input = QLineEdit("qwen3.5:4b")
        self.model_input.setObjectName("DirectModel")
        self.model_input.setStyleSheet(STYLE_INPUT)
        self.model_input.setAccessibleName("直连模型 ID")
        direct_layout.addWidget(self.model_input)

        self.direct_key_label = QLabel(
            "API Key / 环境变量占位符（可空）："
        )
        self.direct_key_label.setObjectName("FieldLabel")
        direct_layout.addWidget(self.direct_key_label)
        self.direct_api_key_input = QLineEdit()
        self.direct_api_key_input.setObjectName("DirectApiKey")
        self.direct_api_key_input.setStyleSheet(STYLE_INPUT)
        self.direct_api_key_input.setEchoMode(QLineEdit.Password)
        self.direct_api_key_input.setAccessibleName("直连 API Key")
        self.direct_api_key_input.setAccessibleDescription(
            "凭据只会保存到本机配置文件，也可填写环境变量占位符"
        )
        self.direct_api_key_input.setPlaceholderText("例如 $MEAPET_API_KEY")
        key_row = QHBoxLayout()
        key_row.addWidget(self.direct_api_key_input, 1)
        self.direct_api_key_visibility = QPushButton("显示 Key")
        self.direct_api_key_visibility.setCheckable(True)
        self.direct_api_key_visibility.setAccessibleName("显示直连 API Key")
        self.direct_api_key_visibility.setProperty(
            "doesNotModifyConfig",
            True,
        )
        self.direct_api_key_visibility.toggled.connect(
            self._toggle_api_key_visibility
        )
        key_row.addWidget(self.direct_api_key_visibility)
        direct_layout.addLayout(key_row)

        tuning = QHBoxLayout()
        tuning.addWidget(QLabel("temperature"))
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setObjectName("DirectTemperature")
        self.temperature_input.setAccessibleName("直连 temperature")
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setDecimals(2)
        self.temperature_input.setSingleStep(0.05)
        self.temperature_input.setValue(0.7)
        tuning.addWidget(self.temperature_input)
        tuning.addWidget(QLabel("max tokens"))
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setObjectName("DirectMaxTokens")
        self.max_tokens_input.setAccessibleName("直连最大输出 token")
        self.max_tokens_input.setRange(1, 1_000_000)
        self.max_tokens_input.setValue(512)
        tuning.addWidget(self.max_tokens_input)
        tuning.addStretch()
        direct_layout.addLayout(tuning)
        layout.addWidget(self.direct_settings)

        # Ollama 状态
        self.ollama_status = QLabel("")
        self.ollama_status.setProperty("status", "muted")
        self.ollama_status.setAccessibleName("Ollama 运行状态")
        layout.addWidget(self.ollama_status)

        layout.addStretch()
        for radio in (
            self.radio_ollama,
            self.radio_ds,
            self.radio_mimo,
            self.radio_custom,
        ):
            radio.toggled.connect(self._on_provider_selected)
        self._on_provider_selected()
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._refresh_ollama_status)
        self._status_timer.start(100)

    def _refresh_ollama_status(self):
        running, models = check_ollama_running()
        installed = check_ollama_installed()
        if running:
            m = ", ".join(models[:3])
            set_status(self.ollama_status, "success", f"Ollama 运行中（模型：{m}）")
        elif installed:
            set_status(self.ollama_status, "warning", "Ollama 已安装但未运行，启动后再继续")
        else:
            set_status(
                self.ollama_status,
                "muted",
                "还没装 Ollama？可以先选 DeepSeek，或回头再装",
            )

    def get_backend(self):
        if self.radio_ollama.isChecked():
            return "ollama"
        elif self.radio_mimo.isChecked():
            return "mimo"
        elif self.radio_custom.isChecked():
            return "custom"
        return "deepseek"

    def set_backend(self, backend: str):
        """恢复上次选择的 AI 后端。"""
        backend = (backend or "ollama").lower()
        if backend == "mimo":
            self.radio_mimo.setChecked(True)
        elif backend == "deepseek":
            self.radio_ds.setChecked(True)
        elif backend not in {"ollama", "hermes", "openclaw"}:
            self.radio_custom.setChecked(True)
        else:
            self.radio_ollama.setChecked(True)

    def _on_provider_selected(self, checked: bool = True) -> None:
        if not checked:
            return
        if self._suspend_provider_switch:
            return
        provider = self.get_backend()
        if self._active_provider == provider:
            return
        if self._active_provider:
            self._provider_drafts[self._active_provider] = (
                self.collect_direct_profile()
            )
        profile = self._provider_drafts.get(provider)
        if profile is None:
            profile = self._default_profile(provider)
        self._apply_profile_fields(profile)
        self._sync_provider_copy(provider)
        self._active_provider = provider

    def _sync_provider_copy(self, provider: str) -> None:
        required = provider in {"deepseek", "mimo"}
        suffix = "必填" if required else "可空"
        self.direct_key_label.setText(
            f"API Key / 环境变量占位符（{suffix}）："
        )

    @staticmethod
    def _default_profile(provider: str) -> dict:
        presets = {
            "ollama": {
                "protocol": "ollama_chat",
                "endpoint": "http://127.0.0.1:11434",
                "model": "qwen3.5:4b",
            },
            "deepseek": {
                "protocol": "openai_chat",
                "endpoint": "https://api.deepseek.com/v1",
                "model": "deepseek-v4-flash",
            },
            "mimo": {
                "protocol": "openai_chat",
                "endpoint": "https://api.xiaomimimo.com/v1",
                "model": "mimo-v2.5",
            },
            "custom": {
                "protocol": "openai_chat",
                "endpoint": "",
                "model": "",
            },
        }
        preset = presets.get(provider, presets["custom"])
        protocol = preset["protocol"]
        endpoint = preset["endpoint"]
        return {
            "provider": provider,
            "protocol": protocol,
            "api_base": "" if protocol == "ollama_chat" else endpoint,
            "host": endpoint if protocol == "ollama_chat" else "",
            "model": preset["model"],
            "api_key": "",
            "temperature": 0.7,
            "max_tokens": 512,
        }

    def _apply_profile_fields(self, profile: dict) -> None:
        protocol = str(profile.get("protocol") or "openai_chat")
        self.set_protocol(protocol)
        endpoint = (
            profile.get("host")
            if protocol == "ollama_chat"
            else profile.get("api_base")
        )
        self.endpoint_input.setText(str(endpoint or ""))
        self.model_input.setText(str(profile.get("model") or ""))
        self.direct_api_key_input.setText(str(profile.get("api_key") or ""))
        try:
            self.temperature_input.setValue(
                float(profile.get("temperature", 0.7))
            )
        except (TypeError, ValueError):
            self.temperature_input.setValue(0.7)
        try:
            self.max_tokens_input.setValue(
                int(profile.get("max_tokens", 512))
            )
        except (TypeError, ValueError):
            self.max_tokens_input.setValue(512)

    def set_protocol(self, protocol: str) -> None:
        index = self.protocol_combo.findData(str(protocol or "").strip())
        if index >= 0:
            self.protocol_combo.setCurrentIndex(index)

    def _toggle_api_key_visibility(self, visible: bool) -> None:
        self.direct_api_key_input.setEchoMode(
            QLineEdit.Normal if visible else QLineEdit.Password
        )
        self.direct_api_key_visibility.setText(
            "隐藏 Key" if visible else "显示 Key"
        )
        self.direct_api_key_visibility.setAccessibleName(
            "隐藏直连 API Key" if visible else "显示直连 API Key"
        )

    def apply_direct_profile(self, profile: dict) -> None:
        profile = profile or {}
        self._suspend_provider_switch = True
        try:
            self.set_backend(profile.get("provider", "ollama"))
            self._apply_profile_fields(profile)
            provider = self.get_backend()
            self._sync_provider_copy(provider)
            self._active_provider = provider
            self._provider_drafts[provider] = self.collect_direct_profile()
        finally:
            self._suspend_provider_switch = False

    def collect_direct_profile(self, api_key: str = "") -> dict:
        protocol = self.protocol_combo.currentData() or "openai_chat"
        endpoint = self.endpoint_input.text().strip()
        return {
            "provider": self.get_backend(),
            "protocol": protocol,
            "api_base": "" if protocol == "ollama_chat" else endpoint,
            "host": endpoint if protocol == "ollama_chat" else "",
            "model": self.model_input.text().strip(),
            "api_key": str(api_key or self.direct_api_key_input.text()).strip(),
            "temperature": self.temperature_input.value(),
            "max_tokens": self.max_tokens_input.value(),
        }
