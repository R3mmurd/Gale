import unittest

import pygame

from gale.stencil import Stencil


class StencilTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.size = (40, 40)
        self.stencil = Stencil(self.size)
        self.stencil.draw(lambda mask: pygame.draw.circle(mask, "white", (20, 20), 10))

    def tearDown(self) -> None:
        pygame.display.quit()

    def _filled_surface(self) -> pygame.Surface:
        surface = pygame.Surface(self.size, pygame.SRCALPHA)
        surface.fill((255, 0, 0, 200))
        return surface

    def test_apply_keeps_pixels_inside_the_shape(self) -> None:
        surface = self._filled_surface()
        self.stencil.apply(surface)
        self.assertEqual(surface.get_at((20, 20)), (255, 0, 0, 200))

    def test_apply_zeroes_pixels_outside_the_shape(self) -> None:
        surface = self._filled_surface()
        self.stencil.apply(surface)
        self.assertEqual(surface.get_at((1, 1)), (0, 0, 0, 0))

    def test_invert_keeps_pixels_outside_the_shape(self) -> None:
        surface = self._filled_surface()
        self.stencil.apply(surface, invert=True)
        self.assertEqual(surface.get_at((1, 1)), (255, 0, 0, 200))

    def test_invert_zeroes_pixels_inside_the_shape(self) -> None:
        surface = self._filled_surface()
        self.stencil.apply(surface, invert=True)
        self.assertEqual(surface.get_at((20, 20)), (0, 0, 0, 0))

    def test_clear_removes_the_previous_shape(self) -> None:
        self.stencil.clear()
        surface = self._filled_surface()
        self.stencil.apply(surface)
        self.assertEqual(surface.get_at((20, 20)), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
