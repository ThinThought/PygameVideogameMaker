# Exporting a Game for Linux

Use the export command after development is complete to create a copy of the
project that starts directly in the game scene and omits the editor and input
tester scenes.

## Create the export

Run the command from the game project directory:

```bash
uv run my-game export game
```

The command prompts for the parent directory where it should create `dist/`.
Press Enter to use the current directory. To run it without a prompt, pass the
parent directory with `--output-dir`:

```bash
uv run my-game export game --output-dir /path/to/release
```

The resulting directory is:

```text
<output-parent>/dist/<project-name>-linux/
```

The exported folder contains the `game/` package and `README-export.txt`. The
exporter copies `PygameVideogameMaker.pygame` when that exact filename exists
in the project root. Projects created with `pygame-editor new` rename this
launcher, so rename it back to `PygameVideogameMaker.pygame` before exporting
those projects. If no matching launcher is present, the exporter currently
does not report an error, and the output will not have a launcher to start.

The exporter removes the editor and input tester scene modules, the editor
package, and the input tester configuration. The saved composition and game
assets remain in place. If a `vendor/` directory exists in the source project,
it is copied into the export.

The exporter will not overwrite an existing destination. Choose another
`--output-dir` or move the old export before exporting again.

## Target requirements

This export is Python source plus assets, not a native Linux executable. The
target device must provide Python 3.12 or newer. If you include a `vendor/`
directory, its packages—especially Pygame and other compiled extensions—must be
compatible with the target's Linux distribution, Python version, and CPU
architecture. The exporter does not bundle Python or cross-compile packages.

Linux devices do not all use the same CPU architecture or graphics/audio
stack. Build or prepare `vendor/` for the actual target device, then copy the
export folder to it. On systems without Python or the required system
libraries, the launcher will not start until those prerequisites are supplied.

## Running the game

Launch the exported `.pygame` file with the target's Python runtime. The
launcher adds `vendor/` to Python's module search path when that directory is
present, changes the working directory to the exported folder, and starts
`game/main.py`.

For development workflow and project structure, see
[`DevelopingAGame.md`](DevelopingAGame.md).
