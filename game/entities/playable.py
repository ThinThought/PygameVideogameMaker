"""Compatibility export; new code should import from ``game.entities.players``."""

from game.entities.players.playable import PlayableMassEntity

__all__ = [
    "PlayableMassEntity",
]
