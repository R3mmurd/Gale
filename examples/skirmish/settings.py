"""
Skirmish: a small squad-tactics demo built to exercise the rest of
gale.ai (fuzzy logic, learning, targeting, formations, Markov chains,
GOAP, rules, data-driven scripting, tactical influence maps, and the
remaining steering behaviors/combinators) on top of gale.ai.agent,
gale.ai.blackboard, and gale.ai.graph/search, which examples/nightwatch
already covers. Every visual is drawn with pygame.draw primitives, so
it needs no image/font/sound assets to run.
"""

import pygame

from gale import input_handler

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
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_s, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")
input_handler.InputHandler.set_keyboard_action(
    input_handler.KEY_r, "restart", modifiers=input_handler.MOD_CTRL
)

TITLE = "Skirmish"

# Size we want to emulate
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 450

# Size of our actual window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

SQUAD_LEADER_SPEED = 130
SQUAD_MEMBER_RADIUS = 8
SQUAD_HITS_TO_LOSE = 3

GUARD_SPEED = 90
GUARD_RADIUS = 9
GUARD_SIGHT_RADIUS = 180
GUARD_FIRE_COOLDOWN = 1.4
GUARD_FIRE_RANGE = 220
BULLET_SPEED = 260
BULLET_RADIUS = 3

CAPTAIN_RADIUS = 11
GRENADE_SPEED = 220
GRENADE_GRAVITY = pygame.Vector2(0, 260)
GRENADE_RADIUS = 5
GRENADE_BLAST_RADIUS = 40
GOAP_COOLDOWN = 6.0

# How far obstacles are inflated (and nav graph corners pushed out) so
# agents keep some clearance from walls instead of grazing corners.
NAV_CLEARANCE = 16

INFLUENCE_CELL_SIZE = 40
INFLUENCE_RADIUS = 160

COLOR_BACKGROUND = (18, 20, 28)
COLOR_WALL = (95, 98, 112)
COLOR_EXTRACTION = (230, 200, 60)
COLOR_LEADER = (90, 200, 255)
COLOR_MEMBER = (140, 210, 255)
COLOR_GUARD_CALM = (150, 150, 160)
COLOR_GUARD_ALERT = (230, 90, 90)
COLOR_CAPTAIN = (230, 150, 60)
COLOR_BULLET = (255, 230, 140)
COLOR_GRENADE = (255, 140, 60)
COLOR_NAV_EDGE = (55, 60, 75)
COLOR_TEXT = (235, 235, 235)
COLOR_ALERT_TEXT = (255, 90, 90)

FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
