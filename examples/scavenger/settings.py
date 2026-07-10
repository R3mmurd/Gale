"""
Scavenger: a small top-down coin-collecting game built to exercise
gale.camera — following a target, zoom, screen shake, and clamping the
view to the world's bounds. Every visual is drawn with pygame.draw
primitives, so it needs no image/font/sound assets to run.
"""

import pygame

from gale import input_handler

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_s, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_EQUALS, "zoom_in")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_MINUS, "zoom_out")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")

# Size we want to emulate
VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 240

# Size of our actual window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

# The world is much bigger than the viewport, so the camera actually
# has somewhere to scroll to.
WORLD_WIDTH = 1600
WORLD_HEIGHT = 1200
GRID_SPACING = 80

PLAYER_RADIUS = 8
PLAYER_SPEED = 140

CAMERA_FOLLOW_RATE = 6.0
CAMERA_MIN_ZOOM = 0.5
CAMERA_MAX_ZOOM = 2.0
CAMERA_ZOOM_STEP = 0.5
SHAKE_MAGNITUDE = 6
SHAKE_DURATION = 0.25

COIN_RADIUS = 6
COIN_COUNT = 12

COLOR_BACKGROUND = (18, 20, 28)
COLOR_GRID = (30, 33, 44)
COLOR_PLAYER = (90, 200, 255)
COLOR_COIN = (255, 210, 60)
COLOR_TEXT = (235, 235, 235)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
