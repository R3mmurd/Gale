import unittest

import pygame

from gale.camera import Camera
from gale.tilemap import TileMap, Tileset


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


if __name__ == "__main__":
    unittest.main()
