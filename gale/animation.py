"""
This file contains the implementation of the class Animation.

Author: Alejandro Mujica (aledrums@gmail.com)
"""
from typing import Sequence, Optional, Any


class Animation:
    """
    This class represents animations as a sequence of frames. Those
    frames change in a given time interval.
    """

    def __init__(
        self,
        frames: Sequence[Any],
        time_interval: float = 0,
        loops: Optional[int] = None,
        on_finish: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Initialize a new Animation.

        :param frames: Sequence of frames
        :param time_interval: Duration time (in seconds) of each frame.
        :param loops: Number of times that this animation shall execute. The default value is None to execute infinitely.
        :param on_finish: Callback to do something after finish loops. The default value is an empty lambda.
        """
        self.frames: Sequence[Any] = frames
        self.interval: float = time_interval
        self.loops: Optional[int] = loops
        self.size: int = len(self.frames)
        self.timer: float = 0
        self.times_played: int = 0
        self.current_frame_index: int = 0
        self.on_finish: Callable[[], None] = (
            (lambda: None) if on_finish is None else on_finish
        )

    def reset(self) -> None:
        """
        Set the animation on its initial values.
        """
        self.times_played = 0
        self.timer = 0
        self.current_frame = 0

    def update(self, dt: float) -> None:
        """
        This function updates the animation timer to check whether the frame
        should be changed or not. If the animation has only one frame or
        it has executed the number of times defined by loops, then
        this operation does not execute.
        """
        if self.size <= 1 or (
            self.loops is not None and self.times_played > self.loops
        ):
            return

        self.timer += dt

        if self.timer >= self.interval:
            self.timer %= self.interval
            self.current_frame_index = (self.current_frame_index + 1) % self.size

            # Only increments times played if there is a value for loops.
            if self.current_frame_index == 0 and self.loops is not None:
                self.times_played += 1

                if self.times_played > self.loops:
                    # Setting the last frame if loops was completed
                    self.current_frame_index = len(self.frames) - 1
                    # Animation fulfilled invoking callback, if exist
                    self.on_finish()

    def get_current_frame(self) -> Any:
        """
        :returns: The current frame of the animation.
        """
        return self.frames[self.current_frame_index]
