import unittest

import pygame

from gale.tilemap import (
    CollisionType,
    TileMap,
    Tileset,
    collision_type_at,
    move_and_collide,
)


def make_tilemap(cols: int = 8, rows: int = 8) -> TileMap:
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    image = pygame.Surface(
        (32, 16)
    )  # 2 tiles of 16x16: gid 1 (solid), gid 2 (platform)
    tileset = Tileset(
        image,
        16,
        16,
        first_gid=1,
        tile_properties={
            0: {"collision": "solid"},
            1: {"collision": "platform"},
        },
    )
    tilemap = TileMap(tile_width=16, tile_height=16, cols=cols, rows=rows)
    tilemap.add_tileset(tileset)
    tilemap.add_layer("ground")
    return tilemap


class CollisionTypeAtTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tilemap = make_tilemap()

    def tearDown(self) -> None:
        pygame.display.quit()

    def test_empty_cell_is_none(self) -> None:
        self.assertEqual(
            collision_type_at(self.tilemap, "ground", 0, 0), CollisionType.NONE
        )

    def test_out_of_bounds_is_none(self) -> None:
        self.assertEqual(
            collision_type_at(self.tilemap, "ground", 100, 100), CollisionType.NONE
        )

    def test_solid_tile(self) -> None:
        self.tilemap.set_gid("ground", 2, 2, 1)
        self.assertEqual(
            collision_type_at(self.tilemap, "ground", 2, 2), CollisionType.SOLID
        )

    def test_platform_tile(self) -> None:
        self.tilemap.set_gid("ground", 2, 2, 2)
        self.assertEqual(
            collision_type_at(self.tilemap, "ground", 2, 2), CollisionType.PLATFORM
        )

    def test_custom_property_name(self) -> None:
        image = pygame.Surface((16, 16))
        tileset = Tileset(
            image, 16, 16, first_gid=1, tile_properties={0: {"blocks": "solid"}}
        )
        tilemap = TileMap(16, 16, cols=4, rows=4)
        tilemap.add_tileset(tileset)
        tilemap.add_layer("ground")
        tilemap.set_gid("ground", 0, 0, 1)
        self.assertEqual(
            collision_type_at(tilemap, "ground", 0, 0, collision_property="blocks"),
            CollisionType.SOLID,
        )


class MoveAndCollideTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tilemap = make_tilemap()

    def tearDown(self) -> None:
        pygame.display.quit()

    def test_unobstructed_move(self) -> None:
        rect = pygame.Rect(0, 0, 12, 12)
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 5, 5)
        self.assertEqual(new_rect.topleft, (5, 5))
        self.assertFalse(cx)
        self.assertFalse(cy)

    def test_stops_against_solid_wall_moving_right(self) -> None:
        self.tilemap.set_gid("ground", 0, 3, 1)  # solid at col 3, x in [48, 64)
        rect = pygame.Rect(0, 0, 12, 12)
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 100, 0)
        self.assertEqual(new_rect.right, 48)
        self.assertTrue(cx)

    def test_stops_against_solid_wall_moving_left(self) -> None:
        self.tilemap.set_gid("ground", 0, 1, 1)  # solid at col 1, x in [16, 32)
        rect = pygame.Rect(50, 0, 12, 12)
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, -100, 0)
        self.assertEqual(new_rect.left, 32)
        self.assertTrue(cx)

    def test_does_not_tunnel_through_solid_wall_on_a_fast_move(self) -> None:
        self.tilemap.set_gid("ground", 5, 2, 1)  # solid at row 5, y in [80, 96)
        rect = pygame.Rect(32, 0, 12, 12)
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 0, 200)
        self.assertEqual(new_rect.bottom, 80)
        self.assertTrue(cy)

    def test_platform_stops_downward_landing(self) -> None:
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform at row 3, y in [48, 64)
        rect = pygame.Rect(32, 0, 12, 12)
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 0, 100)
        self.assertEqual(new_rect.bottom, 48)
        self.assertTrue(cy)

    def test_platform_does_not_block_moving_up_through_it(self) -> None:
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform at row 3, y in [48, 64)
        rect = pygame.Rect(32, 80, 12, 12)  # starts below the platform
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 0, -60)
        self.assertFalse(cy)
        self.assertEqual(new_rect.top, 20)

    def test_platform_does_not_block_sideways_movement(self) -> None:
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform at row 3, y in [48, 64)
        rect = pygame.Rect(0, 50, 12, 12)  # vertically inside the platform's row
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 100, 0)
        self.assertFalse(cx)
        self.assertEqual(new_rect.left, 100)

    def test_platform_does_not_stop_a_body_already_below_it_moving_down(self) -> None:
        # A body that starts already below the platform's top edge (e.g.
        # having walked under it) should be able to keep moving down,
        # matching real one-way-platform behavior.
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform top at y=48
        rect = pygame.Rect(32, 52, 12, 12)
        new_rect, cx, cy = move_and_collide(self.tilemap, "ground", rect, 0, 10)
        self.assertFalse(cy)
        self.assertEqual(new_rect.top, 62)


if __name__ == "__main__":
    unittest.main()
