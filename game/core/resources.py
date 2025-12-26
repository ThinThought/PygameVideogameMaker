from pathlib import Path
import importlib.resources


def get_asset_path(relative_path: str) -> Path:
    """

    Returns the path to an asset file using importlib.resources.

    """
    base_path = importlib.resources.files("game.assets")
    resolved_path = base_path.joinpath(relative_path)
    return resolved_path


def get_config_path(relative_path: str) -> Path:
    """



    Returns the path to a configuration file using importlib.resources.



    """

    base_path = importlib.resources.files("game.configs")

    print(f"DEBUG: get_config_path - base_path: {base_path}, type: {type(base_path)}")

    resolved_path = base_path.joinpath(relative_path)

    print(f"DEBUG: get_config_path - resolved_path: {resolved_path}")

    return resolved_path


def get_composition_path(relative_path: str) -> Path:
    """

    Returns the path to a composition file using importlib.resources.

    """
    base_path = importlib.resources.files("game.compositions")
    resolved_path = base_path.joinpath(relative_path)
    return resolved_path
