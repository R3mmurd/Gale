"""
Leap: a small platformer built to exercise gale.physics's three body
types together — static ground, a dynamic player, and a kinematic
moving platform bridging a gap. Every visual is drawn with pygame.draw
primitives, so it needs no image/font/sound assets to run.
"""

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

# Size we want to emulate
VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 240

# Size of our actual window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

GRAVITY = (0, 900)

PLAYER_SIZE = 16
PLAYER_SPEED = 120
PLAYER_JUMP_IMPULSE = 260

GROUND_HEIGHT = 20
GROUND_LEFT_WIDTH = 120
GROUND_RIGHT_WIDTH = 120
GAP_WIDTH = VIRTUAL_WIDTH - GROUND_LEFT_WIDTH - GROUND_RIGHT_WIDTH

PLATFORM_WIDTH = 50
PLATFORM_HEIGHT = 10
PLATFORM_SPEED = 40
# The platform oscillates between these two x positions (its center),
# ferrying the player across the gap between the two ground segments.
PLATFORM_MIN_X = GROUND_LEFT_WIDTH + PLATFORM_WIDTH / 2 - 5
PLATFORM_MAX_X = VIRTUAL_WIDTH - GROUND_RIGHT_WIDTH - PLATFORM_WIDTH / 2 + 5

GOAL_RADIUS = 10

COLOR_BACKGROUND = (18, 20, 28)
COLOR_GROUND = (95, 98, 112)
COLOR_PLAYER = (90, 200, 255)
COLOR_PLATFORM = (200, 140, 90)
COLOR_GOAL = (255, 210, 60)
COLOR_TEXT = (235, 235, 235)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
