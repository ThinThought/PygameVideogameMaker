"""Compatibility export; new code should import from ``game.entities.core``."""

from game.entities.core.sprite_collider import SpriteColliderMixin

__all__ = [
    "SpriteColliderMixin",
]
