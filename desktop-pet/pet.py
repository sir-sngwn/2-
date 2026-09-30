#!/usr/bin/env python3
"""
Desktop Pet (Shimeji Style)
PyQt6 / Tkinter 하이브리드 투명 오버레이 윈도우 데스크톱 펫 런타임 엔진.
PyQt6가 설치되어 있으면 고성능 Qt 엔진을 사용하고,
PyQt6가 미설치된 환경에서는 추가 설치 없이 즉시 실행 가능한 Tkinter 투명 엔진으로 자동 폴백합니다.
중력/물리 시뮬레이션, 바닥/화면 경계 충돌 판정, 확률 기반 행동 상태머신,
마우스 드래그 & 던지기, 우클릭 컨텍스트 메뉴(크기 조절, 복제, 종료)를 완벽 지원합니다.
"""

import os
import sys
import time
import random
import subprocess
from pathlib import Path

# 상태 정의
STATE_IDLE = "idle"
STATE_WALK_LEFT = "walk_left"
STATE_WALK_RIGHT = "walk_right"
STATE_FALL = "fall"
STATE_DRAG = "drag"
STATE_SIT = "sit"
STATE_JUMP = "jump"

# Qt 사용 가능 여부 확인
QT_LIB = None
try:
    from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
    from PyQt6.QtGui import QPixmap, QPainter, QAction, QActionGroup
    from PyQt6.QtWidgets import QApplication, QWidget, QMenu
    QT_LIB = "PyQt6"
except ImportError:
    try:
        from PySide6.QtCore import Qt, QTimer, QPoint, QRect
        from PySide6.QtGui import QPixmap, QPainter, QAction, QActionGroup
        from PySide6.QtWidgets import QApplication, QWidget, QMenu
        QT_LIB = "PySide6"
    except ImportError:
        QT_LIB = None


# ===================================================================== #
#                   1. PyQt6 / PySide6 기반 런타임 엔진                   #
# ===================================================================== #
ACTIVE_QT_PETS = []

if QT_LIB:
    class DesktopPetQt(QWidget):
        def __init__(self, assets_dir: Path, scale: float = 1.0, initial_pos=None):
            super().__init__()
            ACTIVE_QT_PETS.append(self)

            self.assets_dir = Path(assets_dir)
            self.scale = scale
            self.base_size = (128, 128)

            self.sprites = {}
            self.load_sprites()

            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.SubWindow
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

            self.gravity = 0.85
            self.terminal_velocity = 20.0
            self.restitution = 0.28

            self.x = 200.0
            self.y = 100.0
            self.vx = 0.0
            self.vy = 0.0
            self.is_grounded = False

            self.is_dragging = False
            self.drag_offset = QPoint()
            self.mouse_history = []

            self.state = STATE_FALL
            self.state_timer = 0.0
            self.state_duration = 2.0
            self.current_frame = 0

            self.update_dimensions()
            screen_geo = self.get_screen_geometry()

            if initial_pos:
                self.x, self.y = float(initial_pos[0]), float(initial_pos[1])
            else:
                self.x = float(random.randint(screen_geo.left() + 50, max(screen_geo.left() + 60, screen_geo.right() - 200)))
                self.y = float(screen_geo.top() + 60)

            self.move(int(self.x), int(self.y))

            self.physics_timer = QTimer(self)
            self.physics_timer.timeout.connect(self.physics_tick)
            self.physics_timer.start(16)

            self.anim_timer = QTimer(self)
            self.anim_timer.timeout.connect(self.animation_tick)
            self.anim_timer.start(160)

            self.setMouseTracking(True)
            self.show()

        def get_screen_geometry(self) -> QRect:
            screen = QApplication.screenAt(QPoint(int(self.x), int(self.y)))
            if not screen:
                screen = QApplication.primaryScreen()
            return screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        def update_dimensions(self):
            w = int(self.base_size[0] * self.scale)
            h = int(self.base_size[1] * self.scale)
            self.setFixedSize(w, h)

        def load_sprites(self):
            self.sprites = {
                STATE_IDLE: [],
                STATE_WALK_LEFT: [],
                STATE_WALK_RIGHT: [],
                STATE_FALL: [],
                STATE_DRAG: [],
                STATE_SIT: [],
            }
            for state_name in [STATE_IDLE, STATE_FALL, STATE_DRAG, STATE_SIT]:
                p = self.assets_dir / state_name
                if p.exists():
                    for f in sorted(p.glob("*.png")):
                        self.sprites[state_name].append(QPixmap(str(f)))

            walk_p = self.assets_dir / "walk"
            if walk_p.exists():
                for f in sorted(walk_p.glob("*.png")):
                    if "left" in f.stem:
                        self.sprites[STATE_WALK_LEFT].append(QPixmap(str(f)))
                    elif "right" in f.stem:
                        self.sprites[STATE_WALK_RIGHT].append(QPixmap(str(f)))

            fallback = self.sprites[STATE_IDLE][0] if self.sprites[STATE_IDLE] else QPixmap()
            for k, frames in self.sprites.items():
                if not frames:
                    self.sprites[k] = [fallback]

        def set_state(self, new_state: str, duration: float = 3.0):
            if self.state == new_state:
                return
            self.state = new_state
            self.state_timer = 0.0
            self.state_duration = duration
            self.current_frame = 0

        def decide_ground_behavior(self):
            roll = random.random()
            if roll < 0.40:
                self.vx = 0.0
                self.set_state(STATE_IDLE, random.uniform(2.5, 5.0))
            elif roll < 0.70:
                walk_dir = STATE_WALK_LEFT if random.random() < 0.5 else STATE_WALK_RIGHT
                speed = 2.2
                self.vx = -speed if walk_dir == STATE_WALK_LEFT else speed
                self.set_state(walk_dir, random.uniform(3.0, 6.0))
            elif roll < 0.90:
                self.vx = 0.0
                self.set_state(STATE_SIT, random.uniform(3.0, 7.0))
            else:
                self.vy = -random.uniform(11.0, 14.0)
                self.vx = random.uniform(-3.5, 3.5)
                self.is_grounded = False
                self.set_state(STATE_FALL, 1.0)

        def physics_tick(self):
            if self.is_dragging:
                return
            dt = 0.016
            screen_geo = self.get_screen_geometry()
            cur_w = self.width()
            cur_h = self.height()
            floor_y = float(screen_geo.bottom() - cur_h + 1)
            left_x = float(screen_geo.left())
            right_x = float(screen_geo.right() - cur_w + 1)

            if not self.is_grounded:
                self.vy += self.gravity
                if self.vy > self.terminal_velocity:
                    self.vy = self.terminal_velocity
                self.y += self.vy

                if self.state not in (STATE_FALL, STATE_DRAG):
                    self.set_state(STATE_FALL)

                if self.y >= floor_y:
                    self.y = floor_y
                    if abs(self.vy) > 3.5:
                        self.vy = -self.vy * self.restitution
                    else:
                        self.vy = 0.0
                        self.is_grounded = True
                        self.decide_ground_behavior()
            else:
                self.y = floor_y

            self.x += self.vx
            if self.x <= left_x:
                self.x = left_x
                self.vx = abs(self.vx)
                if self.state == STATE_WALK_LEFT:
                    self.set_state(STATE_WALK_RIGHT, self.state_duration - self.state_timer)
            elif self.x >= right_x:
                self.x = right_x
                self.vx = -abs(self.vx)
                if self.state == STATE_WALK_RIGHT:
                    self.set_state(STATE_WALK_LEFT, self.state_duration - self.state_timer)

            self.move(int(self.x), int(self.y))

            if self.is_grounded:
                self.state_timer += dt
                if self.state_timer >= self.state_duration:
                    self.decide_ground_behavior()

        def animation_tick(self):
            frames = self.sprites.get(self.state, []) or self.sprites.get(STATE_IDLE, [])
            if frames:
                self.current_frame = (self.current_frame + 1) % len(frames)
                self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            frames = self.sprites.get(self.state, []) or self.sprites.get(STATE_IDLE, [])
            if frames:
                pix = frames[self.current_frame % len(frames)]
                if not pix.isNull():
                    scaled_pix = pix.scaled(
                        self.width(), self.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    x = (self.width() - scaled_pix.width()) // 2
                    y = self.height() - scaled_pix.height()
                    painter.drawPixmap(x, y, scaled_pix)

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = True
                self.is_grounded = False
                self.vx = 0.0
                self.vy = 0.0
                self.set_state(STATE_DRAG)
                global_pos = event.globalPosition().toPoint()
                self.drag_offset = global_pos - self.pos()
                self.mouse_history = [(time.time(), global_pos)]
                event.accept()
            elif event.button() == Qt.MouseButton.RightButton:
                self.show_context_menu(event.globalPosition().toPoint())
                event.accept()

        def mouseMoveEvent(self, event):
            if self.is_dragging:
                global_pos = event.globalPosition().toPoint()
                new_pos = global_pos - self.drag_offset
                self.x = float(new_pos.x())
                self.y = float(new_pos.y())
                self.move(int(self.x), int(self.y))
                now = time.time()
                self.mouse_history.append((now, global_pos))
                self.mouse_history = [item for item in self.mouse_history if now - item[0] <= 0.15]
                event.accept()

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
                self.is_dragging = False
                now = time.time()
                self.mouse_history = [item for item in self.mouse_history if now - item[0] <= 0.15]
                if len(self.mouse_history) >= 2:
                    t0, p0 = self.mouse_history[0]
                    t1, p1 = self.mouse_history[-1]
                    dt = max(0.016, t1 - t0)
                    throw_vx = (p1.x() - p0.x()) / (dt * 60.0) * 1.2
                    throw_vy = (p1.y() - p0.y()) / (dt * 60.0) * 1.2
                    self.vx = max(-16.0, min(16.0, throw_vx))
                    self.vy = max(-22.0, min(18.0, throw_vy))
                else:
                    self.vx = 0.0
                    self.vy = 1.0
                self.set_state(STATE_FALL)
                event.accept()

        def show_context_menu(self, global_pos: QPoint):
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2b2b2b; color: #ffffff;
                    border: 1px solid #444444; border-radius: 8px; padding: 4px;
                    font-family: sans-serif; font-size: 13px;
                }
                QMenu::item { padding: 6px 20px 6px 12px; border-radius: 4px; }
                QMenu::item:selected { background-color: #0078d4; }
                QMenu::separator { height: 1px; background-color: #444444; margin: 4px 8px; }
            """)
            scale_menu = menu.addMenu("🔍 크기 조절 (Scale)")
            scale_group = QActionGroup(scale_menu)
            for s, label in [(1.0, "1.0x (128px)"), (1.5, "1.5x (192px)"), (2.0, "2.0x (256px)")]:
                action = QAction(label, scale_menu, checkable=True)
                if abs(self.scale - s) < 0.01:
                    action.setChecked(True)
                action.triggered.connect(lambda checked, new_s=s: self.change_scale(new_s))
                scale_group.addAction(action)
                scale_menu.addAction(action)

            menu.addSeparator()
            menu.addAction("➕ 펫 복제 (Clone Pet)").triggered.connect(self.clone_pet)
            menu.addAction("🪂 높이 띄우기 (Toss Up)").triggered.connect(self.toss_up)
            menu.addSeparator()
            menu.addAction("📁 에셋 폴더 열기 (Open Assets)").triggered.connect(self.open_assets_folder)
            menu.addAction("🔄 에셋 다시 불러오기 (Reload)").triggered.connect(self.reload_assets)
            menu.addSeparator()
            menu.addAction("❌ 이 펫 닫기 (Close)").triggered.connect(self.close_pet)
            menu.addAction("🚪 전체 종료 (Exit All)").triggered.connect(QApplication.instance().quit)
            menu.exec(global_pos)

        def change_scale(self, new_scale: float):
            old_h = self.height()
            self.scale = new_scale
            self.update_dimensions()
            self.y -= (self.height() - old_h)
            self.move(int(self.x), int(self.y))
            self.update()

        def toss_up(self):
            self.is_grounded = False
            self.vy = -16.0
            self.vx = random.uniform(-4.0, 4.0)
            self.set_state(STATE_FALL)

        def clone_pet(self):
            spawn_x = self.x + random.randint(-40, 40)
            spawn_y = max(50.0, self.y - 120)
            DesktopPetQt(self.assets_dir, scale=self.scale, initial_pos=(spawn_x, spawn_y))

        def open_assets_folder(self):
            p = str(self.assets_dir.resolve())
            if sys.platform == "darwin":
                subprocess.Popen(["open", p])
            elif sys.platform == "win32":
                os.startfile(p)
            else:
                subprocess.Popen(["xdg-open", p])

        def reload_assets(self):
            self.load_sprites()
            self.update()

        def close_pet(self):
            if self in ACTIVE_QT_PETS:
                ACTIVE_QT_PETS.remove(self)
            self.close()
            if not ACTIVE_QT_PETS:
                QApplication.instance().quit()


# ===================================================================== #
#            2. Tkinter 기반 경량 투명 오버레이 엔진 (Zero Dependency)     #
# ===================================================================== #
ACTIVE_TK_PETS = []

class DesktopPetTk:
    def __init__(self, master, assets_dir: Path, scale: float = 1.0, initial_pos=None):
        ACTIVE_TK_PETS.append(self)
        self.master = master
        self.assets_dir = Path(assets_dir)
        self.scale = scale
        self.base_size = (128, 128)

        # 윈도우 생성
        if master is None:
            import tkinter as tk
            self.window = tk.Tk()
            self.is_root = True
        else:
            import tkinter as tk
            self.window = tk.Toplevel(master)
            self.is_root = False

        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)

        # OS별 투명 배경 처리
        if sys.platform == "darwin":
            self.window.config(bg='systemTransparent')
            self.window.attributes('-transparent', True)
            self.bg_color = 'systemTransparent'
        elif sys.platform == "win32":
            self.bg_color = '#010203'
            self.window.config(bg=self.bg_color)
            self.window.wm_attributes('-transparentcolor', self.bg_color)
        else:
            self.bg_color = '#ffffff'
            self.window.attributes('-type', 'splash')

        self.w = int(self.base_size[0] * self.scale)
        self.h = int(self.base_size[1] * self.scale)

        import tkinter as tk
        self.canvas = tk.Canvas(
            self.window, width=self.w, height=self.h,
            bg=self.bg_color, highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)
        self.image_item = self.canvas.create_image(self.w // 2, self.h, anchor='s')

        # 물리 & 상태
        self.gravity = 0.85
        self.terminal_velocity = 20.0
        self.restitution = 0.28
        self.is_grounded = False

        self.state = STATE_FALL
        self.state_timer = 0.0
        self.state_duration = 2.0
        self.current_frame = 0

        self.is_dragging = False
        self.mouse_history = []

        # 스프라이트 로드
        self.raw_sprites = {}
        self.tk_sprites = {}
        self.load_sprites()

        # 화면 위치 초기화
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()

        if initial_pos:
            self.x, self.y = float(initial_pos[0]), float(initial_pos[1])
        else:
            self.x = float(random.randint(100, max(120, screen_w - 200)))
            self.y = 80.0
        self.vx = 0.0
        self.vy = 0.0

        self.update_window_position()

        # 이벤트 바인딩
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_motion)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        # 우클릭 (macOS / Windows / Linux)
        self.canvas.bind('<Button-2>', self.show_context_menu)
        self.canvas.bind('<Button-3>', self.show_context_menu)
        self.canvas.bind('<Control-Button-1>', self.show_context_menu)

        # 루프 가동
        self.schedule_physics()
        self.schedule_animation()

    def update_window_position(self):
        self.window.geometry(f"{self.w}x{self.h}+{int(self.x)}+{int(self.y)}")

    def load_sprites(self):
        try:
            from PIL import Image, ImageTk
            self.has_pil = True
        except ImportError:
            self.has_pil = False

        self.file_sprites = {
            STATE_IDLE: [], STATE_WALK_LEFT: [], STATE_WALK_RIGHT: [],
            STATE_FALL: [], STATE_DRAG: [], STATE_SIT: []
        }
        for st in [STATE_IDLE, STATE_FALL, STATE_DRAG, STATE_SIT]:
            p = self.assets_dir / st
            if p.exists():
                for f in sorted(p.glob("*.png")):
                    self.file_sprites[st].append(f)

        walk_p = self.assets_dir / "walk"
        if walk_p.exists():
            for f in sorted(walk_p.glob("*.png")):
                if "left" in f.stem:
                    self.file_sprites[STATE_WALK_LEFT].append(f)
                elif "right" in f.stem:
                    self.file_sprites[STATE_WALK_RIGHT].append(f)

        fallback = self.file_sprites[STATE_IDLE][0] if self.file_sprites[STATE_IDLE] else None
        for k in self.file_sprites:
            if not self.file_sprites[k] and fallback:
                self.file_sprites[k] = [fallback]

        self.cache_tk_sprites()

    def cache_tk_sprites(self):
        import tkinter as tk
        self.tk_sprites = {}

        if self.has_pil:
            from PIL import Image, ImageTk
            for st, files in self.file_sprites.items():
                self.tk_sprites[st] = []
                for f in files:
                    try:
                        img = Image.open(f).convert("RGBA")
                        scaled = img.resize((self.w, self.h), Image.Resampling.LANCZOS)
                        self.tk_sprites[st].append(ImageTk.PhotoImage(scaled))
                    except Exception:
                        pass
        else:
            for st, files in self.file_sprites.items():
                self.tk_sprites[st] = []
                for f in files:
                    try:
                        photo = tk.PhotoImage(file=str(f))
                        if self.scale > 1.2:
                            photo = photo.zoom(int(round(self.scale)))
                        self.tk_sprites[st].append(photo)
                    except Exception:
                        pass

    def set_state(self, new_state: str, duration: float = 3.0):
        if self.state == new_state:
            return
        self.state = new_state
        self.state_timer = 0.0
        self.state_duration = duration
        self.current_frame = 0

    def decide_ground_behavior(self):
        roll = random.random()
        if roll < 0.40:
            self.vx = 0.0
            self.set_state(STATE_IDLE, random.uniform(2.5, 5.0))
        elif roll < 0.70:
            walk_dir = STATE_WALK_LEFT if random.random() < 0.5 else STATE_WALK_RIGHT
            speed = 2.2
            self.vx = -speed if walk_dir == STATE_WALK_LEFT else speed
            self.set_state(walk_dir, random.uniform(3.0, 6.0))
        elif roll < 0.90:
            self.vx = 0.0
            self.set_state(STATE_SIT, random.uniform(3.0, 7.0))
        else:
            self.vy = -random.uniform(11.0, 14.0)
            self.vx = random.uniform(-3.5, 3.5)
            self.is_grounded = False
            self.set_state(STATE_FALL, 1.0)

    def schedule_physics(self):
        self.physics_tick()
        self.window.after(16, self.schedule_physics)

    def physics_tick(self):
        if self.is_dragging:
            return
        dt = 0.016
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()

        # macOS Dock / Windows 작업표시줄 여유
        dock_buffer = 40 if sys.platform == "darwin" else 48
        floor_y = float(screen_h - self.h - dock_buffer)
        left_x = 0.0
        right_x = float(screen_w - self.w)

        if not self.is_grounded:
            self.vy += self.gravity
            if self.vy > self.terminal_velocity:
                self.vy = self.terminal_velocity
            self.y += self.vy

            if self.state not in (STATE_FALL, STATE_DRAG):
                self.set_state(STATE_FALL)

            if self.y >= floor_y:
                self.y = floor_y
                if abs(self.vy) > 3.5:
                    self.vy = -self.vy * self.restitution
                else:
                    self.vy = 0.0
                    self.is_grounded = True
                    self.decide_ground_behavior()
        else:
            self.y = floor_y

        self.x += self.vx
        if self.x <= left_x:
            self.x = left_x
            self.vx = abs(self.vx)
            if self.state == STATE_WALK_LEFT:
                self.set_state(STATE_WALK_RIGHT, self.state_duration - self.state_timer)
        elif self.x >= right_x:
            self.x = right_x
            self.vx = -abs(self.vx)
            if self.state == STATE_WALK_RIGHT:
                self.set_state(STATE_WALK_LEFT, self.state_duration - self.state_timer)

        self.update_window_position()

        if self.is_grounded:
            self.state_timer += dt
            if self.state_timer >= self.state_duration:
                self.decide_ground_behavior()

    def schedule_animation(self):
        self.animation_tick()
        self.window.after(160, self.schedule_animation)

    def animation_tick(self):
        frames = self.tk_sprites.get(self.state, []) or self.tk_sprites.get(STATE_IDLE, [])
        if frames:
            self.current_frame = (self.current_frame + 1) % len(frames)
            current_photo = frames[self.current_frame]
            self.canvas.itemconfig(self.image_item, image=current_photo)
            # 참조 유지
            self.canvas.current_photo = current_photo

    def on_press(self, event):
        self.is_dragging = True
        self.is_grounded = False
        self.vx = 0.0
        self.vy = 0.0
        self.set_state(STATE_DRAG)
        self.drag_start_x = event.x_root - self.x
        self.drag_start_y = event.y_root - self.y
        self.mouse_history = [(time.time(), event.x_root, event.y_root)]

    def on_motion(self, event):
        if self.is_dragging:
            self.x = float(event.x_root - self.drag_start_x)
            self.y = float(event.y_root - self.drag_start_y)
            self.update_window_position()
            now = time.time()
            self.mouse_history.append((now, event.x_root, event.y_root))
            self.mouse_history = [item for item in self.mouse_history if now - item[0] <= 0.15]

    def on_release(self, event):
        if self.is_dragging:
            self.is_dragging = False
            now = time.time()
            self.mouse_history = [item for item in self.mouse_history if now - item[0] <= 0.15]
            if len(self.mouse_history) >= 2:
                t0, x0, y0 = self.mouse_history[0]
                t1, x1, y1 = self.mouse_history[-1]
                dt = max(0.016, t1 - t0)
                throw_vx = (x1 - x0) / (dt * 60.0) * 1.2
                throw_vy = (y1 - y0) / (dt * 60.0) * 1.2
                self.vx = max(-16.0, min(16.0, throw_vx))
                self.vy = max(-22.0, min(18.0, throw_vy))
            else:
                self.vx = 0.0
                self.vy = 1.0
            self.set_state(STATE_FALL)

    def show_context_menu(self, event):
        import tkinter as tk
        menu = tk.Menu(self.window, tearoff=0)

        scale_menu = tk.Menu(menu, tearoff=0)
        scale_menu.add_command(label="1.0x (128px)", command=lambda: self.change_scale(1.0))
        scale_menu.add_command(label="1.5x (192px)", command=lambda: self.change_scale(1.5))
        scale_menu.add_command(label="2.0x (256px)", command=lambda: self.change_scale(2.0))
        menu.add_cascade(label="🔍 크기 조절 (Scale)", menu=scale_menu)

        menu.add_separator()
        menu.add_command(label="➕ 펫 복제 (Clone Pet)", command=self.clone_pet)
        menu.add_command(label="🪂 높이 띄우기 (Toss Up)", command=self.toss_up)
        menu.add_separator()
        menu.add_command(label="📁 에셋 폴더 열기 (Open Assets)", command=self.open_assets_folder)
        menu.add_command(label="🔄 에셋 다시 불러오기 (Reload)", command=self.reload_assets)
        menu.add_separator()
        menu.add_command(label="❌ 이 펫 닫기 (Close)", command=self.close_pet)
        menu.add_command(label="🚪 전체 종료 (Exit All)", command=self.exit_all)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def change_scale(self, new_scale: float):
        old_h = self.h
        self.scale = new_scale
        self.w = int(self.base_size[0] * self.scale)
        self.h = int(self.base_size[1] * self.scale)
        self.canvas.config(width=self.w, height=self.h)
        self.canvas.coords(self.image_item, self.w // 2, self.h)
        self.cache_tk_sprites()
        self.y -= (self.h - old_h)
        self.update_window_position()

    def toss_up(self):
        self.is_grounded = False
        self.vy = -16.0
        self.vx = random.uniform(-4.0, 4.0)
        self.set_state(STATE_FALL)

    def clone_pet(self):
        root = self.window if self.is_root else self.master
        spawn_x = self.x + random.randint(-40, 40)
        spawn_y = max(50.0, self.y - 120)
        DesktopPetTk(root, self.assets_dir, scale=self.scale, initial_pos=(spawn_x, spawn_y))

    def open_assets_folder(self):
        p = str(self.assets_dir.resolve())
        if sys.platform == "darwin":
            subprocess.Popen(["open", p])
        elif sys.platform == "win32":
            os.startfile(p)
        else:
            subprocess.Popen(["xdg-open", p])

    def reload_assets(self):
        self.load_sprites()

    def close_pet(self):
        if self in ACTIVE_TK_PETS:
            ACTIVE_TK_PETS.remove(self)
        self.window.destroy()
        if not ACTIVE_TK_PETS:
            sys.exit(0)

    def exit_all(self):
        sys.exit(0)


# ===================================================================== #
#                              메인 진입점                              #
# ===================================================================== #
def main():
    script_dir = Path(__file__).resolve().parent
    assets_dir = script_dir / "assets"

    idle_dir = assets_dir / "idle"
    if not idle_dir.exists() or not list(idle_dir.glob("*.png")):
        print("💡 에셋이 없어 기본 마스코트 스프라이트를 자동 생성합니다...")
        try:
            from asset_pipeline import process_image
            process_image(None, str(assets_dir))
        except Exception as e:
            print(f"⚠️ 에셋 자동 생성 실패: {e}")

    # PyQt6 / PySide6가 설치되어 있으면 고성능 Qt 엔진 실행
    if QT_LIB:
        print(f"🚀 [{QT_LIB}] 런타임 엔진으로 데스크톱 펫을 실행합니다!")
        app = QApplication(sys.argv)
        app.setApplicationName("DesktopPet")
        DesktopPetQt(assets_dir, scale=1.0)
        sys.exit(app.exec())
    else:
        # PyQt6 미설치 시 무설치 Tkinter 엔진으로 즉시 실행
        print("🚀 [Tkinter] 내장 투명 오버레이 엔진으로 데스크톱 펫을 즉시 실행합니다!")
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 더미 마스터 숨김
        DesktopPetTk(root, assets_dir, scale=1.0)
        root.mainloop()


if __name__ == "__main__":
    main()
