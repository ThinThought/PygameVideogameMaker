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
        self._render_surface: pygame.Surface | None = None
        self._render_surface_size: tuple[int, int] | None = None

    def on_enter(self, app: AppLike) -> None:
        self._load_composition(app)

    def on_exit(self, app: AppLike) -> None:
        self._teardown_nodes(app)

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
        runtime = self.runtime
        if runtime is None:
            return

        target_size = runtime.canvas_size if runtime.canvas_size else screen.get_size()
        render_surface = self._ensure_render_surface(target_size)
        render_surface.fill("white")

        for node in self._iter_runtime_nodes():
            renderer = getattr(node.instance, "render", None)
            if callable(renderer):
                renderer(app, render_surface)

        canvas_rect = self._fit_canvas(screen.get_size(), render_surface.get_size())
        if canvas_rect.width <= 0 or canvas_rect.height <= 0:
            return

        if canvas_rect.size == render_surface.get_size():
            screen.blit(render_surface, canvas_rect.topleft)
        else:
            scaled = pygame.transform.smoothscale(render_surface, canvas_rect.size)
            screen.blit(scaled, canvas_rect.topleft)

    # ---------- Composition helpers ----------

    def _load_composition(self, app: AppLike) -> None:
        if self.composition_path is None:
            self.runtime = None
            self._ordered_nodes = []
            self._render_surface = None
            self._render_surface_size = None
            return

        try:
            self.runtime = load_composition(self.composition_path)
        except FileNotFoundError:
            print(f"[MainScene] Composición no encontrada: {self.composition_path}")
            self.runtime = None
            self._ordered_nodes = []
            self._render_surface = None
            self._render_surface_size = None
            return

        self._ordered_nodes = list(self.runtime.iter_nodes())
        for node in self._ordered_nodes:
            on_spawn = getattr(node.instance, "on_spawn", None)
            if callable(on_spawn):
                on_spawn(app)
        self._render_surface = None
        self._render_surface_size = None

    def _teardown_nodes(self, app: AppLike) -> None:
        for node in reversed(self._ordered_nodes):
            on_despawn = getattr(node.instance, "on_despawn", None)
            if callable(on_despawn):
                on_despawn(app)
        self._ordered_nodes = []
        self.runtime = None
        self._render_surface = None
        self._render_surface_size = None

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

    def _ensure_render_surface(self, size: tuple[int, int]) -> pygame.Surface:
        w = max(1, int(size[0] or 0))
        h = max(1, int(size[1] or 0))
        dims = (w, h)
        if self._render_surface is None or self._render_surface_size != dims:
            self._render_surface = pygame.Surface(dims).convert()
            self._render_surface_size = dims
        return self._render_surface

    def _fit_canvas(self, viewport_size: tuple[int, int], canvas_size: tuple[int, int]) -> pygame.Rect:
        vw, vh = viewport_size
        cw, ch = canvas_size
        if vw <= 0 or vh <= 0 or cw <= 0 or ch <= 0:
            return pygame.Rect(0, 0, 0, 0)
        scale = min(1.0, vw / cw, vh / ch)
        if scale <= 0:
            return pygame.Rect(0, 0, 0, 0)
        scaled_w = max(1, int(round(cw * scale)))
        scaled_h = max(1, int(round(ch * scale)))
        offset_x = (vw - scaled_w) // 2
        offset_y = (vh - scaled_h) // 2
        return pygame.Rect(offset_x, offset_y, scaled_w, scaled_h)
