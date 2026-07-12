"""PNG / Live2D render host: switch modes, size, hit region, standby."""
from __future__ import annotations

import os
import sys

from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainterPath, QRegion

from meapet.desktop.renderer import SpriteRenderer
from meapet.desktop.widgets import SizeScaleDialog
from meapet.utils import safe_print


class PetRenderHostMixin:
    def _init_renderer(self):
        """PNG first (fast), Live2D deferred."""
        char = self.config.get("character", {})
        display_cfg = self.config.get("display", {})
        self._scale = display_cfg.get("scale", 0.5)
        self._size_factor = display_cfg.get("size_factor", 1.0)

        self._use_live2d = False
        self._l2d_model = None
        self._l2d_pending = False
        self.renderer = None
        self.sprite_label = None

        sprite_dir = self.config.get(
            "sprite_dir",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sprites"),
        )
        # Prefer project sprites via config default; fall back to PROJECT_ROOT
        if not os.path.isdir(sprite_dir):
            from meapet.paths import project_path
            sprite_dir = project_path("sprites")
        outfit = char.get("default_outfit", "01")
        direction = char.get("default_direction", "A")
        self.sprite_label = QLabel(self)
        self.sprite_label.setAttribute(Qt.WA_TranslucentBackground)
        self.sprite_label.setStyleSheet("background: transparent;")
        self.sprite_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.sprite_label.show()
        self.renderer = SpriteRenderer(sprite_dir, outfit, direction)
        safe_print(f"[toggle] PNG renderer 创建成功: {self.renderer is not None}")
        self.renderer.expression_changed.connect(self._on_sprite_changed)
        self._update_sprite()
        self.renderer.start_blink_animation()

        l2d_cfg = self.config.get("live2d", {})
        model_dir = l2d_cfg.get("model_dir", "")
        if os.environ.get("MEAPET_FORCE_PNG", "").strip() in ("1", "true", "yes"):
            safe_print("[toggle] MEAPET_FORCE_PNG=1, skip Live2D")
        elif l2d_cfg.get("enabled", False) and os.path.isdir(model_dir):
            self._l2d_pending = True
            # 等主窗口真正 show 后再切 Live2D，降低 OpenGL 初始化闪退概率
            QTimer.singleShot(800, self._deferred_init_live2d)

    def _deferred_init_live2d(self):
        try:
            from meapet.desktop.live2d_widget import init_live2d
            init_live2d()
            png_label = self.sprite_label
            self._init_live2d()
            # 先确认 Live2D 控件真的建好了再拆 PNG，避免“黑屏/消失像闪退”
            if not self.sprite_label:
                raise RuntimeError("Live2D widget not created")
            if png_label is not None and png_label is not self.sprite_label:
                try:
                    png_label.hide()
                    png_label.deleteLater()
                except Exception:
                    pass
            self._use_live2d = True
            if self._size_factor != 1.0:
                self._size_factor_preview(self._size_factor)
            # 重新落到右下角并强制前置，防止 OpenGL 窗体跑到屏外/0 尺寸
            try:
                self._place_bottom_right()
            except Exception:
                pass
            self.setVisible(True)
            self.show()
            self.raise_()
            self.activateWindow()
            if self.sprite_label:
                self.sprite_label.show()
                self.sprite_label.raise_()
            try:
                self._apply_hit_region()
            except Exception:
                pass
            safe_print(
                f"[pet] Live2D 加载完成 size={self.width()}x{self.height()} "
                f"pos=({self.x()},{self.y()}) visible={self.isVisible()}"
            )
            try:
                if hasattr(self, "tray") and self.tray is not None:
                    self.tray.showMessage(
                        "MeaPet",
                        "Live2D 已加载。若看不见角色，请看右下角托盘或右键切换 PNG。",
                        3000,
                    )
            except Exception:
                pass
        except Exception as e:
            safe_print(f"[pet] Live2D 加载失败，使用 PNG: {e}")
            import traceback
            safe_print(traceback.format_exc())
            self._use_live2d = False
            self._l2d_model = None
            # 确保仍有可见 PNG
            try:
                if self.sprite_label is None or not isinstance(self.sprite_label, QLabel):
                    self.sprite_label = QLabel(self)
                    self.sprite_label.setAttribute(Qt.WA_TranslucentBackground)
                    self.sprite_label.setStyleSheet("background: transparent;")
                    self.sprite_label.show()
                if self.renderer is None:
                    from meapet.paths import project_path
                    char = self.config.get("character", {})
                    sprite_dir = self.config.get("sprite_dir") or project_path("sprites")
                    self.renderer = SpriteRenderer(
                        sprite_dir,
                        char.get("default_outfit", "01"),
                        char.get("default_direction", "A"),
                    )
                    self.renderer.expression_changed.connect(self._on_sprite_changed)
                    self.renderer.start_blink_animation()
                self._update_sprite()
                self.show()
            except Exception as e2:
                safe_print(f"[pet] PNG 回退也失败: {e2}")

    def _init_live2d(self):
        from meapet.desktop.live2d_widget import Live2DModel
        l2d_cfg = self.config.get("live2d", {})
        model_dir = l2d_cfg.get("model_dir", "")
        safe_print(f"[live2d] 开始初始化，model_dir={model_dir}")
        if not os.path.isdir(model_dir):
            safe_print("[live2d] 模型目录不存在，回退至 PNG")
            self._use_live2d = False
            return
        self._l2d_model = Live2DModel(model_dir)
        widget = self._l2d_model.create_widget(self)
        self.sprite_label = widget
        widget.head_patted.connect(self._on_head_patted)
        widget.tail_patted.connect(self._on_tail_patted)
        widget.show()
        w0 = widget.width()
        h0 = widget.height()
        widget.move(0, 0)
        widget.resize(w0, h0)
        self.resize(w0, h0)
        safe_print("[live2d] 初始化成功")

    def _safe_renderer(self):
        if self._use_live2d and self._l2d_model:
            return self._l2d_model
        return self.renderer

    def _safe_set_mood(self, mood: str):
        r = self._safe_renderer()
        if r:
            r.set_mood(mood)

    def _safe_set_expression(self, expr: str):
        r = self._safe_renderer()
        if r:
            r.set_expression(expr)

    def _update_sprite(self):
        if self._use_live2d:
            return
        pixmap = self.renderer.get_current_pixmap()
        if pixmap.isNull():
            return
        scaled = pixmap.scaled(
            int(pixmap.width() * self._scale * self._size_factor),
            int(pixmap.height() * self._scale * self._size_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.sprite_label.setPixmap(scaled)
        sw, sh = scaled.width(), scaled.height()
        self.sprite_label.move(0, 0)
        self.sprite_label.resize(scaled.size())
        self.resize(scaled.size())

    def _on_sprite_changed(self, code: str):
        self._update_sprite()

    def _size_factor_preview(self, factor: float):
        self._size_factor = factor
        if self._use_live2d and self.sprite_label:
            base_w, base_h = 400, 660
            new_w = max(80, int(base_w * factor))
            new_h = max(80, int(base_h * factor))
            self.sprite_label.resize(new_w, new_h)
            self.resize(new_w, new_h)
            self._apply_hit_region()
            QApplication.processEvents()
        else:
            if self.renderer is None:
                return
            pixmap = self.renderer.get_current_pixmap()
            if not pixmap.isNull():
                new_w = max(80, int(pixmap.width() * self._scale * factor))
                new_h = max(80, int(pixmap.height() * self._scale * factor))
                self.resize(new_w, new_h)
            self._update_sprite()
            self._apply_hit_region()
            QApplication.processEvents()
        self._position_bubble()

    def _open_size_dialog(self):
        dialog = SizeScaleDialog(self._size_factor, self)
        screen = QApplication.primaryScreen().availableGeometry()
        dlg_w, dlg_h = 280, 130
        x = self.x() + (self.width() - dlg_w) // 2
        y = self.y() + (self.height() - dlg_h) // 2
        x = max(screen.x(), min(x, screen.x() + screen.width() - dlg_w))
        y = max(screen.y(), min(y, screen.y() + screen.height() - dlg_h))
        dialog.move(x, y)
        if dialog.exec_() == QDialog.Accepted:
            new_factor = dialog.get_value()
            self._size_factor = new_factor
            self.config.setdefault("display", {})["size_factor"] = round(new_factor, 2)
            self._save_config()

    def _position_bubble(self):
        if self.bubble.isVisible():
            bubble_x = self.pos().x() + (self.width() - self.bubble.width()) // 2
            # Live2D 模式下气泡再往上移；随 size_factor 缩放（upstream 适配）
            offset = (250 * self._size_factor) if self._use_live2d else (180 * self._size_factor)
            bubble_y = self.pos().y() + self.height() - self.bubble.height() - int(offset)
            self.bubble.move(bubble_x, bubble_y)

    def _place_bottom_right(self):
        """放到主屏右下角，并钳制在可见区域内（防止多屏/DPI 导致“消失”）。"""
        screen = QApplication.primaryScreen().availableGeometry()
        w = max(self.width(), 80)
        h = max(self.height(), 80)
        x = screen.right() - w - 50
        y = screen.bottom() - h - 10
        # 钳制：至少 80% 窗口在主屏内
        x = max(screen.left(), min(x, screen.right() - max(80, w // 5)))
        y = max(screen.top(), min(y, screen.bottom() - max(80, h // 5)))
        self.move(x, y)
        safe_print(
            f"[place] screen=({screen.x()},{screen.y()},{screen.width()}x{screen.height()}) "
            f"-> pos=({x},{y}) size={w}x{h}"
        )

    def _apply_hit_region(self):
        if sys.platform == "win32":
            try:
                import win32gui
                hwnd = int(self.winId())
                w, h = self.width(), self.height()
                if not (w > 0 and h > 0):
                    return
                if self._use_live2d:
                    m = w // 16
                    t = h // 16
                    rgn = win32gui.CreateEllipticRgnIndirect((m, t, w - m, h - t))
                else:
                    rgn = win32gui.CreateRoundRectRgn(0, 0, w, h, 0, 0)
                win32gui.SetWindowRgn(hwnd, rgn, True)
                return
            except Exception as e:
                safe_print(f"[WARN] Win32 hit region failed, fallback to Qt mask: {e}")

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        if self._use_live2d:
            path = QPainterPath()
            path.addEllipse(QRectF(w // 16, h // 16, w - w // 8, h - h // 8))
            region = QRegion(path.toFillPolygon().toPolygon())
        else:
            region = QRegion(0, 0, w, h)
        self.setMask(region)

    def _toggle_standby(self):
        self._standby = not self._standby
        if self._standby:
            self._watcher_timer.stop()
            self._safe_set_expression("011")
            self._show_bubble("💤 梅尔酱待机中……", 0)
            self._position_bubble()
            self._set_standby_region()
        else:
            self._safe_set_expression("001")
            if hasattr(self, "bubble") and self.bubble:
                self.bubble.hide()
            self._show_bubble("✨ 梅尔酱回来了喵～", 2500)
            self._position_bubble()
            self._apply_hit_region()
            self._start_watcher_timer()

    def _set_standby_region(self):
        if sys.platform == "win32":
            try:
                import win32gui
                w, h = self.width(), self.height()
                margin_x = w // 4
                margin_y = h // 4
                rgn = win32gui.CreateRectRgn(
                    margin_x, margin_y, w - margin_x, h - margin_y
                )
                win32gui.SetWindowRgn(int(self.winId()), rgn, True)
                return
            except Exception as e:
                safe_print(f"[WARN] Standby region failed: {e}")
        from PyQt5.QtCore import QRect
        w, h = self.width(), self.height()
        margin_x = w // 4
        margin_y = h // 4
        region = QRegion(QRect(margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y))
        self.setMask(region)

    def _toggle_render_mode(self):
        if self._use_live2d:
            if self.sprite_label:
                self.sprite_label.shutdown()
                self.sprite_label.hide()
                self.sprite_label.deleteLater()
                self.sprite_label = None
            self._l2d_model = None
            self._use_live2d = False
            self.sprite_label = QLabel(self)
            self.sprite_label.setAttribute(Qt.WA_TranslucentBackground)
            self.sprite_label.setStyleSheet("background: transparent;")
            self.sprite_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.sprite_label.show()
            char = self.config.get("character", {})
            from meapet.paths import project_path
            sprite_dir = self.config.get("sprite_dir") or project_path("sprites")
            outfit = char.get("default_outfit", "01")
            direction = char.get("default_direction", "A")
            self.renderer = SpriteRenderer(sprite_dir, outfit, direction)
            self.renderer.expression_changed.connect(self._on_sprite_changed)
            self._update_sprite()
            self.renderer.start_blink_animation()
            if self._size_factor != 1.0:
                self._size_factor_preview(self._size_factor)
            self._apply_hit_region()
            self._show_bubble("🎭 切回 PNG 立绘喵～", 2500)
        else:
            if self.renderer:
                self.renderer.stop_blink_animation()
                self.renderer = None
            if self.sprite_label:
                self.sprite_label.hide()
                self.sprite_label.deleteLater()
                self.sprite_label = None
            self._use_live2d = True
            # 先写 config，避免 PNG→Live2D 中途崩溃导致下次仍按 PNG 启动（upstream fix）
            self.config.setdefault("live2d", {})["enabled"] = True
            self._save_config()
            self._init_live2d()
            if self.sprite_label:
                self.sprite_label.show()
                self.sprite_label.raise_()
            self.show()
            if self._size_factor != 1.0:
                self._size_factor_preview(self._size_factor)
            self._apply_hit_region()
            self._position_bubble()
            self._show_bubble("🎭 Live2D 模式喵～", 2500)

        self.config.setdefault("live2d", {})["enabled"] = self._use_live2d
        self._save_config()
