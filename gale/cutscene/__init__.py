"""
gale.cutscene: a small toolkit for scripted, non-interactive scenes --
a Cutscene (a gale.sequence.Sequence) of beats that show an image,
play a frame-animation "video", move an actor to a mark, switch an
actor's animation/pose, or show a line of dialogue, each one lasting
either a fixed duration or until a specific input advances it (see
gale.sequence.Step). Combine several beats to run at once with
gale.sequence.StepGroup (e.g. a character moving while a line of
dialogue plays over it).

See docs/examples/cutscene.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .actions import (
    Dialogue,
    MoveActor,
    PlayAnimation,
    SetActorAnimation,
    ShowImage,
    Wait,
)
from .cutscene import Cutscene

__all__ = [
    "Cutscene",
    "Dialogue",
    "MoveActor",
    "PlayAnimation",
    "SetActorAnimation",
    "ShowImage",
    "Wait",
]
