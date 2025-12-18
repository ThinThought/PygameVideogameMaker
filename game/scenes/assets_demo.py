from __future__ import annotations

from pathlib import Path
import pygame

from game.scenes.base import Scene, AppLike


class AssetsTestScene(Scene):
    def __init__(self) -> None:
        img_path = Path("assets/images/pygame_lofi.png")
        image = pygame.image.load(img_path).convert_alpha()

        scale = 0.5
        w, h = image.get_size()
        self.image = pygame.transform.smoothscale(
            image,
            (int(w * scale), int(h * scale)),
        )

        self.rect: pygame.Rect | None = None

    def on_enter(self, app: AppLike) -> None:
        # música de fondo del test
        app.audio.play_music("demo.mp3", volume=1.0, fade_ms=500)
        app.audio.play_sound("demo.wav", volume=0.5)

    def on_exit(self, app: AppLike) -> None:
        app.audio.stop_music(fade_ms=200)

    def handle_event(self, app: AppLike, ev: pygame.event.Event) -> None:
        if ev.type == pygame.QUIT:
            app.running = False

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        screen.fill("white")

        if self.rect is None:
            self.rect = self.image.get_rect(center=screen.get_rect().center)

        screen.blit(self.image, self.rect)
