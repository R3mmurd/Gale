from typing import Optional
import unittest


from gale.factory import AbstractFactory, Factory


class GameObject:
    def __init__(
        self, x: float, y: float, texture_name: Optional[str] = None
    ) -> None:
        self.x = x
        self.y = y
        self.texture_name = texture_name or "default_texture.png"


class FactoryTestCase(unittest.TestCase):
    
    def setUp(self) -> None:
        self.factory = Factory(GameObject)

    def test_create_game_object_successfully(self) -> None:
        game_object = self.factory.create(5, 8, {"texture_name": "texture.png"})
        self.assertIsInstance(game_object, GameObject)
        self.assertEqual(game_object.x, 5)
        self.assertEqual(game_object.y, 8)
        self.assertEqual(game_object.texture_name, "texture.png")

    def test_create_game_object_without_properties(self) -> None:
        game_object = self.factory.create(5, 8)
        self.assertIsInstance(game_object, GameObject)
        self.assertEqual(game_object.x, 5)
        self.assertEqual(game_object.y, 8)
        self.assertEqual(game_object.texture_name, "default_texture.png")

    def test_create_game_object_failed(self) -> None:
        with self.assertRaises(TypeError) as ex:
            self.factory.create(5, 8, "texture_name.png")
        self.assertEqual(str(ex.exception), "Argument properties is not a dict")


class AbstractFactoryTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.abstract_factory = AbstractFactory(__name__)
    
    def test_create_game_object_factory_successfully(self) -> None:
        game_object_factory = self.abstract_factory.get_factory("GameObject")
        self.assertIs(game_object_factory._prototype, GameObject)

    def test_create_game_object_factory_failed(self) -> None:
        with self.assertRaises(ValueError) as ex:
            self.abstract_factory.get_factory("GameEntity")
        self.assertEqual(str(ex.exception), "There is no class called GameEntity")
