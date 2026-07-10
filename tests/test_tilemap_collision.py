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
        x, y, cx, cy = move_and_collide(self.tilemap, "ground", 0, 0, 12, 12, 5, 5)
        self.assertEqual((x, y), (5, 5))
        self.assertFalse(cx)
        self.assertFalse(cy)

    def test_stops_against_solid_wall_moving_right(self) -> None:
        self.tilemap.set_gid("ground", 0, 3, 1)  # solid at col 3, x in [48, 64)
        x, y, cx, cy = move_and_collide(self.tilemap, "ground", 0, 0, 12, 12, 100, 0)
        self.assertEqual(x, 36)  # 48 - width
        self.assertTrue(cx)

    def test_stops_against_solid_wall_moving_left(self) -> None:
        self.tilemap.set_gid("ground", 0, 1, 1)  # solid at col 1, x in [16, 32)
        x, y, cx, cy = move_and_collide(self.tilemap, "ground", 50, 0, 12, 12, -100, 0)
        self.assertEqual(x, 32)
        self.assertTrue(cx)

    def test_does_not_tunnel_through_solid_wall_on_a_fast_move(self) -> None:
        self.tilemap.set_gid("ground", 5, 2, 1)  # solid at row 5, y in [80, 96)
        x, y, cx, cy = move_and_collide(self.tilemap, "ground", 32, 0, 12, 12, 0, 200)
        self.assertEqual(y, 68)  # 80 - height
        self.assertTrue(cy)

    def test_platform_stops_downward_landing(self) -> None:
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform at row 3, y in [48, 64)
        x, y, cx, cy = move_and_collide(self.tilemap, "ground", 32, 0, 12, 12, 0, 100)
        self.assertEqual(y, 36)  # 48 - height
        self.assertTrue(cy)

    def test_platform_does_not_block_moving_up_through_it(self) -> None:
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform at row 3, y in [48, 64)
        x, y, cx, cy = move_and_collide(
            self.tilemap, "ground", 32, 80, 12, 12, 0, -60
        )  # starts below the platform
        self.assertFalse(cy)
        self.assertEqual(y, 20)

    def test_platform_does_not_block_sideways_movement(self) -> None:
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform at row 3, y in [48, 64)
        x, y, cx, cy = move_and_collide(
            self.tilemap, "ground", 0, 50, 12, 12, 100, 0
        )  # vertically inside the platform's row
        self.assertFalse(cx)
        self.assertEqual(x, 100)

    def test_platform_does_not_stop_a_body_already_below_it_moving_down(self) -> None:
        # A body that starts already below the platform's top edge (e.g.
        # having walked under it) should be able to keep moving down,
        # matching real one-way-platform behavior.
        self.tilemap.set_gid("ground", 3, 2, 2)  # platform top at y=48
        x, y, cx, cy = move_and_collide(self.tilemap, "ground", 32, 52, 12, 12, 0, 10)
        self.assertFalse(cy)
        self.assertEqual(y, 62)

    def test_settles_flush_against_the_ground_every_frame_under_gravity(self) -> None:
        # Regression test: a rounded/truncated position (e.g. going
        # through a pygame.Rect internally) loses sub-pixel movement,
        # which makes an entity resting under gravity re-fall and
        # re-collide only once every few frames instead of every
        # frame — this simulates exactly that scenario.
        self.tilemap.set_gid("ground", 4, 1, 1)  # solid floor at row 4, y in [64, 80)
        x, y = 20.0, 0.0
        vy = 0.0
        dt = 1 / 60
        gravity = 900.0

        for _ in range(120):
            vy = min(vy + gravity * dt, 500.0)
            x, y, _, collided_y = move_and_collide(
                self.tilemap, "ground", x, y, 12, 14, 0, vy * dt
            )

            if collided_y:
                vy = 0.0

        # By now it should have settled and be resting flush on top of
        # the floor (y + height == the floor's top edge) every frame.
        settled_frames = []

        for _ in range(10):
            vy = min(vy + gravity * dt, 500.0)
            x, y, _, collided_y = move_and_collide(
                self.tilemap, "ground", x, y, 12, 14, 0, vy * dt
            )

            if collided_y:
                vy = 0.0

            settled_frames.append(collided_y)

        self.assertTrue(all(settled_frames))
        self.assertEqual(y, 50.0)  # 64 - 14


if __name__ == "__main__":
    unittest.main()
