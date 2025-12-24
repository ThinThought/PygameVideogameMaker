from __future__ import annotations

from pathlib import Path
import sysconfig

from game.core.app import App
from game.core.config import load_window_config


def _share_path(*parts: str) -> Path:
    # Attempt to find the file relative to the project root (development mode)
    project_root = Path(__file__).resolve().parents[1]
    dev_path = project_root.joinpath(*parts)
    if dev_path.exists():
        return dev_path

    # Fallback to installed share path (installed mode)
    scheme = sysconfig.get_default_scheme()
    data = Path(sysconfig.get_path("data", scheme=scheme))
    installed_path = (data / "share" / "pygame-videogame-maker").joinpath(*parts)
    if installed_path.exists():
        return installed_path

    # If neither exists, return the installed path anyway, as it's what's expected
    # to be installed by setuptools if everything worked. This will lead to FileNotFoundError
    # if the file is truly missing, which is expected behaviour then.
    return installed_path



def main() -> None:
    # En tu wheel actual, settings.toml quedó aplanado en:
    #   <prefix>/share/pygame-videogame-maker/settings.toml
    cfg = load_window_config(_share_path("configs/settings.toml"))
    App(cfg).run()


if __name__ == "__main__":
    main()
