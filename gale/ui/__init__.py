"""
gale.ui: a general-purpose, per-game-customizable widget toolkit
(panels, labels, buttons, progress bars, checkboxes, list views,
containers, text boxes, text inputs, cursors) built on top of
gale.input_handler, gale.text, and gale.timer.

See docs/examples/ui.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .button import Button
from .checkbox import Checkbox
from .container import Container
from .cursor import Cursor
from .label import Label
from .list_view import ListView
from .manager import UIManager
from .panel import Panel
from .progress_bar import ProgressBar
from .text_box import TextBox
from .text_input import TextInput
from .theme import Theme, get_default_theme, set_default_theme
from .widget import Widget

__all__ = [
    "Button",
    "Checkbox",
    "Container",
    "Cursor",
    "Label",
    "ListView",
    "Panel",
    "ProgressBar",
    "Theme",
    "TextBox",
    "TextInput",
    "UIManager",
    "Widget",
    "get_default_theme",
    "set_default_theme",
]
