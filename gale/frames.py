"""
This file contains a function to generate frames from a spritesheets
(a texture with multiple sprites).

Author: Alejandro Mujica
"""

from typing import List

import pygame


def generate_frames(
    spritesheet: pygame.Surface, sprite_width: int, sprite_height: int
) -> List[pygame.Rect]:
    """
    Given a spritesheet, this functions builds a list of frames
    based on the spritesheet dimensions, the width of each sprite,
    and the height of each sprite.

    :param spritesheed: surface with the texture.
    :param sprite_width: width of the sprite.
    :param sprite_height: height of the sprite.
    """
    w, h = spritesheet.get_size()

    num_cols: int = w // sprite_width
    num_rows: int = h // sprite_height

    frames: List[pygame.Rect] = []

    for i in range(num_rows):
        for j in range(num_cols):
            frames.append(
                pygame.Rect(
                    j * sprite_width,  # x position
                    i * sprite_height,  # y position,
                    sprite_width,
                    sprite_height,
                )
            )
    return frames
