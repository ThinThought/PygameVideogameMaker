from __future__ import annotations

from pathlib import Path
import pygame
from rich.console import Console
from rich.panel import Panel

from game.core.clock import GameClock
from game.core.resources import Resources
from game.core.config import WindowConfig
from game.core.audio import AudioManager

import game.scenes as scenes_mod
from game.scenes.base import Scene




console = Console()


def _build_scenes() -> list[type[Scene]]:
    scene_classes = []
    for name in getattr(scenes_mod, "__all__", []):
        obj = getattr(scenes_mod, name, None)
        if isinstance(obj, type) and issubclass(obj, Scene):
            scene_classes.append(obj)

    return scene_classes


class App:
    def __init__(self, config: WindowConfig) -> None:
        self.cfg = config

        pygame.init()
        pygame.joystick.init()

        self.joysticks: list[pygame.joystick.Joystick] = []
        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            self.joysticks.append(js)

        self.joy_buttons_down: set[int] = set()

        pygame.display.set_caption(self.cfg.title)
        self.screen = pygame.display.set_mode((self.cfg.width, self.cfg.height))

        self.clock = GameClock(self.cfg.fps)

        root = Path(__file__).resolve().parents[2]
        assets_dir = root / "assets"
        self.resources = Resources(assets_dir)

        self.audio = AudioManager(assets_dir)
        self.audio.init()

        self.running = True

        self.scenes = _build_scenes()
        self._scene_index = 1
        self.scene: Scene | None = None

        console.print(Panel.fit("✅ Pygame initialized", border_style="green"))
        console.print(Panel.fit("F1/F2 o TAB/SHIFT+TAB: cambiar escena", border_style="cyan"))

        # HUD
        self.hud_font = pygame.font.Font(None, 33)
        self.hud_visible = True
        self.hud_height = 36
        self.hud_alpha = 235  # 0..255 (transparencia del fondo del HUD)

        self._toast_text: str | None = None
        self._toast_t = 0.0

        # Render target cache (evita alloc cada frame)
        self._scene_surf: pygame.Surface | None = None
        self._scene_surf_size: tuple[int, int] | None = None

    # --- Scene switching -------------------------------------------------
    def _wrap_index(self, index: int) -> int:
        return 0 if not self.scenes else index % len(self.scenes)

    def set_scene(self, index: int) -> None:
        if not self.scenes:
            return

        new_index = self._wrap_index(index)
        if new_index == self._scene_index and self.scene is not None:
            return

        if self.scene is not None:
            self.scene.on_exit(self)

        self._scene_index = new_index
        scene_cls = self.scenes[self._scene_index]
        self.scene = scene_cls()
        self.scene.on_enter(self)

        self._toast_text = f"{self.scene.__class__.__name__}  ({self._scene_index + 1}/{len(self.scenes)})"
        self._toast_t = 1.2

        console.print(
            Panel.fit(
                f"🎬 Scene -> {self.scene.__class__.__name__} ({self._scene_index + 1}/{len(self.scenes)})",
                border_style="magenta",
            )
        )

    def cycle_scene(self, step: int = 1) -> None:
        self.set_scene(self._scene_index + step)

    def next_scene(self) -> None:
        self.cycle_scene(+1)

    def prev_scene(self) -> None:
        self.cycle_scene(-1)

    # --- HUD -------------------------------------------------------------

    def toggle_hud(self) -> None:
        self.hud_visible = not self.hud_visible
        self._toast_text = f"HUD {'ON' if self.hud_visible else 'OFF'}"
        self._toast_t = 1.0
        # fuerza recreación del render target (viewport cambia)
        self._scene_surf_size = None

    def scene_viewport(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        hud_h = self.hud_height if self.hud_visible else 0
        return pygame.Rect(0, 0, w, h - hud_h)

    def hud_rect(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(0, h - self.hud_height, w, self.hud_height)

    def _ensure_scene_surface(self, vp: pygame.Rect) -> pygame.Surface:
        size = (vp.w, vp.h)
        if self._scene_surf is None or self._scene_surf_size != size:
            self._scene_surf = pygame.Surface(size).convert()
            self._scene_surf_size = size
        return self._scene_surf

    # --- Main loop -------------------------------------------------------

    def run(self) -> None:
        if self.scene is None:
            self.set_scene(self._scene_index)

        if self.scene is None:
            return

        while self.running:
            dt = self.clock.tick()

            if self._toast_t > 0:
                self._toast_t -= dt
                if self._toast_t <= 0:
                    self._toast_text = None

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    continue

                if ev.type == pygame.KEYDOWN:
                    # HUD toggle
                    if ev.key == pygame.K_h:
                        self.toggle_hud()
                        continue

                    # Scene switching: F1/F2 o TAB/SHIFT+TAB
                    if ev.key in (pygame.K_F2, pygame.K_TAB) and not (ev.mod & pygame.KMOD_SHIFT):
                        self.next_scene()
                        continue

                    if ev.key == pygame.K_F1 or (ev.key == pygame.K_TAB and (ev.mod & pygame.KMOD_SHIFT)):
                        self.prev_scene()
                        continue


                if ev.type == pygame.JOYBUTTONDOWN:
                    self.joy_buttons_down.add(ev.button)

                    # combo: 12 + 14
                    if 12 in self.joy_buttons_down and 14 in self.joy_buttons_down:
                        self.next_scene()
                        self.joy_buttons_down.clear()
                        continue

                    if ev.button == 15:  # botón 11 solo
                        self.prev_scene()
                        self.joy_buttons_down.clear()
                        continue

                    if ev.button == 16:  # botón 9 solo
                        self.next_scene()
                        self.joy_buttons_down.clear()
                        continue

                if ev.type == pygame.JOYBUTTONUP:
                    self.joy_buttons_down.discard(ev.button)

                if self.scene is not None:
                    self.scene.handle_event(self, ev)

            # Update
            if self.scene is not None:
                self.scene.update(self, dt)

            # Render scene into viewport-sized surface
            vp = self.scene_viewport()
            scene_surf = self._ensure_scene_surface(vp)
            if self.scene is not None:
                self.scene.render(self, scene_surf)
            self.screen.blit(scene_surf, vp.topleft)

            # HUD overlay
            if self.hud_visible:
                self._render_hud(dt)

            pygame.display.flip()

        if self.scene is not None:
            self.scene.on_exit(self)
        self.audio.stop_all_sounds()
        self.audio.stop_music()
        pygame.quit()

    def _render_hud(self, dt: float) -> None:
        r = self.hud_rect()
        w, bar_h, bar_y = r.w, r.h, r.y

        # Fondo con alpha
        bar = pygame.Surface((w, bar_h), pygame.SRCALPHA)
        bar.fill((20, 20, 20, int(self.hud_alpha)))
        self.screen.blit(bar, (0, bar_y))

        fps = 0.0 if dt <= 0 else (1.0 / dt)

        left_text = f"{self.scene.__class__.__name__}  [{self._scene_index + 1}/{len(self.scenes)}]"
        center_text = f"FPS {fps:0.1f}   dt {dt * 1000:0.1f} ms"
        right_text = self._toast_text or "F1/F2  TAB / SHIFT+TAB"

        pad_x = 12
        y = bar_y + (bar_h - self.hud_font.get_height()) // 2

        t_left = self.hud_font.render(left_text, True, (255, 255, 255))
        self.screen.blit(t_left, (pad_x, y))

        t_center = self.hud_font.render(center_text, True, (200, 200, 200))
        cx = (w - t_center.get_width()) // 2
        self.screen.blit(t_center, (cx, y))

        t_right = self.hud_font.render(right_text, True, (180, 220, 180))
        rx = w - t_right.get_width() - pad_x
        self.screen.blit(t_right, (rx, y))

        pygame.draw.line(self.screen, (70, 70, 70), (0, bar_y), (w, bar_y), 1)
