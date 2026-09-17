import unittest

import pygame

from gale.camera import Camera
from gale.tilemap import TileMap, Tileset
from gale.tilemap.tilemap import (
    FLIP_DIAGONAL_FLAG,
    FLIP_HORIZONTAL_FLAG,
    FLIP_VERTICAL_FLAG,
    decode_gid,
)


class TilesetTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.image = pygame.Surface((32, 16))  # 2x1 tiles of 16x16

    def tearDown(self) -> None:
        pygame.display.quit()

    def test_tile_count_and_last_gid(self) -> None:
        tileset = Tileset(self.image, 16, 16, first_gid=1)
        self.assertEqual(tileset.tile_count, 2)
        self.assertEqual(tileset.last_gid, 2)

    def test_contains(self) -> None:
        tileset = Tileset(self.image, 16, 16, first_gid=5)
        self.assertFalse(tileset.contains(4))
        self.assertTrue(tileset.contains(5))
        self.assertTrue(tileset.contains(6))
        self.assertFalse(tileset.contains(7))

    def test_rect_for(self) -> None:
        tileset = Tileset(self.image, 16, 16, first_gid=1)
        self.assertEqual(tileset.rect_for(1), pygame.Rect(0, 0, 16, 16))
        self.assertEqual(tileset.rect_for(2), pygame.Rect(16, 0, 16, 16))

    def test_properties_for(self) -> None:
        tileset = Tileset(
            self.image, 16, 16, first_gid=1, tile_properties={1: {"collision": "solid"}}
        )
        self.assertEqual(tileset.properties_for(2), {"collision": "solid"})
        self.assertEqual(tileset.properties_for(1), {})


class TileMapTestCase(unittest.TestCase):
    def setUp(self) -> None:
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.tilemap = TileMap(tile_width=16, tile_height=16, cols=4, rows=3)

    def tearDown(self) -> None:
        pygame.display.quit()

    def test_pixel_dimensions(self) -> None:
        self.assertEqual(self.tilemap.pixel_width, 64)
        self.assertEqual(self.tilemap.pixel_height, 48)

    def test_add_layer_defaults_to_empty_grid(self) -> None:
        grid = self.tilemap.add_layer("ground")
        self.assertEqual(grid, [[0, 0, 0, 0]] * 3)
        self.assertEqual(self.tilemap.layer_names(), ["ground"])

    def test_layer_order_is_add_order(self) -> None:
        self.tilemap.add_layer("background")
        self.tilemap.add_layer("foreground")
        self.assertEqual(self.tilemap.layer_names(), ["background", "foreground"])

    def test_get_set_gid(self) -> None:
        self.tilemap.add_layer("ground")
        self.tilemap.set_gid("ground", 1, 2, 5)
        self.assertEqual(self.tilemap.get_gid("ground", 1, 2), 5)

    def test_in_bounds(self) -> None:
        self.assertTrue(self.tilemap.in_bounds(0, 0))
        self.assertTrue(self.tilemap.in_bounds(2, 3))
        self.assertFalse(self.tilemap.in_bounds(3, 0))
        self.assertFalse(self.tilemap.in_bounds(0, 4))
        self.assertFalse(self.tilemap.in_bounds(-1, 0))

    def test_tile_at(self) -> None:
        self.assertEqual(self.tilemap.tile_at(20, 35), (2, 1))

    def test_position_of(self) -> None:
        self.assertEqual(self.tilemap.position_of(2, 1), (16, 32))

    def test_tileset_for_gid_with_multiple_tilesets(self) -> None:
        image = pygame.Surface((16, 16))
        tileset_a = Tileset(image, 16, 16, first_gid=1)  # gid 1
        tileset_b = Tileset(image, 16, 16, first_gid=5)  # gid 5
        # Added out of gid order on purpose, to check sorting.
        self.tilemap.add_tileset(tileset_b)
        self.tilemap.add_tileset(tileset_a)

        self.assertIs(self.tilemap.tileset_for_gid(1), tileset_a)
        self.assertIs(self.tilemap.tileset_for_gid(5), tileset_b)
        self.assertIsNone(self.tilemap.tileset_for_gid(0))
        self.assertIsNone(self.tilemap.tileset_for_gid(2))  # gap between tilesets

    def test_properties_of_gid(self) -> None:
        image = pygame.Surface((16, 16))
        tileset = Tileset(
            image, 16, 16, first_gid=1, tile_properties={0: {"collision": "solid"}}
        )
        self.tilemap.add_tileset(tileset)
        self.assertEqual(self.tilemap.properties_of_gid(1), {"collision": "solid"})
        self.assertEqual(self.tilemap.properties_of_gid(0), {})

    def test_render_without_camera_draws_every_tile(self) -> None:
        image = pygame.Surface((16, 16))
        image.fill((255, 0, 0))
        tileset = Tileset(image, 16, 16, first_gid=1)
        self.tilemap.add_tileset(tileset)
        ground = self.tilemap.add_layer("ground")
        ground[2][3] = 1

        surface = pygame.Surface((64, 48))
        self.tilemap.render(surface)

        self.assertEqual(surface.get_at((3 * 16 + 4, 2 * 16 + 4)), (255, 0, 0, 255))
        self.assertEqual(surface.get_at((0, 0)), (0, 0, 0, 255))

    def test_render_with_camera_culls_to_visible_range(self) -> None:
        image = pygame.Surface((16, 16))
        image.fill((0, 255, 0))
        tileset = Tileset(image, 16, 16, first_gid=1)

        big_map = TileMap(tile_width=16, tile_height=16, cols=100, rows=1)
        big_map.add_tileset(tileset)
        ground = big_map.add_layer("ground")
        ground[0][0] = 1
        ground[0][99] = 1  # far outside the camera's view

        surface = pygame.Surface((32, 16))
        # Centering the camera at (16, 8) makes its offset (0, 0), so the
        # viewport covers world x in [0, 32) with no extra translation.
        camera = Camera(32, 16, x=16, y=8)
        big_map.render(surface, camera)

        self.assertEqual(surface.get_at((4, 4)), (0, 255, 0, 255))


class DecodeGidTestCase(unittest.TestCase):
    def test_plain_gid_has_no_flags(self) -> None:
        self.assertEqual(decode_gid(5), (5, False, False, False))

    def test_decodes_each_flag(self) -> None:
        self.assertEqual(decode_gid(5 | FLIP_HORIZONTAL_FLAG), (5, True, False, False))
        self.assertEqual(decode_gid(5 | FLIP_VERTICAL_FLAG), (5, False, True, False))
        self.assertEqual(decode_gid(5 | FLIP_DIAGONAL_FLAG), (5, False, False, True))
        self.assertEqual(
            decode_gid(
                5 | FLIP_HORIZONTAL_FLAG | FLIP_VERTICAL_FLAG | FLIP_DIAGONAL_FLAG
            ),
            (5, True, True, True),
        )


class FlippedTileTestCase(unittest.TestCase):
    """
    Uses a 2x2 tileset image (one tile, one distinct color per pixel)
    so every one of Tiled's 8 flip/rotation combinations can be
    checked pixel-by-pixel against its known-correct result, derived
    by hand from the meaning of each flag rather than copied from any
    particular Tiled implementation.
    """

    RED = (255, 0, 0, 255)  # top-left
    GREEN = (0, 255, 0, 255)  # top-right
    BLUE = (0, 0, 255, 255)  # bottom-left
    YELLOW = (255, 255, 0, 255)  # bottom-right

    def setUp(self) -> None:
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        image = pygame.Surface((2, 2))
        image.set_at((0, 0), self.RED)
        image.set_at((1, 0), self.GREEN)
        image.set_at((0, 1), self.BLUE)
        image.set_at((1, 1), self.YELLOW)
        self.tileset = Tileset(image, 2, 2, first_gid=1)
        self.tilemap = TileMap(tile_width=2, tile_height=2, cols=1, rows=1)
        self.tilemap.add_tileset(self.tileset)

    def tearDown(self) -> None:
        pygame.display.quit()

    def _corners(self, raw_gid: int) -> tuple:
        ground = self.tilemap.add_layer("ground")
        ground[0][0] = raw_gid
        surface = pygame.Surface((2, 2))
        self.tilemap.render(surface)
        return (
            surface.get_at((0, 0)),
            surface.get_at((1, 0)),
            surface.get_at((0, 1)),
            surface.get_at((1, 1)),
        )

    def test_unflipped(self) -> None:
        self.assertEqual(
            self._corners(1), (self.RED, self.GREEN, self.BLUE, self.YELLOW)
        )

    def test_flip_horizontal(self) -> None:
        self.assertEqual(
            self._corners(1 | FLIP_HORIZONTAL_FLAG),
            (self.GREEN, self.RED, self.YELLOW, self.BLUE),
        )

    def test_flip_vertical(self) -> None:
        self.assertEqual(
            self._corners(1 | FLIP_VERTICAL_FLAG),
            (self.BLUE, self.YELLOW, self.RED, self.GREEN),
        )

    def test_flip_horizontal_and_vertical(self) -> None:
        self.assertEqual(
            self._corners(1 | FLIP_HORIZONTAL_FLAG | FLIP_VERTICAL_FLAG),
            (self.YELLOW, self.BLUE, self.GREEN, self.RED),
        )

    def test_flip_diagonal(self) -> None:
        self.assertEqual(
            self._corners(1 | FLIP_DIAGONAL_FLAG),
            (self.RED, self.BLUE, self.GREEN, self.YELLOW),
        )

    def test_flip_diagonal_and_horizontal(self) -> None:
        self.assertEqual(
            self._corners(1 | FLIP_DIAGONAL_FLAG | FLIP_HORIZONTAL_FLAG),
            (self.BLUE, self.RED, self.YELLOW, self.GREEN),
        )

    def test_flip_diagonal_and_vertical(self) -> None:
        self.assertEqual(
            self._corners(1 | FLIP_DIAGONAL_FLAG | FLIP_VERTICAL_FLAG),
            (self.GREEN, self.YELLOW, self.RED, self.BLUE),
        )

    def test_flip_all_three(self) -> None:
        self.assertEqual(
            self._corners(
                1 | FLIP_DIAGONAL_FLAG | FLIP_HORIZONTAL_FLAG | FLIP_VERTICAL_FLAG
            ),
            (self.YELLOW, self.GREEN, self.BLUE, self.RED),
        )

    def test_get_gid_strips_flags(self) -> None:
        ground = self.tilemap.add_layer("ground")
        ground[0][0] = 1 | FLIP_HORIZONTAL_FLAG | FLIP_DIAGONAL_FLAG
        self.assertEqual(self.tilemap.get_gid("ground", 0, 0), 1)

    def test_get_flip(self) -> None:
        ground = self.tilemap.add_layer("ground")
        ground[0][0] = 1 | FLIP_HORIZONTAL_FLAG | FLIP_DIAGONAL_FLAG
        self.assertEqual(self.tilemap.get_flip("ground", 0, 0), (True, False, True))

    def test_get_flip_defaults_to_no_flip(self) -> None:
        ground = self.tilemap.add_layer("ground")
        ground[0][0] = 1
        self.assertEqual(self.tilemap.get_flip("ground", 0, 0), (False, False, False))

    def test_tileset_for_gid_accepts_raw_gid(self) -> None:
        self.assertIs(
            self.tilemap.tileset_for_gid(1 | FLIP_HORIZONTAL_FLAG), self.tileset
        )

    def test_properties_of_gid_accepts_raw_gid(self) -> None:
        tileset = Tileset(
            self.tileset.image,
            2,
            2,
            first_gid=1,
            tile_properties={0: {"collision": "solid"}},
        )
        tilemap = TileMap(tile_width=2, tile_height=2, cols=1, rows=1)
        tilemap.add_tileset(tileset)
        self.assertEqual(
            tilemap.properties_of_gid(1 | FLIP_VERTICAL_FLAG), {"collision": "solid"}
        )


if __name__ == "__main__":
    unittest.main()
