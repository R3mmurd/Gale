"""
This file contains the implementation of the class Text.

Author: Alejandro Mujica (aledrums@gmail.com)
"""


def render_text(surface, text, font, x, y, color,
                bgcolor=None, center=False, shadowed=False):
    text_obj = font.render(text, True, color, bgcolor)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.x = x
        text_rect.y = y

    if shadowed:
        shadow_text = font.render(text, True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect()
        shadow_rect.x =  text_rect.x + 1
        shadow_rect.y =  text_rect.y + 1
        surface.blit(shadow_text, shadow_rect)

    surface.blit(text_obj, text_rect)


class Text:
    def __init__(self, text_str, font, x, y, color,
                 bgcolor=None, center=False, shadowed=False):
        self.text_str = text_str
        self.font = font
        self.text = font.render(self.text_str, True, color, bgcolor)
        self.rect = self.text.get_rect()
        self.x = x
        self.y = y
        self.center = center
        self.shadowed = shadowed
        if self.shadowed:
            self.shadow_text = font.render(self.text_str, True, (0, 0, 0))
    
    def render(self, surface):
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



