"""
This file contains the implementation of the class Text.

Author: Alejandro Mujica (aledrums@gmail.com)
"""
from typing import Optional

import pygame

def render_text(surface: pygame.Surface, text: str, font: pygame.font.Font, x: float, y: float,
                color: pygame.Color, bgcolor: Optional[pygame.Color]=None,
                center: bool=False, shadowed: bool=False):
    text_obj: pygame.Surface = font.render(text, True, color, bgcolor)
    text_rect: pygame.Rect = text_obj.get_rect()

    if center:
        text_rect.center = (x, y)
    else:
        text_rect.x = x
        text_rect.y = y

    if shadowed:
        shadow_text: pygame.Surface = font.render(text, True, (0, 0, 0))
        shadow_rect: pygame.Rect = shadow_text.get_rect()
        shadow_rect.x =  text_rect.x + 1
        shadow_rect.y =  text_rect.y + 1
        surface.blit(shadow_text, shadow_rect)

    surface.blit(text_obj, text_rect)


class Text:
    def __init__(self, text_str: str, font: pygame.font.Font, x: float, y: float,
                 color: pygame.Color, bgcolor: Optional[pygame.Color]=None,
                 center: bool=False, shadowed: bool=False):
        self.text_str = text_str
        self.font: pygame.font.Font = font
        self.text: pygame.Surface = font.render(self.text_str, True, color, bgcolor)
        self.rect: pygame.Rect = self.text.get_rect()
        self.x: float = x
        self.y: float = y
        self.center: bool = center
        self.shadowed: bool = shadowed
        if self.shadowed:
            self.shadow_text: pygame.Surface = font.render(self.text_str, True, (0, 0, 0))
    
    def render(self, surface: pygame.Surface) -> None:
        if self.center:
            self.rect.center = (self.x, self.y)
        else:
            self.rect.x = self.x
            self.rect.y = self.y
        
        if self.shadowed:
            shadow_rect = self.shadow_text.get_rect()
            shadow_rect.x =  self.rect.x + 1
            shadow_rect.y =  self.rect.y + 1
            surface.blit(self.shadow_text, shadow_rect)

        surface.blit(self.text, self.rect)
