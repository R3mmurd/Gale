from typing import Optional
import unittest


from gale.factory import Factory


class FactoryTestCase(unittest.TestCase):
    class GameObject:
        def __init__(
            self, x: float, y: float, texture_name: Optional[str] = None
        ) -> None:
            self.x = x
            self.y = y
            self.texture_name = texture_name or "default_texture.png"

    def setUp(self) -> None:
        self.factory = Factory(FactoryTestCase.GameObject)

    def test_create_game_object_successfully(self) -> None:
        game_object = self.factory.create(5, 8, {"texture_name": "texture.png"})
        self.assertIsInstance(game_object, FactoryTestCase.GameObject)
        self.assertEqual(game_object.x, 5)
        self.assertEqual(game_object.y, 8)
        self.assertEqual(game_object.texture_name, "texture.png")

    def test_create_game_object_without_properties(self) -> None:
        game_object = self.factory.create(5, 8)
        self.assertIsInstance(game_object, FactoryTestCase.GameObject)
        self.assertEqual(game_object.x, 5)
        self.assertEqual(game_object.y, 8)
        self.assertEqual(game_object.texture_name, "default_texture.png")

    def test_create_game_object_failed(self) -> None:
        with self.assertRaises(TypeError) as ex:
            self.factory.create(5, 8, "texture_name.png")
        self.assertEqual(str(ex.exception), "Argument properties is not a dict")
