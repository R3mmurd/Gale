"""
Planks: a small platformer built to exercise gale.tilemap — loading a
map exported from Tiled as JSON, one-way platform/solid collision via
move_and_collide, object-layer spawns, and gale.camera scrolling
across a level wider than the viewport. The tileset image is the only
asset (three small hand-drawn tiles); everything else is drawn with
pygame.draw primitives.
"""

import pathlib

import pygame

from gale import input_handler

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "jump")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "jump")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "jump")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")

BASE_DIR = pathlib.Path(__file__).parent

# Size we want to emulate
VIRTUAL_WIDTH = 320
VIRTUAL_HEIGHT = 192

# Size of our actual window
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 576

LEVEL_PATH = str(BASE_DIR / "assets" / "tilemaps" / "level.json")

PLAYER_WIDTH = 12
PLAYER_HEIGHT = 14
PLAYER_SPEED = 110
GRAVITY = 900
JUMP_SPEED = -300
MAX_FALL_SPEED = 500

CAMERA_FOLLOW_RATE = 8.0

COLOR_BACKGROUND = (110, 165, 220)
COLOR_PLAYER = (230, 60, 60)
COLOR_COIN = (255, 210, 60)
COLOR_GOAL = (120, 230, 140)
COLOR_TEXT = (20, 20, 25)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
