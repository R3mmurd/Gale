"""
gale.camera: a 2D scrolling/zooming camera. pygame has no GPU
transform stack to push a matrix onto, so a Camera instead turns
world coordinates into screen ones for you to blit with.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math
import random
from typing import Optional, Tuple

import pygame


class Camera:
    """
    Usage example:

        camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        camera.follow(player, rate=6.0)  # smoothly, rather than snapping every frame
        camera.bounds = pygame.Rect(0, 0, world_width, world_height)

        # In your state:
        def update(self, dt):
            camera.update(dt)

        def render(self, surface):
            for entity in entities:
                surface.blit(entity.image, camera.apply(entity.rect))

    x/y are the world point the camera is centered on — set directly
    for a snap-cut (a new room, a teleport), or drive with follow()
    for it to track a moving target on its own every update().
    """

    def __init__(
        self,
        viewport_width: float,
        viewport_height: float,
        x: float = 0.0,
        y: float = 0.0,
        zoom: float = 1.0,
        bounds: Optional[pygame.Rect] = None,
    ) -> None:
        """
        :param viewport_width: The width of the surface this camera is applied for (typically your virtual/game surface, not the real window).
        :param viewport_height: The height of that surface.
        :param x: The world x-coordinate the camera starts centered on. The default value is 0.0.
        :param y: The world y-coordinate the camera starts centered on. The default value is 0.0.
        :param zoom: A scale factor: > 1.0 zooms in, < 1.0 zooms out. The default value is 1.0.
        :param bounds: A world-space rect the camera's view never scrolls past, clamping x/y accordingly every update(). The default value is None, meaning unbounded scrolling.
        """
        self.viewport_width: float = viewport_width
        self.viewport_height: float = viewport_height
        self.x: float = x
        self.y: float = y
        self.zoom: float = zoom
        self.bounds: Optional[pygame.Rect] = bounds

        self._target = None
        self._follow_rate: Optional[float] = None

        self._shake_duration: float = 0.0
        self._shake_time_left: float = 0.0
        self._shake_magnitude: float = 0.0
        self._shake_offset: Tuple[float, float] = (0.0, 0.0)

    def follow(self, target, rate: Optional[float] = None) -> None:
        """
        :param target: Any object with x/y attributes (e.g. a gale.physics.Node, or your own player/sprite) to track every update(). Read once per update() call, so moving the target elsewhere works with no extra wiring.
        :param rate: How fast the camera catches up to the target, in roughly "fraction closed per second" (a higher rate is snappier; something like 4.0-10.0 reads as a smooth follow). The default value is None, snapping to the target's position exactly every update() instead (no smoothing).
        """
        self._target = target
        self._follow_rate = rate

    def unfollow(self) -> None:
        """
        Stop tracking whatever target was passed to follow(), if any. x/y stay wherever they last were and are no longer moved automatically.
        """
        self._target = None
        self._follow_rate = None

    def shake(self, magnitude: float, duration: float) -> None:
        """
        Start a screen shake: a random offset, in world units, applied
        on top of x/y, its magnitude decaying linearly to 0 over
        duration seconds. Calling this again while a shake is already
        running replaces it (they don't stack).

        :param magnitude: The maximum offset, in world units, at the very start of the shake.
        :param duration: How long, in seconds, the shake lasts.
        """
        self._shake_magnitude = magnitude
        self._shake_duration = duration
        self._shake_time_left = duration

    def update(self, dt: float) -> None:
        if self._target is not None:
            self._follow_target(dt)

        self._update_shake(dt)

        if self.bounds is not None:
            self._clamp_to_bounds()

    def _follow_target(self, dt: float) -> None:
        target_x = self._target.x
        target_y = self._target.y

        if self._follow_rate is None:
            self.x, self.y = target_x, target_y
            return

        # Frame-rate-independent exponential smoothing: closes the same
        # fraction of the remaining distance regardless of dt's size.
        factor = 1.0 - math.exp(-self._follow_rate * dt)
        self.x += (target_x - self.x) * factor
        self.y += (target_y - self.y) * factor

    def _update_shake(self, dt: float) -> None:
        if self._shake_time_left <= 0.0:
            self._shake_offset = (0.0, 0.0)
            return

        self._shake_time_left = max(0.0, self._shake_time_left - dt)
        magnitude = self._shake_magnitude * (
            self._shake_time_left / self._shake_duration
        )
        self._shake_offset = (
            random.uniform(-magnitude, magnitude),
            random.uniform(-magnitude, magnitude),
        )

    def _clamp_to_bounds(self) -> None:
        half_width = self.viewport_width / (2 * self.zoom)
        half_height = self.viewport_height / (2 * self.zoom)
        self.x = _clamp_to_span(self.x, self.bounds.left, self.bounds.right, half_width)
        self.y = _clamp_to_span(
            self.y, self.bounds.top, self.bounds.bottom, half_height
        )

    @property
    def offset(self) -> Tuple[float, float]:
        """
        :returns: The world coordinate of the visible viewport's top-left corner, shake included.
        """
        shake_x, shake_y = self._shake_offset
        return (
            self.x - self.viewport_width / (2 * self.zoom) + shake_x,
            self.y - self.viewport_height / (2 * self.zoom) + shake_y,
        )

    def world_to_screen(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        :param point: A point in world coordinates.
        :returns: Where that point falls on screen, given this camera's current position/zoom.
        """
        offset_x, offset_y = self.offset
        world_x, world_y = point
        return ((world_x - offset_x) * self.zoom, (world_y - offset_y) * self.zoom)

    def screen_to_world(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """
        :param point: A point in screen coordinates (e.g. a rescaled mouse position).
        :returns: The world coordinate under that screen point — the inverse of world_to_screen, for turning a click into "what world entity is under the mouse".
        """
        offset_x, offset_y = self.offset
        screen_x, screen_y = point
        return (screen_x / self.zoom + offset_x, screen_y / self.zoom + offset_y)

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """
        :param rect: A world-space rect (typically an entity's own rect, at its current world position/size).
        :returns: The rect to actually blit at (or otherwise draw), translated and scaled for this camera's current position/zoom.
        """
        x, y = self.world_to_screen((rect.x, rect.y))
        return pygame.Rect(
            round(x),
            round(y),
            round(rect.width * self.zoom),
            round(rect.height * self.zoom),
        )


def _clamp_to_span(value: float, low: float, high: float, half_extent: float) -> float:
    min_value = low + half_extent
    max_value = high - half_extent

    if min_value > max_value:
        # The bounds are narrower than the viewport: center on them
        # instead of clamping to an inverted [max, min] range.
        return (low + high) / 2

    return min(max(value, min_value), max_value)
