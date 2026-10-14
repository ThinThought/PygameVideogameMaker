"""Compatibility exports; new code should import from ``game.entities.core``."""

from game.entities.core.collider import ColliderEntity, Platform

__all__ = [
    "ColliderEntity",
    "Platform",
]
