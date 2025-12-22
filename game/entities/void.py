from __future__ import annotations

import pygame

from game.entities.base import Entity, AppLike


class VoidEntity(Entity):
    """
    Entidad utilitaria sin comportamiento que actúa como ancla de otros environments.

    Su objetivo es permitir que el árbol EEI intercale nodos `entity → environment`
    sin necesidad de crear entidades visibles. Opcionalmente puede dibujarse para
    depurar posiciones en pantalla.
    """

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        visible: bool = False,
        radius: float = 10.0,
        color: pygame.Color | str | tuple[int, int, int] = (90, 90, 90),
    ) -> None:
        self.pos = pygame.Vector2(pos) if pos is not None else pygame.Vector2(0, 0)
        self.visible = bool(visible)
        self.radius = max(1.0, float(radius))
        self.color = self._to_color(color)

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        if not self.visible:
            return

        center = (int(self.pos.x), int(self.pos.y))
        color = self._to_color(getattr(self, "color", self.color))
        pygame.draw.circle(screen, color, center, int(self.radius), width=1)

    @staticmethod
    def _to_color(value: pygame.Color | str | tuple[int, int, int]) -> pygame.Color:
        try:
            if isinstance(value, pygame.Color):
                return pygame.Color(value)
            if isinstance(value, str):
                return pygame.Color(value)
            if isinstance(value, (tuple, list)):
                return pygame.Color(*value)
        except (ValueError, TypeError):
            pass
        return pygame.Color(90, 90, 90)
