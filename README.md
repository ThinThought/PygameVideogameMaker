# Pygame Videogame Maker

A 2D platformer game creator with a built-in visual editor, built with Pygame.

This project lets you design and build levels using an integrated editor and then play them immediately.

[SCREENSHOT: Gameplay showing the player character, platforms, and background.]

## Features

* **Visual Editor**: Create and modify levels in real time. Place platforms, enemies, and other game elements visually.
* **Entity–Environment Interaction Model (EEI)**: A flexible architecture for defining game objects and their interactions.
* **Controller Support**: Configurable controller profiles for a plug-and-play gaming experience.
* **Deployment-Ready**: Includes scripts to package and deploy the game to compatible retro consoles.

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

This will open the main window, loading the editor scene.

### 3. Play the Game

Inside the application, you can switch between different scenes (Editor, Game, Input Test) using the following keys:

* **F2 / Tab**: Switch to the next scene.
* **F1 / Shift+Tab**: Switch to the previous scene.

The main game scene (`MainScene`) is typically the first in the cycle, allowing you to play the levels you’ve created.

## The Visual Editor

The editor is the core tool for building your game. It allows you to:

* **Compose Scenes**: Add, select, and move entities directly in the game space.
* **Configure Properties**: Adjust each entity’s properties, such as its sprite, behavior, and physical attributes.
* **Export Levels**: Save your creations to a composition file (`.eei.json`) that the game can load.

[SCREENSHOT: The visual editor interface, showing entity placement and the properties editor.]

## The Entity–Environment Interaction Model (EEI)

The project uses a design model where the game is built from two main components:

* **Environments (`Environment`)**: Represent spaces or zones that apply rules to the objects inside them. For example, a “gravity” environment applies a downward force to all contained entities. Environments can be nested, and their effects are combined.
* **Entities (`Entity`)**: Interactive game objects such as the player, enemies, platforms, or items. Entities live inside environments and are affected by their rules.

This model enables a flexible and composable way to build complex game logic.

You can adjust screen resolution, FPS, and other general settings in `game/configs/settings.toml`.

```toml
title = "Pygame Videogame Maker"
width = 1280
height = 720
fps = 60
```

### Controls and Controllers

Controller mappings are defined in `game/configs/controllers/generic.toml`. You can edit this file to adapt the game to different gamepads without changing the code.

```toml
# Example button mapping
a = { type = "button", index = 0, label = "A" }
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

