"""
This file contains the implementation of the class Animation.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Sequence, Optional


class Animation:
    """
    This class represents animations as a sequence of frames. Those
    frames change in a given time interval.
    """

    def __init__(
        self,
        frames: Sequence[any],
        time_interval: float = 0,
        loops: Optional[int] = None,
        on_finish: Optional[callable] = None,
    ) -> None:
        """
        Initialize a new Animation.

        :param frames: Sequence of frames
        :param time_interval: Duration time (in seconds) of each frame.
        :param loops: Number of times that this animation shall execute. The default value is None to execute infinitely.
        :param on_finish: Callback to do something after finish loops. The default value is an empty lambda.
        """
        self.__frames: Sequence[any] = frames
        self.__interval: float = time_interval
        self.__loops: Optional[int] = loops
        self.__size: int = len(self.__frames)
        self.__timer: float = 0
        self.__times_played: int = 0
        self.__current_frame_index: int = 0
        self.__on_finish: callable = (lambda: None) if on_finish is None else on_finish

    def reset(self) -> None:
        """
        Set the animation on its initial values.
        """
        self.__times_played = 0
        self.__timer = 0
        self.__current_frame_index = 0

    def update(self, dt: float) -> None:
        """
        This function updates the animation timer to check whether the frame
        should be changed or not. If the animation has only one frame, or
        it has executed the number of times defined by loops, then
        this operation does not execute.

        :param dt: Time elapsed (in seconds) since the last time this function has been executed.
        """
        if self.__size <= 1 or (
            self.__loops is not None and self.__times_played > self.__loops
        ):
            return

        self.__timer += dt

        if self.__timer >= self.__interval:
            self.__timer %= self.__interval
            self.__current_frame_index = (self.__current_frame_index + 1) % self.__size

            # Only increments times played if there is a value for loops.
            if self.__current_frame_index == 0 and self.__loops is not None:
                self.__times_played += 1

                if self.__times_played > self.__loops:
                    # Setting the last frame if loops was completed
                    self.__current_frame_index = len(self.__frames) - 1
                    # Animation fulfilled invoking callback, if exist
                    self.__on_finish()

    def get_current_frame(self) -> any:
        """
        :returns: The current frame of the animation.
        """
        return self.__frames[self.__current_frame_index]

    @property
    def times_played(self) -> int:
        return self.__times_played
