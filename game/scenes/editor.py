from __future__ import annotations

import pygame
from game.scenes.base import Scene, AppLike
import game.entities as entities
import game.environments as environments


class EditorScene(Scene):
    def __init__(self) -> None:
        self.entities: list[object] = []
        self.entity_labels: list[str] = []
        self.selected = 0

        self.available_entities: list[tuple[str, type]] = [
            (name, getattr(entities, name))
            for name in entities.__all__
        ]
        self.available_environments: list[tuple[str, type]] = [
            (name, getattr(environments, name))
            for name in getattr(environments, "__all__", [])
        ]

        self.dragging = False
        self.drag_mode: str | None = None
        self.drag_offset = pygame.Vector2(0, 0)

        self.font = pygame.font.Font(None, 20)
        self.font_mono = pygame.font.Font(None, 18)

        self.margin = 20
        self.gap = 12
        self.palette_item_h = 28
        self.entity_items_rects: list[pygame.Rect] = []
        self.environment_items_rects: list[pygame.Rect] = []

        self._last_size: tuple[int, int] | None = None

    # ---------------- Layout ----------------

    def _ensure_layout(self, screen: pygame.Surface) -> None:
        size = screen.get_size()
        if size != self._last_size:
            self._recompute_layout(size)
            self._last_size = size

    def _recompute_layout(self, size: tuple[int, int]) -> None:
        w, h = size
        self.scene_width, self.scene_height = w, h

        m = self.margin
        gap = self.gap

        left_w = int(w * 0.55)
        self.canvas_rect = pygame.Rect(m, m, left_w - m, h - 2 * m)

        right_x = self.canvas_rect.right + gap
        right_w = w - right_x - m
        self.inspector_rect = pygame.Rect(right_x, m, right_w, h - 2 * m)

        palette_h = min(180, self.inspector_rect.height // 3)
        palette_width = self.inspector_rect.width
        column_gap = min(gap, palette_width)
        entity_w = max(0, (palette_width - column_gap) // 2)
        env_w = max(0, palette_width - entity_w - column_gap)

        palette_y = self.inspector_rect.y
        palette_x = self.inspector_rect.x
        self.entities_palette_rect = pygame.Rect(palette_x, palette_y, entity_w, palette_h)
        env_x = self.entities_palette_rect.right + column_gap
        self.environments_palette_rect = pygame.Rect(env_x, palette_y, env_w, palette_h)

        palettes_bottom = max(self.entities_palette_rect.bottom, self.environments_palette_rect.bottom)
        insp_y = palettes_bottom + gap
        insp_h = self.inspector_rect.bottom - insp_y
        self.inspector_rect = pygame.Rect(self.inspector_rect.x, insp_y, self.inspector_rect.width, insp_h)

        self._rebuild_palette_item_rects()

    def _rebuild_palette_item_rects(self) -> None:
        self.entity_items_rects = self._build_palette_rects(self.entities_palette_rect, len(self.available_entities))
        self.environment_items_rects = self._build_palette_rects(
            self.environments_palette_rect,
            len(self.available_environments),
        )

    def _build_palette_rects(self, rect: pygame.Rect, count: int) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        if rect.width <= 0 or count <= 0:
            return rects

        x = rect.x + 10
        y = rect.y + 36
        w = rect.width - 20
        h = self.palette_item_h

        for _ in range(count):
            rects.append(pygame.Rect(x, y, w, h))
            y += h + 6
        return rects

    # ---------------- Update / Events ----------------

    def update(self, app: AppLike, dt: float) -> None:
        for entity in self.entities:
            entity.update(app, dt)

    # (tu handle_event lo puedes mantener, pero recuerda: VIDEORESIZE en escenas no hace falta si el core gestiona)
    # y recuerda convertir mouse a local si usas viewport/hud.

    # ---------------- Render (orquestador) ----------------

    def render(self, app, screen: pygame.Surface) -> None:
        self._ensure_layout(screen)

        screen.fill("black")

        self._render_canvas(app, screen)
        self._render_palettes(app, screen)
        self._render_inspector(app, screen)

    # ---------------- Render helpers ----------------

    def _render_canvas(self, app: AppLike, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, "white", self.canvas_rect, border_radius=6)

        prev_clip = screen.get_clip()
        screen.set_clip(self.canvas_rect.inflate(-4, -4))

        for i, ent in enumerate(self.entities):
            ent.render(app, screen)
            if i == self.selected:
                self._render_selection_ring(screen, ent)

        screen.set_clip(prev_clip)

    def _render_selection_ring(self, screen: pygame.Surface, ent: object) -> None:
        p = getattr(ent, "pos", None)
        if p is None:
            return
        r = int(getattr(ent, "radius", 26)) + 6
        pygame.draw.circle(screen, (255, 200, 0), (int(p.x), int(p.y)), r, 2)

    def _render_palettes(self, app: AppLike, screen: pygame.Surface) -> None:
        mouse = self._mouse_local(app)
        self._render_palette_column(
            screen,
            self.entities_palette_rect,
            "Entities",
            self.available_entities,
            self.entity_items_rects,
            mouse,
        )
        self._render_palette_column(
            screen,
            self.environments_palette_rect,
            "Environments",
            self.available_environments,
            self.environment_items_rects,
            mouse,
        )

    def _render_palette_column(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        items: list[tuple[str, type]],
        item_rects: list[pygame.Rect],
        mouse_pos: tuple[int, int],
    ) -> None:
        if rect.width <= 0 or rect.height <= 0:
            return
        pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=6)
        self._draw_section_header(screen, rect, title)

        for i, (name, _factory) in enumerate(items):
            if i >= len(item_rects):
                break
            r = item_rects[i]
            hovered = r.collidepoint(mouse_pos)
            col = (55, 55, 55) if hovered else (45, 45, 45)
            pygame.draw.rect(screen, col, r, border_radius=6)
            t = self.font_mono.render(name, True, (220, 220, 220))
            screen.blit(t, (r.x + 8, r.y + 6))

    def _render_inspector(self, app: AppLike, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (30, 30, 30), self.inspector_rect, border_radius=6)
        self._draw_section_header(screen, self.inspector_rect, "Atribs")

        if not self.entities:
            self._draw_empty_inspector(screen)
            return

        ent = self.entities[self.selected]
        self._draw_attrs(screen, self.inspector_rect, ent, self._selected_label())

    def _draw_empty_inspector(self, screen: pygame.Surface) -> None:
        msg = self.font_mono.render("No entities. Pick one from palette.", True, (160, 160, 160))
        screen.blit(msg, (self.inspector_rect.x + 10, self.inspector_rect.y + 40))

    # ---------------- Utilities ----------------

    def _mouse_local(self, app: AppLike) -> tuple[int, int]:
        """Mouse en coords de esta escena (útil si el core usa viewport/HUD)."""
        mx, my = pygame.mouse.get_pos()
        if hasattr(app, "scene_viewport"):
            vp = app.scene_viewport()
            return (mx - vp.x, my - vp.y)
        return (mx, my)

    def _draw_section_header(self, screen: pygame.Surface, rect: pygame.Rect, title: str) -> None:
        t = self.font.render(title, True, (220, 220, 220))
        screen.blit(t, (rect.x + 10, rect.y + 8))
        pygame.draw.line(
            screen, (70, 70, 70),
            (rect.x + 8, rect.y + 28),
            (rect.right - 8, rect.y + 28),
            1
        )

    def _draw_attrs(self, screen: pygame.Surface, rect: pygame.Rect, ent, label: str) -> None:
        y = rect.y + 36
        xk = rect.x + 10
        xv = rect.x + rect.width // 2

        if label:
            ksurf = self.font_mono.render("Nombre", True, (200, 200, 200))
            vsurf = self.font_mono.render(label, True, (220, 200, 160))
            screen.blit(ksurf, (xk, y))
            screen.blit(vsurf, (xv, y))
            y += 20

        for k, v in self._iter_public_attrs(ent):
            if y > rect.bottom - 10:
                break
            ksurf = self.font_mono.render(k, True, (200, 200, 200))
            vsurf = self.font_mono.render(v, True, (160, 220, 160))
            screen.blit(ksurf, (xk, y))
            screen.blit(vsurf, (xv, y))
            y += 20

    def _iter_public_attrs(self, obj) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        d = getattr(obj, "__dict__", {})
        for k in sorted(d.keys()):
            if k.startswith("_"):
                continue
            items.append((k, self._safe_repr(d[k])))
        return items

    def _safe_repr(self, v) -> str:
        try:
            s = repr(v)
        except Exception:
            s = "<unrepr-able>"
        return s if len(s) <= 70 else s[:67] + "..."


    # ---------------- Interaction ----------------

    def handle_event(self, app: AppLike, ev: pygame.event.Event) -> None:
        # layout puede no existir todavía si llega evento muy pronto
        if self._last_size is None:
            return

        pos = self._event_pos_local(app, ev)

        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self._delete_selected()
                return

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and pos is not None:
            # 1) palette -> spawn + drag
            hit = self._palette_hit(pos)
            if hit is not None:
                target, idx = hit
                self._spawn_from_palette(target, idx, pos)
                return

            # 2) canvas -> select + drag
            if self.canvas_rect.collidepoint(pos):
                hit = self._select_entity_at(pos)
                if hit is not None:
                    self._start_drag_existing(pos)
                return

        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dragging = False
            self.drag_mode = None
            return

        if ev.type == pygame.MOUSEMOTION and pos is not None:
            if self.dragging:
                self._drag_to(pos)
            return

        # passthrough
        for ent in self.entities:
            h = getattr(ent, "handle_event", None)
            if callable(h):
                h(app, ev)

    def _event_pos_local(self, app: AppLike, ev: pygame.event.Event) -> tuple[int, int] | None:
        """Convierte ev.pos (coords ventana) a coords del viewport."""
        if not hasattr(ev, "pos"):
            return None
        mx, my = ev.pos
        if hasattr(app, "scene_viewport"):
            vp = app.scene_viewport()
            return (mx - vp.x, my - vp.y)
        return (mx, my)

    # ---------- Palette / Spawn ----------

    def _palette_hit(self, pos: tuple[int, int]) -> tuple[str, int] | None:
        hit = self._palette_hit_column(pos, "entity", self.entities_palette_rect, self.entity_items_rects)
        if hit is not None:
            return hit
        return self._palette_hit_column(pos, "environment", self.environments_palette_rect, self.environment_items_rects)

    def _palette_hit_column(
        self,
        pos: tuple[int, int],
        target: str,
        rect: pygame.Rect,
        rects: list[pygame.Rect],
    ) -> tuple[str, int] | None:
        if rect.width <= 0 or rect.height <= 0:
            return None
        if not rect.collidepoint(pos):
            return None
        for i, r in enumerate(rects):
            if r.collidepoint(pos):
                return (target, i)
        return None

    def _spawn_from_palette(self, target: str, idx: int, mouse_pos: tuple[int, int]) -> None:
        collection = self.available_entities if target == "entity" else self.available_environments
        if not (0 <= idx < len(collection)):
            return

        name, factory = collection[idx]

        spawn_pos = pygame.Vector2(mouse_pos)
        if not self.canvas_rect.collidepoint(mouse_pos):
            spawn_pos = pygame.Vector2(self.canvas_rect.center)

        ent = factory(spawn_pos)
        self.entities.append(ent)
        self.entity_labels.append(self._make_entity_label(name))
        self.selected = len(self.entities) - 1

        self.drag_mode = "spawn-new"
        self._start_drag_existing(mouse_pos)

    # ---------- Select / Drag ----------

    def _select_entity_at(self, mouse_pos: tuple[int, int]) -> int | None:
        mx, my = mouse_pos
        best_i: int | None = None
        best_d2: float | None = None

        for i, e in enumerate(self.entities):
            p = getattr(e, "pos", None)
            if p is None:
                continue
            dx = mx - float(p.x)
            dy = my - float(p.y)
            d2 = dx * dx + dy * dy
            if best_d2 is None or d2 < best_d2:
                best_d2 = d2
                best_i = i

        if best_i is not None:
            self.selected = best_i
        return best_i

    def _start_drag_existing(self, mouse_pos: tuple[int, int]) -> None:
        if not self.entities:
            return
        ent = self.entities[self.selected]
        p = getattr(ent, "pos", None)
        if p is None:
            return

        self.dragging = True
        self.drag_mode = self.drag_mode or "move-existing"
        self.drag_offset = pygame.Vector2(p) - pygame.Vector2(mouse_pos)

        self._drag_to(mouse_pos)

    def _drag_to(self, mouse_pos: tuple[int, int]) -> None:
        if not self.entities:
            return
        ent = self.entities[self.selected]
        p = getattr(ent, "pos", None)
        if p is None:
            return

        desired = pygame.Vector2(mouse_pos) + self.drag_offset

        radius = float(getattr(ent, "radius", 0.0))
        left = self.canvas_rect.left + radius
        right = self.canvas_rect.right - radius
        top = self.canvas_rect.top + radius
        bottom = self.canvas_rect.bottom - radius

        desired.x = max(left, min(right, desired.x))
        desired.y = max(top, min(bottom, desired.y))

        p.x, p.y = desired.x, desired.y

    def _delete_selected(self) -> None:
        if not self.entities:
            return

        idx = min(self.selected, len(self.entities) - 1)
        self.entities.pop(idx)
        self.entity_labels.pop(idx)

        if self.entities:
            self.selected = min(idx, len(self.entities) - 1)
        else:
            self.selected = 0
        self.dragging = False
        self.drag_mode = None

    def _make_entity_label(self, base: str) -> str:
        prefix = f"{base} #"
        count = 0
        for label in self.entity_labels:
            if label == base or label.startswith(prefix):
                count += 1
        if count == 0:
            return base
        return f"{base} #{count + 1}"

    def _selected_label(self) -> str:
        if not self.entities or not self.entity_labels:
            return ""
        idx = max(0, min(self.selected, len(self.entity_labels) - 1))
        return self.entity_labels[idx]
