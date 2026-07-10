import json
import os
import tempfile
import unittest

import pygame

from gale.tilemap import TiledLoadError, load_tiled_map


def _save_tileset_image(path: str) -> None:
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    surface = pygame.Surface((32, 16))  # 2 tiles of 16x16
    pygame.image.save(surface, path)


class LoadTiledMapTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        _save_tileset_image(os.path.join(self.dir, "tiles.png"))

    def tearDown(self) -> None:
        pygame.display.quit()
        self._tmp.cleanup()

    def _write_map(self, map_data: dict, name: str = "level.json") -> str:
        path = os.path.join(self.dir, name)

        with open(path, "w") as f:
            json.dump(map_data, f)

        return path

    def _base_map(self) -> dict:
        return {
            "width": 4,
            "height": 3,
            "tilewidth": 16,
            "tileheight": 16,
            "infinite": False,
            "tilesets": [
                {
                    "firstgid": 1,
                    "image": "tiles.png",
                    "tilewidth": 16,
                    "tileheight": 16,
                    "tiles": [
                        {
                            "id": 0,
                            "properties": [
                                {
                                    "name": "collision",
                                    "type": "string",
                                    "value": "solid",
                                }
                            ],
                        }
                    ],
                }
            ],
            "layers": [
                {
                    "type": "group",
                    "name": "world",
                    "layers": [
                        {
                            "type": "tilelayer",
                            "name": "ground",
                            "width": 4,
                            "height": 3,
                            "data": [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
                        }
                    ],
                },
                {
                    "type": "objectgroup",
                    "name": "spawns",
                    "objects": [
                        {
                            "name": "player_start",
                            "type": "spawn",
                            "x": 16,
                            "y": 0,
                            "width": 16,
                            "height": 16,
                            "properties": [
                                {"name": "facing", "type": "string", "value": "right"}
                            ],
                        }
                    ],
                },
            ],
        }

    def test_loads_dimensions(self) -> None:
        tilemap = load_tiled_map(self._write_map(self._base_map()))
        self.assertEqual(tilemap.cols, 4)
        self.assertEqual(tilemap.rows, 3)
        self.assertEqual(tilemap.tile_width, 16)
        self.assertEqual(tilemap.tile_height, 16)

    def test_flattens_groups_into_layers(self) -> None:
        tilemap = load_tiled_map(self._write_map(self._base_map()))
        self.assertEqual(tilemap.layer_names(), ["ground"])

    def test_tile_layer_data_reshaped_into_rows(self) -> None:
        tilemap = load_tiled_map(self._write_map(self._base_map()))
        ground = tilemap.get_layer("ground")
        self.assertEqual(ground, [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0]])

    def test_object_layer_parsed_with_properties(self) -> None:
        tilemap = load_tiled_map(self._write_map(self._base_map()))
        spawns = tilemap.object_layers["spawns"]
        self.assertEqual(len(spawns), 1)
        spawn = spawns[0]
        self.assertEqual(spawn.name, "player_start")
        self.assertEqual(spawn.type, "spawn")
        self.assertEqual((spawn.x, spawn.y), (16, 0))
        self.assertEqual(spawn.properties, {"facing": "right"})

    def test_tile_properties_loaded(self) -> None:
        tilemap = load_tiled_map(self._write_map(self._base_map()))
        self.assertEqual(tilemap.properties_of_gid(1), {"collision": "solid"})

    def test_external_json_tileset(self) -> None:
        tileset_data = {
            "image": "tiles.png",
            "tilewidth": 16,
            "tileheight": 16,
            "tiles": [
                {
                    "id": 0,
                    "properties": [
                        {"name": "collision", "type": "string", "value": "solid"}
                    ],
                }
            ],
        }

        with open(os.path.join(self.dir, "tiles.tsj"), "w") as f:
            json.dump(tileset_data, f)

        map_data = self._base_map()
        map_data["tilesets"] = [{"firstgid": 1, "source": "tiles.tsj"}]
        tilemap = load_tiled_map(self._write_map(map_data))

        self.assertEqual(tilemap.properties_of_gid(1), {"collision": "solid"})

    def test_external_tsx_tileset_raises(self) -> None:
        map_data = self._base_map()
        map_data["tilesets"] = [{"firstgid": 1, "source": "tiles.tsx"}]

        with self.assertRaises(TiledLoadError):
            load_tiled_map(self._write_map(map_data))

    def test_infinite_map_raises(self) -> None:
        map_data = self._base_map()
        map_data["infinite"] = True

        with self.assertRaises(TiledLoadError):
            load_tiled_map(self._write_map(map_data))

    def test_compressed_layer_data_raises(self) -> None:
        map_data = self._base_map()
        map_data["layers"][0]["layers"][0]["data"] = "not-a-list-base64-or-whatever"

        with self.assertRaises(TiledLoadError):
            load_tiled_map(self._write_map(map_data))


if __name__ == "__main__":
    unittest.main()
