"""MeaPet 的键盘友好型浮动消息输入框。"""

from __future__ import annotations

import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from meapet.desktop.theme import CHAT_COMPOSER_STYLE
from meapet.ui_theme import MIN_TARGET_SIZE


class ChatInputBox(QWidget):
    """置顶的消息编辑器，支持 Enter 发送与 Esc 关闭。"""

    text_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("和梅尔对话")
        self.setObjectName("ChatComposerRoot")
        self.setFixedSize(560, 154)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAccessibleName("和梅尔对话")
        self.setAccessibleDescription("输入消息后按 Enter 或点击发送；按 Escape 关闭")
        self.setStyleSheet(CHAT_COMPOSER_STYLE)

        self._opacity = 0.0
        self._fade_step = 0.08
        self._closing = False
        self._reduced_motion = os.environ.get("MEAPET_REDUCED_MOTION", "").lower() in {
            "1",
            "true",
            "yes",
        }

        self._build_ui()

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_in)
        if self._reduced_motion:
            self._opacity = 1.0
            self.setWindowOpacity(1.0)
        else:
            self.setWindowOpacity(0.0)
            self._anim_timer.start(18)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setObjectName("ChatComposer")
        outer.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("发消息给梅尔")
        title.setObjectName("ComposerTitle")
        title.setAccessibleName("消息编辑器")
        header.addWidget(title)

        hint = QLabel("Enter 发送 · Esc 关闭")
        hint.setObjectName("ComposerHint")
        header.addWidget(hint)
        header.addStretch()

        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("ComposerCloseButton")
        self.close_button.setMinimumSize(64, MIN_TARGET_SIZE)
        self.close_button.setAccessibleName("关闭消息输入框")
        self.close_button.setToolTip("关闭（Esc）")
        self.close_button.clicked.connect(self._close_with_fade)
        header.addWidget(self.close_button)
        layout.addLayout(header)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input = QLineEdit()
        self.input.setObjectName("MessageInput")
        self.input.setMinimumHeight(MIN_TARGET_SIZE)
        self.input.setPlaceholderText("输入你想说的话")
        self.input.setAccessibleName("消息内容")
        self.input.setAccessibleDescription("按 Enter 发送消息")
        self.input.returnPressed.connect(self._submit)
        self.input.textChanged.connect(self._clear_feedback)
        input_row.addWidget(self.input, 1)

        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("SendButton")
        self.send_button.setMinimumSize(80, MIN_TARGET_SIZE)
        self.send_button.setAccessibleName("发送消息")
        self.send_button.clicked.connect(self._submit)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("ComposerFeedback")
        self.feedback_label.setAccessibleName("消息输入提示")
        self.feedback_label.setMinimumHeight(14)
        layout.addWidget(self.feedback_label)

        self.setTabOrder(self.input, self.send_button)
        self.setTabOrder(self.send_button, self.close_button)

    def _animate_in(self) -> None:
        if self._closing:
            return
        self._opacity = min(1.0, self._opacity + self._fade_step)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0:
            self._anim_timer.stop()

    def _submit(self) -> None:
        text = self.input.text().strip()
        if not text:
            self.feedback_label.setText("请输入内容后再发送")
            self.input.setFocus(Qt.OtherFocusReason)
            return
        self.feedback_label.clear()
        self.text_submitted.emit(text)
        self._close_with_fade()

    def _clear_feedback(self, _text: str) -> None:
        if self.feedback_label.text():
            self.feedback_label.clear()

    def _close_with_fade(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self._reduced_motion:
            self.close()
            return
        self._fade_step = 0.10
        self._anim_timer.stop()
        try:
            self._anim_timer.timeout.disconnect()
        except TypeError:
            pass
        self._anim_timer.timeout.connect(self._fade_out)
        self._anim_timer.start(20)

    def _fade_out(self) -> None:
        self._opacity = max(0.0, self._opacity - self._fade_step)
        if self._opacity <= 0.0:
            self._anim_timer.stop()
            self.close()
            return
        self.setWindowOpacity(self._opacity)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self._close_with_fade()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.input.setFocus(Qt.OtherFocusReason)
        self.input.selectAll()

    def closeEvent(self, event) -> None:
        self._anim_timer.stop()
        super().closeEvent(event)
