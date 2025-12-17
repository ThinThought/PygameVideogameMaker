# game/core/video.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import pygame


@dataclass(slots=True)
class VideoConfig:
    loop: bool = False
    fps_fallback: float = 30.0


class VideoPlayer:
    def __init__(
        self,
        path: Path,
        *,
        size: tuple[int, int],
        position: tuple[int, int] = (0, 0),
        loop: bool = False,
    ) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(str(self.path))

        self.size = size
        self.position = pygame.Vector2(position)
        self.loop = loop

        self.cap = cv2.VideoCapture(str(self.path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video: {self.path}")

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = float(fps) if fps and fps > 0 else 30.0
        self.frame_interval_ms = 1000.0 / self.fps

        self.timer_ms = 0.0
        self.playing = False
        self.finished = False

        self.surface: pygame.Surface = pygame.Surface((1, 1), pygame.SRCALPHA)
        self._read_first_frame()

    # ----- public API -----

    def set_position(self, x: int, y: int) -> None:
        self.position.update(x, y)

    def set_size(self, w: int, h: int) -> None:
        self.size = (w, h)
        # reescalamos el frame actual a la nueva size
        self.surface = pygame.transform.smoothscale(self.surface, self.size)

    def play(self) -> None:
        if self.finished:
            self.stop()
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def stop(self) -> None:
        self.playing = False
        self.finished = False
        self.timer_ms = 0.0
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self._read_first_frame()

    def update(self, dt_s: float) -> None:
        if not self.playing or self.finished:
            return
        dt_ms = dt_s * 1000
        self.timer_ms += dt_ms
        while self.timer_ms >= self.frame_interval_ms:
            self.timer_ms -= self.frame_interval_ms
            ok, frame = self.cap.read()

            if not ok:
                if self.loop:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = self.cap.read()
                    if not ok:
                        self.finished = True
                        return
                else:
                    self.finished = True
                    return

            self._frame_to_surface(frame)

    def draw(self, screen: pygame.Surface) -> None:
        if self.finished:
            return
        screen.blit(self.surface, (int(self.position.x), int(self.position.y)))

    # ----- internals -----

    def _read_first_frame(self) -> None:
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError(f"Could not read first frame: {self.path}")
        self._frame_to_surface(frame)

    def _frame_to_surface(self, frame) -> None:
        # OpenCV: BGR -> pygame: RGB(A)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        h, w = frame.shape[:2]
        surf = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGBA").convert_alpha()

        if surf.get_size() != self.size:
            surf = pygame.transform.smoothscale(surf, self.size)

        self.surface = surf

    def __del__(self) -> None:
        try:
            self.cap.release()
        except Exception:
            pass
