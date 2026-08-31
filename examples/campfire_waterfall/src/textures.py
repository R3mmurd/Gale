"""
make_soft_blob procedurally builds the small, soft radial-gradient
surface Campfire's smoke and Waterfall's spray hand to
gale.particle_system's set_textures -- no image file needed, any
plain pygame.Surface works as a particle texture, including one drawn
at startup. It's plain white so BLEND_RGBA_MULT tinting (which
Particle already applies per-particle from its own color) can recolor
it into smoke grey, water blue, or anything else, freely.
"""

import pygame


def make_soft_blob(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size / 2

    for radius in range(int(center), 0, -1):
        alpha = int(255 * (1 - radius / center) ** 1.5)
        pygame.draw.circle(surface, (255, 255, 255, alpha), (center, center), radius)

    return surface
