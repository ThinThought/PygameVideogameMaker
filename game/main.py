from __future__ import annotations

import importlib.resources
from pathlib import Path

from game.core.app import App
from game.core.config import load_window_config


def _share_path(*parts: str) -> Path:
    """
    Return the path to a packaged resource inside the 'game' directory.

    Uses importlib.resources to resolve the path robustly in both
    development and installed environments.
    """
    return importlib.resources.files("game").joinpath(*parts)


def main() -> None:
    # Now that 'configs' lives inside the 'game' package, load it this way.
    cfg = load_window_config(_share_path("configs", "settings.toml"))
    App(cfg).run()


if __name__ == "__main__":
    main()
