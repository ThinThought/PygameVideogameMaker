from __future__ import annotations
from typing import Protocol
import pygame


class AppLike(Protocol):
    running: bool

    def cycle_resolution(self) -> None:
        ...


class Scene:
    def on_enter(self, app: AppLike) -> None:
        pass

    def on_exit(self, app: AppLike) -> None:
        pass

    def handle_event(self, app: AppLike, ev: pygame.event.Event) -> None:
        pass

    def update(self, app: AppLike, dt: float) -> None:
        pass

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        pass

    def on_window_resize(self, size: tuple[int, int]) -> None:
        pass

    def debug_hud_rows(self, app: AppLike) -> list[str] | None:
        """Hook opcional para publicar filas extras en el HUD."""
        return None
