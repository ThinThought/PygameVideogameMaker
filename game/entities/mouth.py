from __future__ import annotations
import pygame
from game.entities.base import Entity, AppLike


class Mouth(Entity):
    """
    Entidad Boca básica.
    Puede abrirse y cerrarse (hablar / reaccionar).
    """

    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.radius = 18  # tamaño base

        # Estado de apertura
        self.open_amount = 0.0        # 0.0 cerrada, 1.0 abierta
        self.open_speed = 6.0         # velocidad de animación

        self.talking = False

    # ---------------- Input ----------------

    def handle_event(self, app: AppLike, ev: pygame.event.Event):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
            self.talking = True
            return True

        if ev.type == pygame.KEYUP and ev.key == pygame.K_SPACE:
            self.talking = False
            return True

        return False

    # ---------------- Update ----------------

    def update(self, app, dt: float):
        target = 1.0 if self.talking else 0.0

        # Interpolación suave
        if self.open_amount < target:
            self.open_amount = min(target, self.open_amount + self.open_speed * dt)
        elif self.open_amount > target:
            self.open_amount = max(target, self.open_amount - self.open_speed * dt)

    # ---------------- Render ----------------

    def render(self, app, screen):
        x, y = int(self.pos.x), int(self.pos.y)

        # Altura de la boca según apertura
        open_h = int(self.radius * self.open_amount)

        if open_h <= 1:
            # Boca cerrada → línea
            pygame.draw.line(
                screen,
                "black",
                (x - self.radius, y),
                (x + self.radius, y),
                3,
            )
        else:
            # Boca abierta → óvalo
            rect = pygame.Rect(
                x - self.radius,
                y - open_h // 2,
                self.radius * 2,
                open_h,
            )
            pygame.draw.ellipse(screen, "black", rect, 2)
