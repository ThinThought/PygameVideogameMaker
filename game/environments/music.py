from __future__ import annotations

import pygame

from game.environments.base import Environment, AppLike


class MusicEnvironment(Environment):
    """
    Environment that only manages background music.

    - Plays a track on spawn.
    - Stops music on despawn.
    - Renders nothing.
    """

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        track: str = "demo.mp3",
        volume: float = 1.0,
        loop: bool = True,
        fade_ms: int = 0,
        stop_fade_ms: int | None = None,
    ) -> None:
        # Environments are instantiated with a default position by the loader.
        self.pos = pygame.Vector2(pos) if pos is not None else pygame.Vector2(0, 0)
        resolved_track = track if isinstance(track, str) else "demo.mp3"
        self.track = resolved_track
        self._default_track = resolved_track
        self.volume = volume
        self.loop = loop
        self.fade_ms = fade_ms
        self.stop_fade_ms = stop_fade_ms if stop_fade_ms is not None else fade_ms
        self._active = False

    def on_spawn(self, app: AppLike) -> None:
        """Starts playing the configured track."""
        track = (
            self.track
            if isinstance(self.track, str) and self.track
            else self._default_track
        )
        if not isinstance(self.track, str):
            print(
                "[MusicEnvironment] Invalid track in composition. Using default."
            )
        app.audio.play_music(
            track,
            volume=self.volume,
            loop=self.loop,
            fade_ms=self.fade_ms,
        )
        self._active = True

    def on_despawn(self, app: AppLike) -> None:
        """Stops music when removed from the tree."""
        if not self._active:
            return
        app.audio.stop_music(fade_ms=self.stop_fade_ms)
        self._active = False

    def handle_event(self, app: AppLike, ev: pygame.event.Event) -> None:
        """No event handling (placeholder for compatibility)."""
        return

    def update(self, app: AppLike, dt: float) -> None:
        """No update logic needed."""
        return

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        """Renders nothing."""
        return
