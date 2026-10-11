from __future__ import annotations

import shutil
from pathlib import Path


_DEVELOPMENT_SCENES = ("editor.py", "editor_panels.py", "input_tester.py")

_RUNTIME_SCENES_INIT = '''from .base import Scene
from .main import MainScene

SCENES = {"main": MainScene}

__all__ = ["MainScene", "Scene"]
'''

_RUNTIME_APP_IMPORT = "from game.scenes import MainScene, Scene"
_RUNTIME_SCENE_BUILDER = '''def _build_scenes() -> dict[str, Type[Scene]]:
    from game.scenes import SCENES

    return SCENES
'''


def export_game(project_root: Path, output_dir: Path) -> Path:
    """Create a distributable, game-only copy of a project."""
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    destination = output_dir / f"{project_root.name}-linux"

    try:
        destination.relative_to(project_root / "game")
    except ValueError:
        pass
    else:
        raise ValueError("The export destination cannot be inside the source game/")

    if not (project_root / "game" / "scenes" / "__init__.py").is_file():
        raise FileNotFoundError(f"No game package found under {project_root}")

    if destination.exists():
        raise FileExistsError(
            f"Export destination already exists: {destination}. "
            "Choose another --output-dir or remove the existing export."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        project_root / "game",
        destination / "game",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )

    scenes_dir = destination / "game" / "scenes"
    for filename in _DEVELOPMENT_SCENES:
        (scenes_dir / filename).unlink(missing_ok=True)
    shutil.rmtree(destination / "game" / "editor", ignore_errors=True)
    (destination / "game" / "configs" / "input_tester_joystick.json").unlink(
        missing_ok=True
    )
    (destination / "game" / "scenes" / "__init__.py").write_text(
        _RUNTIME_SCENES_INIT, encoding="utf-8"
    )

    app_path = destination / "game" / "core" / "app.py"
    app_source = app_path.read_text(encoding="utf-8")
    editor_import = "from game.scenes import MainScene, EditorScene, Scene"
    if editor_import not in app_source:
        raise ValueError("Could not locate the scene import in game/core/app.py")
    app_source = app_source.replace(editor_import, _RUNTIME_APP_IMPORT)
    start = app_source.index("def _build_scenes()")
    end = app_source.index("\n\n\nclass App:", start)
    app_source = app_source[:start] + _RUNTIME_SCENE_BUILDER + app_source[end:]
    app_path.write_text(app_source, encoding="utf-8")

    launcher = project_root / "PygameVideogameMaker.pygame"
    if launcher.is_file():
        shutil.copy2(launcher, destination / launcher.name)
    vendor = project_root / "vendor"
    if vendor.is_dir():
        shutil.copytree(vendor, destination / "vendor")

    (destination / "README-export.txt").write_text(
        "Linux game export\n"
        "=================\n\n"
        "Run PygameVideogameMaker.pygame with Python 3.12 or newer.\n"
        "Required Python packages must be available in vendor/ or installed\n"
        "in the Python environment used to launch the game.\n\n"
        "This export contains the game runtime and project assets. The scene\n"
        "editor and input tester have been removed.\n",
        encoding="utf-8",
    )
    return destination
