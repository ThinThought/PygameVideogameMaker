from __future__ import annotations


from typing import Protocol
import pygame


class AppLike(Protocol):
    """The minimal interface an entity may need from the world."""

    pass


class Environment:
    """
    Basic unit of the game.

    - Does not know about scenes
    - Does not handle input directly
    - Does not manage the loop
    """

    def on_spawn(self, app: AppLike) -> None:
        """Called when the entity enters the scene."""
        pass

    def on_despawn(self, app: AppLike) -> None:
        """Called when the entity leaves the scene."""
        pass

    def handle_event(self, app: AppLike, ev: pygame.event.Event):
        """Propagate the event to the entity."""
        pass

    def update(self, app: AppLike, dt: float) -> None:
        """Per-frame logic."""
        pass

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        """Rendering."""
        pass
