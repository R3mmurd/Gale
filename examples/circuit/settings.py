"""
Circuit: a small online racing prototype built to exercise the newest
additions to gale.net (gale.net.PredictionBuffer for client-side
prediction/server reconciliation, gale.net.SnapshotInterpolator and
gale.net.lag_compensated_position for entity interpolation/lag
compensation) together with gale.ai's steering-based path following
(gale.ai.steering, gale.ai.graph.NavGraph, gale.ai.search.a_star). Every
visual is drawn with pygame.draw primitives, so it needs no image/font/
sound assets to run.
"""

import pygame

from gale import input_handler
from gale.ui.cursor import Cursor

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "throttle_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "throttle_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "throttle_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_s, "throttle_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "steer_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "steer_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "steer_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "steer_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "bump")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_BACKSPACE, "text_key")
input_handler.InputHandler.set_mouse_click_action(input_handler.MOUSE_BUTTON_1, "click")
# A wildcard fallback (see InputHandler.set_mouse_motion_action) so
# gale.ui's hover highlighting reacts to every mouse move, not just
# ones matching an exact unit-vector direction.
input_handler.InputHandler.set_mouse_motion_action(None, "mouse_move")

# Size we want to emulate
VIRTUAL_WIDTH = 480
VIRTUAL_HEIGHT = 320

# Size of our actual window
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640

DEFAULT_PORT = 9100
DEFAULT_DISCOVERY_PORT = 9998

# -- Track geometry (a simple rectangular oval, drawn as an outer rect
# minus an inner one; the ring between them is the driveable surface).
TRACK_MARGIN = 40
TRACK_WIDTH = 70
OUTER_RECT = pygame.Rect(
    TRACK_MARGIN,
    TRACK_MARGIN,
    VIRTUAL_WIDTH - 2 * TRACK_MARGIN,
    VIRTUAL_HEIGHT - 2 * TRACK_MARGIN,
)
INNER_RECT = OUTER_RECT.inflate(-2 * TRACK_WIDTH, -2 * TRACK_WIDTH)

# Finish line: a short vertical segment crossing the bottom straight.
FINISH_X = OUTER_RECT.centerx
FINISH_Y0 = INNER_RECT.bottom
FINISH_Y1 = OUTER_RECT.bottom

LAPS_TO_WIN = 2

# -- Car movement model (see src/car.py's apply_input, the pure function
# replayed by PredictionBuffer.reconcile).
CAR_MAX_SPEED = 160.0
CAR_MIN_SPEED = -60.0
CAR_ACCELERATION = 220.0
CAR_FRICTION = 0.6
CAR_TURN_RATE = 3.2
OFFTRACK_DAMPING = 0.985
CAR_RADIUS = 6

# -- AI racer (see src/path_follower.py + src/ai_car.py).
AI_MAX_SPEED = 130.0
AI_MAX_ACCELERATION = 140.0
AI_ARRIVAL_RADIUS = 18

# -- Networking recipe tuning.
# How far in the past (beyond the render delay already implied by half
# the RTT) a client samples its SnapshotInterpolator instances, to
# smooth over jitter in packet arrival times.
INTERP_DELAY = 0.08

# Distance within which a "bump" attempt against the AI racer counts as
# a hit (see PlayState._on_bump_attempt for the lag-compensated check).
BUMP_RADIUS = 16.0

COLOR_BACKGROUND = (10, 12, 18)
COLOR_TRACK = (56, 56, 64)
COLOR_GRASS = (18, 46, 24)
COLOR_FINISH = (235, 235, 235)
COLOR_HOST_CAR = (235, 90, 70)
COLOR_JOINER_CAR = (80, 160, 235)
COLOR_AI_CAR = (235, 200, 60)
COLOR_TEXT = (235, 235, 235)

pygame.font.init()

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
