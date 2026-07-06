"""
Nightwatch: a small top-down stealth demo built to exercise gale.ai
(steering, behavior tree, decision tree, blackboard, graphs/search) on
top of the rest of gale (game, state, input_handler, particle_system,
timer, text, factory). Every visual is drawn with pygame.draw
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
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")
# A key combo (Ctrl+R) to restart, alongside the plain-key bindings above.
input_handler.InputHandler.set_keyboard_action(
    input_handler.KEY_r, "restart", modifiers=input_handler.MOD_CTRL
)

# Size we want to emulate
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 360

# Size of our actual window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

PLAYER_SPEED = 140
PLAYER_RADIUS = 8
CATCH_RADIUS = 14

GUARD_PATROL_SPEED = 90
GUARD_CHASE_SPEED = 130
GUARD_RADIUS = 10
GUARD_SIGHT_RADIUS = 120
GUARD_LOSE_INTEREST_TIME = 3.0

CIVILIAN_SPEED = 70
CIVILIAN_FLEE_SPEED = 120
CIVILIAN_RADIUS = 8
CIVILIAN_FLEE_RADIUS = 90

# How far obstacles are inflated (and nav graph corners pushed out) so
# agents keep some clearance from walls instead of grazing corners.
NAV_CLEARANCE = 16

COLOR_BACKGROUND = (18, 20, 28)
COLOR_WALL = (95, 98, 112)
COLOR_EXIT = (230, 200, 60)
COLOR_PLAYER = (90, 200, 255)
COLOR_GUARD_PATROL = (210, 90, 90)
COLOR_GUARD_ALERT = (255, 210, 60)
COLOR_CIVILIAN = (120, 220, 130)
COLOR_NAV_EDGE = (55, 60, 75)
COLOR_TEXT = (235, 235, 235)
COLOR_ALERT_TEXT = (255, 90, 90)

# No custom font file needed for this demo, just pygame's built-in default.
pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
