from __future__ import annotations

from typing import Any

from game.entities.playable import PlayableMassEntity
from dataclasses import dataclass
import random
from pathlib import Path
from game.core.resources import get_asset_path
import pygame


@dataclass
class AnimClip:
    frames: list[pygame.Surface]
    fps: float = 10.0
    loop: bool = True

    t: float = 0.0
    idx: int = 0

    def reset(self) -> None:
        self.t = 0.0
        self.idx = 0

    def update(self, dt: float) -> None:
        if len(self.frames) <= 1 or self.fps <= 0:
            return

        self.t += dt
        frame_time = 1.0 / self.fps

        # avanzar de forma robusta aunque dt venga grande
        while self.t >= frame_time:
            self.t -= frame_time
            self.idx += 1
            if self.loop:
                self.idx %= len(self.frames)
            else:
                self.idx = min(self.idx, len(self.frames) - 1)

    def current(self) -> pygame.Surface:
        if not self.frames:
            raise RuntimeError("AnimClip sin frames")
        return self.frames[self.idx]


class SpriteAnimator:
    def __init__(
        self,
        base_asset_path_str: str,
        *,
        scale_factor: float | None = None,
        min_size: tuple[int, int] | None = None,
    ) -> None:
        self.base_asset_path_str = base_asset_path_str
        self.scale_factor = scale_factor
        self.min_size = min_size
        self.clips: dict[str, AnimClip] = {}
        self.state: str = "idle"
        self.facing: int = 1  # 1 derecha, -1 izquierda

    def load_clip(self, state: str, *, fps: float, loop: bool = True) -> None:
        relative_folder_path = Path(self.base_asset_path_str) / state

        frames: list[pygame.Surface] = []
        i = 1
        while True:
            try:
                relative_frame_path = relative_folder_path / f"{i}.png"
                full_path = get_asset_path(relative_frame_path.as_posix())
                surf = pygame.image.load(full_path).convert_alpha()
                frames.append(surf)
                i += 1
            except FileNotFoundError:
                break

        if not frames:
            raise FileNotFoundError(f"No hay frames para estado {state!r} en {relative_folder_path}")

        # scaling logic...
        if self.scale_factor is not None and self.scale_factor != 1.0:
            for i in range(len(frames)):
                surf = frames[i]
                original_size = surf.get_size()
                new_size = (
                    int(original_size[0] * self.scale_factor),
                    int(original_size[1] * self.scale_factor),
                )

                if self.min_size is not None:
                    new_size = (
                        max(new_size[0], self.min_size[0]),
                        max(new_size[1], self.min_size[1]),
                    )

                if new_size != original_size:
                    frames[i] = pygame.transform.smoothscale(surf, new_size)

        self.clips[state] = AnimClip(frames=frames, fps=fps, loop=loop)

    def set_state(self, state: str) -> None:
        if state == self.state:
            return
        self.state = state
        self.clips[state].reset()

    def update(self, dt: float) -> None:
        self.clips[self.state].update(dt)

    def frame(self) -> pygame.Surface:
        surf = self.clips[self.state].current()
        if self.facing < 0:
            surf = pygame.transform.flip(surf, True, False)
        return surf


class SpykePlayer(PlayableMassEntity):
    SPRITE_BASE = "images/pc/spyke"  # relativo a assets/
    SPRITE_SCALE_FACTOR = 1.0  # 1.0 = 100% del tamaño original
    COLLIDER_SIZE = (32, 60)  # tamaño para físicas
    WALK_FPS = 12.0
    IDLE_FPS = 6.0
    JUMP_FPS = 10.0

    # cache preview por clase (barato y suficiente para editor)
    _preview_surface: pygame.Surface | None = None
    _preview_loaded: bool = False

    def __init__(self, pos=None, *, mass: float = 1.0, **kwargs: Any) -> None:
        super().__init__(pos=pos, mass=mass, size=self.COLLIDER_SIZE, **kwargs)

        self._left = False
        self._right = False
        self._jump_pressed = False
        self._jump_time_left = 0.0
        self._is_jumping = False

        self.anim: SpriteAnimator | None = None

    def on_spawn(self, app: Any) -> None:
        super().on_spawn(app)

        self.anim = SpriteAnimator(
            self.SPRITE_BASE,
            scale_factor=self.SPRITE_SCALE_FACTOR,
            min_size=self.COLLIDER_SIZE,
        )
        self.anim.load_clip("idle", fps=self.IDLE_FPS, loop=True)
        self.anim.load_clip("walk", fps=self.WALK_FPS, loop=True)
        self.anim.load_clip("jump", fps=self.JUMP_FPS, loop=True)

    def update(self, app: Any, dt: float) -> None:
        # --- tu lógica existente ---
        self._bind_runtime(app)

        grounded = bool(getattr(self, "grounded", False))
        ppm = float(getattr(self, "PIXELS_PER_METER", 100.0))

        move_dir = 0
        if self._left and not self._right:
            move_dir = -1
        elif self._right and not self._left:
            move_dir = 1

        vx_mps = self.velocity.x / ppm

        accel = self.GROUND_ACCEL if grounded else self.AIR_ACCEL
        damping = self.GROUND_DAMPING if grounded else self.AIR_DAMPING

        if move_dir != 0:
            ax = move_dir * accel
            self.apply_force((self.mass * ax, 0.0))
        else:
            self.apply_force((-self.mass * damping * vx_mps, 0.0))

        vmax_px = self.MAX_SPEED_X * ppm
        self.velocity.x = max(-vmax_px, min(vmax_px, self.velocity.x))

        if self._jump_pressed and grounded and not self._is_jumping:
            self._start_jump()

        if self._jump_time_left > 0.0 and self._is_jumping and self._jump_pressed:
            self.apply_force((0.0, -self.mass * self.JUMP_HOLD_ACCEL))
            self._jump_time_left -= dt
            if self._jump_time_left <= 0.0:
                self._jump_time_left = 0.0
                self._is_jumping = False

        self._apply_platform_collisions()
        super().update(app, dt)

        if getattr(self, "grounded", False):
            self._jump_time_left = 0.0
            self._is_jumping = False
            if self.velocity.y > 0.0:
                self.velocity.y = 0.0

        # --- anim state box ---
        self._update_anim_state(dt)
        self._update_anim_state(dt)

    def _update_anim_state(self, dt: float) -> None:
        if self.anim is None:
            return

        grounded = bool(getattr(self, "grounded", False))
        vx = self.velocity.x
        dead = 5.0  # px/s, umbral para considerar “quieto”

        # facing por input (mejor que por vx si hay damping)
        if self._left and not self._right:
            self.anim.facing = -1
        elif self._right and not self._left:
            self.anim.facing = 1
        elif abs(vx) > dead:
            self.anim.facing = 1 if vx > 0 else -1

        if not grounded:
            self.anim.set_state("jump")
        else:
            if abs(vx) > dead:
                self.anim.set_state("walk")
            else:
                self.anim.set_state("idle")

        self.anim.update(dt)

    def render(self, app, screen: pygame.Surface) -> None:
        # 1) Si tenemos animación, usamos el frame actual
        if self.anim is not None:
            frame = self.anim.frame()
        else:
            # 2) Editor/preview: frame por defecto
            frame = self._get_editor_preview_frame(
                app, prefer_idle=True, random_fallback=True
            )
            if frame is None:
                # Si no hay sprite, dibujamos el collider para depurar
                if hasattr(self, "_collider_rect"):
                    pygame.draw.rect(screen, self.color, self._collider_rect(), 2)
                return

        # Anclar el sprite a la parte inferior del colisionador de físicas
        collider_rect = self._collider_rect()
        sprite_rect = frame.get_rect(midbottom=collider_rect.midbottom)

        screen.blit(frame, sprite_rect)

        # Opcional: dibujar el colisionador para depurar
        if getattr(app, "DEBUG_COLLIDERS", False):
            pygame.draw.rect(screen, (255, 0, 0), collider_rect, 1)

    @classmethod
    def _get_editor_preview_frame(
        cls,
        app,
        *,
        prefer_idle: bool = True,
        random_fallback: bool = True,
    ) -> pygame.Surface | None:
        if cls._preview_loaded:
            return cls._preview_surface
        cls._preview_loaded = True

        base_asset_path_str = cls._resolve_sprite_base_dir()
        if base_asset_path_str is None:
            return None

        candidate_relative_paths: list[str] = []
        if prefer_idle:
            try:
                get_asset_path(f"{base_asset_path_str}/idle/1.png") # Check existence
                candidate_relative_paths.append(f"{base_asset_path_str}/idle/1.png")
            except FileNotFoundError:
                pass

        if not candidate_relative_paths:
            return None

        try:
            full_path = get_asset_path(candidate_relative_paths[0])
            surf = pygame.image.load(full_path).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

        if hasattr(cls, "SPRITE_SCALE_FACTOR") and cls.SPRITE_SCALE_FACTOR != 1.0:
            scale_factor = cls.SPRITE_SCALE_FACTOR
            original_size = surf.get_size()
            new_size = (
                int(original_size[0] * scale_factor),
                int(original_size[1] * scale_factor),
            )

            if hasattr(cls, "COLLIDER_SIZE"):
                min_size = cls.COLLIDER_SIZE
                new_size = (
                    max(new_size[0], min_size[0]),
                    max(new_size[1], min_size[1]),
                )

            if new_size != original_size:
                surf = pygame.transform.smoothscale(surf, new_size)

        cls._preview_surface = surf
        return surf

    @classmethod
    def _resolve_sprite_base_dir(cls) -> str | None:
        if not cls.SPRITE_BASE:
            return None
        return cls.SPRITE_BASE