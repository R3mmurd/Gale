"""
This file contains the implementation of the class Game: the window,
virtual-resolution scaling, and game loop (a variable-rate
update/render pair driven by real elapsed time, plus a fixed_update
that steps at a constant rate regardless of frame rate) every gale
game is built on top of. Every constructor argument is optional and
falls back to gale.conf.settings (see gale.conf) when omitted, so a
project's settings.py is enough to configure it without passing
anything explicitly.

Importing this module calls pygame.init().

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import sys

from typing import Optional, Any, Tuple, Dict

import pygame

from .conf import settings
from .timer import Timer
from .input_handler import InputHandler, InputListener, InputData, INPUT_EVENTS

pygame.init()


class Game(InputListener):
    """
    Base class to implemente a game by using pygame.

    This class handles the window to show the game an a virtual
    screen with the resolution that you want to emulate. This also
    handles timer and the game loop.

    Usage example:

        class MyGame(Game):
            def init(self) -> None:
                # Set your own initial configuration of the game.
                self.player = Player()
                self.world = World()

            def on_input(self, input_id: str, input_data: InputData) -> None:
                # Make your action when an input is detected.
                if input_id == "quit" and input_data.pressed:
                    self.quit()

            def update(self, dt: float) -> None:
                # Update of all your game elements here.
                # dt is the elapsed time in secconds.
                self.world.update(dt)
                self.player.update(dt)
                self.player.interact_with(self.world)

            def render(self, surface: pygame.Surface) -> None:
                # Render all of your game elements on the virtual
                # screen surface.
                self.world.render(surface)
                self.player.render(surface)

        game = MyGame(title='Title of my game')
        game.exec()

    fixed_update() is optional and only needed for logic that must
    advance by the same amount of time every call, independent of the
    frame rate (e.g. driving gale.physics.World.fixed_update()
    directly instead of its own internal accumulator, or a networked
    simulation tick):

        class MyGame(Game):
            def init(self) -> None:
                self.world = World()

            def fixed_update(self) -> None:
                self.world.fixed_update()
    """

    def __init__(
        self,
        title: Optional[str] = None,
        window_width: Optional[int] = None,
        window_height: Optional[int] = None,
        virtual_width: Optional[int] = None,
        virtual_height: Optional[int] = None,
        fps: Optional[int] = None,
        fixed_timestep: Optional[float] = None,
        *args: Tuple[Any],
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Set the basic elements of the game in their initial values.

        Every parameter below defaults to None, in which case it is
        resolved from gale.conf.settings instead: the project's own
        settings.py if it defines that setting, or
        gale.conf.global_settings otherwise. Pass a value explicitly
        to override settings for this instance specifically.

        :param title: Title of the game to show in the window title. Resolved from settings.TITLE, itself None by default, meaning 'Game'.
        :param window_width: Width of the window to show the game. Resolved from settings.WINDOW_WIDTH, itself 800 by default.
        :param window_height: Height of the window to show the game. Resolved from settings.WINDOW_HEIGHT, itself 600 by default.
        :param virtual_width: Width we're trying to emulate. Resolved from settings.VIRTUAL_WIDTH, itself None by default, meaning the same value as window_width.
        :param virtual_height: Height we're trying to emulate. Resolved from settings.VIRTUAL_HEIGHT, itself None by default, meaning the same value as window_height.
        :param fps: Number of frame per seconds. Resolved from settings.FPS, itself 60 by default. *args and **kwargs Any argument list of keyword arguments that are accepted by pygame.display.set_mode.
        :param fixed_timestep: Seconds between two fixed_update() calls. Resolved from settings.FIXED_TIMESTEP, itself 1/60 by default. Unrelated to fps: fixed_update() runs zero, one, or several times per frame so it always advances by exactly this much real time, regardless of the frame rate.
        """
        self.window_width: int = (
            window_width if window_width is not None else settings.WINDOW_WIDTH
        )
        self.window_height: int = (
            window_height if window_height is not None else settings.WINDOW_HEIGHT
        )
        resolved_virtual_width = (
            virtual_width if virtual_width is not None else settings.VIRTUAL_WIDTH
        )
        resolved_virtual_height = (
            virtual_height if virtual_height is not None else settings.VIRTUAL_HEIGHT
        )
        self.virtual_width: int = resolved_virtual_width or self.window_width
        self.virtual_height: int = resolved_virtual_height or self.window_height
        self.fps = fps if fps is not None else settings.FPS
        self.fixed_timestep: float = (
            fixed_timestep if fixed_timestep is not None else settings.FIXED_TIMESTEP
        )

        if self.fixed_timestep <= 0:
            raise ValueError(
                f"fixed_timestep must be positive, got {self.fixed_timestep!r} -- "
                "a zero or negative value would make __update's accumulator loop "
                "run forever."
            )

        self._accumulator: float = 0.0

        # Setting the screen
        self.screen: pygame.Surface = pygame.display.set_mode(
            (self.window_width, self.window_height), *args, **kwargs
        )
        self.title: str = title or settings.TITLE or "Game"
        pygame.display.set_caption(self.title)

        # Creating the virtual screen
        self.render_surface = pygame.Surface((self.virtual_width, self.virtual_height))
        self.clock = pygame.time.Clock()

        self.running: bool = False

        InputHandler.register_listener(self)

        self.init()

    def init(self) -> None:
        """
        Empty. This should be implemented by the extension class.
        """
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        """
        Empty. This should be implemented by the extension class.
        """
        pass

    def update(self, dt: float) -> None:
        """
        Empty. This should be implemented by the extension class.

        :param dt: Time elapsed (in seconds) since the last time this function has been executed.
        """
        pass

    def fixed_update(self) -> None:
        """
        Empty. Override for deterministic, frame-rate-independent logic
        (e.g. driving a gale.physics.World, or anything else that
        needs to advance by the same amount of time on every call
        regardless of how fast frames are rendering): unlike update(),
        this runs zero, one, or several times per frame so that it
        always advances the game by exactly fixed_timestep seconds
        each time it's called.
        """
        pass

    def render(self, surface: pygame.Surface) -> None:
        """
        Empty. This should be implemented by the extension class.


        :param render_surface: The surface where you should render all of the game elements on. Its dimensions are virtual_width x virtual_height.
        """
        pass

    def __update(self, dt: float) -> None:
        """
        Advance fixed_update() by as many fixed_timestep steps as the
        accumulated time covers, update the timer, and call the
        method update that you should implement.
        """
        self._accumulator += dt

        while self._accumulator >= self.fixed_timestep:
            self.fixed_update()
            self._accumulator -= self.fixed_timestep

        Timer.update(dt)
        self.update(dt)

    def __render(self) -> None:
        """
        Prepare screen for render and calls the method render
        that you should implement.
        """
        self.render_surface.fill((0, 0, 0))
        self.render(self.render_surface)
        self.screen.blit(
            pygame.transform.scale(self.render_surface, self.screen.get_size()), (0, 0)
        )
        pygame.display.update()

    def exec(self) -> None:
        """
        Execute the game loop.
        """
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type in INPUT_EVENTS:
                    InputHandler.handle_input(event)

            dt = self.clock.tick(self.fps) / 1000.0
            self.__update(dt)
            self.__render()

        # pygame.quit() already uninitializes every subsystem
        # pygame.init() started (font and mixer included), so there's
        # no need to quit them individually first.
        pygame.quit()

    def quit(self) -> None:
        """
        Mark the game to exit and stop it from receiving further input,
        undoing the registration __init__ made with InputHandler.
        """
        self.running = False
        InputHandler.unregister_listener(self)
