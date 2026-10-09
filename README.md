# Pygame Videogame Maker

A 2D platformer game creator with a built-in visual editor, built with Pygame.

This project lets you compose game scenes in an integrated editor, save them as
EEI compositions, and run them immediately.

## Features

* **Scene editor**: Compose scenes from a scrollable palette of exported entities and environments, then inspect the scene tree and edit supported properties.
* **Extended viewport**: The target game resolution is centered inside a larger composition workspace. Elements can be placed outside the target area and remain in the composition; the game view clips them at runtime.
* **EEI compositions**: Save scene hierarchy, class paths, transforms, and state to versioned `.eei.json` files.
* **Editor-only markers**: Logical nodes such as music can expose a selectable marker without adding a sprite to gameplay.
* **Keyboard and gamepad editing**: Use mouse controls or the virtual cursor and buttons on a connected controller.
* **Project generator**: Create a new game folder with the editor, runtime, starter components, and an empty composition.

## Getting Started

### 1. Installation

To install the project dependencies, run:

```bash
uv sync
```

### 2. Run the Editor

The project includes a visual editor that runs by default. To launch it, use:

```bash
uv run pygame-editor
```

This will open the editor scene. To run the current game composition directly, use:

```bash
uv run pygame-editor run
```

### Create a game project

From this repository, generate a clean project folder:

```bash
uv run pygame-editor new MyGame --output-dir ../games
cd ../games/MyGame
uv sync
uv run my-game editor
```

The generated project keeps the editor, runtime, and generic entities and
environments, but starts with an empty composition. Run it with
`uv run my-game run`. See `game/docs/DevelopingAGame.md` for instructions on
adding game-specific entities, environments, assets, and mechanics. Replace
`my-game` with the command generated from your chosen project name.

### Switch scenes

Use **F2** or **Tab** to move to the next scene, and **F1** or **Shift+Tab** to
move to the previous one. Press **Escape** to close the application.

## The Visual Editor

The editor provides these current scene-building features:

* **Target resolution**: Choose 720×480, 1024×768, desktop size, or enter a custom resolution. The game target stays centered in the workspace.
* **Palette**: Add concrete entities and environments exported by the game modules. Scroll each palette column when it contains more items than fit on screen; placing an item starts a drag so you can position it immediately.
* **Composition workspace**: Select and drag nodes inside the extended workspace, including areas outside the target game frame. Nodes keep their game-space coordinates when you save or play.
* **Scene tree**: Select nodes from the hierarchy, review parent/child relationships, and scroll through larger compositions.
* **Property inspector**: Edit supported public values on the selected node. Booleans toggle on click; text and numeric values can be edited with the keyboard.
* **Context menu**: Right-click a node to delete it, change its render order, or add an allowed entity or environment before or after it.
* **Save and play**: Use the toolbar buttons or **Ctrl+S** to save. **Play** saves the composition and opens it in the game scene.
* **Controller cursor**: When a joystick is connected, the left stick moves a virtual cursor, A/B act as the primary click, Y/X act as the secondary click, and the right stick scrolls panels.

To add a selectable editor marker for a logical object without a sprite, define
`EDITOR_MARKER_LABEL` on its class. The marker is drawn by the editor only.

## The Entity–Environment Interaction Model (EEI)

The project uses a design model where the game is built from two main components:

* **Environments (`Environment`)**: Represent spaces or zones that apply rules to their child entities. Built-ins include backgrounds, forces, music, and void containers; environments may be nested under entities.
* **Entities (`Entity`)**: Game objects such as players, platforms, and items. Each entity belongs to an environment and may contain child environments.

The editor enforces these parent/child rules when adding nodes and records the
hierarchy in the composition file. Learn how to extend it in
[`game/docs/DevelopingAGame.md`](game/docs/DevelopingAGame.md).

You can adjust the initial window size, title, FPS, and display settings in
`game/configs/settings.toml`. The editor also lets you choose the target
resolution per composition.

```toml
[window]
title = "Videogame Maker"
width = 720
height = 480
fps = 60
```

### Controls and Controllers

The editor loads its controller labels and mappings from
`game/configs/controllers/generic.toml`. Define controls as TOML arrays of
tables; the editor also has fallback button and axis indices.

```toml
name = "Generic Controller"
deadzone = 0.2

[[buttons]]
name = "a"
index = 0
label = "A"

[[axes]]
name = "left_x"
index = 0
```

## Console Deployment

If you’re working with a retro console or a similar device, you can use the deployment script to package and transfer your game:

```bash
bash deploy_to_console.sh
```

The script handles packaging dependencies and required assets.

## Utility Scripts

### Optimize PNG Images

The project includes a script to trim excess transparent space from your sprites, optimizing their memory footprint.

```bash
# Trim all images in the platforms folder
uv run python scripts/prune_pngs.py game/assets/images/platforms/grass_platforms
```

