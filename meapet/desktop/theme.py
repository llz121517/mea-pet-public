"""桌面浮窗、菜单与对话框的统一 MeaPet 主题。"""

from __future__ import annotations

from meapet.ui_theme import (
    FONT_FAMILY,
    MONO_FONT_FAMILY,
    PALETTE,
    RADIUS_LARGE,
    RADIUS_MEDIUM,
    RADIUS_SMALL,
    rgba,
)


COLOR_BG = PALETTE["canvas"]
COLOR_CARD = PALETTE["surface"]
COLOR_ELEVATED = PALETTE["surface_elevated"]
COLOR_INPUT = PALETTE["surface_input"]
COLOR_ACCENT = PALETTE["primary"]
COLOR_ACCENT_2 = PALETTE["secondary"]
COLOR_TEXT = PALETTE["text_primary"]
COLOR_SECONDARY = PALETTE["text_secondary"]
COLOR_MUTED = PALETTE["text_muted"]
COLOR_BORDER = PALETTE["border"]
COLOR_BORDER_STRONG = PALETTE["border_strong"]
COLOR_FOCUS = PALETTE["focus"]
COLOR_OK = PALETTE["success"]
COLOR_WARN = PALETTE["warning"]
COLOR_ERR = PALETTE["danger"]


MENU_STYLE = f"""
    QMenu {{
        background: {rgba(COLOR_CARD, 248)};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_MEDIUM}px;
        padding: 7px;
        font-family: {FONT_FAMILY};
        font-size: 13px;
    }}
    QMenu::item {{
        min-height: 28px;
        padding: 8px 28px 8px 14px;
        border: 1px solid transparent;
        border-radius: {RADIUS_SMALL}px;
        margin: 1px 0;
    }}
    QMenu::item:selected {{
        background: {rgba(COLOR_FOCUS, 35)};
        border-color: {rgba(COLOR_FOCUS, 90)};
        color: {COLOR_TEXT};
    }}
    QMenu::item:disabled {{
        color: {rgba(COLOR_MUTED, 135)};
    }}
    QMenu::separator {{
        height: 1px;
        background: {COLOR_BORDER};
        margin: 6px 10px;
    }}
    QMenu::indicator {{
        width: 16px;
        height: 16px;
        left: 8px;
    }}
"""


DIALOG_STYLE = f"""
    QDialog {{
        background: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: {FONT_FAMILY};
    }}
    QFrame#SizeDialogCard {{
        background: {COLOR_CARD};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_MEDIUM}px;
    }}
    QLabel {{
        color: {COLOR_TEXT};
        background: transparent;
        border: none;
    }}
    QLabel#ScaleValue {{
        color: {COLOR_ACCENT};
        font-size: 24px;
        font-weight: 750;
    }}
    QPushButton {{
        min-height: 44px;
        background: {COLOR_ELEVATED};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_SMALL}px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: {rgba(COLOR_FOCUS, 28)};
        border-color: {COLOR_MUTED};
    }}
    QPushButton:focus {{
        border: 2px solid {COLOR_FOCUS};
        padding: 7px 15px;
    }}
    QPushButton#PrimaryButton {{
        background: {COLOR_ACCENT};
        color: {PALETTE['on_primary']};
        border-color: {COLOR_ACCENT};
    }}
    QPushButton#PrimaryButton:hover {{
        background: {PALETTE['primary_hover']};
    }}
    QSlider::groove:horizontal {{
        height: 6px;
        background: {COLOR_BORDER};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {COLOR_ACCENT};
        border: 2px solid {COLOR_FOCUS};
        width: 20px;
        margin: -8px 0;
        border-radius: 11px;
    }}
    QSlider::sub-page:horizontal {{
        background: {COLOR_ACCENT};
        border-radius: 3px;
    }}
    QSlider:focus {{
        border: 1px solid {COLOR_FOCUS};
        border-radius: 5px;
    }}
"""


CHAT_COMPOSER_STYLE = f"""
    QWidget#ChatComposerRoot {{
        color: {COLOR_TEXT};
        font-family: {FONT_FAMILY};
        background: transparent;
    }}
    QFrame#ChatComposer {{
        background: {rgba(COLOR_CARD, 250)};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_MEDIUM}px;
    }}
    QLabel {{
        background: transparent;
        border: none;
    }}
    QLabel#ComposerTitle {{
        color: {COLOR_TEXT};
        font-size: 13px;
        font-weight: 700;
    }}
    QLabel#ComposerHint {{
        color: {COLOR_MUTED};
        font-size: 11px;
    }}
    QLabel#ComposerFeedback {{
        color: {COLOR_ERR};
        font-size: 11px;
    }}
    QLineEdit {{
        min-height: 44px;
        background: {COLOR_INPUT};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_SMALL}px;
        padding: 0 14px;
        font-size: 14px;
        selection-background-color: {rgba(COLOR_ACCENT, 100)};
    }}
    QLineEdit:hover {{
        border-color: {COLOR_MUTED};
    }}
    QLineEdit:focus {{
        border: 2px solid {COLOR_FOCUS};
        padding: 0 13px;
    }}
    QPushButton {{
        min-height: 44px;
        min-width: 44px;
        background: {COLOR_ELEVATED};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_SMALL}px;
        padding: 0 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background: {rgba(COLOR_FOCUS, 28)};
        border-color: {COLOR_MUTED};
    }}
    QPushButton:focus {{
        border: 2px solid {COLOR_FOCUS};
    }}
    QPushButton#SendButton {{
        min-width: 80px;
        background: {COLOR_ACCENT};
        color: {PALETTE['on_primary']};
        border-color: {COLOR_ACCENT};
    }}
    QPushButton#SendButton:hover {{
        background: {PALETTE['primary_hover']};
    }}
    QPushButton#ComposerCloseButton {{
        background: transparent;
        color: {COLOR_MUTED};
        border-color: transparent;
        padding: 0 10px;
    }}
    QPushButton#ComposerCloseButton:hover {{
        background: {rgba(COLOR_ERR, 35)};
        color: {COLOR_ERR};
        border-color: {rgba(COLOR_ERR, 90)};
    }}
"""


DIALOGUE_STYLE = f"""
    QFrame#DialogueCard {{
        background: {rgba(COLOR_CARD, 248)};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_MEDIUM}px;
    }}
    QLabel#DialogueName {{
        background: {COLOR_ELEVATED};
        color: {COLOR_ACCENT};
        border: none;
        border-bottom: 1px solid {COLOR_BORDER_STRONG};
        border-top-left-radius: {RADIUS_MEDIUM}px;
        border-top-right-radius: {RADIUS_MEDIUM}px;
        padding: 7px 18px;
        font-family: {FONT_FAMILY};
        font-size: 13px;
        font-weight: 700;
    }}
    QLabel#DialogueText {{
        background: transparent;
        color: {COLOR_TEXT};
        border: none;
        padding: 14px 20px 16px 20px;
        font-family: {FONT_FAMILY};
        font-size: 15px;
    }}
    QLabel#DialogueAccent {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {rgba(COLOR_ACCENT, 0)},
            stop:0.28 {rgba(COLOR_ACCENT, 150)},
            stop:0.72 {rgba(COLOR_ACCENT_2, 150)},
            stop:1 {rgba(COLOR_ACCENT_2, 0)});
        border: none;
    }}
"""


STATUS_PANEL_STYLE = f"""
    QWidget#StatusPanelRoot {{
        color: {COLOR_TEXT};
        font-family: {FONT_FAMILY};
        background: transparent;
    }}
    QLabel {{
        background: transparent;
        border: none;
        color: {COLOR_TEXT};
    }}
    QLabel#PanelEyebrow {{
        color: {COLOR_ACCENT};
        font-size: 11px;
        font-weight: 700;
    }}
    QLabel#PanelTitle {{
        color: {COLOR_TEXT};
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#TierLabel {{
        color: {COLOR_WARN};
        font-size: 17px;
        font-weight: 700;
    }}
    QLabel#QuoteLabel {{
        color: {COLOR_SECONDARY};
        font-size: 13px;
        font-style: italic;
    }}
    QLabel#StatsLabel {{
        color: {COLOR_SECONDARY};
        font-size: 13px;
    }}
    QLabel#MemoryLabel {{
        color: {COLOR_MUTED};
        font-size: 12px;
    }}
    QLabel#PanelHint {{
        color: {COLOR_MUTED};
        font-size: 11px;
    }}
    QFrame#StatusCard {{
        background: {rgba(COLOR_CARD, 230)};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_MEDIUM}px;
    }}
    QPushButton#PanelCloseButton {{
        min-width: 44px;
        min-height: 44px;
        background: {rgba(COLOR_CARD, 225)};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: 10px;
        font-weight: 600;
    }}
    QPushButton#PanelCloseButton:hover {{
        background: {rgba(COLOR_ERR, 45)};
        color: {COLOR_ERR};
        border-color: {COLOR_ERR};
    }}
    QPushButton#PanelCloseButton:focus {{
        border: 2px solid {COLOR_FOCUS};
    }}
    QProgressBar {{
        min-height: 20px;
        background: {COLOR_INPUT};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: 6px;
        text-align: center;
        font-weight: 700;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_2});
        border-radius: 5px;
    }}
"""


SPLASH_STYLE = f"""
    QWidget#SplashRoot {{
        color: {COLOR_TEXT};
        font-family: {FONT_FAMILY};
        background: transparent;
    }}
    QFrame#SplashCard {{
        background: {COLOR_CARD};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_LARGE}px;
    }}
    QLabel {{
        background: transparent;
        border: none;
    }}
    QLabel#SplashMark {{
        background: {COLOR_ACCENT};
        color: {PALETTE['on_primary']};
        border-radius: 18px;
        font-size: 18px;
        font-weight: 800;
    }}
    QLabel#SplashTitle {{
        color: {COLOR_TEXT};
        font-size: 26px;
        font-weight: 750;
    }}
    QLabel#SplashSubtitle {{
        color: {COLOR_SECONDARY};
        font-size: 13px;
    }}
    QLabel#SplashStatus {{
        color: {COLOR_TEXT};
        font-size: 14px;
        font-weight: 600;
    }}
    QLabel#SplashStatus[status="success"] {{
        color: {COLOR_OK};
    }}
    QLabel#SplashStatus[status="error"] {{
        color: {COLOR_ERR};
    }}
    QLabel#SplashDetail,
    QLabel#SplashHint {{
        color: {COLOR_MUTED};
        font-size: 11px;
    }}
    QProgressBar {{
        background: {COLOR_ELEVATED};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_2});
        border-radius: 3px;
    }}
"""
