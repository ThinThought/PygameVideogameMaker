# Desarrollar un videojuego con esta plantilla

El proyecto incluye el editor y el runtime reutilizables, además del contenido
del juego. Empieza componiendo una escena en el editor; añade código cuando la
paleta y el formato de composición no cubran el comportamiento que necesitas.

## Crear y ejecutar un proyecto

Desde el repositorio de Pygame Videogame Maker, crea una carpeta para el juego:

```bash
uv run pygame-editor new MiJuego --output-dir ../juegos
cd ../juegos/MiJuego
uv sync
uv run mi-juego editor
```

El proyecto conserva el editor, el runtime, las entidades y los entornos
genéricos, y la documentación. La composición inicial está vacía para no copiar
la escena de otro juego. Sustituye `mi-juego` por el comando generado a partir
del nombre de tu proyecto.

Ejecuta `uv run mi-juego run` para jugar. El editor guarda la escena en
`game/configs/compositions/editor_export.eei.json`.

## Componer una escena

La paleta incluye entidades y entornos básicos. Puedes empezar con
`VoidEntity`, las plataformas, `BackgroundEnvironment`, `ForceEnvironment` y
`MusicEnvironment`. `SpykePlayer` es un personaje de ejemplo que sirve como
referencia o que puedes sustituir por el personaje de tu juego.

En el modelo EEI, cada entidad vive dentro de un entorno. Un entorno puede
contener entidades y una entidad puede contener entornos, formando reglas
anidadas. La composición guarda rutas de clases, transformaciones y estado
editable; los marcadores exclusivos del editor no se guardan como sprites.

## Añadir una entidad del juego

1. Crea un módulo Python en `game/entities/custom/`.
2. Hereda de `Entity` o de una clase base adecuada.
3. Exporta la clase desde `game/entities/custom/__init__.py` y añádela a
   `__all__`. El editor descubre automáticamente las clases concretas exportadas.
4. Guarda la composición para registrar la ruta importable de la clase y su
   estado.

```python
from __future__ import annotations

import pygame

from game.entities.core.base import AppLike, Entity


class Moneda(Entity):
    def __init__(self, pos: pygame.Vector2 | tuple[float, float] | None = None):
        self.pos = pygame.Vector2(pos if pos is not None else (0, 0))
        self.radius = 10

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, (255, 210, 0), self.pos, self.radius)
```

Si un nodo no tiene sprite ni otra representación visible, define el atributo
de clase `EDITOR_MARKER_LABEL`. El editor dibujará el marcador y permitirá
seleccionarlo; el runtime del juego no lo renderiza.

## Añadir un entorno

Crea un módulo en `game/environments/`, hereda de `Environment` y exporta la
clase desde `game/environments/__init__.py`. Usa `on_spawn` y `on_despawn` para
inicializar y limpiar recursos, y `update` para la lógica continua. Las reglas
específicas del juego deben vivir en su entorno, sin modificar el cargador EEI
compartido.

## Organización recomendada

- Guarda entidades propias en `game/entities/custom/` y entornos propios en
  `game/environments/`.
- Guarda imágenes, sonidos y música en `game/assets/`; resuélvelos mediante
  `game.core.resources.get_asset_path` para que funcionen en instalaciones.
- Guarda ajustes en `game/configs/settings.toml` y composiciones en
  `game/configs/compositions/`.
- Mantén estables los nombres de módulo y las rutas de clase que usan las
  composiciones, o actualiza los archivos de escena afectados.
- Deja los cambios reutilizables de editor, entrada y física en los módulos
  compartidos; implementa las mecánicas del juego en sus clases de contenido.

Consulta también [`eei_composition_format.md`](eei_composition_format.md).
