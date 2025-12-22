from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pygame

from game.entities.base import AppLike
from game.entities.collider import Platform


class SpritePlatform(Platform):
    """
    Plataforma basada en sprite que reutiliza la lógica de colisión de Platform.

    Cada subclase define el sprite asociado, el tamaño del collider y el tamaño
    de render por defecto. El collider sigue siendo invisible salvo que
    `show_collider=True`.
    """

    SPRITE_PATH: ClassVar[str] = ""
    RENDER_SIZE: ClassVar[tuple[int, int] | None] = None
    COLLIDER_SIZE: ClassVar[pygame.Vector2] = pygame.Vector2(200, 32)
    _surface_cache: ClassVar[dict[str, pygame.Surface]] = {}

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        show_collider: bool = False,
    ) -> None:
        super().__init__(pos, size=self.COLLIDER_SIZE, visible=show_collider)
        self._sprite: pygame.Surface | None = None

    # ------------------------------------------------------------------
    def on_spawn(self, app: AppLike) -> None:
        super().on_spawn(app)
        self._sprite = self._ensure_sprite(app)

    def on_despawn(self, app: AppLike) -> None:
        super().on_despawn(app)
        self._sprite = None

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        sprite = self._sprite or self._ensure_sprite(app)
        if sprite is not None:
            rect = sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(sprite, rect)

        if self.visible:
            self.render_collider_rect(screen)

    def render_collider_rect(self, screen: pygame.Surface) -> None:
        """Dibuja el rectángulo del collider para depuración."""
        collider_rect = self.rect
        pygame.draw.rect(screen, self.debug_fill_color, collider_rect, border_radius=4)
        pygame.draw.rect(screen, self.debug_outline_color, collider_rect, width=1, border_radius=4)

    # ------------------------------------------------------------------
    def _ensure_sprite(self, app: AppLike) -> pygame.Surface | None:
        key = self._cache_key()
        cached = self._surface_cache.get(key)
        if cached is not None:
            return cached

        sprite = self._load_sprite(app)
        if sprite is not None:
            self._surface_cache[key] = sprite
        return sprite

    def _load_sprite(self, app: AppLike) -> pygame.Surface | None:
        path = self._resolve_asset_path(app)
        if path is None:
            print(f"[SpritePlatform] Ruta de asset inválida: {self.SPRITE_PATH!r}")
            return None

        if not path.exists():
            print(f"[SpritePlatform] Sprite no encontrado: {path}")
            return None

        try:
            sprite = pygame.image.load(path.as_posix()).convert_alpha()
        except pygame.error as exc:
            print(f"[SpritePlatform] No se pudo cargar {path}: {exc}")
            return None

        if self.RENDER_SIZE is not None:
            width, height = self.RENDER_SIZE
            if width > 0 and height > 0:
                sprite = pygame.transform.smoothscale(sprite, (int(width), int(height)))

        return sprite

    def _cache_key(self) -> str:
        size = self.RENDER_SIZE or (-1, -1)
        return f"{self.__class__.__name__}:{self.SPRITE_PATH}:{size[0]}x{size[1]}"

    @classmethod
    def _resolve_asset_path(cls, app: AppLike) -> Path | None:
        if not cls.SPRITE_PATH:
            return None

        candidate = Path(cls.SPRITE_PATH)
        if candidate.is_absolute():
            return candidate

        resources = getattr(app, "resources", None)
        if resources is not None and hasattr(resources, "path"):
            try:
                resolved = Path(resources.path(*candidate.parts))
                return resolved
            except TypeError:
                pass

        root = Path(__file__).resolve().parents[2] / "assets"
        return root / candidate


class GrassSmallPlatform(SpritePlatform):
    """Plataforma corta de pasto."""

    SPRITE_PATH = "images/platforms/grass_platforms/small1.png"
    RENDER_SIZE = (192, 60)
    COLLIDER_SIZE = pygame.Vector2(168, 28)


class GrassWidePlatform(SpritePlatform):
    """Plataforma mediana con vegetación."""

    SPRITE_PATH = "images/platforms/grass_platforms/medium1.png"
    RENDER_SIZE = (256, 72)
    COLLIDER_SIZE = pygame.Vector2(228, 34)


class GrassLargePlatform(SpritePlatform):
    """Plataforma larga ideal para secciones horizontales."""

    SPRITE_PATH = "images/platforms/grass_platforms/large2.png"
    RENDER_SIZE = (320, 84)
    COLLIDER_SIZE = pygame.Vector2(296, 38)


class GrassFloorPlatform(SpritePlatform):
    """Segmento amplio que puede actuar como piso base."""

    SPRITE_PATH = "images/platforms/grass_platforms/floor.png"
    RENDER_SIZE = (512, 96)
    COLLIDER_SIZE = pygame.Vector2(488, 44)
