import unittest

import pygame

from gale.camera import Camera
from gale.tilemap import Tileset
from gale.tilemap.isometric import (
    IsometricTileMap,
    cartesian_to_isometric,
    isometric_to_cartesian,
)


class CartesianIsometricConversionTestCase(unittest.TestCase):
    def test_cartesian_to_isometric_origin(self) -> None:
        self.assertEqual(cartesian_to_isometric(0, 0, 64, 32), (0.0, 0.0))

    def test_cartesian_to_isometric_known_values(self) -> None:
        self.assertEqual(cartesian_to_isometric(1, 0, 64, 32), (32.0, 16.0))
        self.assertEqual(cartesian_to_isometric(0, 1, 64, 32), (-32.0, 16.0))

    def test_round_trip(self) -> None:
        for x, y in [(0, 0), (3, 5), (10.5, 2.25), (-4, 7), (100, 100)]:
            screen_x, screen_y = cartesian_to_isometric(x, y, 64, 32)
            self.assertEqual(isometric_to_cartesian(screen_x, screen_y, 64, 32), (x, y))


class IsometricTileMapTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.tilemap = IsometricTileMap(tile_width=64, tile_height=32, cols=5, rows=5)

    def tearDown(self) -> None:
        pygame.display.quit()

    def test_pixel_dimensions(self) -> None:
        self.assertEqual(self.tilemap.pixel_width, 320)  # (5 + 5) * 64 / 2
        self.assertEqual(self.tilemap.pixel_height, 160)  # (5 + 5) * 32 / 2

    def test_position_of_top_corner_is_non_negative_x(self) -> None:
        for row in range(self.tilemap.rows):
            for col in range(self.tilemap.cols):
                x, _ = self.tilemap.position_of(row, col)
                self.assertGreaterEqual(x, 0)

    def test_position_of_row0_col0_is_map_top(self) -> None:
        x, y = self.tilemap.position_of(0, 0)
        self.assertEqual(y, 0)

    def test_position_of_and_tile_at_round_trip_for_cell_centers(self) -> None:
        for row in range(self.tilemap.rows):
            for col in range(self.tilemap.cols):
                top_x, top_y = self.tilemap.position_of(row, col)
                center_x = top_x
                center_y = top_y + self.tilemap.tile_height / 2
                self.assertEqual(self.tilemap.tile_at(center_x, center_y), (row, col))

    def test_render_without_camera_runs(self) -> None:
        image = pygame.Surface((64, 32))
        image.fill((255, 0, 0))
        tileset = Tileset(image, 64, 32, first_gid=1)
        self.tilemap.add_tileset(tileset)
        ground = self.tilemap.add_layer("ground")
        ground[2][2] = 1

        surface = pygame.Surface((self.tilemap.pixel_width, self.tilemap.pixel_height))
        self.tilemap.render(surface)

    def test_render_with_camera_runs(self) -> None:
        image = pygame.Surface((64, 32))
        image.fill((0, 255, 0))
        tileset = Tileset(image, 64, 32, first_gid=1)
        self.tilemap.add_tileset(tileset)
        ground = self.tilemap.add_layer("ground")
        ground[0][0] = 1
        ground[4][4] = 1

        surface = pygame.Surface((160, 120))
        camera = Camera(
            160, 120, x=self.tilemap.pixel_width / 2, y=self.tilemap.pixel_height / 2
        )
        self.tilemap.render(surface, camera)


if __name__ == "__main__":
    unittest.main()
