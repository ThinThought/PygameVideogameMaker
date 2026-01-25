from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class WindowConfig:
    width: int
    height: int
    title: str
    fps: int
    resizable: bool
    fullscreen: bool
    display_index: int | None
    window_pos: tuple[int, int] | None


def load_window_config(path: Path) -> WindowConfig:
    data = tomllib.loads(path.read_text())
    w = data["window"]
    window_pos_raw = w.get("window_pos", None)
    window_pos = None
    if isinstance(window_pos_raw, (list, tuple)) and len(window_pos_raw) == 2:
        try:
            window_pos = (int(window_pos_raw[0]), int(window_pos_raw[1]))
        except (TypeError, ValueError):
            window_pos = None
    return WindowConfig(
        width=w["width"],
        height=w["height"],
        title=w["title"],
        fps=w["fps"],
        resizable=w.get("resizable", False),
        fullscreen=w.get("fullscreen", False),
        display_index=w.get("display_index", None),
        window_pos=window_pos,
    )
