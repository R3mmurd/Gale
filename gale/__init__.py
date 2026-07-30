"""
gale: a collection of reusable building blocks (state machines, input
handling, physics, networking, UI, AI, and more) to speed up building
2D games with pygame. Each submodule (gale.state, gale.input_handler,
gale.physics, gale.net, gale.ui, gale.ai, ...) is independent — import
only the ones a given game actually needs.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import pygame

# A project's settings.py commonly builds TEXTURES/FONTS/SOUNDS at
# import time (pygame.image.load/pygame.font.Font/pygame.mixer.Sound),
# which needs pygame's font/mixer/display subsystems already
# initialized. Rather than relying on every settings.py -- or whatever
# happens to import it first, directly or through some other project
# module -- to get that ordering right on its own, guarantee it here:
# importing anything under the gale package (which any code reaching
# gale.conf.settings/gale.game/etc. already does) always runs this
# module first. pygame.init() is idempotent (safe to call again
# wherever gale.game also calls it) and never raises on its own if a
# subsystem isn't available (no display, no audio device); it only
# degrades that one subsystem silently.
pygame.init()
