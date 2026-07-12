"""UI 重构的视觉语义、可访问性与组件契约。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QEvent, Qt  # noqa: E402
from PyQt5.QtGui import QKeyEvent  # noqa: E402
from PyQt5.QtWidgets import (  # noqa: E402
    QAbstractButton,
    QApplication,
    QComboBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class _MemoryStub:
    """StatusPanel 的最小只读内存替身。"""

    def get_affection(self) -> int:
        return 42

    def get_affection_tier(self) -> tuple[int, str, str]:
        return 1, "熟悉", "今天也一起聊聊吧"

    def get_mood(self) -> str:
        return "开心"

    def get_total_chats(self) -> int:
        return 18

    def get_total_days(self) -> int:
        return 3

    def get_today_chat_count(self) -> int:
        return 4

    def get_important_memories(self, _limit: int) -> list[str]:
        return ["你喜欢安静的夜晚"]


class UiRefactorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._widgets = []

    def tearDown(self) -> None:
        for widget in reversed(self._widgets):
            try:
                widget.close()
            except RuntimeError:
                pass

    def _track(self, widget):
        self._widgets.append(widget)
        return widget

    def test_semantic_palette_meets_text_contrast_targets(self) -> None:
        from meapet.ui_theme import PALETTE, contrast_ratio

        required_pairs = (
            ("text_primary", "surface", 4.5),
            ("text_secondary", "surface", 4.5),
            ("text_muted", "canvas", 4.5),
            ("on_primary", "primary", 4.5),
            ("success", "surface", 4.5),
            ("danger", "surface", 4.5),
        )
        for foreground, background, minimum in required_pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(
                    contrast_ratio(PALETTE[foreground], PALETTE[background]),
                    minimum,
                )

    def test_theme_helpers_validate_color_inputs(self) -> None:
        from meapet.ui_theme import contrast_ratio, rgba

        self.assertEqual(rgba("#FF91B4", 128), "rgba(255, 145, 180, 128)")
        self.assertAlmostEqual(contrast_ratio("#FFFFFF", "#000000"), 21.0)
        with self.assertRaises(ValueError):
            rgba("#FFF", 128)
        with self.assertRaises(ValueError):
            rgba("#FFFFFF", 256)
        with self.assertRaises(ValueError):
            contrast_ratio("invalid", "#000000")

    def test_wizard_is_resizable_and_core_actions_have_accessible_targets(self) -> None:
        from wizard.app import SetupWizard
        from wizard.styles import MIN_TARGET_SIZE

        wizard = self._track(SetupWizard())
        self.assertGreaterEqual(wizard.minimumWidth(), 680)
        self.assertGreater(wizard.maximumWidth(), wizard.minimumWidth())
        self.assertEqual(wizard.objectName(), "WizardRoot")
        self.assertEqual(wizard.container.objectName(), "WizardShell")

        for button in (wizard.close_btn, wizard.back_btn, wizard.next_btn):
            with self.subTest(button=button.text()):
                self.assertGreaterEqual(button.minimumWidth(), MIN_TARGET_SIZE)
                self.assertGreaterEqual(button.minimumHeight(), MIN_TARGET_SIZE)
                self.assertTrue(button.accessibleName())

    def test_wizard_form_controls_are_keyboard_ready_and_named(self) -> None:
        from wizard.app import SetupWizard
        from wizard.styles import MIN_TARGET_SIZE

        wizard = self._track(SetupWizard())
        pages = (
            wizard.key_page_ds,
            wizard.key_page_mimo,
            wizard.tts_page,
            wizard.vision_page,
        )
        controls = []
        for page in pages:
            controls.extend(page.findChildren(QLineEdit))
            controls.extend(page.findChildren(QComboBox))

        self.assertGreater(len(controls), 10)
        for control in controls:
            with self.subTest(control=control.objectName() or type(control).__name__):
                self.assertGreaterEqual(control.minimumHeight(), MIN_TARGET_SIZE)
                self.assertTrue(control.accessibleName())
                self.assertNotEqual(control.focusPolicy(), 0)

        tab_chain = [wizard.back_btn, wizard.next_btn]
        for button in tab_chain:
            self.assertNotEqual(button.focusPolicy(), 0)

    def test_chat_composer_exposes_send_close_and_inline_feedback(self) -> None:
        from meapet.desktop.chat_input import ChatInputBox
        from meapet.ui_theme import MIN_TARGET_SIZE

        composer = self._track(ChatInputBox())
        self.assertGreaterEqual(composer.height(), 120)
        self.assertEqual(composer.input.accessibleName(), "消息内容")
        self.assertTrue(composer.feedback_label.accessibleName())

        for button in (composer.send_button, composer.close_button):
            with self.subTest(button=button.text()):
                self.assertGreaterEqual(button.minimumWidth(), MIN_TARGET_SIZE)
                self.assertGreaterEqual(button.minimumHeight(), MIN_TARGET_SIZE)
                self.assertTrue(button.accessibleName())

        composer.input.clear()
        composer._submit()
        self.assertTrue(composer.feedback_label.text())
        self.assertFalse(composer._closing)

    def test_chat_composer_submission_motion_and_escape_paths(self) -> None:
        from meapet.desktop.chat_input import ChatInputBox

        composer = self._track(ChatInputBox())
        composer._anim_timer.stop()

        composer._opacity = 0.95
        composer._animate_in()
        self.assertEqual(composer._opacity, 1.0)

        composer.feedback_label.setText("旧提示")
        composer.input.setText("  晚上好  ")
        self.assertEqual(composer.feedback_label.text(), "")
        submitted = []
        composer.text_submitted.connect(submitted.append)
        composer._submit()
        self.assertEqual(submitted, ["晚上好"])
        self.assertTrue(composer._closing)
        composer._close_with_fade()

        composer._opacity = 0.2
        composer._fade_step = 0.1
        composer._fade_out()
        self.assertAlmostEqual(composer._opacity, 0.1)
        composer._fade_out()
        self.assertEqual(composer._opacity, 0.0)

        second = self._track(ChatInputBox())
        escape = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        with patch.object(second, "_close_with_fade") as close_with_fade:
            second.keyPressEvent(escape)
            close_with_fade.assert_called_once_with()

        second._closing = True
        before = second._opacity
        second._animate_in()
        self.assertEqual(second._opacity, before)

        with patch.dict(os.environ, {"MEAPET_REDUCED_MOTION": "1"}):
            reduced = self._track(ChatInputBox())
        self.assertTrue(reduced._reduced_motion)
        self.assertEqual(reduced._opacity, 1.0)
        reduced._close_with_fade()
        self.assertTrue(reduced._closing)

    def test_accessibility_helpers_cover_legacy_and_unlabeled_controls(self) -> None:
        from wizard.styles import MIN_TARGET_SIZE, prepare_accessible_page, set_status

        class LegacyStatus:
            def __init__(self) -> None:
                self.text = ""
                self.style_sheet = ""

            def setText(self, text: str) -> None:
                self.text = text

            def setStyleSheet(self, style_sheet: str) -> None:
                self.style_sheet = style_sheet

        legacy = LegacyStatus()
        set_status(legacy, "warning", "需要处理")
        self.assertEqual(legacy.text, "需要处理")
        self.assertIn("color:", legacy.style_sheet)

        label = QLabel()
        set_status(label, "success", "就绪")
        self.assertEqual(label.property("status"), "success")

        root = self._track(QWidget())
        layout = QVBoxLayout(root)
        icon_button = QPushButton("×")
        icon_button.setToolTip("关闭")
        icon_button.setFixedWidth(32)
        line_edit = QLineEdit()
        text_edit = QTextEdit()
        plain_edit = QPlainTextEdit()
        combo = QComboBox()
        slider = QSlider(Qt.Horizontal)
        for control in (icon_button, line_edit, text_edit, plain_edit, combo, slider):
            layout.addWidget(control)

        prepare_accessible_page(root)
        for control in (icon_button, line_edit, text_edit, plain_edit, combo, slider):
            self.assertGreaterEqual(control.minimumHeight(), MIN_TARGET_SIZE)
            self.assertTrue(control.accessibleName())
        self.assertGreaterEqual(icon_button.minimumWidth(), MIN_TARGET_SIZE)

    def test_desktop_surfaces_share_semantic_structure(self) -> None:
        from meapet.desktop.splash import StartupSplash
        from meapet.desktop.status_panel import StatusPanel
        from meapet.desktop.widgets import DialogueBox, SizeScaleDialog
        from meapet.ui_theme import MIN_TARGET_SIZE

        splash = self._track(StartupSplash())
        self.assertEqual(splash.card.objectName(), "SplashCard")
        self.assertTrue(splash.status.accessibleName())
        self.assertTrue(splash.progress.accessibleName())

        dialogue = self._track(DialogueBox())
        self.assertEqual(dialogue.text_label.accessibleName(), "梅尔的消息")
        self.assertEqual(dialogue.name_label.accessibleName(), "发言角色")

        panel = self._track(StatusPanel(_MemoryStub()))
        self.assertGreaterEqual(panel.close_button.minimumWidth(), MIN_TARGET_SIZE)
        self.assertGreaterEqual(panel.close_button.minimumHeight(), MIN_TARGET_SIZE)
        self.assertTrue(panel.close_button.accessibleName())
        self.assertGreaterEqual(
            len(
                [
                    card
                    for card in panel.findChildren(QFrame)
                    if card.objectName() == "StatusCard"
                ]
            ),
            3,
        )

        dialog = self._track(SizeScaleDialog(1.0))
        self.assertTrue(dialog._slider.accessibleName())
        for button in dialog.findChildren(QAbstractButton):
            with self.subTest(button=button.text()):
                self.assertGreaterEqual(button.minimumHeight(), MIN_TARGET_SIZE)
                self.assertTrue(button.accessibleName())

    def test_splash_success_failure_and_completion_states(self) -> None:
        from meapet.desktop.splash import StartupSplash

        splash = self._track(StartupSplash())
        splash.set_steps([("加载资源", lambda: "ready")])
        self.assertEqual(splash.progress.maximum(), 1)

        with patch("meapet.desktop.splash.QTimer") as timer:
            splash._run_next()
            timer.singleShot.assert_called_once()
            self.assertEqual(splash.result, "ready")
            self.assertEqual(splash._index, 1)

            timer.reset_mock()
            splash._run_next()
            timer.singleShot.assert_called_once()
            self.assertEqual(splash.status.property("status"), "success")

        finished = []
        splash.finished.connect(lambda: finished.append(True))
        splash._emit_finished()
        self.assertEqual(finished, [True])

        failed_splash = self._track(StartupSplash())

        def fail() -> None:
            raise RuntimeError("资源损坏")

        failed_splash.set_steps([("加载失败项", fail)])
        failures = []
        failed_splash.failed.connect(failures.append)
        with patch("meapet.desktop.splash.QTimer"):
            failed_splash._run_next()
        self.assertEqual(failures, ["资源损坏"])
        self.assertEqual(failed_splash.status.property("status"), "error")

        empty = self._track(StartupSplash())
        empty.set_steps([])
        with (
            patch.object(empty, "show") as show,
            patch.object(empty, "raise_") as raise_window,
            patch("meapet.desktop.splash.QTimer") as timer,
        ):
            empty.start()
            show.assert_called_once_with()
            raise_window.assert_called_once_with()
            timer.singleShot.assert_called_once()

    def test_dialogue_motion_and_scale_dialog_preview_paths(self) -> None:
        from meapet.desktop.widgets import DialogueBox, SizeScaleDialog

        dialogue = self._track(DialogueBox())
        with patch.object(dialogue, "show"), patch.object(dialogue, "raise_"):
            dialogue.show_text("【happy】今天也辛苦啦", duration_ms=1000, name="梅尔")
        self.assertEqual(dialogue.text_label.text(), "今天也辛苦啦")
        self.assertTrue(dialogue._hide_timer.isActive())

        dialogue._fade_out = True
        dialogue._opacity = 0.05
        dialogue._fade_step = 0.1
        dialogue._animate()
        self.assertEqual(dialogue._opacity, 0.0)
        self.assertFalse(dialogue.isVisible())

        dialogue._fade_out = False
        dialogue._opacity = 0.95
        dialogue._fade_step = 0.1
        dialogue._animate()
        self.assertEqual(dialogue._opacity, 1.0)
        dialogue._start_fadeout()
        self.assertTrue(dialogue._fade_out)

        previews = []
        pet = self._track(QWidget())
        pet._size_factor_preview = previews.append
        dialog = self._track(SizeScaleDialog(1.25, pet))
        dialog._on_slider(150)
        self.assertEqual(dialog.get_value(), 1.5)
        self.assertEqual(previews[-1], 1.5)
        dialog._reset()
        self.assertEqual(dialog._slider.value(), 100)
        dialog._on_slider(180)
        dialog.reject()
        self.assertEqual(dialog.get_value(), 1.25)
        self.assertEqual(previews[-1], 1.25)


if __name__ == "__main__":
    unittest.main()
