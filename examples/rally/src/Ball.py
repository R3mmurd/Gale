import random

import pygame

import settings


class Ball:
    def __init__(self) -> None:
        self.size: float = settings.BALL_SIZE
        self.x: float = 0.0
        self.y: float = 0.0
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.reset()

    def reset(self, direction: int = 1) -> None:
        self.x = settings.VIRTUAL_WIDTH / 2 - self.size / 2
        self.y = settings.VIRTUAL_HEIGHT / 2 - self.size / 2
        angle = random.uniform(-0.4, 0.4)
        self.vx = direction * settings.BALL_SPEED * (1 if abs(angle) < 1 else -1)
        self.vy = settings.BALL_SPEED * angle

    def update(self, dt: float, left_paddle, right_paddle) -> int:
        """
        Advance the ball one step. Only meant to be called by the host,
        which is authoritative for the simulation.

        :returns: 0 if nobody scored, 1 if the left player scored, 2 if the right player did.
        """
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y <= 0:
            self.y = 0
            self.vy = abs(self.vy)
        elif self.y + self.size >= settings.VIRTUAL_HEIGHT:
            self.y = settings.VIRTUAL_HEIGHT - self.size
            self.vy = -abs(self.vy)

        ball_rect = self.get_rect()

        if self.vx < 0 and ball_rect.colliderect(left_paddle.get_rect()):
            self.x = left_paddle.get_rect().right
            self.vx = abs(self.vx) * 1.05
        elif self.vx > 0 and ball_rect.colliderect(right_paddle.get_rect()):
            self.x = right_paddle.get_rect().left - self.size
            self.vx = -abs(self.vx) * 1.05

        if self.x + self.size < 0:
            return 2

        if self.x > settings.VIRTUAL_WIDTH:
            return 1

        return 0

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.size), int(self.size))

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, settings.COLOR_BALL, self.get_rect())
