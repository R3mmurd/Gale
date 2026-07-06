"""
This file contains the implementation of the class UIManager.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Dict, Optional

from gale.input_handler import KeyboardData, MouseClickData, MouseMotionData

from .container import Container
from .widget import Direction, Widget


class UIManager:
    """
    Connects a widget tree (a root Container) to gale.input_handler,
    rescaling mouse positions from window to virtual coordinates and
    routing keyboard "confirm"/navigation actions and raw key events
    to the right widget.

    Not self-registered with InputHandler.register_listener: like
    StateMachine/StateStack, its owner (typically a BaseState) must
    call on_input manually, so only the currently active UI receives
    input.

    Usage example:

        class LobbyState(BaseState):
            def enter(self, **kwargs) -> None:
                self.ui = UIManager(
                    build_lobby_menu(),
                    virtual_width=settings.VIRTUAL_WIDTH,
                    window_width=settings.WINDOW_WIDTH,
                    virtual_height=settings.VIRTUAL_HEIGHT,
                    window_height=settings.WINDOW_HEIGHT,
                    confirm_action="confirm",
                    navigate_actions={"move_up": (0, -1), "move_down": (0, 1)},
                )

            def update(self, dt: float) -> None:
                self.ui.update(dt)

            def render(self, surface: pygame.Surface) -> None:
                self.ui.render(surface)

            def on_input(self, input_id: str, input_data) -> None:
                self.ui.on_input(input_id, input_data)
    """

    def __init__(
        self,
        root: Container,
        virtual_width: int,
        window_width: int,
        virtual_height: int,
        window_height: int,
        confirm_action: str = "confirm",
        navigate_actions: Optional[Dict[str, Direction]] = None,
    ) -> None:
        """
        :param root: The root of the widget tree this manager drives.
        :param virtual_width: The width of the surface the game renders to.
        :param window_width: The width of the real window that virtual surface is scaled up to.
        :param virtual_height: The height of the surface the game renders to.
        :param window_height: The height of the real window that virtual surface is scaled up to.
        :param confirm_action: The input_id that should invoke the focused widget. The default value is "confirm".
        :param navigate_actions: A map from input_id to the Direction it should move focus/selection in. The default value is None, meaning no keyboard navigation.
        """
        self.root: Container = root
        self.virtual_width: int = virtual_width
        self.window_width: int = window_width
        self.virtual_height: int = virtual_height
        self.window_height: int = window_height
        self.confirm_action: str = confirm_action
        self.navigate_actions: Dict[str, Direction] = navigate_actions or {}

    def update(self, dt: float) -> None:
        self.root.update(dt)

    def render(self, surface) -> None:
        self.root.render(surface)

    def on_input(self, input_id: str, input_data) -> None:
        """
        :param input_id: The action id notified by InputHandler.
        :param input_data: The associated input data.
        """
        if isinstance(input_data, MouseMotionData):
            self.root.on_mouse_motion(self._rescale(input_data.position))
        elif isinstance(input_data, MouseClickData):
            self.root.on_mouse_click(self._rescale(input_data.position), input_data)
        elif isinstance(input_data, KeyboardData):
            self._on_keyboard(input_id, input_data)

    def _on_keyboard(self, input_id: str, input_data: KeyboardData) -> None:
        if not input_data.pressed:
            return

        if input_id == self.confirm_action:
            self.root.on_confirm()
            return

        if input_id in self.navigate_actions:
            self.root.on_navigate(self.navigate_actions[input_id])
            return

        focused = _deepest_focused(self.root)

        if focused is not None and focused.wants_raw_keyboard:
            focused.handle_key(input_data)

    def _rescale(self, position):
        x, y = position
        return (
            x * self.virtual_width // self.window_width,
            y * self.virtual_height // self.window_height,
        )


def _deepest_focused(widget: Widget) -> Optional[Widget]:
    children = getattr(widget, "children", None)

    if not children:
        return widget if widget.focused else None

    for child in children:
        if child.focused:
            return _deepest_focused(child)

    return None
