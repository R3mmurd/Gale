"""
Wayfarer: a small top-down adventure built to exercise gale.sequence,
gale.cutscene, and gale.quest together -- an intro cutscene hands off
into free-roam play tracked by a quest log, and the quest's completion
hands off into a closing cutscene. Every visual is drawn with
pygame.draw primitives, so it needs no image/font/sound assets to run.
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
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "confirm")

# Size we want to emulate
VIRTUAL_WIDTH = 480
VIRTUAL_HEIGHT = 270

# Size of our actual window
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540

PLAYER_SPEED = 120
ACTOR_RADIUS = 9
INTERACT_RADIUS = 22

ELDER_POS = (240, 56)
HERO_INTRO_START = (240, 220)
HERO_MEET_ELDER = (240, 92)
HERO_PLAY_START = (240, 140)

HERB_POSITIONS = [(90, 170), (390, 190), (240, 230)]
WOLF_POS = (380, 70)
WOLF_RADIUS = 11

# A few decorative obstacles, drawn only -- no collision, keeping the
# world itself as simple as possible.
DECORATIONS = [
    pygame.Rect(30, 40, 60, 24),
    pygame.Rect(400, 40, 50, 20),
    pygame.Rect(20, 200, 40, 40),
    pygame.Rect(420, 210, 36, 36),
]

COLOR_BACKGROUND = (24, 32, 22)
COLOR_GROUND = (36, 48, 32)
COLOR_DECORATION = (54, 66, 46)
COLOR_HERO = (90, 200, 255)
COLOR_ELDER = (230, 200, 120)
COLOR_HERB = (110, 230, 120)
COLOR_WOLF = (200, 70, 70)
COLOR_TEXT = (235, 235, 235)
COLOR_QUEST_TITLE = (255, 210, 90)
COLOR_QUEST_DONE = (120, 230, 140)
COLOR_POSE_MARKER = (255, 240, 180)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
