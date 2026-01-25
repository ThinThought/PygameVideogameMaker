from __future__ import annotations

import pygame

from game.entities.core.base import Entity, AppLike


class NewEntity(Entity):
    """Template for a new entity.

    - Rename the class.
    - Save a copy of this file without the leading underscore.
    - Import the class in game.entities.custom.__init__ and add to __all__.
    """

    def __init__(self, pos: pygame.Vector2 | tuple[float, float] | None = None) -> None:
        self.pos = pygame.Vector2(pos) if pos is not None else pygame.Vector2(0, 0)
        self.radius = 10

    def update(self, app: AppLike, dt: float) -> None:
        pass

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, (255, 210, 0), self.pos, self.radius)
