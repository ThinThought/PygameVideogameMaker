from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pygame
from game.editor import PaletteItem, PaletteRegistry


@dataclass
class AttrEntry:
    label: str
    display: str
    editable: bool = False
    attr_name: str | None = None
    raw_value: Any = None
    component: str | None = None


class SectionPanel:
    def __init__(
        self,
        font: pygame.font.Font,
        font_mono: pygame.font.Font,
        *,
        section_header_h: int = 36,
        section_body_pad: int = 8,
    ) -> None:
        self.font = font
        self.font_mono = font_mono
        self.section_header_h = section_header_h
        self.section_body_pad = section_body_pad

    @staticmethod
    def clamp_scroll(value: int, max_scroll: int) -> int:
        if max_scroll <= 0:
            return 0
        return max(0, min(value, max_scroll))

    @staticmethod
    def apply_scroll_delta(value: int, delta: float, max_scroll: int) -> int:
        if max_scroll <= 0:
            return 0
        new_value = value + int(delta)
        return SectionPanel.clamp_scroll(new_value, max_scroll)

    def section_body_bounds(self, rect: pygame.Rect) -> tuple[int, int]:
        top = rect.y + self.section_header_h
        bottom = rect.bottom - self.section_body_pad
        if bottom < top:
            bottom = top
        return top, bottom

    def visible_body_height(self, rect: pygame.Rect) -> int:
        top, bottom = self.section_body_bounds(rect)
        return max(0, bottom - top)

    def draw_section_header(
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


class ToolbarPanel:
    def __init__(
        self,
        font: pygame.font.Font,
        font_mono: pygame.font.Font,
        *,
        title: str,
        buttons: list[tuple[str, str]],
        label_pad: int = 20,
    ) -> None:
        self.font = font
        self.font_mono = font_mono
        self.title = title
        self.buttons = buttons
        self._label_pad = label_pad
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.button_rects: dict[str, pygame.Rect] = {}

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def rebuild_buttons(self) -> None:
        self.button_rects = {}
        rect = self.rect
        if rect.width <= 0 or rect.height <= 0 or not self.buttons:
            return

        pad_x = 12
        btn_gap = 10
        btn_count = len(self.buttons)
        label_w = self.font.size(self.title)[0] + self._label_pad
        pad_left = pad_x + label_w
        pad_right = pad_x
        available_w = rect.width - pad_left - pad_right - (btn_gap * (btn_count - 1))
        available_w = max(0, available_w)
        btn_w = available_w // btn_count if btn_count else 0
        if btn_count and btn_w <= 0:
            btn_w = max(0, rect.width // btn_count)

        btn_h = max(0, rect.height - 16)
        y = rect.y + (rect.height - btn_h) // 2
        x = rect.x + pad_left

        for key, _ in self.buttons:
            self.button_rects[key] = pygame.Rect(x, y, btn_w, btn_h)
            x += btn_w + btn_gap

    def render(self, screen: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        rect = self.rect
        if rect.width <= 0 or rect.height <= 0:
            return

        pygame.draw.rect(screen, (25, 25, 25), rect, border_radius=6)

        for key, label in self.buttons:
            btn_rect = self.button_rects.get(key)
            if btn_rect is None or btn_rect.width <= 0 or btn_rect.height <= 0:
                continue
            hovered = btn_rect.collidepoint(mouse_pos)
            base = (50, 50, 50)
            if key == "play":
                base = (40, 80, 40)
            elif key == "save":
                base = (60, 60, 60)

            if hovered:
                if key == "play":
                    base = (60, 110, 60)
                elif key == "save":
                    base = (85, 75, 35)
                else:
                    base = (70, 70, 70)
            pygame.draw.rect(screen, base, btn_rect, border_radius=6)
            pygame.draw.rect(
                screen, (120, 120, 120), btn_rect, width=1, border_radius=6
            )

            text = self.font_mono.render(label, True, (235, 235, 235))
            tx = btn_rect.x + (btn_rect.width - text.get_width()) // 2
            ty = btn_rect.y + (btn_rect.height - text.get_height()) // 2
            screen.blit(text, (tx, ty))

        header = self.font.render(self.title, True, (220, 220, 220))
        hx = rect.x + 12
        hy = rect.y + (rect.height - header.get_height()) // 2
        screen.blit(header, (hx, hy))

    def hit(self, pos: tuple[int, int]) -> str | None:
        if self.rect.width <= 0 or self.rect.height <= 0:
            return None
        if not self.rect.collidepoint(pos):
            return None
        for key, rect in self.button_rects.items():
            if rect.collidepoint(pos):
                return key
        return None


class PalettePanel(SectionPanel):
    def __init__(
        self,
        font: pygame.font.Font,
        font_mono: pygame.font.Font,
        registry: PaletteRegistry,
        *,
        palette_item_h: int = 28,
        section_header_h: int = 36,
        section_body_pad: int = 8,
    ) -> None:
        super().__init__(
            font,
            font_mono,
            section_header_h=section_header_h,
            section_body_pad=section_body_pad,
        )
        self.registry = registry
        self.palette_item_h = palette_item_h
        self.entities_rect = pygame.Rect(0, 0, 0, 0)
        self.environments_rect = pygame.Rect(0, 0, 0, 0)
        self.entity_item_rects: list[pygame.Rect] = []
        self.environment_item_rects: list[pygame.Rect] = []
        self.scroll: dict[str, int] = {"entity": 0, "environment": 0}

    def set_rects(
        self,
        entities_rect: pygame.Rect,
        environments_rect: pygame.Rect,
    ) -> None:
        self.entities_rect = entities_rect
        self.environments_rect = environments_rect

    def rebuild_item_rects(self) -> None:
        self.entity_item_rects = self._build_palette_rects(
            self.entities_rect, len(self.registry.entities)
        )
        self.environment_item_rects = self._build_palette_rects(
            self.environments_rect, len(self.registry.environments)
        )

    def clamp_scroll_states(self) -> None:
        entity_max = self._palette_max_scroll(
            self.entities_rect, len(self.registry.entities)
        )
        env_max = self._palette_max_scroll(
            self.environments_rect, len(self.registry.environments)
        )
        self.scroll["entity"] = self.clamp_scroll(self.scroll.get("entity", 0), entity_max)
        self.scroll["environment"] = self.clamp_scroll(
            self.scroll.get("environment", 0), env_max
        )

    def render(self, screen: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        self._render_palette_column(
            screen,
            self.entities_rect,
            "Entities",
            "entity",
            self.registry.entities,
            self.entity_item_rects,
            mouse_pos,
        )
        self._render_palette_column(
            screen,
            self.environments_rect,
            "Environments",
            "environment",
            self.registry.environments,
            self.environment_item_rects,
            mouse_pos,
        )

    def _render_palette_column(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        kind: str,
        items: list[PaletteItem],
        item_rects: list[pygame.Rect],
        mouse_pos: tuple[int, int],
    ) -> None:
        if rect.width <= 0 or rect.height <= 0:
            return
        pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=6)
        self.draw_section_header(screen, rect, title)

        max_scroll = self._palette_max_scroll(rect, len(items))
        scroll = self.clamp_scroll(self.scroll.get(kind, 0), max_scroll)
        if scroll != self.scroll.get(kind):
            self.scroll[kind] = scroll
        body_top, body_bottom = self.section_body_bounds(rect)

        count = min(len(items), len(item_rects))
        for i in range(count):
            item = items[i]
            base_rect = item_rects[i]
            r = base_rect.move(0, -scroll)
            if r.bottom < body_top or r.top > body_bottom:
                continue
            hovered = r.collidepoint(mouse_pos)
            col = (55, 55, 55) if hovered else (45, 45, 45)
            pygame.draw.rect(screen, col, r, border_radius=6)
            t = self.font_mono.render(item.name, True, (220, 220, 220))
            screen.blit(t, (r.x + 8, r.y + 6))

    def handle_scroll(self, pos: tuple[int, int], delta: float) -> bool:
        if self.entities_rect.collidepoint(pos):
            self._scroll_kind("entity", delta)
            return True
        if self.environments_rect.collidepoint(pos):
            self._scroll_kind("environment", delta)
            return True
        return False

    def _scroll_kind(self, kind: str, delta: float) -> None:
        rect = self.entities_rect if kind == "entity" else self.environments_rect
        items = (
            self.registry.entities if kind == "entity" else self.registry.environments
        )
        max_scroll = self._palette_max_scroll(rect, len(items))
        self.scroll[kind] = self.apply_scroll_delta(self.scroll.get(kind, 0), delta, max_scroll)

    def hit(self, pos: tuple[int, int]) -> tuple[str, int] | None:
        hit = self._palette_hit_column(
            pos,
            "entity",
            self.entities_rect,
            self.entity_item_rects,
            len(self.registry.entities),
        )
        if hit is not None:
            return hit
        return self._palette_hit_column(
            pos,
            "environment",
            self.environments_rect,
            self.environment_item_rects,
            len(self.registry.environments),
        )

    def _palette_hit_column(
        self,
        pos: tuple[int, int],
        target: str,
        rect: pygame.Rect,
        rects: list[pygame.Rect],
        count: int,
    ) -> tuple[str, int] | None:
        if rect.width <= 0 or rect.height <= 0:
            return None
        if not rect.collidepoint(pos):
            return None
        scroll = self.scroll.get(target, 0)
        limit = min(count, len(rects))
        body_top, body_bottom = self.section_body_bounds(rect)
        for i in range(limit):
            r = rects[i].move(0, -scroll)
            if r.bottom < body_top or r.top > body_bottom:
                continue
            if r.collidepoint(pos):
                return (target, i)
        return None

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

    def _palette_content_height(self, count: int) -> int:
        if count <= 0:
            return 0
        gap = 6
        return count * self.palette_item_h + max(0, (count - 1) * gap)

    def _palette_max_scroll(self, rect: pygame.Rect, count: int) -> int:
        visible = self.visible_body_height(rect)
        content = self._palette_content_height(count)
        return max(0, content - visible)


class TreePanel(SectionPanel):
    def __init__(
        self,
        font: pygame.font.Font,
        font_mono: pygame.font.Font,
        model: Any,
        *,
        tree_line_h: int = 20,
        section_header_h: int = 36,
        section_body_pad: int = 8,
    ) -> None:
        super().__init__(
            font,
            font_mono,
            section_header_h=section_header_h,
            section_body_pad=section_body_pad,
        )
        self.model = model
        self.tree_line_h = tree_line_h
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.scroll = 0
        self.hitboxes: list[tuple[pygame.Rect, int]] = []

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def clamp_scroll_state(self) -> None:
        self.scroll = self.clamp_scroll(self.scroll, self._max_scroll())

    def render(self, screen: pygame.Surface) -> None:
        rect = self.rect
        if rect.width <= 0 or rect.height <= 0:
            self.hitboxes = []
            return

        pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=6)
        self.draw_section_header(screen, rect, "Tree")

        body_top, body_bottom = self.section_body_bounds(rect)
        visible = max(0, body_bottom - body_top)
        nodes = list(self.model.iter_tree())
        line_h = self.tree_line_h
        max_scroll = max(0, len(nodes) * line_h - visible)
        scroll = self.clamp_scroll(self.scroll, max_scroll)
        if scroll != self.scroll:
            self.scroll = scroll

        y = body_top - scroll
        self.hitboxes = []

        for depth, node in nodes:
            line_rect = pygame.Rect(rect.x + 6, y - 2, rect.width - 12, line_h)
            if line_rect.bottom < body_top:
                y += line_h
                continue
            if line_rect.top > body_bottom:
                break
            is_selected = node.id == self.model.selected_id
            if is_selected:
                pygame.draw.rect(screen, (80, 70, 30), line_rect, border_radius=4)

            indent = depth * 14
            text_x = rect.x + 12 + indent
            text = node.name
            if node.kind in ("entity", "environment"):
                tag = " [Ent]" if node.kind == "entity" else " [Env]"
                text = f"{node.name}{tag}"
            color = (255, 220, 160) if is_selected else (210, 210, 210)
            t = self.font_mono.render(text, True, color)
            screen.blit(t, (text_x, y))

            self.hitboxes.append((line_rect.copy(), node.id))
            y += line_h

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if self.rect.width <= 0 or self.rect.height <= 0:
            return False
        if not self.rect.collidepoint(pos):
            return False
        node_id = self.node_at(pos)
        if node_id is not None:
            self.model.select_node(node_id)
        else:
            self.model.select_node(None)
        return True

    def node_at(self, pos: tuple[int, int]) -> int | None:
        if self.rect.width <= 0 or self.rect.height <= 0:
            return None
        if not self.rect.collidepoint(pos):
            return None
        for rect, node_id in self.hitboxes:
            if rect.collidepoint(pos):
                return node_id
        return None

    def handle_scroll(self, pos: tuple[int, int], delta: float) -> bool:
        if not self.rect.collidepoint(pos):
            return False
        self.scroll = self.apply_scroll_delta(self.scroll, delta, self._max_scroll())
        return True

    def _max_scroll(self) -> int:
        visible = self.visible_body_height(self.rect)
        if visible <= 0:
            return 0
        total_lines = sum(1 for _ in self.model.iter_tree())
        content = total_lines * self.tree_line_h
        return max(0, content - visible)


class AttrsPanel(SectionPanel):
    def __init__(
        self,
        font: pygame.font.Font,
        font_mono: pygame.font.Font,
        model: Any,
        *,
        attr_line_h: int = 20,
        section_header_h: int = 36,
        section_body_pad: int = 8,
        print_status: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            font,
            font_mono,
            section_header_h=section_header_h,
            section_body_pad=section_body_pad,
        )
        self.model = model
        self.attr_line_h = attr_line_h
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.scroll = 0
        self.focus_index = 0
        self._focus_changed = False
        self.editing = False
        self.input = ""
        self.cursor_pos = 0
        self._edit_attr: str | None = None
        self._edit_node_id: int | None = None
        self._edit_component: str | None = None
        self._edit_raw_value: Any = None
        self._last_node_id: int | None = None
        self._print_status = print_status

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def clamp_scroll_state(self) -> None:
        entries = self.current_entries()
        self.scroll = self.clamp_scroll(self.scroll, self._max_scroll(entries)) if entries else 0

    def render(self, screen: pygame.Surface) -> None:
        rect = self.rect
        if rect.width <= 0 or rect.height <= 0:
            return

        pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=6)
        self.draw_section_header(screen, rect, "Attributes")

        node = self.model.selected_node()
        if node is None:
            self.scroll = 0
            self._draw_empty_inspector(screen, rect)
            self._last_node_id = None
            self.cancel_edit()
            return

        if self._last_node_id != node.id:
            self._last_node_id = node.id
            self.focus_index = 0
            self._focus_changed = True
            self.cancel_edit()

        entries = self._collect_attr_entries(node, self._selected_label())
        self._sync_focus(entries, node.id)
        self._draw_attrs(screen, rect, entries)

    def handle_text_input(self, text: str) -> None:
        if not self.editing or not text:
            return
        pre = self.input[: self.cursor_pos]
        post = self.input[self.cursor_pos :]
        self.input = f"{pre}{text}{post}"
        self.cursor_pos += len(text)

    def handle_keydown(self, ev: pygame.event.Event) -> bool:
        if ev.key == pygame.K_RETURN:
            self._commit_edit()
            return True
        if ev.key in (pygame.K_ESCAPE, pygame.K_TAB):
            self.cancel_edit()
            return True
        if ev.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            return True
        if ev.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.input), self.cursor_pos + 1)
            return True
        if ev.key == pygame.K_HOME:
            self.cursor_pos = 0
            return True
        if ev.key == pygame.K_END:
            self.cursor_pos = len(self.input)
            return True
        if ev.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                pre = self.input[: self.cursor_pos - 1]
                post = self.input[self.cursor_pos :]
                self.input = f"{pre}{post}"
                self.cursor_pos -= 1
            return True
        if ev.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.input):
                pre = self.input[: self.cursor_pos]
                post = self.input[self.cursor_pos + 1 :]
                self.input = f"{pre}{post}"
            return True
        return True

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if self.rect.width <= 0 or self.rect.height <= 0:
            return False
        if not self.rect.collidepoint(pos):
            return False

        node = self.model.selected_node()
        if node is None:
            return False

        entries = self._collect_attr_entries(node, self._selected_label())
        if not entries:
            return False

        idx = self._entry_index_at(pos, entries)
        if idx is None:
            return False

        self.focus_index = idx
        self._focus_changed = True
        entry = entries[idx]
        if entry.editable:
            if isinstance(entry.raw_value, bool):
                self._toggle_boolean_attr(node, entry)
            else:
                self._begin_edit(node, entry)
        return True

    def handle_scroll(self, pos: tuple[int, int], delta: float) -> bool:
        if not self.rect.collidepoint(pos):
            return False
        node = self.model.selected_node()
        if node is None:
            self.scroll = 0
            return True
        entries = self._collect_attr_entries(node, self._selected_label())
        max_scroll = self._max_scroll(entries)
        self.scroll = self.apply_scroll_delta(self.scroll, delta, max_scroll)
        return True

    def cancel_edit(self) -> None:
        if self.editing:
            pygame.key.stop_text_input()
        self.editing = False
        self.input = ""
        self.cursor_pos = 0
        self._edit_attr = None
        self._edit_node_id = None
        self._edit_raw_value = None
        self._edit_component = None

    def current_entries(self) -> list[AttrEntry]:
        node = self.model.selected_node()
        if node is None:
            return []
        return self._collect_attr_entries(node, self._selected_label())

    def _selected_label(self) -> str:
        return self.model.selected_label()

    def _draw_empty_inspector(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        msg = self.font_mono.render(
            "No entities. Pick one from palette.", True, (160, 160, 160)
        )
        screen.blit(msg, (rect.x + 10, rect.y + 40))

    def _draw_attrs(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        entries: list[AttrEntry],
    ) -> None:
        if not entries:
            return
        xk = rect.x + 10
        xv = rect.x + rect.width // 2
        body_top, body_bottom = self.section_body_bounds(rect)
        visible = max(0, body_bottom - body_top)
        if visible <= 0:
            return

        max_scroll = self._max_scroll(entries)
        scroll = self.clamp_scroll(self.scroll, max_scroll)
        if scroll != self.scroll:
            self.scroll = scroll

        y = body_top - scroll
        cursor_on = (pygame.time.get_ticks() // 400) % 2 == 0
        for idx, entry in enumerate(entries):
            line_rect = pygame.Rect(rect.x + 4, y, rect.width - 8, self.attr_line_h)
            if line_rect.bottom >= body_top:
                if line_rect.top > body_bottom:
                    break
                is_focus = idx == self.focus_index
                if is_focus:
                    color = (90, 70, 40) if entry.editable else (60, 60, 60)
                    pygame.draw.rect(screen, color, line_rect, border_radius=4)

                key_color = (210, 210, 210)
                value_color = (235, 210, 160) if entry.editable else (180, 180, 180)
                value_text = entry.display
                if self.editing and is_focus:
                    value_text = self.input
                    if cursor_on:
                        pre = self.input[: self.cursor_pos]
                        post = self.input[self.cursor_pos :]
                        value_text = f"{pre}|{post}"

                ksurf = self.font_mono.render(entry.label, True, key_color)
                vsurf = self.font_mono.render(value_text, True, value_color)
                screen.blit(ksurf, (xk, y))
                screen.blit(vsurf, (xv, y))
            y += self.attr_line_h

    def _sync_focus(self, entries: list[AttrEntry], node_id: int) -> None:
        if not entries:
            self.focus_index = 0
            self.cancel_edit()
            return
        max_idx = len(entries) - 1

        old_idx = self.focus_index
        self.focus_index = max(0, min(self.focus_index, max_idx))
        if old_idx != self.focus_index:
            self._focus_changed = True

        if self.editing and self._edit_node_id != node_id:
            self.cancel_edit()

        if self._focus_changed:
            self._scroll_focus_into_view(entries)
            self._focus_changed = False

    def _scroll_focus_into_view(self, entries: list[AttrEntry]) -> None:
        if not entries:
            return
        rect = self.rect
        body_top, body_bottom = self.section_body_bounds(rect)
        visible = body_bottom - body_top
        if visible <= 0:
            return
        idx = max(0, min(self.focus_index, len(entries) - 1))
        entry_top = idx * self.attr_line_h
        entry_bottom = entry_top + self.attr_line_h
        view_top = self.scroll
        view_bottom = self.scroll + visible
        if entry_top < view_top:
            self.scroll = entry_top
        elif entry_bottom > view_bottom:
            self.scroll = entry_bottom - visible
        max_scroll = self._max_scroll(entries)
        self.scroll = self.clamp_scroll(self.scroll, max_scroll)

    def _collect_attr_entries(self, node, label: str) -> list[AttrEntry]:
        entries: list[AttrEntry] = []
        if label:
            entries.append(AttrEntry("Name", label))
        entries.append(AttrEntry("Type", node.kind.title()))
        parent_label = self.model.parent_label(node.id) or "Scene Root"
        entries.append(AttrEntry("Parent", parent_label))
        children = ", ".join(self.model.child_labels(node.id)) or "-"
        entries.append(AttrEntry("Children", children))
        entries.extend(self._iter_public_attrs(node.payload))
        return entries

    def _iter_public_attrs(self, obj) -> list[AttrEntry]:
        items: list[AttrEntry] = []
        if obj is None:
            return items

        seen_attrs = set()

        for cls in reversed(obj.__class__.__mro__):
            if cls is object:
                continue

            class_level_attrs: list[AttrEntry] = []

            for k in sorted(cls.__dict__.keys()):
                if k.startswith("_") or k in seen_attrs:
                    continue

                v = cls.__dict__[k]
                is_property = isinstance(v, property)
                is_data_like = not callable(v) or is_property

                if not is_data_like:
                    continue

                try:
                    value = getattr(obj, k)
                except AttributeError:
                    continue

                editable = False
                if is_property:
                    editable = v.fset is not None and self._attr_supports_edit(value)
                elif k in obj.__dict__:
                    editable = self._attr_supports_edit(value)

                if isinstance(value, pygame.Vector2):
                    class_level_attrs.extend(self._vector_attr_entries(k, value))
                else:
                    class_level_attrs.append(
                        AttrEntry(
                            k,
                            self._safe_repr(value),
                            editable=editable,
                            attr_name=k,
                            raw_value=value,
                        )
                    )
                seen_attrs.add(k)

            if class_level_attrs:
                items.append(AttrEntry(f"[{cls.__name__}]", "", editable=False))
                items.extend(sorted(class_level_attrs, key=lambda x: x.label))

        remaining_instance_attrs: list[AttrEntry] = []
        for k, value in sorted(obj.__dict__.items()):
            if k.startswith("_") or k in seen_attrs:
                continue

            editable = self._attr_supports_edit(value)
            if isinstance(value, pygame.Vector2):
                remaining_instance_attrs.extend(self._vector_attr_entries(k, value))
            else:
                remaining_instance_attrs.append(
                    AttrEntry(
                        k,
                        self._safe_repr(value),
                        editable=editable,
                        attr_name=k,
                        raw_value=value,
                    )
                )
            seen_attrs.add(k)

        if remaining_instance_attrs:
            items.append(AttrEntry("[Instance]", "", editable=False))
            items.extend(sorted(remaining_instance_attrs, key=lambda x: x.label))

        return items

    def _vector_attr_entries(self, name: str, vec: pygame.Vector2) -> list[AttrEntry]:
        entries = [AttrEntry(name, self._safe_repr(vec))]
        for axis in ("x", "y"):
            comp_label = f"{name}.{axis}"
            comp_value = float(getattr(vec, axis))
            entries.append(
                AttrEntry(
                    comp_label,
                    self._safe_repr(comp_value),
                    editable=True,
                    attr_name=name,
                    raw_value=comp_value,
                    component=axis,
                )
            )
        return entries

    def _safe_repr(self, v) -> str:
        try:
            s = repr(v)
        except Exception:
            s = "<unrepr-able>"
        return s if len(s) <= 70 else s[:67] + "..."

    def _attr_supports_edit(self, value: Any) -> bool:
        if isinstance(value, (int, float, str, bool)) or value is None:
            return True
        return self._is_editable_sequence(value)

    def _is_editable_sequence(self, value: Any) -> bool:
        if not isinstance(value, (list, tuple)):
            return False
        if not value:
            return True
        return all(isinstance(item, str) for item in value)

    def _begin_edit(self, node, entry: AttrEntry) -> None:
        if not entry.editable or entry.attr_name is None or node.payload is None:
            return
        self.editing = True
        self.input = self._format_attr_value(entry.raw_value)
        self.cursor_pos = len(self.input)
        self._edit_attr = entry.attr_name
        self._edit_node_id = node.id
        self._edit_raw_value = entry.raw_value
        self._edit_component = entry.component
        pygame.key.start_text_input()

    def _commit_edit(self) -> None:
        if not self.editing or self._edit_attr is None or self._edit_node_id is None:
            self.cancel_edit()
            return
        node = self.model.selected_node()
        if node is None or node.payload is None or node.id != self._edit_node_id:
            self.cancel_edit()
            return

        current_value = getattr(node.payload, self._edit_attr, None)
        if self._edit_component is not None and isinstance(
            current_value, pygame.Vector2
        ):
            original_value = getattr(
                current_value, self._edit_component, self._edit_raw_value
            )
        else:
            original_value = current_value
        if original_value is None and self._edit_raw_value is not None:
            original_value = self._edit_raw_value
        success, parsed = self._parse_attr_input(original_value, self.input)
        if not success:
            if self._print_status is not None:
                self._print_status(f"[Editor] Invalid value for {self._edit_attr}.")
            self.cancel_edit()
            return

        if self._edit_component is None:
            setattr(node.payload, self._edit_attr, parsed)
        else:
            vec = (
                pygame.Vector2(current_value)
                if current_value is not None
                else pygame.Vector2(0, 0)
            )
            setattr(vec, self._edit_component, float(parsed))
            setattr(node.payload, self._edit_attr, vec)
        self.cancel_edit()

    def _format_attr_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if self._is_editable_sequence(value):
            return ", ".join(value)
        return str(value)

    def _parse_attr_input(self, original: Any, text: str) -> tuple[bool, Any]:
        if isinstance(original, bool):
            value = text.strip().lower()
            if value in ("1", "true", "on", "yes"):
                return True, True
            if value in ("0", "false", "off", "no"):
                return True, False
            return False, original
        if isinstance(original, int) and not isinstance(original, bool):
            try:
                return True, int(text.strip())
            except ValueError:
                return False, original
        if isinstance(original, float):
            try:
                return True, float(text.strip())
            except ValueError:
                return False, original
        if isinstance(original, (list, tuple)) and self._is_editable_sequence(original):
            parsed = self._parse_sequence_input(text)
            if isinstance(original, tuple):
                return True, tuple(parsed)
            return True, parsed
        if isinstance(original, str) or original is None:
            return True, text
        return True, text

    def _parse_sequence_input(self, text: str) -> list[str]:
        if not text.strip():
            return []
        normalized = text.replace("\r\n", ",").replace("\n", ",").replace(";", ",")
        parts = normalized.split(",")
        values = [part.strip() for part in parts if part.strip()]
        return values

    def _entry_index_at(
        self,
        pos: tuple[int, int],
        entries: list[AttrEntry],
    ) -> int | None:
        rect = self.rect
        body_top, body_bottom = self.section_body_bounds(rect)
        if pos[1] < body_top or pos[1] >= body_bottom:
            return None
        visible = body_bottom - body_top
        if visible <= 0:
            return None
        relative_y = (pos[1] - body_top) + self.scroll
        if relative_y < 0:
            return None
        idx = int(relative_y // self.attr_line_h)
        return idx if 0 <= idx < len(entries) else None

    def _toggle_boolean_attr(self, node, entry: AttrEntry) -> None:
        if not entry.editable or not isinstance(entry.raw_value, bool):
            return
        if node.payload is None or entry.attr_name is None:
            return

        current_value = getattr(node.payload, entry.attr_name, None)
        if isinstance(current_value, bool):
            setattr(node.payload, entry.attr_name, not current_value)

    def _max_scroll(self, entries: list[AttrEntry]) -> int:
        visible = self.visible_body_height(self.rect)
        if visible <= 0:
            return 0
        content = len(entries) * self.attr_line_h
        return max(0, content - visible)


class ResolutionPanel(SectionPanel):
    def __init__(
        self,
        font: pygame.font.Font,
        font_mono: pygame.font.Font,
        *,
        item_h: int = 26,
        section_header_h: int = 36,
        section_body_pad: int = 8,
    ) -> None:
        super().__init__(
            font,
            font_mono,
            section_header_h=section_header_h,
            section_body_pad=section_body_pad,
        )
        self.item_h = item_h
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.options: list[tuple[str, str]] = []
        self.item_rects: list[tuple[str, pygame.Rect]] = []
        self.selected_key: str | None = None
        self.custom_size: tuple[int, int] | None = None
        self.editing = False
        self.input = ""
        self.cursor_pos = 0
        self.scroll = 0

    def set_rect(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self._rebuild_item_rects()
        self.scroll = self.clamp_scroll(self.scroll, self._max_scroll())

    def set_options(self, options: list[tuple[str, str]]) -> None:
        self.options = options
        self._rebuild_item_rects()
        self.scroll = self.clamp_scroll(self.scroll, self._max_scroll())

    def render(self, screen: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        rect = self.rect
        if rect.width <= 0 or rect.height <= 0:
            return
        if len(self.item_rects) != len(self.options):
            self._rebuild_item_rects()

        pygame.draw.rect(screen, (30, 30, 30), rect, border_radius=6)
        self.draw_section_header(screen, rect, "Resolution")

        label_map = {key: label for key, label in self.options}
        if self.custom_size is not None:
            cw, ch = self.custom_size
            label_map["custom"] = f"Custom ({cw}x{ch})"
        body_top, body_bottom = self.section_body_bounds(rect)
        for key, item_rect in self.item_rects:
            r = item_rect.move(0, -self.scroll)
            if r.bottom < body_top or r.top > body_bottom:
                continue
            hovered = r.collidepoint(mouse_pos)
            is_selected = key == self.selected_key
            color = (70, 65, 40) if is_selected else (45, 45, 45)
            if hovered:
                color = (85, 75, 35) if is_selected else (55, 55, 55)
            pygame.draw.rect(screen, color, r, border_radius=4)
            label = label_map.get(key, key)
            if key == "custom" and self.editing:
                label = self._format_edit_label(label)
            surf = self.font_mono.render(label, True, (235, 235, 235))
            ty = r.y + (r.height - surf.get_height()) // 2
            screen.blit(surf, (r.x + 8, ty))

    def hit(self, pos: tuple[int, int]) -> str | None:
        if self.rect.width <= 0 or self.rect.height <= 0:
            return None
        if not self.rect.collidepoint(pos):
            return None
        body_top, body_bottom = self.section_body_bounds(self.rect)
        for key, item_rect in self.item_rects:
            r = item_rect.move(0, -self.scroll)
            if r.bottom < body_top or r.top > body_bottom:
                continue
            if r.collidepoint(pos):
                return key
        return None

    def handle_scroll(self, delta: float) -> bool:
        if self.editing or delta == 0 or not self.options:
            return False
        max_scroll = self._max_scroll()
        self.scroll = self.apply_scroll_delta(self.scroll, delta, max_scroll)
        return True

    def begin_edit(self) -> None:
        self.editing = True
        if self.custom_size is not None:
            w, h = self.custom_size
            self.input = f"{w}x{h}"
        else:
            self.input = ""
        self.cursor_pos = len(self.input)
        pygame.key.start_text_input()

    def cancel_edit(self) -> None:
        if self.editing:
            pygame.key.stop_text_input()
        self.editing = False
        self.input = ""
        self.cursor_pos = 0

    def handle_text_input(self, text: str) -> None:
        if not self.editing or not text:
            return
        pre = self.input[: self.cursor_pos]
        post = self.input[self.cursor_pos :]
        self.input = f"{pre}{text}{post}"
        self.cursor_pos += len(text)

    def handle_keydown(self, ev: pygame.event.Event) -> tuple[int, int] | None:
        if ev.key == pygame.K_RETURN:
            size = self._parse_size(self.input)
            if size is None:
                return None
            self.custom_size = size
            self.cancel_edit()
            return size
        if ev.key in (pygame.K_ESCAPE, pygame.K_TAB):
            self.cancel_edit()
            return None
        if ev.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            return None
        if ev.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.input), self.cursor_pos + 1)
            return None
        if ev.key == pygame.K_HOME:
            self.cursor_pos = 0
            return None
        if ev.key == pygame.K_END:
            self.cursor_pos = len(self.input)
            return None
        if ev.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                pre = self.input[: self.cursor_pos - 1]
                post = self.input[self.cursor_pos :]
                self.input = f"{pre}{post}"
                self.cursor_pos -= 1
            return None
        if ev.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.input):
                pre = self.input[: self.cursor_pos]
                post = self.input[self.cursor_pos + 1 :]
                self.input = f"{pre}{post}"
            return None
        return None

    def _parse_size(self, text: str) -> tuple[int, int] | None:
        if not text:
            return None
        normalized = text.lower().replace(",", " ").replace("x", " ")
        parts = [p for p in normalized.split() if p]
        if len(parts) < 2:
            return None
        try:
            w = int(parts[0])
            h = int(parts[1])
        except ValueError:
            return None
        if w <= 0 or h <= 0:
            return None
        return (w, h)

    def _format_edit_label(self, base_label: str) -> str:
        cursor_on = (pygame.time.get_ticks() // 400) % 2 == 0
        value = self.input
        if cursor_on:
            pre = self.input[: self.cursor_pos]
            post = self.input[self.cursor_pos :]
            value = f"{pre}|{post}"
        return f"{base_label}: {value}"

    def _rebuild_item_rects(self) -> None:
        rect = self.rect
        rects: list[tuple[str, pygame.Rect]] = []
        if rect.width <= 0 or rect.height <= 0:
            self.item_rects = rects
            return

        body_top, body_bottom = self.section_body_bounds(rect)
        x = rect.x + 10
        y = body_top
        w = rect.width - 20
        for key, _ in self.options:
            item_rect = pygame.Rect(x, y, w, self.item_h)
            rects.append((key, item_rect))
            y += self.item_h + 6
        self.item_rects = rects

    def _content_height(self) -> int:
        if not self.options:
            return 0
        gap = 6
        count = len(self.options)
        return count * self.item_h + max(0, (count - 1) * gap)

    def _max_scroll(self) -> int:
        visible = self.visible_body_height(self.rect)
        if visible <= 0:
            return 0
        content = self._content_height()
        return max(0, content - visible)
