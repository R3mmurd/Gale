"""
This file contains the concrete cutscene beats gale.cutscene ships
with: Wait (a pure pause), ShowImage, PlayAnimation (a "video" -- see
its own docstring for why that's a deliberate, dependency-free
choice), MoveActor, SetActorAnimation, and Dialogue. Every one of them
is a gale.sequence.Step, so duration/advance_on_input (and
gale.sequence.StepGroup, for running several of them side by side) all
just work. Write your own Step subclasses for anything game-specific a
cutscene needs beyond these.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Optional, Tuple

import pygame

from gale.animation import Animation
from gale.sequence import Step
from gale.text import render_text


class Wait(Step):
    """
    Does nothing on its own -- a pure pause. Useful inside a
    gale.sequence.StepGroup to give the group itself a
    duration/advance_on_input distinct from its children's, or on its
    own as a beat with nothing to show ("hold on black for half a
    second").
    """

    pass


class ShowImage(Step):
    """
    Displays a single image (a title card, a still illustration for a
    story beat, ...) until this step completes.

    Usage example:

        ShowImage(pygame.image.load("chapter_1.png"), duration=3.0, advance_on_input="confirm")
    """

    def __init__(
        self,
        image: pygame.Surface,
        position: Tuple[float, float] = (0, 0),
        **kwargs: Any,
    ) -> None:
        """
        :param image: The image to display.
        :param position: Where to blit it. The default value is (0, 0).
        """
        super().__init__(**kwargs)
        self.image: pygame.Surface = image
        self.position: Tuple[float, float] = position

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.position)


class PlayAnimation(Step):
    """
    Plays a gale.animation.Animation as this step's content -- gale's
    stand-in for "play a video". Deliberately not real video-codec
    (mp4/webm) playback: gale never depends on a decoder library
    (ffmpeg, OpenCV, ...), the same way gale.tilemap never depends on
    gale.physics. Pre-render the real footage as a frame sequence
    (most video editors, and ffmpeg itself, can export a PNG-per-frame
    sequence) and load those the same way any other sprite animation
    would.

    Complete once the animation runs out of loops, or via
    duration/advance_on_input if it loops forever (loops=None) and
    only those should end it.

    Usage example:

        frames = [pygame.image.load(f"intro_{i:03d}.png") for i in range(90)]
        PlayAnimation(Animation(frames, time_interval=1 / 30, loops=1))
    """

    def __init__(
        self,
        animation: Animation,
        position: Tuple[float, float] = (0, 0),
        **kwargs: Any,
    ) -> None:
        """
        :param animation: The animation to play. Reset to its first frame every time this step becomes active.
        :param position: Where to blit each frame. The default value is (0, 0).
        """
        super().__init__(**kwargs)
        self.animation: Animation = animation
        self.position: Tuple[float, float] = position

    def enter(self, *args: Any, **kwargs: Any) -> None:
        super().enter(*args, **kwargs)
        self.animation.reset()

    def update(self, dt: float) -> None:
        self.animation.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.animation.get_current_frame(), self.position)

    def is_complete(self) -> bool:
        if (
            self.animation.loops is not None
            and self.animation.times_played >= self.animation.loops
        ):
            return True

        return super().is_complete()


class MoveActor(Step):
    """
    Moves actor.position linearly from wherever it is when this step
    becomes active to target, over duration seconds -- the classic
    "walk to the mark" cutscene beat. actor is duck-typed: any object
    exposing a mutable, pygame.Vector2-compatible .position works (an
    Agent, a custom Player class, ...), so this plugs into whatever
    character class the game already has without gale.cutscene needing
    to know its shape.

    Usage example:

        MoveActor(hero, target=(400, 200), duration=1.5)
    """

    def __init__(
        self, actor: Any, target: Tuple[float, float], duration: float, **kwargs: Any
    ) -> None:
        """
        :param actor: Any object with a .position attribute (a pygame.Vector2, or a value pygame.Vector2(...) accepts).
        :param target: The position to move actor to.
        :param duration: How many seconds the move takes.
        """
        super().__init__(duration=duration, **kwargs)
        self.actor: Any = actor
        self.target: pygame.Vector2 = pygame.Vector2(target)
        self._start: pygame.Vector2 = pygame.Vector2()

    def enter(self, *args: Any, **kwargs: Any) -> None:
        super().enter(*args, **kwargs)
        self._start = pygame.Vector2(self.actor.position)

    def update(self, dt: float) -> None:
        t = 1.0 if self.duration <= 0 else min(1.0, self.elapsed / self.duration)
        self.actor.position = self._start.lerp(self.target, t)


class SetActorAnimation(Step):
    """
    Switches actor.animation to a different gale.animation.Animation
    (a pose/expression change, e.g. "surprised" instead of "idle"),
    then completes right away, unless duration/advance_on_input say
    otherwise. actor is duck-typed the same way MoveActor's is: any
    object with a settable .animation attribute.

    Usage example:

        SetActorAnimation(hero, surprised_animation)
    """

    def __init__(self, actor: Any, animation: Animation, **kwargs: Any) -> None:
        """
        :param actor: Any object with an .animation attribute.
        :param animation: The animation to switch actor to. Reset to its first frame.
        """
        super().__init__(**kwargs)
        self.actor: Any = actor
        self.animation: Animation = animation

    def enter(self, *args: Any, **kwargs: Any) -> None:
        super().enter(*args, **kwargs)
        self.animation.reset()
        self.actor.animation = self.animation

    def is_complete(self) -> bool:
        if self.duration is None and self.advance_on_input is None:
            return True

        return super().is_complete()


class Dialogue(Step):
    """
    Shows a speaker name and a line of text in a simple box until this
    step completes -- usually via advance_on_input, the classic "press
    a key to continue" dialogue box, though duration works too for an
    auto-advancing line. Draws a plain rectangle behind the text by
    default; override render (or subclass) for a game's own dialogue
    box art/gale.ui widgets instead.

    Usage example:

        Dialogue("Elder", "The forest holds many secrets...", font, advance_on_input="confirm")
    """

    def __init__(
        self,
        speaker: str,
        text: str,
        font: pygame.font.Font,
        box_rect: Optional[pygame.Rect] = None,
        text_color: Any = (255, 255, 255),
        speaker_color: Any = (255, 220, 120),
        box_color: Any = (20, 20, 20),
        **kwargs: Any,
    ) -> None:
        """
        :param speaker: Name shown above the line, e.g. a character's name.
        :param text: The line of dialogue itself.
        :param font: Font used for both speaker and text.
        :param box_rect: Where to draw the dialogue box. The default value is None, using a bar across the bottom of whatever surface render() is given.
        :param text_color: Color of the dialogue text.
        :param speaker_color: Color of the speaker's name.
        :param box_color: Fill color of the dialogue box.
        """
        super().__init__(**kwargs)
        self.speaker: str = speaker
        self.text: str = text
        self.font: pygame.font.Font = font
        self.box_rect: Optional[pygame.Rect] = box_rect
        self.text_color: Any = text_color
        self.speaker_color: Any = speaker_color
        self.box_color: Any = box_color

    def render(self, surface: pygame.Surface) -> None:
        box_rect = self.box_rect

        if box_rect is None:
            width, height = surface.get_size()
            box_rect = pygame.Rect(0, height - 90, width, 90)

        pygame.draw.rect(surface, self.box_color, box_rect)
        render_text(
            surface,
            self.speaker,
            self.font,
            box_rect.x + 16,
            box_rect.y + 10,
            self.speaker_color,
        )
        render_text(
            surface,
            self.text,
            self.font,
            box_rect.x + 16,
            box_rect.y + 40,
            self.text_color,
        )
