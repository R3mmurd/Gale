"""
This file contains the implementation of a mixins to animable game objects.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any

from gale.animation import Animation


class AnimableMixin:
    """
    This mixin requires that derivated classes have the following attributes:
        - animations: dict[str, Animation]
        - current_animation: Animation
    """

    def generate_animations(self, animation_defs: dict[str, dict[str, Any]]) -> None:
        """
        Generate animations from a dictionary of definitions.

        :param animation_defs: Dictionary of definitions.
        """
        for animation_id, definition in animation_defs.items():
            self.animations[animation_id] = Animation(
                frames=definition["frames"],
                time_interval=definition.get(
                    "time_interval", 0
                ),  # Given interval or zero
                loops=definition.get("loops"),  # Given loops or None
                on_finish=definition.get("on_finish"),  # Given callable or None
            )

    def change_animation(self, animation_id: str) -> None:
        new_animation = self.animations.get(animation_id)
        if new_animation is not None and new_animation != self.current_animation:
            self.current_animation = new_animation
            self.current_animation.reset()
            self.frame_index = self.current_animation

    def update(self, dt: float) -> None:
        self.current_animation.update(dt)
        self.frame_index = self.current_animation.get_current_frame()
