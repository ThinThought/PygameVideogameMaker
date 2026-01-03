# Creating Entities and Environments (EEIM)

Quick guide to create entities and environments following the
Entity-Environment-Interaction Model (EEIM) philosophy.

## Core EEIM rules

- An Entity always lives inside an Environment.
- An Environment can hang from the root or from an Entity.
- Environment rules affect their child Entities.
- An Entity can contain Environments to nest behavior.

General reference: `game/docs/TheEntityEnvironmentModel.md`.

## Where to place each class

Entities:
- Base/abstract: `game/entities/core/`
- Players: `game/entities/players/`
- Platforms: `game/entities/platforms/`
- Misc: `game/entities/misc/`

Environments:
- `game/environments/`

## Create a new Entity

1) Create the class inheriting from `Entity` or a concrete base (e.g. `VisibleMassEntity`).
2) Implement the methods you need: `on_spawn`, `update`, `render`, etc.
3) Put the file in the right subfolder.
4) Export the class so the editor can see it (see "Editor palette").

Minimal example:

```python
from __future__ import annotations
import pygame

from game.entities.core.base import Entity, AppLike


class Coin(Entity):
    def __init__(self, pos: pygame.Vector2 | tuple[float, float] | None = None) -> None:
        self.pos = pygame.Vector2(pos) if pos is not None else pygame.Vector2(0, 0)
        self.radius = 10

    def update(self, app: AppLike, dt: float) -> None:
        pass

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, (255, 210, 0), self.pos, self.radius)
```

## Create a new Environment

1) Inherit from `Environment`.
2) Apply rules to child entities from `update` or events.
3) Export the class so it appears in the editor.

Minimal example:

```python
from __future__ import annotations
import pygame

from game.environments.base import Environment, AppLike


class SlowZone(Environment):
    def __init__(self, pos: pygame.Vector2 | tuple[float, float] | None = None) -> None:
        self.pos = pygame.Vector2(pos) if pos is not None else pygame.Vector2(0, 0)

    def update(self, app: AppLike, dt: float) -> None:
        for entity in self._iter_entities():
            if hasattr(entity, "velocity"):
                entity.velocity *= 0.98
```

## Editor palette

The palette uses `__all__` to populate the catalog:

- Entities: `game/entities/__init__.py`
- Environments: `game/environments/__init__.py`

If a class is abstract, mark it as:

```python
__abstract__ = True
```

Classes with `__abstract__` do not appear in the palette.

## Use in compositions

When saving a composition, the `type` field must be an importable path.
Use the stable route via `game.entities.<Class>` or `game.environments.<Class>`.

Example:

```json
{
  "id": "ent-coin-1",
  "kind": "entity",
  "type": "game.entities.Coin",
  "parent": "env-main-1",
  "transform": {"position": [120, 180]},
  "state": {"radius": 12}
}
```

More format details: `game/docs/eei_composition_format.md`.
