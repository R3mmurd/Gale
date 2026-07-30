"""
Rally: a small online Pong built to exercise gale.net (LAN/internet
multiplayer over a hand-rolled reliable UDP layer) and gale.ui (menus,
text entry, buttons) together. Every visual is drawn with pygame.draw
primitives, so it needs no image/font/sound assets to run.
"""

import pygame

from gale import input_handler
from gale.ui.cursor import Cursor

# This module builds FONTS (and possibly TEXTURES/SOUNDS/CURSORS)
# below, which needs pygame's font/mixer/display subsystems already
# initialized -- and since other project modules are free to `import
# settings` directly (not only indirectly, by importing gale.game
# first), this module can't rely on something else having initialized
# pygame first. Safe to call again if gale.game's own import already
# did (pygame.init() is idempotent), and never raises even without an
# audio device, unlike calling pygame.mixer.init()/pygame.font.init()
# directly.
pygame.init()

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_s, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_BACKSPACE, "text_key")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "text_key")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "text_key")
input_handler.InputHandler.set_mouse_click_action(input_handler.MOUSE_BUTTON_1, "click")
# A wildcard fallback (see InputHandler.set_mouse_motion_action) so
# gale.ui's hover highlighting reacts to every mouse move, not just
# ones matching an exact unit-vector direction.
input_handler.InputHandler.set_mouse_motion_action(None, "mouse_move")

TITLE = "Rally"

# Size we want to emulate
VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 300

# Size of our actual window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

DEFAULT_PORT = 9000
DEFAULT_DISCOVERY_PORT = 9998

PADDLE_WIDTH = 10
PADDLE_HEIGHT = 60
PADDLE_MARGIN = 20
PADDLE_SPEED = 220

BALL_SIZE = 8
BALL_SPEED = 160

WIN_SCORE = 5

COLOR_BACKGROUND = (10, 10, 16)
COLOR_PADDLE = (230, 230, 230)
COLOR_BALL = (255, 210, 60)
COLOR_NET = (60, 60, 72)
COLOR_TEXT = (235, 235, 235)

FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}


def _build_pointer_cursor() -> pygame.Surface:
    # A tiny hand-drawn arrow, so the example needs no image asset.
    image = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.polygon(
        image,
        (255, 255, 255),
        [(0, 0), (0, 12), (4, 9), (7, 15), (9, 14), (6, 8), (12, 8)],
    )
    return image


CURSORS = {
    "pointer": Cursor(_build_pointer_cursor(), hotspot=(0, 0)),
}
