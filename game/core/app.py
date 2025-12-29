from __future__ import annotations

from collections import deque
from pathlib import Path
from time import perf_counter
from typing import NamedTuple, Type

import pygame

from game.core.audio import AudioManager
from game.core.clock import GameClock
from game.core.config import WindowConfig
from game.scenes import MainScene, EditorScene, Scene

from rich.console import Console
from rich.panel import Panel

console = Console()


class HudLine(NamedTuple):
    text: str
    color: tuple[int, int, int]
    align: str = "left"  # "left" | "center" | "right"


def _build_scenes() -> dict[str, Type[Scene]]:
    # SCENES: dict[str, Type[Scene]]
    import game.scenes as scenes_for_app

    return scenes_for_app.SCENES


class App:
    def __init__(self, config: WindowConfig) -> None:
        self.cfg = config

        pygame.init()
        pygame.joystick.init()

        self.joysticks: list[pygame.joystick.Joystick] = []
        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            js.init()
            self.joysticks.append(js)

        self.joy_buttons_down: set[int] = set()

        pygame.display.set_caption(self.cfg.title)
        self.screen_flags = 0
        if self.cfg.resizable:
            self.screen_flags |= pygame.RESIZABLE
        self.screen = pygame.display.set_mode(
            (self.cfg.width, self.cfg.height), self.screen_flags
        )

        self.clock = GameClock(self.cfg.fps)

        self.audio = AudioManager()
        self.audio.init()

        self.running = True

        # --- Scenes ------------------------------------------------------
        self.scenes: dict[str, Type[Scene]] = _build_scenes()
        self._scene_ids: list[str] = list(self.scenes.keys())

        # índice numérico para “ciclar”
        self._scene_index: int = 0
        if "main" in self.scenes:
            self._scene_index = self._scene_ids.index("main")

        self.scene: Scene | None = None

        console.print(Panel.fit("✅ Pygame initialized", border_style="green"))
        console.print(
            Panel.fit("F1/F2 o TAB/SHIFT+TAB: cambiar escena", border_style="cyan")
        )

        # HUD
        self.hud_font = pygame.font.Font(None, 33)
        self.hud_visible = True
        self.hud_height = 20
        self.hud_alpha = 75
        self._hud_last_input = "-"
        self._hud_recent_inputs: deque[str] = deque(maxlen=5)

        self._avg_timings: dict[str, float] = {
            "events": 0.0,
            "update": 0.0,
            "render": 0.0,
        }
        self._avg_fps = 0.0
        self._avg_dt_ms = 0.0
        self._hud_stats_alpha = 0.12

        self._toast_text: str | None = None
        self._toast_t = 0.0

        # Render target cache
        self._scene_surf: pygame.Surface | None = None
        self._scene_surf_size: tuple[int, int] | None = None

        self._timings: dict[str, float] = {"events": 0.0, "update": 0.0, "render": 0.0}
        self._hud_show_timings = False
        self._hud_text_cache: dict[str, tuple[str, pygame.Surface]] = {}

        self._hud_bar_surface: pygame.Surface | None = None
        self._hud_bar_size: tuple[int, int] | None = None
        self._hud_bar_alpha: int | None = None

        self._profiling_mode = False
        self._profiling_frame_window = 60
        self._profiling_frames = 0
        self._profiling_accumulator: dict[str, float] = {
            "events": 0.0,
            "update": 0.0,
            "render": 0.0,
        }

    # --- Scene switching -------------------------------------------------
    def _wrap_index(self, index: int) -> int:
        return 0 if not self._scene_ids else index % len(self._scene_ids)

    def set_scene(self, index: int, composition_path: str | Path | None = None) -> None:
        if not self._scene_ids:
            return

        new_index = self._wrap_index(index)
        if new_index == self._scene_index and self.scene is not None:
            return

        if self.scene is not None:
            self.scene.on_exit(self)

        self._scene_index = new_index
        scene_id = self._scene_ids[self._scene_index]
        scene_cls = self.scenes[scene_id]
        # Caso especial: MainScene recibe composition_path
        if getattr(scene_cls, "__name__", "") == "MainScene":
            self.scene = scene_cls(composition_path=composition_path)  # type: ignore[call-arg]
        else:
            self.scene = scene_cls()

        self.scene.on_enter(self)

        self._toast_text = (
            f"{scene_id}  ({self._scene_index + 1}/{len(self._scene_ids)})"
        )
        self._toast_t = 1.2

        console.print(
            Panel.fit(
                f"🎬 Scene -> {scene_id} ({self._scene_index + 1}/{len(self._scene_ids)})",
                border_style="magenta",
            )
        )

    def cycle_scene(self, step: int = 1) -> None:
        self.set_scene(self._scene_index + step)

    def next_scene(self) -> None:
        self.cycle_scene(+1)

    def prev_scene(self) -> None:
        self.cycle_scene(-1)

    def cycle_resolution(self) -> None:
        if self.scene is None:
            return

        # Check if the scene has a method to toggle native resolution
        toggler = getattr(self.scene, "toggle_native_resolution", None)
        if callable(toggler):
            toggler()

    # --- HUD -------------------------------------------------------------
    def _apply_hud_visibility(self, visible: bool) -> None:
        if self.hud_visible == visible:
            return
        self.hud_visible = visible
        self._scene_surf_size = None

    def toggle_hud(self) -> None:
        self._apply_hud_visibility(not self.hud_visible)
        self._toast_text = f"HUD {'ON' if self.hud_visible else 'OFF'}"
        self._toast_t = 1.0

    def cycle_hud_mode(self) -> None:
        if not self.hud_visible:
            self._apply_hud_visibility(True)
            self._hud_show_timings = False
            label = "HUD normal"
        elif not self._hud_show_timings:
            self._hud_show_timings = True
            label = "HUD complejo"
        else:
            self._hud_show_timings = False
            self._apply_hud_visibility(False)
            label = "HUD oculto"
        self._toast_text = label
        self._toast_t = 1.0

    def scene_viewport(self) -> pygame.Rect:
        w, h = self.screen.get_size()
        return pygame.Rect(0, 0, w, h)

    def hud_rect(self, rows: int | None = None) -> pygame.Rect:
        w, h = self.screen.get_size()
        rows = rows or (2 if self._hud_show_timings else 1)
        rows = max(1, rows)
        height = self.hud_height * rows
        return pygame.Rect(0, h - height, w, height)

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

            events_start = perf_counter()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    continue

                if ev.type == pygame.VIDEORESIZE:
                    if self.scene:
                        self.scene.on_window_resize(ev.size)
                    continue

                self._track_last_input(ev)

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_p:
                        self._profiling_mode = not self._profiling_mode
                        self._toast_text = (
                            f"Profiling {'ON' if self._profiling_mode else 'OFF'}"
                        )
                        self._toast_t = 1.0
                        self._profiling_frames = 0
                        self._reset_profiling_accumulators()
                        continue

                    if ev.key == pygame.K_h:
                        self.toggle_hud()
                        continue

                    if ev.key in (pygame.K_F2, pygame.K_TAB) and not (
                        ev.mod & pygame.KMOD_SHIFT
                    ):
                        self.next_scene()
                        continue

                    if ev.key == pygame.K_F1 or (
                        ev.key == pygame.K_TAB and (ev.mod & pygame.KMOD_SHIFT)
                    ):
                        self.prev_scene()
                        continue

                if ev.type == pygame.JOYBUTTONDOWN:
                    self.joy_buttons_down.add(ev.button)

                    # combo: 12 + 14
                    if 12 in self.joy_buttons_down and 14 in self.joy_buttons_down:
                        self.cycle_hud_mode()
                        self.joy_buttons_down.clear()
                        continue

                    if ev.button == 15:
                        self.prev_scene()
                        self.joy_buttons_down.clear()
                        continue

                    if ev.button == 16:
                        self.next_scene()
                        self.joy_buttons_down.clear()
                        continue

                if ev.type == pygame.JOYBUTTONUP:
                    self.joy_buttons_down.discard(ev.button)

                if self.scene is not None:
                    self.scene.handle_event(self, ev)

            self._timings["events"] = (perf_counter() - events_start) * 1000.0

            update_start = perf_counter()
            if self.scene is not None:
                self.scene.update(self, dt)
            self._timings["update"] = (perf_counter() - update_start) * 1000.0

            render_start = perf_counter()
            vp = self.scene_viewport()
            scene_surf = self._ensure_scene_surface(vp)

            if self.scene is not None:
                self.scene.render(self, scene_surf)

            self.screen.blit(scene_surf, vp.topleft)
            self._timings["render"] = (perf_counter() - render_start) * 1000.0

            self._update_hud_stats(dt)

            if self.hud_visible:
                self._render_hud(dt)

            pygame.display.flip()

            if self._profiling_mode:
                self._profiling_frames += 1
                for key in self._timings:
                    self._profiling_accumulator[key] += self._timings[key]
                if self._profiling_frames >= self._profiling_frame_window:
                    self._emit_profiling_summary()
                    self._profiling_frames = 0
                    self._reset_profiling_accumulators()

        if self.scene is not None:
            self.scene.on_exit(self)

        self.audio.stop_all_sounds()
        self.audio.stop_music()
        pygame.quit()

    # --- Profiling helpers ----------------------------------------------
    def _reset_profiling_accumulators(self) -> None:
        for key in self._profiling_accumulator:
            self._profiling_accumulator[key] = 0.0

    def _emit_profiling_summary(self) -> None:
        frames = self._profiling_frame_window
        if frames <= 0:
            return

        avg_events = self._profiling_accumulator["events"] / frames
        avg_update = self._profiling_accumulator["update"] / frames
        avg_render = self._profiling_accumulator["render"] / frames

        lines = [
            f"avg events {avg_events:0.2f}ms   update {avg_update:0.2f}ms   render {avg_render:0.2f}ms"
        ]

        update_top: list[tuple[str, float]] = []
        render_top: list[tuple[str, float]] = []
        if self.scene is not None:
            reporter = getattr(self.scene, "node_timing_report", None)
            if callable(reporter):
                update_top, render_top = reporter()

        if update_top:
            lines.append(
                "Update top: "
                + ", ".join(f"{name} {time:0.2f}ms" for name, time in update_top)
            )
        if render_top:
            lines.append(
                "Render top: "
                + ", ".join(f"{name} {time:0.2f}ms" for name, time in render_top)
            )

        console.print(
            Panel.fit("\n".join(lines), title="Profiling (avg)", border_style="yellow")
        )

    # --- HUD render ------------------------------------------------------
    def _render_hud(self, dt: float) -> None:
        extra_lines = self._build_hud_lines()
        rows = 1 + len(extra_lines)
        r = self.hud_rect(rows)
        w, bar_h, bar_y = r.w, r.h, r.y
        row_height = self.hud_height

        bar = self._ensure_hud_bar_surface(w, bar_h, int(self.hud_alpha))
        self.screen.blit(bar, (0, bar_y))

        fps = 0.0 if dt <= 0 else (1.0 / dt)
        scene_name = self.scene.__class__.__name__ if self.scene else "None"
        scene_id = self._scene_ids[self._scene_index] if self._scene_ids else "-"
        left_text = (
            f"{scene_name}  [{scene_id} {self._scene_index + 1}/{len(self._scene_ids)}]"
        )

        center_text = f"FPS {fps:0.1f}   dt {dt * 1000:0.1f} ms"
        right_text = self._toast_text or "F1/F2  TAB / SHIFT+TAB"

        pad_x = 12
        line_h = self.hud_font.get_height()
        y = bar_y + (row_height - line_h) // 2

        t_left = self._hud_text_surface("left", left_text, (255, 255, 255))
        self.screen.blit(t_left, (pad_x, y))

        t_center = self._hud_text_surface("center", center_text, (200, 200, 200))
        cx = (w - t_center.get_width()) // 2
        self.screen.blit(t_center, (cx, y))

        t_right = self._hud_text_surface("right", right_text, (180, 220, 180))
        rx = w - t_right.get_width() - pad_x
        self.screen.blit(t_right, (rx, y))

        for idx, line in enumerate(extra_lines, start=1):
            ty = bar_y + idx * row_height + (row_height - line_h) // 2
            surface = self._hud_text_surface(f"extra_{idx}", line.text, line.color)
            if line.align == "center":
                tx = (w - surface.get_width()) // 2
            elif line.align == "right":
                tx = w - surface.get_width() - pad_x
            else:
                tx = pad_x
            self.screen.blit(surface, (tx, ty))

        pygame.draw.line(self.screen, (70, 70, 70), (0, bar_y), (w, bar_y), 1)

    def _hud_text_surface(
        self, key: str, text: str, color: tuple[int, int, int]
    ) -> pygame.Surface:
        cached = self._hud_text_cache.get(key)
        if cached and cached[0] == text:
            return cached[1]
        surface = self.hud_font.render(text, True, color)
        self._hud_text_cache[key] = (text, surface)
        return surface

    def _ensure_hud_bar_surface(
        self, width: int, height: int, alpha: int
    ) -> pygame.Surface:
        size = (width, height)
        if (
            self._hud_bar_surface is None
            or self._hud_bar_size != size
            or self._hud_bar_alpha != alpha
        ):
            bar = pygame.Surface(size, pygame.SRCALPHA)
            bar.fill((20, 20, 20, alpha))
            self._hud_bar_surface = bar
            self._hud_bar_size = size
            self._hud_bar_alpha = alpha
        return self._hud_bar_surface

    # --- HUD data --------------------------------------------------------
    def _track_last_input(self, ev: pygame.event.Event) -> None:
        label: str | None = None
        if ev.type == pygame.KEYDOWN:
            label = f"Key {pygame.key.name(ev.key)}"
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            label = f"Mouse {ev.button}"
        elif ev.type == pygame.MOUSEWHEEL:
            label = "Mouse wheel"
        elif ev.type == pygame.JOYBUTTONDOWN:
            label = f"Joy{ev.joy} Btn{ev.button}"
        elif ev.type == pygame.JOYAXISMOTION:
            label = f"Joy{ev.joy} Axis{ev.axis}:{ev.value:0.2f}"
        elif ev.type == pygame.JOYHATMOTION:
            label = f"Joy{ev.joy} Hat{ev.hat} {ev.value}"

        if label:
            self._hud_last_input = label
            self._hud_recent_inputs.appendleft(label)

    def _build_hud_lines(self) -> list[HudLine]:
        lines: list[HudLine] = []
        lines.append(HudLine(self._input_status_text(), (200, 200, 200), "left"))

        audio_line = self._audio_status_text()
        if audio_line:
            lines.append(HudLine(audio_line, (200, 220, 220), "left"))

        avg_line = self._avg_timings_text()
        if avg_line:
            lines.append(HudLine(avg_line, (160, 200, 255), "left"))

        if self._hud_show_timings:
            timings_text = (
                f"Frame events {self._timings['events']:0.1f}ms   "
                f"update {self._timings['update']:0.1f}ms   "
                f"render {self._timings['render']:0.1f}ms"
            )
            lines.append(HudLine(timings_text, (160, 200, 255), "center"))

        return [line for line in lines if line.text]

    def _input_status_text(self) -> str:
        pads = len(self.joysticks)
        pressed = len(self.joy_buttons_down)
        recent = ", ".join(self._hud_recent_inputs)
        if recent:
            recent = f"  recent [{recent}]"
        return f"Input: pads {pads}  btn {pressed}  last {self._hud_last_input}{recent}"

    def _audio_status_text(self) -> str:
        if not pygame.mixer.get_init():
            return "Audio: mixer OFF"

        parts: list[str] = []
        if pygame.mixer.music.get_busy():
            name = getattr(self.audio, "current_music", None)
            pos_ms = max(0, pygame.mixer.music.get_pos())
            pos_s = pos_ms / 1000.0
            parts.append(
                f"music {name} {pos_s:0.1f}s" if name else f"music {pos_s:0.1f}s"
            )
        else:
            parts.append("music idle")

        busy_channels = self._busy_channels()
        total_channels = pygame.mixer.get_num_channels()
        parts.append(f"sfx {busy_channels}/{total_channels} busy")
        return "Audio: " + "  •  ".join(parts)

    def _busy_channels(self) -> int:
        total = pygame.mixer.get_num_channels()
        busy = 0
        for idx in range(total):
            if pygame.mixer.Channel(idx).get_busy():
                busy += 1
        return busy

    def _avg_timings_text(self) -> str:
        return (
            f"Avg FPS {self._avg_fps:0.1f}  dt {self._avg_dt_ms:0.1f}ms  "
            f"events {self._avg_timings['events']:0.2f}ms  "
            f"update {self._avg_timings['update']:0.2f}ms  "
            f"render {self._avg_timings['render']:0.2f}ms"
        )

    def _update_hud_stats(self, dt: float) -> None:
        fps = 0.0 if dt <= 0 else 1.0 / dt
        alpha = self._hud_stats_alpha
        self._avg_fps = (1 - alpha) * self._avg_fps + alpha * fps
        self._avg_dt_ms = (1 - alpha) * self._avg_dt_ms + alpha * (dt * 1000.0)
        for key, value in self._timings.items():
            prev = self._avg_timings.get(key, 0.0)
            self._avg_timings[key] = (1 - alpha) * prev + alpha * value
