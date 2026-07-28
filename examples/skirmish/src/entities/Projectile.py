import pygame

import settings
from src import level


class Projectile:
    """
    A fired shot: a straight, fast "bullet" (from a Guard, aimed with
    gale.ai.targeting.predict_intercept_time) or a slower, arcing
    "grenade" (from the Captain, aimed with
    gale.ai.targeting.iterative_targeting_angle and affected by
    gravity every update, the same per-step formula
    gale.ai.targeting.simulate_drag_trajectory uses to precompute a
    trajectory, just applied live one frame at a time here).
    """

    def __init__(
        self, kind: str, position: pygame.Vector2, velocity: pygame.Vector2
    ) -> None:
        """
        :param kind: Either "bullet" or "grenade".
        :param position: Starting position.
        :param velocity: Starting velocity.
        """
        self.kind: str = kind
        self.position: pygame.Vector2 = pygame.Vector2(position)
        self.velocity: pygame.Vector2 = pygame.Vector2(velocity)
        self.radius: float = (
            settings.BULLET_RADIUS if kind == "bullet" else settings.GRENADE_RADIUS
        )
        self.blast_radius: float = (
            self.radius if kind == "bullet" else settings.GRENADE_BLAST_RADIUS
        )
        self.age: float = 0.0
        self.alive: bool = True

    def update(self, dt: float) -> None:
        if self.kind == "grenade":
            self.velocity += settings.GRENADE_GRAVITY * dt

        self.position += self.velocity * dt
        self.age += dt

        if not level.BOUNDS.collidepoint(self.position) or level.blocked_by_obstacle(
            tuple(self.position)
        ):
            self.alive = False
        elif self.kind == "grenade" and self.age > 3.0:
            self.alive = False

    def hits(self, position: pygame.Vector2, radius: float) -> bool:
        """
        :param position: Center of whoever might be hit.
        :param radius: Their radius.
        :returns: Whether this projectile is within its blast radius of position.
        """
        return (self.position - position).length() <= self.blast_radius + radius

    def render(self, surface: pygame.Surface) -> None:
        color = (
            settings.COLOR_BULLET if self.kind == "bullet" else settings.COLOR_GRENADE
        )
        pygame.draw.circle(
            surface, color, (int(self.position.x), int(self.position.y)), self.radius
        )
