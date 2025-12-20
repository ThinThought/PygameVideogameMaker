from __future__ import annotations

import pygame
from pathlib import Path

from game.compositions import CompositionRuntime, load_composition
from game.scenes.base import Scene, AppLike

class MainScene(Scene):
    def __init__(self, composition_path: str | Path | None = None) -> None:
        self.runtime: CompositionRuntime | None = None
        self._ordered_nodes: list = []
        self.composition_path: Path | None = self._resolve_composition_path(composition_path)

    def on_enter(self, app: AppLike) -> None:
        self._load_composition(app)
        app.audio.play_music("demo.mp3", volume=1.0, fade_ms=500)

    def on_exit(self, app: AppLike) -> None:
        self._teardown_nodes(app)
        app.audio.stop_music(fade_ms=200)

    def handle_event(self, app: AppLike, ev: pygame.event.Event) -> None:
        for node in self._iter_runtime_nodes():
            handler = getattr(node.instance, "handle_event", None)
            if callable(handler):
                handler(app, ev)

    def update(self, app: AppLike, dt: float) -> None:
        for node in self._iter_runtime_nodes():
            updater = getattr(node.instance, "update", None)
            if callable(updater):
                updater(app, dt)

    def render(self, app: AppLike, screen: pygame.Surface) -> None:
        screen.fill("white")

        for node in self._iter_runtime_nodes():
            renderer = getattr(node.instance, "render", None)
            if callable(renderer):
                renderer(app, screen)

    # ---------- Composition helpers ----------

    def _load_composition(self, app: AppLike) -> None:
        if self.composition_path is None:
            self.runtime = None
            self._ordered_nodes = []
            return

        try:
            self.runtime = load_composition(self.composition_path)
        except FileNotFoundError:
            print(f"[MainScene] Composición no encontrada: {self.composition_path}")
            self.runtime = None
            self._ordered_nodes = []
            return

        self._ordered_nodes = list(self.runtime.iter_nodes())
        for node in self._ordered_nodes:
            on_spawn = getattr(node.instance, "on_spawn", None)
            if callable(on_spawn):
                on_spawn(app)

    def _teardown_nodes(self, app: AppLike) -> None:
        for node in reversed(self._ordered_nodes):
            on_despawn = getattr(node.instance, "on_despawn", None)
            if callable(on_despawn):
                on_despawn(app)
        self._ordered_nodes = []
        self.runtime = None

    def _iter_runtime_nodes(self):
        return self._ordered_nodes

    def _default_composition_path(self) -> Path | None:
        root = Path(__file__).resolve().parents[2] / "configs" / "compositions"
        preferred = root / "editor_export.eei.json"
        if preferred.exists():
            return preferred
        demo = root / "demo_face.eei.json"
        return demo if demo.exists() else None

    def _resolve_composition_path(self, provided: str | Path | None) -> Path | None:
        if provided is not None:
            candidate = Path(provided)
            return candidate if candidate.exists() else None
        return self._default_composition_path()
