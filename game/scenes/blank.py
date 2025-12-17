from __future__ import annotations
import pygame
from game.scenes.base import Scene, AppLike
from pathlib import Path


class BlankScene(Scene):
    def __init__(self) -> None:
        pass

    def handle_event(self, app, ev: pygame.event.Event) -> None:
        if ev.type == pygame.QUIT:
            app.running = False

    def render(self, app, screen: pygame.Surface) -> None:
        screen.fill("white")
