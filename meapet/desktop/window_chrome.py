"""Tray, context menu, autostart, quit — window chrome for MeaPet."""
from __future__ import annotations

import os
import sys

from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from meapet.desktop.theme import COLOR_ACCENT, COLOR_ACCENT_2, COLOR_TEXT, MENU_STYLE
from meapet.paths import PROJECT_ROOT
from meapet.utils import safe_print


class PetWindowChromeMixin:
    """System tray + right-click menu + Windows autostart."""

    def _setup_tray(self):
        from PyQt5.QtGui import QPixmap, QColor, QPainter
        from meapet.utils import safe_print

        available = QSystemTrayIcon.isSystemTrayAvailable()
        safe_print(f"[tray] system tray available={available}")
        if not available:
            safe_print("[tray] 系统托盘不可用（WSL/部分桌面环境）。仍继续运行窗口。")
            self.tray = None
            return

        icon = QIcon()
        try:
            if getattr(self, "renderer", None) is not None and not getattr(self, "_use_live2d", False):
                pixmap = self.renderer.get_current_pixmap()
                if pixmap is not None and not pixmap.isNull():
                    icon = QIcon(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            safe_print(f"[tray] sprite icon failed: {e}")
        if icon.isNull():
            # 生成粉色猫爪色块图标，避免空 QIcon 导致托盘不显示
            pm = QPixmap(32, 32)
            pm.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(COLOR_ACCENT))
            painter.setPen(QColor(COLOR_ACCENT_2))
            painter.drawEllipse(2, 2, 28, 28)
            painter.setBrush(QColor(COLOR_TEXT))
            painter.drawEllipse(10, 10, 12, 12)
            painter.end()
            icon = QIcon(pm)

        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("梅尔桌宠 · MeaPet")

        menu = QMenu()
        menu.setStyleSheet(MENU_STYLE)
        show_action = QAction("显示 / 隐藏", self)
        show_action.triggered.connect(self._toggle_visibility)
        menu.addAction(show_action)
        snap_tray = QAction("看看我在干嘛", self)
        snap_tray.triggered.connect(lambda: self._do_screen_watch(force=True))
        menu.addAction(snap_tray)
        menu.addSeparator()
        auto_started = self._is_auto_start()
        auto_tray_action = QAction("开机自启", self)
        auto_tray_action.setCheckable(True)
        auto_tray_action.setChecked(auto_started)
        auto_tray_action.triggered.connect(self._toggle_auto_start)
        menu.addAction(auto_tray_action)
        menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        try:
            self.tray.activated.connect(self._on_tray_activated)
        except Exception:
            pass
        self.tray.show()
        safe_print(f"[tray] shown visible={self.tray.isVisible()}")
        try:
            self.tray.showMessage(
                "MeaPet 已启动",
                "桌宠在运行中。找不到时看右下角托盘图标；右键桌宠可退出。",
                QSystemTrayIcon.Information,
                5000,
            )
        except Exception:
            pass

    def _on_tray_activated(self, reason):
        # 单击/双击托盘：显示桌宠
        try:
            if reason in (
                QSystemTrayIcon.Trigger,
                QSystemTrayIcon.DoubleClick,
                QSystemTrayIcon.MiddleClick,
            ):
                self.show()
                self.raise_()
                self.activateWindow()
        except Exception:
            pass

    def _toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def _quit(self):
        safe_print("[pet] quitting by user/menu…")
        try:
            if not self._use_live2d and self.renderer:
                self.renderer.stop_blink_animation()
        except Exception:
            pass
        try:
            if self._use_live2d and self._l2d_model and self.sprite_label:
                self.sprite_label.shutdown()
        except Exception:
            pass
        try:
            self._idle_timer.stop()
            self._watcher_timer.stop()
        except Exception:
            pass
        if hasattr(self, "_watcher") and self._watcher is not None:
            try:
                self._watcher.stop()
                self._watcher.wait(3000)
            except Exception:
                pass
        for attr in ["_chat_worker", "_tts_worker", "_speak_worker"]:
            w = getattr(self, attr, None)
            if w is not None:
                try:
                    w.wait(3000)
                except Exception:
                    pass
        if hasattr(self, "tray"):
            try:
                self.tray.hide()
            except Exception:
                pass
        if hasattr(self, "bubble"):
            try:
                self.bubble.close()
            except Exception:
                pass
        if hasattr(self, "memory"):
            try:
                self.memory.close()
            except Exception:
                pass
        try:
            from meapet.desktop.live2d_widget import dispose_live2d
            dispose_live2d()
        except Exception:
            pass
        QApplication.quit()

    def _is_auto_start(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            val, _ = winreg.QueryValueEx(key, "MeaPet")
            winreg.CloseKey(key)
            path = val.split('"')[1] if '"' in val else val.split()[0]
            return os.path.exists(path)
        except Exception:
            return False

    def _toggle_auto_start(self):
        if sys.platform != "win32":
            self._show_bubble("开机自启目前仅支持 Windows 喵", 2500)
            return
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, "MeaPet")
            winreg.DeleteValue(key, "MeaPet")
            winreg.CloseKey(key)
            self._show_bubble("已关闭开机自启喵", 2000)
        except FileNotFoundError:
            winreg.CloseKey(key)
            py = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(py):
                py = sys.executable
            pet_path = str(PROJECT_ROOT / "pet.py")
            cmd = f'"{py}" "{pet_path}"'
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "MeaPet", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
            self._show_bubble("已开启开机自启喵 🖥️", 2000)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        expr_menu = QMenu("切换表情", self)
        expr_menu.setStyleSheet(MENU_STYLE)
        moods = [
            ("😊 默认", "neutral"),
            ("😄 开心", "happy"),
            ("😢 悲伤", "sad"),
            ("😳 害羞", "shy"),
            ("🤔 好奇", "curious"),
            ("😤 烦闷", "annoyed"),
            ("😔 忧郁", "melancholy"),
        ]
        for label, mood in moods:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, m=mood: self._safe_set_mood(m))
            expr_menu.addAction(action)
        menu.addMenu(expr_menu)

        vision_cfg = self.config.get("vision", {}) or {}
        llm_cfg = self.config.get("llm", {}) or {}
        vision_backend = (
            vision_cfg.get("backend") or llm_cfg.get("backend") or "ollama"
        ).lower()
        vision_menu = QMenu("识图设置", self)
        vision_menu.setStyleSheet(MENU_STYLE)
        current_vision = vision_cfg.get("model", "minicpm-v")
        for label, bname in (
            ("后端: Ollama 本地", "ollama"),
            ("后端: MiMo 云端", "mimo"),
        ):
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(vision_backend == bname)
            act.triggered.connect(lambda checked, b=bname: self._set_vision_backend(b))
            vision_menu.addAction(act)
        vision_menu.addSeparator()
        if vision_backend != "mimo":
            for label, model_name in (
                ("minicpm-v (5.5G, 快)", "minicpm-v"),
                ("qwen2.5vl:7b (6G)", "qwen2.5vl:7b"),
            ):
                action = QAction(label, self)
                action.setCheckable(True)
                action.setChecked(current_vision == model_name)
                action.triggered.connect(
                    lambda checked, m=model_name: self._set_vision_model(m)
                )
                vision_menu.addAction(action)
        else:
            tip = QAction("MiMo 使用 vision/llm 的云端模型", self)
            tip.setEnabled(False)
            vision_menu.addAction(tip)
        menu.addMenu(vision_menu)

        status_action = QAction("养成状态", self)
        status_action.triggered.connect(self._show_status_panel)
        menu.addAction(status_action)

        w_enabled = self.config.get("watcher", {}).get("enabled", False)
        watch_text = "关闭屏幕观察" if w_enabled else "开启屏幕观察"
        watch_action = QAction(watch_text, self)
        watch_action.triggered.connect(self._toggle_watcher_enabled)
        menu.addAction(watch_action)

        standby_text = "取消待机" if self._standby else "待机（暂停识图）"
        standby_action = QAction(standby_text, self)
        standby_action.triggered.connect(self._toggle_standby)
        menu.addAction(standby_action)

        mode_text = "切回 PNG 立绘" if self._use_live2d else "切换到 Live2D"
        mode_action = QAction(mode_text, self)
        mode_action.triggered.connect(self._toggle_render_mode)
        menu.addAction(mode_action)

        size_action = QAction("立绘大小调节…", self)
        size_action.triggered.connect(self._open_size_dialog)
        menu.addAction(size_action)

        snap_action = QAction("看看我在干嘛", self)
        snap_action.triggered.connect(lambda: self._do_screen_watch(force=True))
        menu.addAction(snap_action)

        menu.addSeparator()
        reset_action = QAction("重置所有记忆", self)
        reset_action.triggered.connect(self._reset_memory)
        menu.addAction(reset_action)
        menu.addSeparator()

        auto_started = self._is_auto_start()
        auto_action = QAction("开机自启", self)
        auto_action.setCheckable(True)
        auto_action.setChecked(auto_started)
        auto_action.triggered.connect(self._toggle_auto_start)
        menu.addAction(auto_action)
        menu.addSeparator()

        reconf_action = QAction("再次配置", self)
        reconf_action.triggered.connect(self._reopen_setup_wizard)
        menu.addAction(reconf_action)
        menu.addSeparator()
        menu.addAction("退出", self._quit)
        menu.exec_(self.mapToGlobal(pos))

    def _show_status_panel(self):
        from meapet.desktop.status_panel import StatusPanel
        if not hasattr(self, "_status_panel") or self._status_panel is None:
            self._status_panel = StatusPanel(self.memory)
            self._status_panel.move(self.x() + self.width() + 10, self.y())
        self._status_panel.show()
        self._status_panel.refresh()

    def _reset_memory(self):
        import random
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要让梅尔忘掉一切喵？\n\n聊天记录、好感度、记忆都会清空。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.memory.reset_all()
            self._show_bubble(
                "-什么都没发生喵。" if random.random() < 0.1 else "……你是谁喵？",
                3000,
            )

    def _reopen_setup_wizard(self):
        try:
            from wizard.app import SetupWizard
            self._setup_wizard = SetupWizard()
            self._setup_wizard.show()
        except Exception as e:
            safe_print(f"[pet] 启动配置向导失败: {e}")
            self._show_bubble(f"启动配置向导失败喵: {e}", 3000)
