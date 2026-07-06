"""
Hillclimb: a small physics-vehicle demo built to exercise gale.physics's
joints — a chassis and two wheels connected by wheel joints (motorized,
with a spring/damper suspension), driving over bumpy static terrain.
Every visual is drawn with pygame.draw primitives, so it needs no
image/font/sound assets to run.
"""

import pygame

from gale import input_handler

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "accelerate")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "accelerate")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "reverse")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "reverse")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")

# Size we want to emulate
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 200

# Size of our actual window
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 300

GRAVITY = (0, 900)

# Terrain is a chain of static polygon segments following this curve
# (a sum of two sine waves), sampled every TERRAIN_STEP pixels.
TERRAIN_BASE_Y = 150
TERRAIN_AMPLITUDE_1 = 18
TERRAIN_FREQUENCY_1 = 0.02
TERRAIN_AMPLITUDE_2 = 8
TERRAIN_FREQUENCY_2 = 0.05
TERRAIN_STEP = 20
TERRAIN_FRICTION = 1.0

CHASSIS_WIDTH = 70
CHASSIS_HEIGHT = 22
CHASSIS_START_X = 60

WHEEL_RADIUS = 14
WHEEL_OFFSET_X = 24
WHEEL_OFFSET_Y = 14
WHEEL_FRICTION = 1.5

SUSPENSION_FREQUENCY = 4.0
SUSPENSION_DAMPING = 0.7
MOTOR_SPEED = 24.0
MOTOR_TORQUE = 3500

# Reaching this x position, or tipping past this angle, ends the run.
GOAL_X = VIRTUAL_WIDTH - 40
FLIP_ANGLE = 2.5

COLOR_BACKGROUND = (18, 22, 30)
COLOR_TERRAIN = (95, 98, 112)
COLOR_CHASSIS = (90, 200, 255)
COLOR_WHEEL = (40, 44, 54)
COLOR_WHEEL_MARK = (200, 200, 200)
COLOR_GOAL = (255, 210, 60)
COLOR_TEXT = (235, 235, 235)

pygame.font.init()
FONTS = {
    "small": pygame.font.Font(None, 16),
    "medium": pygame.font.Font(None, 24),
    "large": pygame.font.Font(None, 40),
}


def terrain_height(x: float) -> float:
    import math

    return (
        TERRAIN_BASE_Y
        - TERRAIN_AMPLITUDE_1 * math.sin(x * TERRAIN_FREQUENCY_1)
        - TERRAIN_AMPLITUDE_2 * math.sin(x * TERRAIN_FREQUENCY_2 + 1.3)
    )
