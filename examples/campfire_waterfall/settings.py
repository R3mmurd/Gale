"""
Campfire & Waterfall: a non-interactive ambient scene built to show
gale.particle_system's shapes/textures/combination in motion — a
campfire (sharp, shaped flame particles rising over soft, textured
smoke) and a waterfall (shaped-and-textured spray falling into a
splash at its base). Every visual is drawn with pygame.draw
primitives or procedurally generated textures, so it needs no
image/font/sound assets to run.
"""

import pygame

from gale import input_handler
from gale.particle_system import SHAPE_CIRCLE, SHAPE_DIAMOND, SHAPE_LINE, SHAPE_TRIANGLE

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")

TITLE = "Campfire & Waterfall"

# Size we want to emulate
VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 240

# Size of our actual window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480

COLOR_SKY_TOP = (12, 14, 28)
COLOR_SKY_BOTTOM = (26, 24, 40)
COLOR_GROUND = (36, 30, 26)
COLOR_LOG = (74, 46, 30)
COLOR_ROCK = (58, 58, 66)
COLOR_ROCK_SHADOW = (40, 40, 48)
COLOR_POOL = (24, 60, 82)

# --- Campfire -----------------------------------------------------------

CAMPFIRE_X = 110
CAMPFIRE_Y = 205

FLAME_SPAWN_INTERVAL = 0.05
FLAME_PARTICLES_PER_BURST = 3
FLAME_LIFE_TIME = (0.35, 0.6)
# ax1, ay1, ax2, ay2 -- mostly straight up (negative y is up), with a
# little horizontal jitter so the flame flickers instead of standing
# perfectly still.
#
# gale.particle_system.Particle.update() advances position by the raw
# per-frame velocity (self.x += self.vx), not velocity * dt, so a
# velocity/acceleration expressed in "pixels per second" ends up
# moving a particle roughly 1/dt (60, at 60 FPS) times further than
# that -- and since velocity itself is accumulated from acceleration
# every frame, total displacement over a burst's life_time actually
# grows with life_time squared. These acceleration values (here and
# below) are deliberately tiny to compensate; see
# examples/nightwatch and examples/outpost for the same convention
# with their own (much shorter-lived) particle bursts.
FLAME_ACCELERATION = (-1, -6, 1, -3)
FLAME_COLORS = [
    (255, 235, 120, 235),
    (255, 170, 60, 225),
    (255, 100, 40, 200),
]
FLAME_SPREAD = (4, 1)
FLAME_SHAPES = [SHAPE_TRIANGLE, SHAPE_DIAMOND]
FLAME_SIZE = (3, 7)
FLAME_ANGULAR_VELOCITY = (-160, 160)

SMOKE_SPAWN_INTERVAL = 0.18
SMOKE_PARTICLES_PER_BURST = 2
SMOKE_Y_OFFSET = 14  # smoke starts a little above the flame's own origin
SMOKE_LIFE_TIME = (1.4, 2.2)
# Even smaller than the flame's own -- smoke lives much longer, and
# the quadratic-in-life_time growth described above means a life_time
# roughly 4x as long needs an acceleration roughly 16x smaller to
# travel a comparable distance.
SMOKE_ACCELERATION = (-0.2, -0.6, 0.2, -0.3)
SMOKE_COLORS = [
    (170, 170, 180, 170),
    (120, 120, 132, 140),
    (80, 80, 92, 110),
]
SMOKE_SPREAD = (3, 1)
SMOKE_SIZE = (8, 16)
SMOKE_ANGULAR_VELOCITY = (-30, 30)
SMOKE_TEXTURE_SIZE = 16

# --- Waterfall ------------------------------------------------------------

WATERFALL_X = 300
WATERFALL_TOP_Y = 18
WATERFALL_BOTTOM_Y = 195
WATERFALL_WIDTH = 34

SPRAY_SPAWN_INTERVAL = 0.04
SPRAY_PARTICLES_PER_BURST = 4
SPRAY_LIFE_TIME = (0.45, 0.75)
# Gravity-dominated fall (positive y is down), with a little
# horizontal spread so the stream doesn't look like a single line.
# Tuned (see the note above FLAME_ACCELERATION) so a burst's total
# fall roughly covers WATERFALL_BOTTOM_Y - WATERFALL_TOP_Y by the end
# of its life_time, instead of shooting through the whole scene in a
# couple of frames.
SPRAY_ACCELERATION = (-1, 9, 1, 12)
SPRAY_COLORS = [
    (210, 235, 255, 190),
    (170, 215, 245, 170),
    (140, 195, 235, 150),
]
SPRAY_SPREAD = (WATERFALL_WIDTH / 4, 1)
SPRAY_SHAPES = [SHAPE_CIRCLE, SHAPE_LINE]
SPRAY_SIZE = (2, 5)
SPRAY_TEXTURE_SIZE = 6

SPLASH_SPAWN_INTERVAL = 0.12
SPLASH_PARTICLES_PER_BURST = 5
SPLASH_LIFE_TIME = (0.25, 0.45)
# A wide acceleration range: some droplets kick up and out before
# gravity pulls them back down, others fall away immediately --
# reads as a scatter of droplets bouncing off the pool's surface.
SPLASH_ACCELERATION = (-4, -6, 4, 10)
SPLASH_COLORS = [
    (235, 248, 255, 230),
    (200, 230, 250, 200),
]
SPLASH_SPREAD = (WATERFALL_WIDTH / 2, 1)
SPLASH_SIZE = (2, 4)

FONTS = {
    "small": pygame.font.Font(None, 16),
}
