from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pygame

from game.environments.base import Environment, AppLike
from game.core.resources import get_asset_path


class BackgroundEnvironment(Environment):
    """
    Environment that composes a background image from multiple layers.

    Cada capa es una ruta relativa dentro de `assets/` y se mezcla en orden.
    It can render as a movable node (uses `pos`) and accepts an editable `size`
    or an optional target size for rescaling layers.
    """

    def __init__(
        self,
        pos: pygame.Vector2 | tuple[float, float] | None = None,
        *,
        layers: Sequence[str] | None = None,
        fill_color: str | tuple[int, int, int] | tuple[int, int, int, int] = "#0b0b0f",
        target_size: tuple[int, int] | None = None,
    ) -> None:
        self.pos = pygame.Vector2(pos) if pos is not None else pygame.Vector2(0, 0)
        DEFAULT_BACKGROUND_PATHS = [
            str(get_asset_path("images/backgrounds/bg1/bg_sky.png")),
        ]

        self.layers = (
            list(layers) if layers is not None else list(DEFAULT_BACKGROUND_PATHS)
        )
        self.fill_color = fill_color
        self.target_size = target_size
        if target_size is not None:
            self.size = pygame.Vector2(target_size)
        else:
            self.size = pygame.Vector2(0, 0)

        self._surface: pygame.Surface | None = None
        self._surface_size: tuple[int, int] | None = None
        self._layer_size: tuple[int, int] | None = None
        self._layer_probe_path: str | None = None

    def on_spawn(self, app: AppLike) -> None:
        size = self._initial_scene_size(app)
        self._compose_background(app, size)

    def on_despawn(self, app: AppLike) -> None:
        self._surface = None
        self._surface_size = None

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        desired_size = self._desired_surface_size(app, screen)
        if self._surface is None or self._surface_size != desired_size:
            self._compose_background(app, desired_size)

        if self._surface is None:
            return

        screen.blit(self._surface, (int(self.pos.x), int(self.pos.y)))

    def _desired_surface_size(
        self, app: AppLike, screen: pygame.Surface
    ) -> tuple[int, int]:
        if self.size.x > 0 and self.size.y > 0:
            return (int(self.size.x), int(self.size.y))
        if self.target_size is not None:
            return self.target_size
        if self.layers:
            if self._layer_size is not None and self._layer_probe_path == self.layers[0]:
                return self._layer_size
            return screen.get_size()
        return self._initial_scene_size(app)

    def _initial_scene_size(self, app: AppLike) -> tuple[int, int]:
        viewport_fn = getattr(app, "scene_viewport", None)
        if callable(viewport_fn):
            rect = viewport_fn()
            if rect is not None:
                return (max(0, int(rect.width)), max(0, int(rect.height)))

        screen = getattr(app, "screen", None)
        if screen is not None:
            return screen.get_size()

        cfg = getattr(app, "cfg", None)
        width = getattr(cfg, "width", 0) or 0
        height = getattr(cfg, "height", 0) or 0
        return (int(width), int(height))

    def _compose_background(self, app: AppLike, size: tuple[int, int]) -> None:
        width, height = size
        if width <= 0 or height <= 0:
            self._surface = None
            self._surface_size = None
            return

        layer_iter = iter(self.layers)
        first_surface: pygame.Surface | None = None
        if (
            self.target_size is None
            and self.size.x <= 0
            and self.size.y <= 0
            and self.layers
        ):
            first_path = next(layer_iter, None)
            if first_path is not None:
                first_surface = self._load_layer(first_path, app, None)
                if first_surface is not None:
                    target_size = first_surface.get_size()
                    self._layer_size = target_size
                    self._layer_probe_path = first_path
                    width, height = target_size
                else:
                    self._layer_size = None
                    self._layer_probe_path = None

        composed = pygame.Surface((width, height), pygame.SRCALPHA)
        color = self._coerce_color(self.fill_color)
        if color is not None:
            composed.fill(color)

        if first_surface is not None:
            if first_surface.get_size() != (width, height):
                first_surface = pygame.transform.smoothscale(
                    first_surface, (width, height)
                )
            composed.blit(first_surface, (0, 0))

        for layer_path in layer_iter:
            layer_surface = self._load_layer(layer_path, app, (width, height))
            if layer_surface is None:
                continue
            composed.blit(layer_surface, (0, 0))

        self._surface = composed.convert_alpha()
        self._surface_size = (width, height)

    def _load_layer(
        self, layer_path: str, app: AppLike, size: tuple[int, int] | None
    ) -> pygame.Surface | None:
        resolved_path = self._resolve_layer_path(app, layer_path)
        if resolved_path is None:
            print(f"[BackgroundEnvironment] Invalid layer path: {layer_path!r}")
            return None

        try:
            image = pygame.image.load(resolved_path).convert_alpha()
        except FileNotFoundError:
            print(f"[BackgroundEnvironment] Archivo no encontrado: {resolved_path}")
            return None
        except pygame.error as exc:
            print(f"[BackgroundEnvironment] Failed to load {resolved_path}: {exc}")
            return None

        if size is not None and image.get_size() != size:
            image = pygame.transform.smoothscale(image, size)

        return image

    def _resolve_layer_path(self, app: AppLike, layer_path: str) -> Path | None:
        if not isinstance(layer_path, str) or not layer_path.strip():
            return None

        candidate = Path(layer_path)
        if candidate.is_absolute():
            return candidate

        try:
            return get_asset_path(layer_path)
        except FileNotFoundError:
            return None

    @staticmethod
    def _coerce_color(
        value: str | tuple[int, int, int] | tuple[int, int, int, int] | None,
    ) -> tuple[int, int, int, int] | None:
        if value is None:
            return None
        try:
            color = pygame.Color(value)
            return (color.r, color.g, color.b, color.a)
        except (ValueError, TypeError):
            print(f"[BackgroundEnvironment] Invalid color: {value!r}")
            return None
