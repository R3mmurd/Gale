"""
This file contains generate_frames, slicing a spritesheet (one image
holding a regular grid of same-sized sprites, optionally with a margin
around it and/or spacing between sprites) into the list of
pygame.Rects each individual sprite occupies within it.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import List

import pygame


def generate_frames(
    spritesheet: pygame.Surface,
    sprite_width: int,
    sprite_height: int,
    margin: int = 0,
    spacing: int = 0,
) -> List[pygame.Rect]:
    """
    Given a spritesheet, this functions builds a list of frames
    based on the spritesheet dimensions, the width of each sprite,
    and the height of each sprite.

    :param spritesheed: surface with the texture.
    :param sprite_width: width of the sprite.
    :param sprite_height: height of the sprite.
    :param margin: Empty pixels around the whole spritesheet, before the first row/column of sprites. The default value is 0. Matches the "margin" a tileset exported from Tiled (https://www.mapeditor.org/) may have.
    :param spacing: Empty pixels between adjacent sprites, both horizontally and vertically. The default value is 0. Matches the "spacing" a tileset exported from Tiled may have.
    """
    w, h = spritesheet.get_size()

    num_cols: int = (w - 2 * margin + spacing) // (sprite_width + spacing)
    num_rows: int = (h - 2 * margin + spacing) // (sprite_height + spacing)

    frames: List[pygame.Rect] = []

    for i in range(num_rows):
        for j in range(num_cols):
            frames.append(
                pygame.Rect(
                    margin + j * (sprite_width + spacing),  # x position
                    margin + i * (sprite_height + spacing),  # y position,
                    sprite_width,
                    sprite_height,
                )
            )
    return frames
