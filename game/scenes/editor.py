from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame
from game.compositions import load_composition
from game.scenes.base import Scene, AppLike
import game.entities as entities
import game.environments as environments
from game.editor import EditorModel, PaletteRegistry
from game.scenes.editor_panels import (
    AttrsPanel,
    PalettePanel,
    ResolutionPanel,
    ToolbarPanel,
    TreePanel,
)
from game.input import ActionBinding, InputBinding, ControllerProfile


class EditorScene(Scene):
    INPUT_ACTIONS = [
        ActionBinding(
            action="Delete Selection",
            description="Delete/Backspace removes the active node.",
            bindings=(
                InputBinding(device="keyboard", control="K_DELETE", label="Delete"),
                InputBinding(
                    device="keyboard", control="K_BACKSPACE", label="Backspace"
                ),
            ),
        ),
        ActionBinding(
            action="Save Composition",
            description="Ctrl+S saves the open composition.",
            bindings=(
                InputBinding(
                    device="keyboard", control="K_s", label="S", modifiers=("CTRL",)
                ),
            ),
        ),
        ActionBinding(
            action="Inspector Navigate",
            description="Up/Down arrows move inspector focus.",
            bindings=(
                InputBinding(device="keyboard", control="K_UP", label="Up Arrow"),
                InputBinding(device="keyboard", control="K_DOWN", label="Down Arrow"),
            ),
        ),
        ActionBinding(
            action="Inspector Edit",
            description="Enter starts editing, Esc cancels, type to edit.",
            bindings=(
                InputBinding(device="keyboard", control="K_RETURN", label="Enter"),
            ),
        ),
        ActionBinding(
            action="VCursor Move",
            description="Left stick controls the virtual cursor.",
            bindings=(
                InputBinding(
                    device="joystick_axis", control="left_x", label="Left Stick X"
                ),
                InputBinding(
                    device="joystick_axis", control="left_y", label="Left Stick Y"
                ),
            ),
        ),
        ActionBinding(
            action="VCursor Primary",
            description="Emulates left click with A/B for quick editing.",
            bindings=(
                InputBinding(device="joystick_button", control="a", label="Button A"),
                InputBinding(device="joystick_button", control="b", label="Button B"),
                InputBinding(
                    device="mouse", control="button1", label="Left Click"
                ),
            ),
        ),
        ActionBinding(
            action="VCursor Secondary",
            description="Emulates right click/context menu with Y/X buttons.",
            bindings=(
                InputBinding(device="joystick_button", control="y", label="Button Y"),
                InputBinding(device="joystick_button", control="x", label="Button X"),
                InputBinding(device="mouse", control="button3", label="Right Click"),
            ),
        ),
    ]

    def __init__(self) -> None:
        self.registry = PaletteRegistry.from_modules(entities, environments)
        self.model = EditorModel(self.registry)

        self.dragging = False
        self.drag_mode: str | None = None
        self.drag_offset = pygame.Vector2(0, 0)

        self.font = pygame.font.Font(None, 20)
        self.font_mono = pygame.font.Font(None, 18)

        self.margin = 20
        self.gap = 12
        self.preview_scale = 0.6  # 60% of target resolution
        self.canvas_scale = 1.0
        self.scroll_step = 28
        self.section_header_h = 36
        self.section_body_pad = 8

        self.toolbar_panel = ToolbarPanel(
            self.font,
            self.font_mono,
            title="Scene",
            buttons=[("save", "Save"), ("play", "Play")],
            label_pad=20,
        )
        self.palette_panel = PalettePanel(
            self.font,
            self.font_mono,
            self.registry,
            palette_item_h=28,
            section_header_h=self.section_header_h,
            section_body_pad=self.section_body_pad,
        )
        self.resolution_panel = ResolutionPanel(
            self.font,
            self.font_mono,
            section_header_h=self.section_header_h,
            section_body_pad=self.section_body_pad,
        )
        self.tree_panel = TreePanel(
            self.font,
            self.font_mono,
            self.model,
            tree_line_h=20,
            section_header_h=self.section_header_h,
            section_body_pad=self.section_body_pad,
        )
        self.attrs_panel = AttrsPanel(
            self.font,
            self.font_mono,
            self.model,
            attr_line_h=20,
            section_header_h=self.section_header_h,
            section_body_pad=self.section_body_pad,
            print_status=self._print_status,
        )

        self._last_size: tuple[int, int] | None = None
        self._last_saved_path: Path | None = None
        self._composition_path: Path | None = None

        self.scene_width = 0
        self.scene_height = 0
        self.canvas_rect = pygame.Rect(0, 0, 0, 0)
        self.scene_canvas_rect = pygame.Rect(0, 0, 0, 0)  # editable virtual space
        self._canvas_surface: pygame.Surface | None = None
        self._canvas_surface_size: tuple[int, int] | None = None
        self.vcursor_enabled = False
        self.vcursor_pos = pygame.Vector2(80, 80)
        self.vcursor_vel = pygame.Vector2(0, 0)
        self.vcursor_speed = 220.0  # px/s
        self.vcursor_deadzone = 0.18
        self.vcursor_buttons: dict[int, bool] = {1: False, 3: False}  # LMB/RMB
        self.context_menu_active = False
        self.context_menu_rect = pygame.Rect(0, 0, 0, 0)
        self.context_menu_item_rects: list[tuple[str, pygame.Rect]] = []
        self.context_menu_items: list[tuple[str, str]] = [("delete", "Delete")]
        self.context_menu_target_id: int | None = None
        self.context_menu_hover: str | None = None
        self.context_menu_stage: str = "root"
        self.context_menu_stage_data: dict[str, Any] = {}
        root = Path(__file__).resolve().parents[2]
        self._controller_cfg_path = (
            root / "game" / "configs" / "controllers" / "generic.toml"
        )
        self.controller_profile = ControllerProfile.default()
        self._vcursor_axes: tuple[int, int] = (0, 1)
        self._vcursor_primary_buttons: tuple[int, ...] = (0,)
        self._vcursor_secondary_buttons: tuple[int, ...] = (1,)
        self._vscroll_axis: int = self._controller_axis_index(
            "right_y", 3
        )  # typical fallback
        self._vscroll_value: float = 0.0

        self._vscroll_deadzone: float = 0.18
        self._vscroll_speed_steps: float = 14.0  # steps/sec at full stick
        self._vscroll_accum: float = 0.0

        self._load_controller_profile()

    def on_enter(self, app: AppLike) -> None:
        self._init_scene_canvas(app)
        self._update_resolution_options()
        self._sync_resolution_selection()
        self._sync_vcursor_enabled()
        self._load_initial_composition()

    # ---------------- Layout ----------------

    def _init_scene_canvas(self, app: AppLike) -> None:
        cfg = getattr(app, "cfg", None)
        width = getattr(cfg, "width", None)
        height = getattr(cfg, "height", None)
        if not width or not height:
            width, height = 1028, 720  # fallback
        self.scene_canvas_rect = pygame.Rect(0, 0, int(width), int(height))
        self._canvas_surface = None
        self._canvas_surface_size = None

    def _desktop_size(self) -> tuple[int, int]:
        sizes = getattr(pygame.display, "get_desktop_sizes", None)
        if callable(sizes):
            available = pygame.display.get_desktop_sizes()
            if available:
                return available[0]
        info = pygame.display.Info()
        if info.current_w and info.current_h:
            return (int(info.current_w), int(info.current_h))
        return (self.scene_canvas_rect.width or 1024, self.scene_canvas_rect.height or 768)

    def _update_resolution_options(self) -> None:
        desktop_w, desktop_h = self._desktop_size()
        options = [
            ("720x480", "720x480"),
            ("1024x768", "1024x768"),
            ("desktop", f"Desktop ({desktop_w}x{desktop_h})"),
            ("custom", "Custom"),
        ]
        self.resolution_panel.set_options(options)

    def _sync_resolution_selection(self) -> None:
        width = self.scene_canvas_rect.width
        height = self.scene_canvas_rect.height
        desktop_w, desktop_h = self._desktop_size()
        if (width, height) == (720, 480):
            self.resolution_panel.selected_key = "720x480"
        elif (width, height) == (1024, 768):
            self.resolution_panel.selected_key = "1024x768"
        elif (width, height) == (desktop_w, desktop_h):
            self.resolution_panel.selected_key = "desktop"
        else:
            self.resolution_panel.custom_size = (width, height)
            self.resolution_panel.selected_key = "custom"

    def _apply_resolution(self, key: str) -> None:
        if key == "720x480":
            width, height = 720, 480
        elif key == "1024x768":
            width, height = 1024, 768
        elif key == "desktop":
            width, height = self._desktop_size()
        else:
            return

        if (width, height) == (
            self.scene_canvas_rect.width,
            self.scene_canvas_rect.height,
        ):
            self.resolution_panel.selected_key = key
            return

        self.scene_canvas_rect.size = (int(width), int(height))
        self._canvas_surface = None
        self._canvas_surface_size = None
        self.resolution_panel.selected_key = key
        self._last_size = None

    def _apply_custom_resolution(self, size: tuple[int, int]) -> None:
        width, height = size
        if (width, height) == (
            self.scene_canvas_rect.width,
            self.scene_canvas_rect.height,
        ):
            self.resolution_panel.custom_size = size
            self.resolution_panel.selected_key = "custom"
            return
        self.scene_canvas_rect.size = (int(width), int(height))
        self._canvas_surface = None
        self._canvas_surface_size = None
        self.resolution_panel.custom_size = size
        self.resolution_panel.selected_key = "custom"
        self._last_size = None

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
        canvas_area = pygame.Rect(m, m, max(0, left_w - m), max(0, h - 2 * m))
        self.canvas_scale = self._compute_canvas_scale(
            canvas_area.width, canvas_area.height
        )
        target_w = self.scene_canvas_rect.width or 1
        target_h = self.scene_canvas_rect.height or 1
        scaled_w = int(target_w * self.canvas_scale)
        scaled_h = int(target_h * self.canvas_scale)
        scaled_w = max(0, min(canvas_area.width, scaled_w))
        scaled_h = max(0, min(canvas_area.height, scaled_h))
        cx = canvas_area.x + max(0, (canvas_area.width - scaled_w) // 2)
        cy = canvas_area.y + max(0, (canvas_area.height - scaled_h) // 2)
        self.canvas_rect = pygame.Rect(cx, cy, scaled_w, scaled_h)

        right_x = canvas_area.right + gap
        right_w = max(0, w - right_x - m)
        right_panel_rect = pygame.Rect(right_x, m, right_w, h - 2 * m)

        toolbar_h = min(44, right_panel_rect.height)
        toolbar_rect = pygame.Rect(
            right_panel_rect.x, right_panel_rect.y, right_panel_rect.width, toolbar_h
        )
        self.toolbar_panel.set_rect(toolbar_rect)

        resolution_h = min(120, max(0, right_panel_rect.height // 6))
        resolution_y = toolbar_rect.bottom + gap
        resolution_rect = pygame.Rect(
            right_panel_rect.x,
            resolution_y,
            right_panel_rect.width,
            resolution_h,
        )
        self.resolution_panel.set_rect(resolution_rect)

        palette_y = resolution_rect.bottom + gap
        palette_bottom_limit = right_panel_rect.bottom
        available_palettes_h = max(0, palette_bottom_limit - palette_y)
        palette_h = (
            min(180, available_palettes_h // 3) if available_palettes_h > 0 else 0
        )
        palette_width = right_panel_rect.width
        column_gap = min(gap, palette_width)
        entity_w = max(0, (palette_width - column_gap) // 2)
        env_w = max(0, palette_width - entity_w - column_gap)

        palette_x = right_panel_rect.x
        entities_rect = pygame.Rect(palette_x, palette_y, entity_w, palette_h)
        env_x = entities_rect.right + column_gap
        environments_rect = pygame.Rect(env_x, palette_y, env_w, palette_h)
        self.palette_panel.set_rects(entities_rect, environments_rect)

        palettes_bottom = max(
            entities_rect.bottom, environments_rect.bottom
        )
        insp_y = palettes_bottom + gap
        insp_h = right_panel_rect.bottom - insp_y
        inspector_rect = pygame.Rect(
            right_panel_rect.x, insp_y, right_panel_rect.width, max(0, insp_h)
        )

        tree_h = min(
            max(120, int(inspector_rect.height * 0.45)), inspector_rect.height
        )
        attr_y = inspector_rect.y + tree_h + gap
        attr_y = min(attr_y, inspector_rect.bottom)
        attr_h = max(0, inspector_rect.bottom - attr_y)

        tree_rect = pygame.Rect(
            inspector_rect.x,
            inspector_rect.y,
            inspector_rect.width,
            tree_h,
        )
        attrs_rect = pygame.Rect(
            inspector_rect.x, attr_y, inspector_rect.width, attr_h
        )
        self.tree_panel.set_rect(tree_rect)
        self.attrs_panel.set_rect(attrs_rect)

        self.palette_panel.rebuild_item_rects()
        self.toolbar_panel.rebuild_buttons()
        self.palette_panel.clamp_scroll_states()
        self.tree_panel.clamp_scroll_state()
        self.attrs_panel.clamp_scroll_state()

    def _compute_canvas_scale(self, available_w: int, available_h: int) -> float:
        if available_w <= 0 or available_h <= 0:
            return 0.0
        target_w = max(1, self.scene_canvas_rect.width)
        target_h = max(1, self.scene_canvas_rect.height)
        max_scale_w = available_w / target_w
        max_scale_h = available_h / target_h
        scale = min(self.preview_scale, max_scale_w, max_scale_h)
        return max(0.0, scale)

    def _ensure_canvas_surface(self) -> pygame.Surface:
        size = (
            max(1, self.scene_canvas_rect.width),
            max(1, self.scene_canvas_rect.height),
        )
        if self._canvas_surface is None or self._canvas_surface_size != size:
            self._canvas_surface = pygame.Surface(size).convert()
            self._canvas_surface_size = size
        return self._canvas_surface

    # ---------------- Update / Events ----------------

    def update(self, app: AppLike, dt: float) -> None:
        self._sync_vcursor_enabled()

        if self.vcursor_enabled:
            self.vcursor_pos += self.vcursor_vel * dt
            self.vcursor_pos.x = max(0, min(self.scene_width - 1, self.vcursor_pos.x))
            self.vcursor_pos.y = max(0, min(self.scene_height - 1, self.vcursor_pos.y))

            # 🎮 right stick scroll -> "wheel steps"
            if self._vscroll_value != 0.0:
                # Invert: stick up is usually negative; we want "scroll up"
                steps_per_sec = self._vscroll_speed_steps * (-self._vscroll_value)
                self._vscroll_accum += steps_per_sec * dt

                steps = int(self._vscroll_accum)
                if steps != 0:
                    self._vscroll_accum -= steps
                    self._handle_scroll_input(
                        (int(self.vcursor_pos.x), int(self.vcursor_pos.y)),
                        steps,
                    )

    # ---------------- Render (orquestador) ----------------

    def render(self, app, screen: pygame.Surface) -> None:
        self._ensure_layout(screen)

        screen.fill("black")

        self._render_canvas(app, screen)
        mouse = self._mouse_local(app)
        self.toolbar_panel.render(screen, mouse)
        self.resolution_panel.render(screen, mouse)
        self.palette_panel.render(screen, mouse)
        self.tree_panel.render(screen)
        self.attrs_panel.render(screen)
        self._render_context_menu(screen)
        if self.vcursor_enabled:
            x, y = int(self.vcursor_pos.x), int(self.vcursor_pos.y)

            BLACK = (15, 15, 15)
            WHITE = (245, 245, 245)
            ACCENT = (40, 120, 255)  # cool blue, optional

            # --- outer halo (white, visible on dark backgrounds) ---
            pygame.draw.circle(screen, WHITE, (x, y), 9, 2)

            # --- main outline (black, visible on white) ---
            pygame.draw.circle(screen, BLACK, (x, y), 7, 2)

            # --- solid core (black) ---
            pygame.draw.circle(screen, BLACK, (x, y), 2)

            # --- crosshair with two layers ---
            arm = 6

            # shadow / outline
            pygame.draw.line(screen, BLACK, (x - arm, y), (x + arm, y), 3)
            pygame.draw.line(screen, BLACK, (x, y - arm), (x, y + arm), 3)

            # light layer on top
            pygame.draw.line(screen, WHITE, (x - arm, y), (x + arm, y), 1)
            pygame.draw.line(screen, WHITE, (x, y - arm), (x, y + arm), 1)

            # --- direction dot ---
            pygame.draw.circle(screen, ACCENT, (x + 4, y - 4), 1)

    # ---------------- Render helpers ----------------

    def _render_canvas(self, app: AppLike, screen: pygame.Surface) -> None:
        rect = self.canvas_rect
        if rect.width <= 0 or rect.height <= 0 or self.canvas_scale <= 0:
            return

        target = self._ensure_canvas_surface()
        target.fill("white")

        for node in self.model.iter_drawable_nodes():
            renderer = getattr(node.payload, "render", None)
            if callable(renderer):
                renderer(app, target)
            if node.id == self.model.selected_id:
                self._render_selection_ring(target, node)

        if (target.get_width(), target.get_height()) == (rect.width, rect.height):
            screen.blit(target, rect.topleft)
        else:
            scaled = pygame.transform.smoothscale(target, (rect.width, rect.height))
            screen.blit(scaled, rect.topleft)

        pygame.draw.rect(screen, (200, 200, 200), rect, width=1, border_radius=6)

    def _render_selection_ring(self, surface: pygame.Surface, node) -> None:
        p = getattr(node.payload, "pos", None)
        if p is None:
            return
        r = int(getattr(node.payload, "radius", 26)) + 6
        pygame.draw.circle(surface, (255, 200, 0), (int(p.x), int(p.y)), r, 2)

    def _render_context_menu(self, screen: pygame.Surface) -> None:
        if not self.context_menu_active:
            return
        rect = self.context_menu_rect
        if rect.width <= 0 or rect.height <= 0:
            return

        pygame.draw.rect(screen, (20, 20, 20), rect, border_radius=6)
        pygame.draw.rect(screen, (120, 120, 120), rect, width=1, border_radius=6)

        label_map = {key: label for key, label in self.context_menu_items}
        for key, item_rect in self.context_menu_item_rects:
            hovered = key == self.context_menu_hover
            color = (90, 50, 50) if hovered else (45, 45, 45)
            pygame.draw.rect(screen, color, item_rect, border_radius=4)
            text = label_map.get(key, key.title())
            surf = self.font_mono.render(text, True, (235, 235, 235))
            ty = item_rect.y + (item_rect.height - surf.get_height()) // 2
            screen.blit(surf, (item_rect.x + 10, ty))

    def _open_context_menu(self, pos: tuple[int, int], target_id: int) -> None:
        self.context_menu_target_id = target_id
        self._set_context_menu_stage("root")
        self._layout_context_menu(pos)
        self.context_menu_active = True
        self.context_menu_hover = None
        self.dragging = False
        self.drag_mode = None

    def _close_context_menu(self) -> None:
        self.context_menu_active = False
        self.context_menu_target_id = None
        self.context_menu_hover = None
        self.context_menu_item_rects = []
        self.context_menu_stage = "root"
        self.context_menu_stage_data = {}

    def _context_menu_hit(self, pos: tuple[int, int]) -> str | None:
        if not self.context_menu_active or not self.context_menu_rect.collidepoint(pos):
            return None
        for key, item_rect in self.context_menu_item_rects:
            if item_rect.collidepoint(pos):
                return key
        return None

    def _context_menu_click(self, app: AppLike, pos: tuple[int, int]) -> bool:
        key = self._context_menu_hit(pos)
        if key is None:
            return False
        should_close = self._perform_context_menu_action(app, key)
        if should_close:
            self._close_context_menu()
        return True

    def _update_context_menu_hover(self, pos: tuple[int, int]) -> None:
        if not self.context_menu_active:
            return
        self.context_menu_hover = self._context_menu_hit(pos)

    def _perform_context_menu_action(self, app: AppLike, key: str) -> bool:
        target_id = self.context_menu_target_id
        if target_id is None:
            return True

        if key == "noop":
            return False

        if key == "back":
            if self.context_menu_stage == "choose-kind":
                self._set_context_menu_stage("root")
            elif self.context_menu_stage == "choose-item":
                before = self.context_menu_stage_data.get("before")
                self._set_context_menu_stage("choose-kind", before=before)
            self._layout_context_menu()
            return False

        if self.context_menu_stage == "root":
            if key == "delete":
                if self.model.selected_id != target_id:
                    self.model.select_node(target_id)
                self._delete_selected()
                return True
            if key == "move-up":
                self.model.move_up(target_id)
                return True
            if key == "move-down":
                self.model.move_down(target_id)
                return True
            if key in {"add-before", "add-after"}:
                before = key == "add-before"
                if not self._context_menu_allowed_kinds(target_id):
                    return False
                self._set_context_menu_stage("choose-kind", before=before)
                self._layout_context_menu()
            return False

        if self.context_menu_stage == "choose-kind":
            if not key.startswith("kind-"):
                return False
            kind = key.split("-", 1)[1]
            if kind not in self._context_menu_allowed_kinds(target_id):
                return False
            before = bool(self.context_menu_stage_data.get("before"))
            self._set_context_menu_stage("choose-item", before=before, kind=kind)
            self._layout_context_menu()
            return False

        if self.context_menu_stage == "choose-item":
            if not key.startswith("item-"):
                return False
            try:
                idx = int(key.split("-", 1)[1])
            except ValueError:
                return False
            kind = self.context_menu_stage_data.get("kind")
            if kind not in {"entity", "environment"}:
                return False
            before = bool(self.context_menu_stage_data.get("before"))
            if self._context_menu_spawn_relative(kind, idx, before=before):
                return True
            return False

        return False

    def _set_context_menu_stage(
        self,
        stage: str,
        *,
        before: bool | None = None,
        kind: str | None = None,
    ) -> None:
        data: dict[str, Any] = {}
        if before is not None:
            data["before"] = before
        if kind is not None:
            data["kind"] = kind
        self.context_menu_stage = stage
        self.context_menu_stage_data = data
        if stage == "root":
            items = self._context_menu_root_items()
        elif stage == "choose-kind":
            items = self._context_menu_kind_items()
        elif stage == "choose-item":
            items = self._context_menu_palette_items(kind)
        else:
            items = []
        if not items:
            items = [("noop", "No actions")]
        self.context_menu_items = items

    def _layout_context_menu(self, pos: tuple[int, int] | None = None) -> None:
        width = 200
        item_h = 26
        pad = 8
        count = max(1, len(self.context_menu_items))
        height = pad * 2 + item_h * count

        if pos is None:
            x, y = self.context_menu_rect.x, self.context_menu_rect.y
        else:
            x, y = pos

        max_x = max(0, self.scene_width - width)
        max_y = max(0, self.scene_height - height)
        x = min(max(0, x), max_x)
        y = min(max(0, y), max_y)
        rect = pygame.Rect(x, y, width, height)

        item_rects: list[tuple[str, pygame.Rect]] = []
        item_y = rect.y + pad
        for key, _ in self.context_menu_items:
            item_rects.append(
                (key, pygame.Rect(rect.x + 4, item_y, rect.width - 8, item_h))
            )
            item_y += item_h

        self.context_menu_rect = rect
        self.context_menu_item_rects = item_rects
        self.context_menu_hover = None

    def _context_menu_root_items(self) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        allowed = self._context_menu_allowed_kinds(self.context_menu_target_id)
        if allowed:
            items.append(("add-before", "Add Before..."))
            items.append(("add-after", "Add After..."))
        items.append(("move-up", "Move Forward"))
        items.append(("move-down", "Move Back"))
        items.append(("delete", "Delete"))
        return items

    def _context_menu_kind_items(self) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = [("back", "← Back")]
        allowed = self._context_menu_allowed_kinds(self.context_menu_target_id)
        labels = {"entity": "Entities", "environment": "Environments"}
        for kind in allowed:
            items.append((f"kind-{kind}", labels.get(kind, kind.title())))
        return items

    def _context_menu_palette_items(self, kind: str | None) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = [("back", "← Back")]
        if kind == "entity":
            collection = self.registry.entities
        elif kind == "environment":
            collection = self.registry.environments
        else:
            collection = []
        for idx, entry in enumerate(collection):
            items.append((f"item-{idx}", entry.name))
        return items

    def _context_menu_allowed_kinds(self, target_id: int | None) -> list[str]:
        allowed: list[str] = []
        if target_id is None:
            return allowed
        for kind in ("entity", "environment"):
            if self.model.can_add_sibling(target_id, kind):
                allowed.append(kind)
        return allowed

    def _context_menu_spawn_relative(
        self,
        kind: str,
        idx: int,
        *,
        before: bool,
    ) -> bool:
        target_id = self.context_menu_target_id
        if target_id is None:
            return False
        if kind not in self._context_menu_allowed_kinds(target_id):
            return False
        reference = self.model.node_by_id(target_id)
        if reference is None:
            return False
        pos = reference.position()
        if pos is None:
            pos = pygame.Vector2(self.scene_canvas_rect.center)
        new_node = self.model.spawn_from_palette_relative(
            kind,
            idx,
            (int(pos.x), int(pos.y)),
            target_id,
            before=before,
        )
        if new_node is None:
            self._print_status("[Editor] Could not insert the item.")
            return False
        self._save_composition()
        return True

    def _handle_context_menu_request(self, pos: tuple[int, int]) -> None:
        target_id: int | None = None

        tree_rect = self.tree_panel.rect
        if (
            tree_rect.width > 0
            and tree_rect.height > 0
            and tree_rect.collidepoint(pos)
        ):
            target_id = self.tree_panel.node_at(pos)
            if target_id == self.model.root_id:
                target_id = None
            elif target_id is not None:
                self.model.select_node(target_id)
        elif self.canvas_rect.collidepoint(pos):
            scene_pos = self._canvas_point_to_scene(pos, clamp=False)
            if scene_pos is not None:
                target_id = self._select_node_at_scene(scene_pos)

        if target_id is None:
            self._close_context_menu()
            return

        self._open_context_menu(pos, target_id)

    # ---------------- Utilities ----------------

    def _mouse_local(self, app: AppLike) -> tuple[int, int]:
        """Mouse in this scene's coordinates (useful with viewport/HUD)."""
        mx, my = pygame.mouse.get_pos()
        if hasattr(app, "scene_viewport"):
            vp = app.scene_viewport()
            return (mx - vp.x, my - vp.y)
        return (mx, my)

    def _canvas_point_to_scene(
        self,
        pos: tuple[int, int],
        *,
        clamp: bool = True,
    ) -> pygame.Vector2 | None:
        rect = self.canvas_rect
        if rect.width <= 0 or rect.height <= 0 or self.canvas_scale <= 0:
            return None
        local_x = pos[0] - rect.x
        local_y = pos[1] - rect.y
        if not clamp and not rect.collidepoint(pos):
            return None
        if clamp:
            local_x = max(0, min(rect.width, local_x))
            local_y = max(0, min(rect.height, local_y))
        # evita divisiones extra si la escala es cero
        if self.canvas_scale <= 0:
            return None
        scene_x = local_x / self.canvas_scale
        scene_y = local_y / self.canvas_scale
        return pygame.Vector2(scene_x, scene_y)

    def _draw_section_header(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        title: str,
    ) -> None:
        t = self.font.render(title, True, (220, 220, 220))
        screen.blit(t, (rect.x + 10, rect.y + 8))
        pygame.draw.line(
            screen,
            (70, 70, 70),
            (rect.x + 8, rect.y + 28),
            (rect.right - 8, rect.y + 28),
            1,
        )

    # ---------------- VCursor helpers ----------------

    def _load_controller_profile(self) -> None:
        try:
            self.controller_profile = ControllerProfile.from_toml(
                self._controller_cfg_path
            )
        except (OSError, ValueError):
            self.controller_profile = ControllerProfile.default()
        self._vscroll_axis = self._controller_axis_index("right_y", 3)
        self._vscroll_deadzone = getattr(
            self.controller_profile, "deadzone", self._vscroll_deadzone
        )

        self._vcursor_axes = (
            self._controller_axis_index("left_x", 0),
            self._controller_axis_index("left_y", 1),
        )
        self._vcursor_primary_buttons = self._controller_button_indices(
            ("a", "b"), (0, 1, 5, 4)
        )
        self._vcursor_secondary_buttons = self._controller_button_indices(
            ("y", "x"), (3, 2, 6, 7)
        )
        self.vcursor_deadzone = getattr(
            self.controller_profile, "deadzone", self.vcursor_deadzone
        )

    def _controller_button_indices(
        self,
        names: tuple[str, ...],
        fallback: tuple[int, ...],
    ) -> tuple[int, ...]:
        seen: set[int] = set()
        result: list[int] = []
        for name in names:
            idx = self.controller_profile.button_index(name)
            if idx is None or idx in seen:
                continue
            result.append(idx)
            seen.add(idx)

        for idx in fallback:
            if idx in seen:
                continue
            result.append(idx)
            seen.add(idx)

        return tuple(result) if result else (0,)

    def _controller_axis_index(self, name: str, fallback: int) -> int:
        idx = self.controller_profile.axis_index(name)
        return idx if idx is not None else fallback

    def _sync_vcursor_enabled(self) -> None:
        self._set_vcursor_enabled(self._has_any_joystick())

    def _has_any_joystick(self) -> bool:
        if not pygame.joystick.get_init():
            return False
        try:
            return pygame.joystick.get_count() > 0
        except pygame.error:
            return False

    def _set_vcursor_enabled(self, enabled: bool) -> None:
        if self.vcursor_enabled == enabled:
            return
        self.vcursor_enabled = enabled
        if not enabled:
            self.vcursor_vel.xy = (0.0, 0.0)
            pos = (int(self.vcursor_pos.x), int(self.vcursor_pos.y))
            for button, was_down in list(self.vcursor_buttons.items()):
                if was_down:
                    self._pointer_up(button, pos)
                self.vcursor_buttons[button] = False

    # ---------------- Scroll helpers ----------------

    def _handle_scroll_input(self, pos: tuple[int, int] | None, steps: int) -> None:
        if pos is None or steps == 0:
            return
        if self.resolution_panel.rect.collidepoint(pos):
            if self.resolution_panel.handle_scroll(-steps * self.scroll_step):
                return
            return
        delta = -steps * self.scroll_step
        if self.palette_panel.handle_scroll(pos, delta):
            return
        if self.tree_panel.handle_scroll(pos, delta):
            return
        self.attrs_panel.handle_scroll(pos, delta)

    # ---------------- Interaction ----------------

    def handle_event(self, app: AppLike, ev: pygame.event.Event) -> None:
        # Layout may not exist yet if an event arrives too early.
        if self._last_size is None:
            return

        pos = self._event_pos_local(app, ev)
        if ev.type == pygame.TEXTINPUT:
            if self.resolution_panel.editing:
                self.resolution_panel.handle_text_input(ev.text)
                return
            if self.attrs_panel.editing:
                self.attrs_panel.handle_text_input(ev.text)
                return

        if ev.type == pygame.MOUSEWHEEL:
            self._handle_scroll_input(self._mouse_local(app), ev.y)
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and pos is not None:
            self._pointer_down(app, ev.button, pos)
            return
        if ev.type == pygame.MOUSEBUTTONUP and pos is not None:
            self._pointer_up(ev.button, pos)
            return
        if ev.type == pygame.MOUSEMOTION and pos is not None:
            self._pointer_move(pos)
            return

        if ev.type == pygame.KEYDOWN:
            if self.resolution_panel.editing:
                size = self.resolution_panel.handle_keydown(ev)
                if size is not None:
                    self._apply_custom_resolution(size)
                return
            if self.attrs_panel.editing and self.attrs_panel.handle_keydown(ev):
                return
            if ev.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self._delete_selected()
                return
            if ev.key == pygame.K_s and (ev.mod & pygame.KMOD_CTRL):
                self._save_composition(app)
                return

        if ev.type == pygame.JOYAXISMOTION and self.vcursor_enabled:
            joy = pygame.joystick.Joystick(ev.joy)

            # --- vcursor move (left stick) ---
            if ev.axis in self._vcursor_axes:
                ax_idx, ay_idx = self._vcursor_axes
                ax = joy.get_axis(ax_idx)
                ay = joy.get_axis(ay_idx)

                def dz(v: float, dead: float) -> float:
                    return 0.0 if abs(v) < dead else v

                ax = dz(ax, self.vcursor_deadzone)
                ay = dz(ay, self.vcursor_deadzone)

                self.vcursor_vel.x = ax * self.vcursor_speed
                self.vcursor_vel.y = ay * self.vcursor_speed

                self._pointer_move((int(self.vcursor_pos.x), int(self.vcursor_pos.y)))

            # --- scroll (right stick Y) ---
            if ev.axis == self._vscroll_axis:
                v = joy.get_axis(self._vscroll_axis)
                self._vscroll_value = 0.0 if abs(v) < self._vscroll_deadzone else v

            return

        if ev.type == pygame.JOYHATMOTION and self.vcursor_enabled:
            hx, hy = ev.value  # -1/0/1
            self.vcursor_vel.x = hx * self.vcursor_speed
            self.vcursor_vel.y = (
                -hy * self.vcursor_speed
            )  # Note: up is usually +1, invert Y
            self._pointer_move((int(self.vcursor_pos.x), int(self.vcursor_pos.y)))
            return

        if (
            ev.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP)
            and self.vcursor_enabled
        ):
            is_down = ev.type == pygame.JOYBUTTONDOWN

            if ev.button in self._vcursor_primary_buttons:
                self.vcursor_buttons[1] = is_down
                if is_down:
                    self._pointer_down(
                        app, 1, (int(self.vcursor_pos.x), int(self.vcursor_pos.y))
                    )
                else:
                    self._pointer_up(
                        1, (int(self.vcursor_pos.x), int(self.vcursor_pos.y))
                    )
                return

            if ev.button in self._vcursor_secondary_buttons:
                self.vcursor_buttons[3] = is_down
                if is_down:
                    self._pointer_down(
                        app, 3, (int(self.vcursor_pos.x), int(self.vcursor_pos.y))
                    )
                else:
                    self._pointer_up(
                        3, (int(self.vcursor_pos.x), int(self.vcursor_pos.y))
                    )
                return

    def _event_pos_local(
        self,
        app: AppLike,
        ev: pygame.event.Event,
    ) -> tuple[int, int] | None:
        """Convierte ev.pos (coords ventana) a coords del viewport."""
        if not hasattr(ev, "pos"):
            return None
        mx, my = ev.pos
        if hasattr(app, "scene_viewport"):
            vp = app.scene_viewport()
            return (mx - vp.x, my - vp.y)
        return (mx, my)

    def _spawn_from_palette(
        self,
        target: str,
        idx: int,
        mouse_pos: tuple[int, int],
    ) -> None:
        spawn_pos_vec = self._canvas_point_to_scene(mouse_pos, clamp=False)
        if spawn_pos_vec is None:
            spawn_pos_vec = pygame.Vector2(self.scene_canvas_rect.center)

        node = self.model.spawn_from_palette(
            target, idx, (int(spawn_pos_vec.x), int(spawn_pos_vec.y))
        )
        if node is None:
            return

        self.drag_mode = "spawn-new"
        self._start_drag_existing(spawn_pos_vec)

    # ---------- Select / Drag ----------

    def _select_node_at_scene(self, scene_pos: pygame.Vector2) -> int | None:
        return self.model.select_at_position((int(scene_pos.x), int(scene_pos.y)))

    def _start_drag_existing(self, scene_pos: pygame.Vector2) -> None:
        node = self.model.selected_node()
        if node is None or node.payload is None:
            return
        p = getattr(node.payload, "pos", None)
        if p is None:
            return

        self.dragging = True
        self.drag_mode = self.drag_mode or "move-existing"
        self.drag_offset = pygame.Vector2(p) - pygame.Vector2(scene_pos)

        self._drag_to_scene(scene_pos)

    def _drag_to_scene(self, scene_pos: pygame.Vector2 | None) -> None:
        if scene_pos is None:
            return
        if self.model.selected_node() is None:
            return

        desired = pygame.Vector2(scene_pos) + self.drag_offset
        self.model.move_selected_within(self.scene_canvas_rect, desired)

    def _delete_selected(self) -> None:
        node = self.model.selected_node()
        if node is None:
            return

        self.attrs_panel.cancel_edit()
        self.model.delete_selected()
        self.dragging = False
        self.drag_mode = None
        self._save_composition()
        self._close_context_menu()

    # ---------- Saving ----------

    def _composition_output_path(self) -> Path:
        if self._composition_path is not None:
            return self._composition_path
        root = Path(__file__).resolve().parents[2]
        return root / "game" / "configs" / "compositions" / "editor_export.eei.json"

    def _composition_candidates(self) -> list[Path]:
        root = Path(__file__).resolve().parents[2] / "game" / "configs" / "compositions"
        return [
            root / "editor_export.eei.json",
        ]

    def _initial_composition_path(self) -> Path | None:
        for candidate in self._composition_candidates():
            if candidate.exists():
                return candidate
        return None

    def _load_initial_composition(self) -> None:
        path = self._initial_composition_path()
        if path is None:
            self._print_status(
                "[Editor] No initial composition found. Start a new scene."
            )
            return
        try:
            runtime = load_composition(path)
        except FileNotFoundError:
            self._print_status(f"[Editor] Initial file not found: {path}")
            return
        except Exception as exc:  # pragma: no cover - feedback
            self._print_status(f"[Editor] Failed to load composition: {exc}")
            return

        self.model.load_from_runtime(runtime)
        if runtime.canvas_size:
            self.scene_canvas_rect.size = (
                int(runtime.canvas_size[0]),
                int(runtime.canvas_size[1]),
            )
            self._canvas_surface = None
            self._canvas_surface_size = None
            self._last_size = None
            self._sync_resolution_selection()
        self._composition_path = path
        self._last_saved_path = path
        self._print_status(f"[Editor] Composition loaded from {path.name}")

    def _save_composition(self, app: AppLike | None = None) -> bool:
        target = self._composition_output_path()
        canvas = [
            self.scene_canvas_rect.width or 640,
            self.scene_canvas_rect.height or 360,
        ]
        try:
            path = self.model.save_composition(
                target,
                metadata={"name": target.stem},
                scene={"canvas": canvas, "origin": [0, 0]},
            )
        except Exception as exc:  # pragma: no cover - feedback
            self._print_status(f"[Editor] Failed to save composition: {exc}")
            return False

        self._last_saved_path = path
        self._composition_path = path
        self._print_status(f"[Editor] Composition saved to {path}")
        return True

    def _handle_toolbar_click(self, app: AppLike, key: str) -> None:
        if key == "save":
            self._save_composition(app)
        elif key == "play":
            self._play_from_editor(app)

    def _play_from_editor(self, app: AppLike) -> None:
        if self._save_composition(app):
            self._goto_main_scene(app)

    def _goto_main_scene(self, app: AppLike) -> None:
        set_scene = getattr(app, "set_scene", None)
        scene_list = getattr(app, "scenes", None)
        if not callable(set_scene) or not scene_list:
            self._print_status("[Editor] Cannot jump to MainScene from here.")
            return

        for idx, value in enumerate(scene_list.values()):
            print(f"Scene {idx}: {value.__name__}")
            if value.__name__ == "MainScene":
                self._print_status("[Editor] Running composition in MainScene...")
                composition_path = self._composition_output_path()
                set_scene(idx, composition_path=composition_path)
                return

        self._print_status("[Editor] MainScene is not registered in this app.")

    def _print_status(self, msg: str) -> None:
        print(msg)

    def _pointer_down(self, app: AppLike, button: int, pos: tuple[int, int]) -> None:
        if self.attrs_panel.editing:
            self.attrs_panel.cancel_edit()
        if self.resolution_panel.editing:
            self.resolution_panel.cancel_edit()

        if button == 3:
            self.dragging = False
            self.drag_mode = None
            self._handle_context_menu_request(pos)
            return

        if button != 1:
            return

        if self.context_menu_active:
            if self._context_menu_click(app, pos):
                return
            self._close_context_menu()

        toolbar_hit = self.toolbar_panel.hit(pos)
        if toolbar_hit is not None:
            self._handle_toolbar_click(app, toolbar_hit)
            return

        resolution_hit = self.resolution_panel.hit(pos)
        if resolution_hit is not None:
            if resolution_hit == "custom":
                if self.attrs_panel.editing:
                    self.attrs_panel.cancel_edit()
                self.resolution_panel.begin_edit()
            else:
                if self.resolution_panel.editing:
                    self.resolution_panel.cancel_edit()
                self._apply_resolution(resolution_hit)
            return

        hit = self.palette_panel.hit(pos)
        if hit is not None:
            target, idx = hit
            self._spawn_from_palette(target, idx, pos)
            return

        if self.tree_panel.handle_click(pos):
            return

        if self.attrs_panel.handle_click(pos):
            return

        if self.canvas_rect.collidepoint(pos):
            scene_pos = self._canvas_point_to_scene(pos, clamp=False)
            if scene_pos is None:
                return
            hit2 = self._select_node_at_scene(scene_pos)
            if hit2 is not None:
                self._start_drag_existing(scene_pos)
            return

    def _pointer_move(self, pos: tuple[int, int]) -> None:
        if self.context_menu_active:
            self._update_context_menu_hover(pos)
            if not self.dragging:
                return
        if self.dragging:
            scene_pos = self._canvas_point_to_scene(pos, clamp=True)
            self._drag_to_scene(scene_pos)

    def _pointer_up(self, button: int, pos: tuple[int, int]) -> None:
        if button == 1:
            was_spawn_new = self.drag_mode == "spawn-new"
            self.dragging = False
            self.drag_mode = None
            if was_spawn_new:
                self._save_composition()
