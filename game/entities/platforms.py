from __future__ import annotations

from typing import ClassVar

import pygame

from game.entities.collider import Platform
from game.entities.sprite_collider import SpriteColliderMixin


class SpritePlatform(SpriteColliderMixin, Platform):
    """
    Sprite-based platform that reuses Platform collision logic.

    Define `SPRITE_PATH`, `RENDER_SIZE`, and `COLLIDER_SIZE` to configure the
    associated image and keep the collider inside the sprite.
    """

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


class GrassSmallPlatform(SpritePlatform):
    """Short grass platform."""

    SPRITE_PATH = "images/platforms/grass_platforms/small1.png"
    RENDER_SIZE = (192, 60)
    COLLIDER_SIZE = pygame.Vector2(175, 40)

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        show_collider: bool = False,
        **platform_kwargs,
    ) -> None:
        super().__init__(pos, show_collider=show_collider, **platform_kwargs)


class GrassWidePlatform(SpritePlatform):
    """Medium grass platform."""

    SPRITE_PATH = "images/platforms/grass_platforms/medium1.png"
    RENDER_SIZE = (256, 72)
    COLLIDER_SIZE = pygame.Vector2(230, 50)

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        show_collider: bool = False,
        **platform_kwargs,
    ) -> None:
        super().__init__(pos, show_collider=show_collider, **platform_kwargs)


class GrassLargePlatform(SpritePlatform):
    """Long platform for horizontal sections."""

    SPRITE_PATH = "images/platforms/grass_platforms/large2.png"
    RENDER_SIZE = (320, 84)
    COLLIDER_SIZE = pygame.Vector2(300, 40)

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        show_collider: bool = False,
        **platform_kwargs,
    ) -> None:
        super().__init__(pos, show_collider=show_collider, **platform_kwargs)

class GrassFloorPlatform(SpritePlatform):
    """Wide segment that can act as a base floor."""

    SPRITE_PATH = "images/platforms/grass_platforms/floor.png"
    RENDER_SIZE = (720, 480)
    COLLIDER_SIZE = pygame.Vector2(720, 110)

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        show_collider: bool = False,
        **platform_kwargs,
    ) -> None:
        super().__init__(pos, show_collider=show_collider, **platform_kwargs)
