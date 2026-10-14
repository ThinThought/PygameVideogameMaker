from __future__ import annotations

from typing import ClassVar

import pygame

from game.entities.core.collider import Platform
from game.entities.core.sprite_collider import SpriteColliderMixin


class SpritePlatform(SpriteColliderMixin, Platform):
    """
    Sprite-based platform that reuses Platform collision logic.

    Define `SPRITE_PATH`, `RENDER_SIZE`, and `COLLIDER_SIZE` for the defaults.
    Each instance exposes editable `render_size` and `size` values for its sprite
    and collider respectively.
    """

    __abstract__ = True

    SPRITE_PATH: ClassVar[str] = ""
    RENDER_SIZE: ClassVar[tuple[int, int] | None] = None
    COLLIDER_SIZE: ClassVar[pygame.Vector2] = pygame.Vector2(200, 32)

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        show_collider: bool = False,
        **platform_kwargs,
    ) -> None:
        super().__init__(pos, show_collider=show_collider, **platform_kwargs)


__all__ = ["SpritePlatform"]
