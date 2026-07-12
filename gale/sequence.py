"""
This file contains a small, generic toolkit for anything that plays
out as an ordered series of steps, each one active for a while before
handing off to the next: Step (one step, complete after a fixed
duration, in response to a specific input, or by whatever custom
condition a subclass implements), StepGroup (several Steps run side by
side, complete once all of them are -- or any one of them, with
require_all=False), and Sequence (drives a list of Steps one at a
time, forwarding update/on_input/render to whichever is currently
active).

This is the shared engine behind both gale.quest (a quest's stages and
objectives) and gale.cutscene (a cutscene's beats): both are, at their
core, "do this until it's done, then do the next thing," and only
differ in what "done" means and what a step actually shows/does on
screen.

See docs/examples/sequence.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, List, Optional

import pygame

from .input_handler import InputData


class Step:
    """
    One step of a Sequence. A step becomes active when the Sequence
    reaches it (enter() is called), runs update(dt) every tick while
    active, and is dropped in favor of the next step once
    is_complete() returns True.

    The two most common ways a step finishes on its own are already
    built in -- after a fixed duration, or as soon as a specific input
    is pressed -- since that's exactly the choice a cutscene beat, a
    line of dialogue, or a tutorial prompt usually needs ("show this
    for 2 seconds, or let the player press a key to skip ahead").
    Passing neither leaves is_complete() at its default of "never, on
    its own", meaning a subclass is expected to override it with its
    own condition instead (a quest objective's progress, a scripted
    event finishing, ...) -- call super().is_complete() too if
    duration/advance_on_input should still be able to force it, the
    same way gale.state.HierarchicalState expects overrides of
    enter/update/render to call through to keep its own delegation
    working.

    Usage example:

        class ShowBanner(Step):
            def __init__(self, text, font, **kwargs):
                super().__init__(**kwargs)
                self.text = text
                self.font = font

            def render(self, surface):
                render_text(surface, self.text, self.font, 400, 300, "white", center=True)

        # Shown for 2 seconds, or skipped early with the "confirm" input.
        ShowBanner("Chapter 1", font, duration=2.0, advance_on_input="confirm")
    """

    def __init__(
        self,
        duration: Optional[float] = None,
        advance_on_input: Optional[str] = None,
    ) -> None:
        """
        :param duration: Seconds this step stays active before is_complete() reports True on its own. The default value is None, meaning duration alone never completes it.
        :param advance_on_input: The input_id that completes this step as soon as it's pressed (see on_input). The default value is None, meaning no input completes it on its own.
        """
        self.duration: Optional[float] = duration
        self.advance_on_input: Optional[str] = advance_on_input
        self.elapsed: float = 0.0
        self._input_triggered: bool = False

    def enter(self, *args: Any, **kwargs: Any) -> None:
        """
        Called once when the Sequence makes this step the active one.
        Resets the bookkeeping duration/advance_on_input rely on.

        :param args and kwargs: Accepted for subclasses that need extra setup data; unused by the base implementation.
        """
        self.elapsed = 0.0
        self._input_triggered = False

    def exit(self) -> None:
        """
        Called once when the Sequence moves on from this step.
        """
        pass

    def update(self, dt: float) -> None:
        """
        Override to do this step's per-frame work. Called every tick
        while this step is active, after elapsed has already been
        advanced by dt.

        :param dt: Time elapsed (in seconds) since the last update.
        """
        pass

    def render(self, surface: pygame.Surface) -> None:
        """
        Override to draw whatever this step shows while active.

        :param surface: The surface to draw on.
        """
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        Reacts to input while this step is active. The default
        implementation is what makes advance_on_input work -- call
        super().on_input(...) first if you override it and still want
        that.

        :param input_id: The string that describes the input.
        :param input_data: Data associated to the input type.
        """
        if (
            self.advance_on_input is not None
            and input_id == self.advance_on_input
            and getattr(input_data, "pressed", False)
        ):
            self._input_triggered = True

    def is_complete(self) -> bool:
        """
        :returns: Whether this step is done and the Sequence should move to the next one. The default implementation is True once duration has elapsed or advance_on_input has been pressed, and False otherwise -- override (calling super() too, if duration/advance_on_input should still apply) to add a custom condition.
        """
        if self.duration is not None and self.elapsed >= self.duration:
            return True

        return self._input_triggered

    def _tick(self, dt: float) -> None:
        self.elapsed += dt
        self.update(dt)


class StepGroup(Step):
    """
    Runs several Steps side by side (e.g. a character walking across
    the screen while a line of dialogue plays over it, or a quest
    stage's several objectives tracked at once), completing once all
    -- or any one, with require_all=False -- of them report
    is_complete(). Also accepts its own duration/advance_on_input
    (inherited from Step), which forcibly completes the whole group
    regardless of its children, e.g. a hard timeout.

    Usage example:

        StepGroup([
            MoveActor(hero, target=(400, 200), duration=1.5),
            Dialogue("Hero", "This way!", font),
        ])
    """

    def __init__(
        self, steps: List[Step], require_all: bool = True, **kwargs: Any
    ) -> None:
        """
        :param steps: The steps to run concurrently.
        :param require_all: Whether every step must complete (True) or just one of them (False) for this group to be done. The default value is True.
        """
        super().__init__(**kwargs)
        self.steps: List[Step] = steps
        self.require_all: bool = require_all

    def enter(self, *args: Any, **kwargs: Any) -> None:
        super().enter(*args, **kwargs)

        for step in self.steps:
            step.enter()

    def exit(self) -> None:
        for step in self.steps:
            step.exit()

    def update(self, dt: float) -> None:
        for step in self.steps:
            if not step.is_complete():
                step._tick(dt)

    def render(self, surface: pygame.Surface) -> None:
        for step in self.steps:
            step.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        super().on_input(input_id, input_data)

        for step in self.steps:
            step.on_input(input_id, input_data)

    def is_complete(self) -> bool:
        if super().is_complete():
            return True

        completed = (step.is_complete() for step in self.steps)
        return all(completed) if self.require_all else any(completed)


class Sequence:
    """
    Drives a list of Steps one at a time: enters the first, keeps
    ticking/rendering/forwarding input to whichever is active, and
    moves on to the next one as soon as the active step's
    is_complete() turns True, until none are left.

    Usage example:

        sequence = Sequence(
            [Step(duration=1.0), Step(advance_on_input="confirm")],
            on_finished=lambda: print("done"),
        )

        # In the game loop:
        sequence.update(dt)
        sequence.render(surface)
        # And forward input from wherever your game dispatches it:
        sequence.on_input(input_id, input_data)
    """

    def __init__(
        self,
        steps: List[Step],
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        :param steps: The steps to run in order. Empty is valid: the sequence is immediately finished, and on_finished (if given) fires right away.
        :param on_finished: Called once, with no arguments, when the last step completes and there's nothing left to advance to. The default value is None.
        """
        self.steps: List[Step] = steps
        self.on_finished: Optional[Callable[[], None]] = on_finished
        self.index: int = -1
        self.current: Optional[Step] = None
        self.finished: bool = False
        self._advance()

    def update(self, dt: float) -> None:
        """
        :param dt: Time elapsed (in seconds) since the last update.
        """
        if self.finished or self.current is None:
            return

        self.current._tick(dt)

        if self.current.is_complete():
            self._advance()

    def render(self, surface: pygame.Surface) -> None:
        """
        :param surface: The surface to draw on.
        """
        if self.current is not None:
            self.current.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        :param input_id: The string that describes the input.
        :param input_data: Data associated to the input type.
        """
        if self.current is not None:
            self.current.on_input(input_id, input_data)

    def skip_current(self) -> None:
        """
        Force the current step to end right now and move to the next
        one, regardless of its own is_complete(). Useful for a
        "skip"/"hold to fast-forward" input on top of whatever a
        step's own duration/advance_on_input already allow.
        """
        if not self.finished:
            self._advance()

    def _advance(self) -> None:
        if self.current is not None:
            self.current.exit()

        self.index += 1

        if self.index >= len(self.steps):
            self.current = None
            self.finished = True

            if self.on_finished is not None:
                self.on_finished()

            return

        self.current = self.steps[self.index]
        self.current.enter()
