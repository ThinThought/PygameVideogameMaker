from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Sequence

_COPY_DIRS = ("game",)
_COPY_FILES = (
    "pyproject.toml",
    "README.md",
    ".gitignore",
    "LICENSE",
    "deploy_to_console.sh",
    "PygameVideogameMaker.pygame",
)
_IGNORE_PATTERNS = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "*.py[co]")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="pygame-editor",
        description="Run the current template or generate a new project from it.",
    )
    parser.set_defaults(func=_run_game)
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run", help="Run the game defined by the template."
    )
    run_parser.set_defaults(func=_run_game)

    editor_parser = subparsers.add_parser("editor", help="Launch the game editor.")
    editor_parser.set_defaults(func=_run_editor)

    new_parser = subparsers.add_parser(
        "new",
        help="Generate a new project by copying the template files.",
    )
    new_parser.add_argument(
        "name",
        help="Project name or destination path. A folder is inferred from this name.",
    )
    new_parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory where the project will be created (defaults to current).",
    )
    new_parser.set_defaults(func=_generate_project)

    args = parser.parse_args(argv)
    func = args.func
    func(args)


def _run_game(_: argparse.Namespace) -> None:
    from game.main import main as run_game

    run_game()


def _run_editor(_: argparse.Namespace) -> None:
    from game.core.app import App
    from game.core.config import load_window_config
    from game.main import _share_path
    from game.scenes.editor import EditorScene
    import sys  # Import sys for sys.exit

    cfg = load_window_config(_share_path("configs", "settings.toml"))
    app = App(cfg)

    editor_scene_index = -1
    for i, scene_cls in enumerate(app.scenes.values()):
        if scene_cls is EditorScene:
            editor_scene_index = i
            break
    if editor_scene_index != -1:
        app.set_scene(editor_scene_index)
    else:
        print("Error: EditorScene not found in available scenes.")
        sys.exit(1)  # Exit if editor scene isn't found

    app.run()


def _generate_project(args: argparse.Namespace) -> None:
    destination = _resolve_destination(args.name, args.output_dir)
    template_root = Path(__file__).resolve().parents[1]

    if destination.exists():
        raise SystemExit(
            f"Destination path '{destination}' already exists. Choose another folder."
        )

    destination.mkdir(parents=True)

    for folder in _COPY_DIRS:
        src = template_root / folder
        if not src.exists():
            continue
        shutil.copytree(
            src, destination / folder, dirs_exist_ok=True, ignore=_IGNORE_PATTERNS
        )

    for file_name in _COPY_FILES:
        src_file = template_root / file_name
        if not src_file.exists():
            continue
        (destination / file_name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, destination / file_name)

    name_tokens = _tokenize_name(Path(args.name).name)
    slug = (
        _slugify("-".join(name_tokens)) if name_tokens else _slugify(destination.name)
    )
    readable_name = _to_display_name(name_tokens) if name_tokens else destination.name
    launcher_stub = _to_pascal_case(name_tokens)

    _rewrite_pyproject(destination / "pyproject.toml", slug)
    _rewrite_window_title(
        destination / "game" / "configs" / "settings.toml", readable_name
    )
    _rename_launcher(destination, launcher_stub)
    _write_project_readme(destination / "README.md", readable_name, slug)
    starter_composition = (
        destination / "game" / "configs" / "compositions" / "editor_export.eei.json"
    )
    _write_starter_composition(starter_composition)

    rel_path = (
        destination.relative_to(Path.cwd())
        if destination.is_relative_to(Path.cwd())
        else destination
    )
    print(f"Project generated at: {rel_path}")


def _resolve_destination(name: str, base_dir: str) -> Path:
    path_candidate = Path(name.strip())
    if not path_candidate.is_absolute():
        path_candidate = Path(base_dir).expanduser() / path_candidate
    return path_candidate.resolve()


def _tokenize_name(raw_name: str) -> list[str]:
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", raw_name)
    tokens = re.split(r"[^A-Za-z0-9]+", normalized)
    return [token for token in tokens if token]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise SystemExit("Could not infer a valid project name.")
    return slug


def _to_display_name(tokens: list[str]) -> str:
    return " ".join(token.capitalize() for token in tokens) if tokens else "New Game"


def _to_pascal_case(tokens: list[str]) -> str:
    return "".join(token.capitalize() for token in tokens) if tokens else "Game"


def _rewrite_pyproject(pyproject_path: Path, project_slug: str) -> None:
    if not pyproject_path.exists():
        return

    content = pyproject_path.read_text(encoding="utf-8")
    content = re.sub(
        r'(?m)^name\s*=\s*".*"$', f'name = "{project_slug}"', content, count=1
    )
    content = re.sub(
        r'(?m)^pygame-editor\s*=\s*"game\.cli:main"$',
        f'{project_slug} = "game.cli:main"',
        content,
        count=1,
    )
    pyproject_path.write_text(content, encoding="utf-8")


def _rewrite_window_title(settings_path: Path, project_name: str) -> None:
    if not settings_path.exists():
        return
    content = settings_path.read_text(encoding="utf-8")
    content = re.sub(
        r'(?m)^title\s*=\s*".*"$',
        f'title = "{project_name}"',
        content,
        count=1,
    )
    settings_path.write_text(content, encoding="utf-8")


def _rename_launcher(project_root: Path, launcher_stub: str) -> None:
    original_launcher = project_root / "PygameVideogameMaker.pygame"
    if not original_launcher.exists():
        return
    new_name = project_root / f"{launcher_stub or 'Game'}.pygame"
    original_launcher.rename(new_name)


def _write_project_readme(readme_path: Path, project_name: str, command: str) -> None:
    readme_path.write_text(
        f"""# {project_name}

A 2D game project created with Pygame Videogame Maker. The editor, runtime,
composition format, and generic starter entities and environments are included.

## Get started

```bash
uv sync
uv run {command} editor
```

Use the editor palette to add entities and environments, then save the scene.
To run the game, use:

```bash
uv run {command} run
```

## Develop the game

Read [`game/docs/DevelopingAGame.md`](game/docs/DevelopingAGame.md) for the
project structure, EEI model, and instructions for adding game-specific code.
The Spanish guide is [`game/docs/DesarrollarUnJuego.md`](game/docs/DesarrollarUnJuego.md).
The scene is stored in `game/configs/compositions/editor_export.eei.json`.
""",
        encoding="utf-8",
    )


def _write_starter_composition(composition_path: Path) -> None:
    composition_path.write_text(
        '{\n'
        '  "version": 1,\n'
        '  "metadata": {"name": "starter-scene", "description": "", "tags": []},\n'
        '  "scene": {"canvas": [720, 480], "origin": [0, 0]},\n'
        '  "nodes": [],\n'
        '  "interactions": []\n'
        '}\n',
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(sys.argv[1:])
