"""Compatibility exports; new code should import from ``game.entities.core``."""

from game.entities.core.base import AppLike, Entity

__all__ = [
    "AppLike",
    "Entity",
]
