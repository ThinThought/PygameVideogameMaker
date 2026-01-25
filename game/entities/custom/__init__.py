"""Custom entities live here.

Add new entity classes in this package and import them
into __all__ so the editor palette can discover them via game.entities.
"""

from .galagos_ear import GalagosEar

__all__: list[str] = [
    "GalagosEar",
]
