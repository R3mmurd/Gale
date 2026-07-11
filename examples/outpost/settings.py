"""
Outpost: a small isometric "Commandos"-style stealth prototype built to
exercise gale.tilemap.isometric (IsometricTileMap), gale.ai.perception
(VisionCone/Perception/AlertLevel), gale.state.HierarchicalState (a
guard's patrol/search/alert HFSM), and gale.ai.minimax (the terminal
minigame's defense AI). No image/font/sound assets are needed: the
isometric tileset is three small diamonds drawn in code with
pygame.draw, and every other visual is drawn with pygame.draw
primitives too.
"""

import math

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
input_handler.InputHandler.set_keyboard_action(
    input_handler.KEY_r, "restart", modifiers=input_handler.MOD_CTRL
)

# Size we want to emulate
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 480

# Size of our actual window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 768

# --- Isometric grid ------------------------------------------------------

GRID_COLS = 12
GRID_ROWS = 10
TILE_WIDTH = 48
TILE_HEIGHT = 24

# Where the map's pixel origin (row 0, col 0's top vertex) is placed on
# the virtual screen, leaving room above/below for the HUD text.
MAP_OFFSET = (136, 84)

# Movement/collision/perception logic (Player, Guard, level.OBSTACLES,
# the NavGraph...) all happen in a plain cartesian "world space" measured
# in these units per grid cell, exactly like a regular (non-isometric)
# top-down game would use pixels -- only rendering projects a world
# position through cartesian_to_isometric (see level.to_screen). Keeping world units
# reasonably large (rather than using the 0..12 grid coordinates
# directly) matters because both pygame.Rect and
# gale.ai.perception.has_line_of_sight truncate coordinates to ints
# internally, which would destroy precision at a tiny 0..12 scale.
CELL_SIZE = 40  # world units per grid cell

# --- Player ---------------------------------------------------------------

PLAYER_SPEED = 88  # world units per second
PLAYER_RADIUS = 11  # world units

# --- Guards -----------------------------------------------------------------

GUARD_PATROL_SPEED = 40
GUARD_SEARCH_SPEED = 64
GUARD_RADIUS = 12
CATCH_RADIUS = 22

VISION_RANGE_NEAR = 64
VISION_RANGE_FAR = 168
VISION_HALF_ANGLE = math.radians(32)

PERCEPTION_DECAY_RATE = 0.25
PERCEPTION_SUSPICIOUS_THRESHOLD = 0.35
PERCEPTION_ALERTED_THRESHOLD = 1.0

LOOK_AROUND_DURATION = 1.6
LOOK_AROUND_ROTATION_SPEED = 1.8  # radians per second

# How far, in world units, obstacles are inflated (and nav graph corners
# pushed out) so guards keep some clearance from walls.
NAV_CLEARANCE = 14

# --- Colors --------------------------------------------------------------

COLOR_BACKGROUND = (14, 16, 22)
COLOR_FLOOR = (72, 82, 78)
COLOR_FLOOR_EDGE = (52, 60, 58)
COLOR_WALL = (86, 70, 62)
COLOR_WALL_EDGE = (54, 44, 40)
COLOR_TERMINAL_TILE = (70, 110, 130)
COLOR_TERMINAL_EDGE = (140, 200, 230)
COLOR_PLAYER = (90, 200, 255)
COLOR_GUARD_PATROL = (210, 90, 90)
COLOR_GUARD_SUSPICIOUS = (240, 190, 60)
COLOR_GUARD_ALERTED = (255, 90, 60)
COLOR_VISION_CONE = (255, 255, 255)
COLOR_NAV_EDGE = (55, 60, 75)
COLOR_TEXT = (235, 235, 235)
COLOR_ALERT_TEXT = (255, 90, 90)
COLOR_GOOD_TEXT = (140, 230, 160)

# No custom font file needed for this demo, just pygame's built-in default.
pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}
