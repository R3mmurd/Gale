"""
Lantern: a small top-down exploration game built to exercise
gale.stencil — the room is covered in darkness except for a circle
around the player, punched out of the overlay every frame with a
Stencil. Every visual is drawn with pygame.draw primitives, so it
needs no image/font/sound assets to run.
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
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")

# Size we want to emulate
VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 240

# Size of our actual window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

PLAYER_RADIUS = 6
PLAYER_SPEED = 110

WALL_THICKNESS = 12

TORCH_RADIUS = 5
LIGHT_RADIUS_START = 36
LIGHT_RADIUS_STEP = 22
LIGHT_GROW_TIME = 0.6

EXIT_SIZE = 16

OVERLAY_ALPHA = 235

COLOR_BACKGROUND = (18, 20, 28)
COLOR_FLOOR = (54, 48, 40)
COLOR_WALL = (80, 72, 60)
COLOR_PLAYER = (90, 200, 255)
COLOR_TORCH = (255, 210, 60)
COLOR_EXIT = (120, 230, 140)
COLOR_OVERLAY = (5, 5, 8)
COLOR_TEXT = (235, 235, 235)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
