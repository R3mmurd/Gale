"""
This file contains the class Cutscene: a thin gale.sequence.Sequence
of beats (see gale.cutscene.actions) that also ticks/renders any
actors involved every frame, regardless of which beat is currently
active -- a beat like MoveActor only ever touches an actor's
.position, it doesn't drive whatever else that actor's own class needs
updated every frame (its own sprite Animation advancing, its own
render, ...).

See docs/examples/cutscene.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, List, Optional, Sequence as SequenceType

import pygame

from gale.sequence import Sequence, Step


class Cutscene(Sequence):
    """
    A cutscene: a Sequence of beats, plus the one bit of bookkeeping
    that's specific to cutscenes rather than sequences in general --
    ticking/rendering any actors involved every frame so they keep
    animating even on beats that don't otherwise touch them (a
    character idling in the background while another one is talking,
    for instance).

    Usage example:

        cutscene = Cutscene(
            [
                MoveActor(hero, (400, 200), duration=1.5),
                Dialogue("Hero", "This way!", font, advance_on_input="confirm"),
            ],
            actors=[hero],
            on_finished=lambda: state_machine.change("play"),
        )

        # In the game loop:
        cutscene.update(dt)
        cutscene.render(surface)
        # And forward input from wherever your game dispatches it:
        cutscene.on_input(input_id, input_data)
    """

    def __init__(
        self,
        beats: List[Step],
        actors: Optional[SequenceType[Any]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        :param beats: The Steps that make up this cutscene, in order.
        :param actors: Objects with their own update(dt) (and usually render(surface)) to tick/draw every frame regardless of which beat is active -- typically the same character objects the beats themselves reference (e.g. via MoveActor). Objects missing either method are simply not called for it. The default value is None (no actors ticked automatically).
        :param on_finished: Called once, with no arguments, when the cutscene's last beat completes.
        """
        self.actors: SequenceType[Any] = actors if actors is not None else []
        super().__init__(beats, on_finished=on_finished)

    def update(self, dt: float) -> None:
        for actor in self.actors:
            update = getattr(actor, "update", None)

            if update is not None:
                update(dt)

        super().update(dt)

    def render(self, surface: pygame.Surface) -> None:
        for actor in self.actors:
            render = getattr(actor, "render", None)

            if render is not None:
                render(surface)

        super().render(surface)
