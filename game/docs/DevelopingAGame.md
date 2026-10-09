# Developing a game with this template

This project contains two parts: the reusable editor/runtime and the content of
your game. Start by building a scene in the editor; add code only when the
palette and composition format do not cover the behavior you need.

## Start a project

From the Pygame Videogame Maker repository, generate a clean project folder:

```bash
uv run pygame-editor new MyGame --output-dir ../games
cd ../games/MyGame
uv sync
uv run my-game editor
```

The generated project keeps the editor, runtime, generic entities and
environments, and documentation. Its starter composition is empty, so it does
not inherit another game's scene. Replace `my-game` with the generated command
name if you chose a different project name.

Use `uv run my-game run` to launch the game. The editor writes its scene to
`game/configs/compositions/editor_export.eei.json`.

## Compose a scene first

The editor palette includes the built-in entities and environments. A useful
starting set is `VoidEntity`, the platform entities, `BackgroundEnvironment`,
`ForceEnvironment`, and `MusicEnvironment`. `SpykePlayer` is an included sample
player that can be used as a reference or replaced with a game's own character.

In the EEI model, every entity belongs to an environment. Environments may
contain entities, and entities may contain environments to form nested rules.
The composition stores class paths, transforms, and editable state; it does not
store editor-only viewport markers.

## Add a game entity

1. Add a Python module under `game/entities/custom/`.
2. Inherit from `Entity` or a suitable built-in base class.
3. Export the class from `game/entities/custom/__init__.py` and add it to
   `__all__`. The editor discovers exported concrete classes automatically.
4. Save a composition after adding the entity so its import path and state are
   recorded.

For example:

```python
from __future__ import annotations

import pygame

from game.entities.core.base import AppLike, Entity


class Coin(Entity):
    def __init__(self, pos: pygame.Vector2 | tuple[float, float] | None = None):
        self.pos = pygame.Vector2(pos if pos is not None else (0, 0))
        self.radius = 10

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, (255, 210, 0), self.pos, self.radius)
```

If a node has no sprite or other visible rendering, give it an
`EDITOR_MARKER_LABEL` class attribute. The editor draws and hit-tests that marker;
the game runtime does not render it.

## Add an environment

Create a module under `game/environments/`, inherit from `Environment`, and
export the class from `game/environments/__init__.py`. Use `on_spawn` and
`on_despawn` for setup and cleanup, and `update` for ongoing behavior. Environments
can apply rules to descendant entities; keep game-specific rules in the new
environment rather than changing the shared EEI loader.

## Keep game content organized

- Put game-specific entities in `game/entities/custom/` and game-specific
  environments in `game/environments/`.
- Put images, sounds, and music under `game/assets/`; resolve them through
  `game.core.resources.get_asset_path` so installed builds can find them.
- Keep settings in `game/configs/settings.toml` and scenes in
  `game/configs/compositions/`.
- Use importable class paths in saved compositions. Keep class/module names
  stable after scenes have been saved, or update the affected composition files.
- Keep reusable editor, input, and physics changes in their respective core
  modules; keep game-specific mechanics in game content classes.

More detail on the tree format is in [`eei_composition_format.md`](eei_composition_format.md).
