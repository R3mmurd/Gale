"""
This file contains the implementation of a basic class
to implement a Game with pygame.

When this module is imported, it calls to pygame.init() to
start a game.

Author: Alejandro Mujica
"""
import sys

import pygame

from .timer import Timer

pygame.init()


class Game:
    """
    Base class to implemente a game by using pygame.

    This class handles the window to show the game an a virtual
    screen with the resolution that you want to emulate. This also
    handles timer and the game loop.

    Usage example:

        class MyGame(Game):
            def init(self):
                # Set your own initial configuration of the game.
                self.player = Player()
                self.world = World()
        
            def update(self, dt):
                # Update of all your game elements here.
                # dt is the elapsed time in secconds.
                self.world.update(dt)
                self.player.update(dt)
                self.player.interact_with(self.world)

            def render(self, surface):
                # Render all of your game elements on the virtual
                # screen surface.
                self.world.render(surface)
                self.player.render(surface)

            def keydown(self, key):
                # Make your action when key has been pressed.
                if key == pygame.K_ESCAPE:
                    self.quit()
    
        game = MyGame(title='Title of my game')
        game.exec()
    """
    def __init__(self, title=None, window_width=800, window_height=600,
                 virtual_width=None, virtual_height=None, *args, **kwargs):
        """
        Set the basic elements of the game in their initial values.

        Args:
            :param title: Title of the game to show in the window title.
            By default is None to set the title 'Game'.
            :param window_width: Width of the window to show the game.
            By default is 800.
            :param window_height: Height of the window to show the game.
            By default is 600.
            :param virtual_width: Width we're trying to emulate. By default
            is None to set the same value of window_width.
            :param virtual_height: Height we're trying to emulate. By default
            is None to set the same value of window_height.
            *args and **kwargs Any argument list of keyword arguments that
            are accepted by pygame.display.set_mode.
        """
        self.window_width = window_width
        self.window_height = window_height
        self.virtual_width = virtual_width or self.window_width
        self.virtual_height = virtual_height or self.window_height
            
        # Setting the screen
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height), *args, **kwargs
        )
        self.title = title or 'Game'
        pygame.display.set_caption(self.title)

        # Creating the virtual screen
        self.surface = pygame.Surface(
            (self.virtual_width, self.virtual_height)
        )
        self.clock = pygame.time.Clock()

        self.running = False

        self.init()

    def init(self):
        """
        Empty. This should be implemented by the extension class.
        """
        pass

    def update(self, dt):
        """
        Empty. This should be implemented by the extension class.

        Args:
            :param dt: Time elapsed (in seconds) since the last time
            this function has been executed.
        """
        pass

    def render(self, surface):
        """
        Empty. This should be implemented by the extension class.

        Args:
            :param surface: The surface where you should render all
                of the game elements on. Its dimensions are
                virtual_width x virtual_height.
        """
        pass

    def keydown(self, key):
        """
        Empty. This should be implemented by the extension class.

        Args:
            :param key: The value of the key that has been pressed.
            Check the constant names for keys here:
            https://www.pygame.org/docs/ref/key.html
        """
        pass

    def keyup(self, key):
        """
        Empty. This should be implemented by the extension class.

        Args:
            :param key: The value of the key that has been released.
            Check the constant names for keys here:
            https://www.pygame.org/docs/ref/key.html
        """
        pass

    def _render(self):
        """
        Prepare screen for render and calls the method render
        that you should implmenent.
        """
        self.surface.fill((0, 0, 0))
        self.render(self.surface)
        self.screen.blit(
            pygame.transform.scale(self.surface, self.screen.get_size()),
            (0, 0)
        )
        pygame.display.update()

    def exec(self):
        """
        Execute the game loop.
        """
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()  
                elif event.type == pygame.KEYDOWN:
                    self.keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.keyup(event.key)
            
            dt = self.clock.tick() / 1000
            Timer.update(dt)
            self.update(dt)
            self._render()

        pygame.font.quit()
        pygame.mixer.quit()
        pygame.quit()

    def quit(self):
        """
        Mark the game to exit.
        """
        self.running = False

