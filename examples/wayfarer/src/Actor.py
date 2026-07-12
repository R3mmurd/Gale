import pygame

from gale.animation import Animation

import settings


class Actor:
    """
    A character shared between the cutscenes and free-roam play: it
    has the .position gale.cutscene.MoveActor moves and the
    .animation gale.cutscene.SetActorAnimation switches, plus a
    velocity used only during free-roam play (untouched, and
    harmless, while a cutscene is driving .position directly).
    """

    def __init__(self, name: str, x: float, y: float, color) -> None:
        self.name = name
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.color = color
        self.radius = settings.ACTOR_RADIUS
        self.animation = Animation(["idle"])

    @property
    def pose(self) -> str:
        return self.animation.get_current_frame()

    def update(self, dt: float) -> None:
        self.animation.update(dt)
        self.position += self.velocity * dt

    def clamp_to_world(self) -> None:
        self.position.x = max(
            self.radius, min(settings.VIRTUAL_WIDTH - self.radius, self.position.x)
        )
        self.position.y = max(
            self.radius, min(settings.VIRTUAL_HEIGHT - self.radius, self.position.y)
        )

    def render(self, surface: pygame.Surface) -> None:
        position = (round(self.position.x), round(self.position.y))
        pygame.draw.circle(surface, self.color, position, self.radius)

        if self.pose != "idle":
            pygame.draw.circle(
                surface, settings.COLOR_POSE_MARKER, position, self.radius + 4, 1
            )

        settings.FONTS["small"].set_bold(False)
        text = settings.FONTS["small"].render(self.name, True, settings.COLOR_TEXT)
        rect = text.get_rect(center=(position[0], position[1] - self.radius - 10))
        surface.blit(text, rect)
