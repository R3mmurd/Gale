"""
This file contains the implementation of the class Animation.

Author: Alejandro Mujica (aledrums@gmail.com)
"""


class Animation:
    """
    This class represents animations as a sequence of frames. Those
    frames change in a given time interval.
    """
    def __init__(self, frames, time_interval=0, loops=None):
        """
        Initialize a new Animation.

        Args:
            :param frames: Sequence of frames.
            :param time_interval: Duration time (in seconds) of each frame.
            :param loops: Number of times that this animation shall execute.
            The default value is None to execute infinitely.
        """
        self.frames = frames
        self.interval = time_interval
        self.loops = loops
        self.size = len(self.frames)
        self.timer = 0
        self.times_played = 0
        self.current_frame = 0

    def reset(self):
        """
        Set the animation on its initial values.
        """
        self.times_played = 0
        self.timer = 0
        self.current_frame = 0

    def update(self, dt):
        """
        This function updates the animation timer to check whether the frame
        should be changed or not. If the animation has only one frame or
        it has executed the number of times defined by loops, then
        this operation does not execute.
        """
        if (self.size <= 1 or (self.loops is not None
                and self.times_played > self.loops)):
            return
        
        self.timer += dt

        if self.timer >= self.interval:
            self.timer %= self.interval
            self.current_frame = (self.current_frame + 1) % self.size

            if self.current_frame == 0:
                self.times_played += 1

    def get_current_frame(self):
        """
        :return: The current frame of the animation.
        """
        return self.frames[self.current_frame]

