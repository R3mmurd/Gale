import pygame

import settings


class FlyingSaucer:
    def __init__(self, x: float, y: float) -> None:
        self.width, self.height = settings.TEXTURES['ufo'].get_size()
        self.position = pygame.Vector2(x - self.width / 2, y - self.height / 2)
        self.velocity = pygame.Vector2(0, 0)
        self.movement_direction = pygame.Vector2(0, 0)

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.position.x + 5, self.position.y - 10, self.width - 10, 22)
    
    def accelerate(self, x: float, y: float) -> None:
        self.movement_direction.x = x
        self.movement_direction.y = y
    
    def __limit_boundaries(self):
        if not (0 < self.position.x < settings.VIRTUAL_WIDTH - self.width):
            self.position.x = max(0, min(self.position.x, settings.VIRTUAL_WIDTH - self.width))
            self.velocity.x = 0

        if not (0 < self.position.y < settings.VIRTUAL_HEIGHT - self.height):            
            self.position.y = max(0, min(self.position.y, settings.VIRTUAL_HEIGHT - self.height))
            self.velocity.y = 0

    def update(self, dt: float) -> None:
        if self.movement_direction.length() > 1:
            self.movement_direction.normalize_ip()
        
        acceleration = self.movement_direction * 200
        dv = acceleration * dt
        v0 = self.velocity
        v1 = self.velocity + dv
        movement = (v0 + v1) * dt * 0.5
        self.position += movement
        self.velocity = v1
        self.__limit_boundaries()

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES['ufo'], self.position)
