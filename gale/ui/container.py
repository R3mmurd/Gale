"""
This file contains the implementation of the class Container: a
scene-graph node holding any number of child widgets, dispatching
input to them (mouse hit-testing, keyboard focus/navigation) and
rendering/updating them in add order.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import List, Optional, Sequence, Tuple

import pygame

from gale.input_handler import MouseClickData

from .theme import Theme
from .widget import Direction, Widget


class Container(Widget):
    """
    A real scene-graph node holding any number of child widgets.
    Rendered/updated in add order (which is also z-order: to bring a
    widget to front, remove and re-add it). Mouse events hit-test
    children in reverse add order (top-most first) and stop at the
    first one that consumes the event. on_confirm/on_navigate are
    forwarded only to the currently focused child; an unconsumed
    on_navigate instead moves focus to the next focusable sibling
    (linearly by add order by default, or spatially in 2D if spatial=True).

    Usage example:

        menu = Container(40, 40, 240, 160, children=[
            Panel(40, 40, 240, 160),
            ListView(48, 48, 224, 144, items=[("Host", start_hosting), ("Join", start_joining)]),
        ])
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        children: Optional[Sequence[Widget]] = None,
        theme: Optional[Theme] = None,
        visible: bool = True,
        spatial: bool = False,
    ) -> None:
        super().__init__(x, y, width, height, theme=theme, visible=visible)
        self.spatial: bool = spatial
        self.children: List[Widget] = []

        for child in children or []:
            self.add_child(child)

        if self._focusable_children() and not any(
            child.focused for child in self.children
        ):
            self._focus_first()

    @property
    def focusable(self) -> bool:
        return any(child.focusable for child in self.children)

    def add_child(self, widget: Widget) -> None:
        widget.parent = self
        self.children.append(widget)

    def remove_child(self, widget: Widget) -> None:
        if widget in self.children:
            widget.parent = None
            self.children.remove(widget)

    def update(self, dt: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        for child in self.children:
            if child.visible:
                child.render(surface)

    def on_mouse_motion(self, position: Tuple[float, float]) -> None:
        self.hovered = self.contains(position)

        for child in self.children:
            if child.visible and child.enabled:
                child.on_mouse_motion(position)

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        for child in reversed(self.children):
            if not child.visible or not child.enabled:
                continue

            if child.on_mouse_click(position, data):
                self._focus_only(child)
                return True

        return False

    def on_confirm(self) -> bool:
        focused_child = self._focused_child()
        return focused_child.on_confirm() if focused_child is not None else False

    def on_navigate(self, direction: Direction) -> bool:
        focused_child = self._focused_child()

        if focused_child is not None and focused_child.on_navigate(direction):
            return True

        return self._move_focus(direction)

    def _focusable_children(self) -> List[Widget]:
        return [
            child
            for child in self.children
            if child.visible and child.enabled and child.focusable
        ]

    def _focused_child(self) -> Optional[Widget]:
        for child in self.children:
            if child.focused:
                return child

        return None

    def _focus_first(self) -> None:
        focusable = self._focusable_children()

        if focusable:
            focusable[0].focused = True

    def _focus_only(self, widget: Widget) -> None:
        for child in self.children:
            child.focused = child is widget

    def _move_focus(self, direction: Direction) -> bool:
        """
        Move focus to another focusable child in the given direction,
        delegating to either 2D spatial navigation or linear list-order
        navigation based on self.spatial.
        """
        if self.spatial:
            return self._spatial_move_focus(direction)
        return self._linear_move_focus(direction)

    def _linear_move_focus(self, direction: Direction) -> bool:
        """
        Move focus forward or backward along the vertical axis based on
        list index (add order), wrapping around cyclically when reaching
        either end. Horizontal navigation (dy == 0) is ignored.
        """
        focusable = self._focusable_children()

        if not focusable:
            return False

        _, dy = direction

        if dy == 0:
            return False

        current = self._focused_child()
        current_index = focusable.index(current) if current in focusable else -1
        next_index = (current_index + dy) % len(focusable)
        self._focus_only(focusable[next_index])
        return True

    def _spatial_move_focus(self, direction: Direction) -> bool:
        """
        Move focus spatially across 2D space. Evaluates candidate widgets
        by calculating centroid distance and directional alignment (dot
        product), penalizing off-axis deviations. Supports 4-way and
        diagonal inputs, and stops at edges (returning False) rather than
        wrapping around.
        """
        focusable = self._focusable_children()

        if not focusable:
            return False

        dx, dy = direction
        current = self._focused_child()

        if current is None:
            self._focus_only(focusable[0])
            return True

        best_child = None
        best_score = float("inf")

        cx1 = current.x + getattr(current, "width", 0) / 2
        cy1 = current.y + getattr(current, "height", 0) / 2

        for child in focusable:
            if child is current:
                continue

            cx2 = child.x + getattr(child, "width", 0) / 2
            cy2 = child.y + getattr(child, "height", 0) / 2

            vx = cx2 - cx1
            vy = cy2 - cy1

            dot = vx * dx + vy * dy

            if dot > 0:
                dist = (vx**2 + vy**2) ** 0.5
                cross = abs(vx * dy - vy * dx)
                score = dist + cross * 2

                if score < best_score:
                    best_score = score
                    best_child = child

        if best_child is not None:
            self._focus_only(best_child)
            return True

        return False
