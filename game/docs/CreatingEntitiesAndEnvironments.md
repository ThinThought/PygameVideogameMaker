# Crear Entities y Environments (EEIM)

Guia rapida para crear entidades y entornos siguiendo la filosofia del
Entity-Environment-Interaction Model (EEIM).

## Reglas base del EEIM

- Un Entity siempre vive dentro de un Environment.
- Un Environment puede colgar del root o de un Entity.
- Las reglas del Environment afectan a sus Entities hijas.
- Un Entity puede contener Environments para anidar logica.

Referencia general: `game/docs/TheEntityEnvironmentModel.md`.

## Donde poner cada clase

Entidades:
- Base/abstractas: `game/entities/core/`
- Jugadores: `game/entities/players/`
- Plataformas: `game/entities/platforms/`
- Miscelaneo: `game/entities/misc/`

Environments:
- `game/environments/`

## Crear una Entity nueva

1) Crea la clase heredando de `Entity` o alguna base concreta (ej: `VisibleMassEntity`).
2) Implementa los metodos que necesites: `on_spawn`, `update`, `render`, etc.
3) Coloca el archivo en la subcarpeta correcta.
4) Exporta la clase para que el editor la vea (ver "Selector del editor").

Ejemplo minimo:

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

## Crear un Environment nuevo

1) Hereda de `Environment`.
2) Aplica reglas a sus entities hijas desde `update` o eventos.
3) Exporta la clase para que aparezca en el editor.

Ejemplo minimo:

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

## Selector del editor

El selector usa `__all__` para poblar el catalogo:

- Entities: `game/entities/__init__.py`
- Environments: `game/environments/__init__.py`

Si una clase es abstracta, marca:

```python
__abstract__ = True
```

Las clases con `__abstract__` no aparecen en el selector.

## Usar en composiciones

Cuando guardas una composicion, el campo `type` debe apuntar a una ruta importable.
Puedes usar la ruta estable via `game.entities.<Clase>` o `game.environments.<Clase>`.

Ejemplo:

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

Para mas detalles del formato: `game/docs/eei_composition_format.md`.
