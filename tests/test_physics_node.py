import unittest

from gale.physics.node import Node
from gale.physics.shapes import CircleShape
from gale.physics.world import World


class NodeTestCase(unittest.TestCase):
    def test_fixed_position_without_body_or_parent(self) -> None:
        node = Node(x=10, y=20)
        self.assertEqual(tuple(node.world_position), (10, 20))

    def test_body_drives_position(self) -> None:
        world = World(gravity=(0, 900))
        body = world.create_dynamic_body(50, 0, CircleShape(radius=5))
        node = Node(body=body)

        world.fixed_update()
        node.update(1 / 60)

        self.assertAlmostEqual(node.world_position.x, body.position.x)
        self.assertAlmostEqual(node.world_position.y, body.position.y)
        self.assertGreater(node.world_position.y, 0)

    def test_child_offset_from_parent(self) -> None:
        parent = Node(x=100, y=100)
        child = Node(x=5, y=-5)
        parent.add_child(child)

        self.assertEqual(tuple(child.world_position), (105, 95))

    def test_child_follows_parent_body(self) -> None:
        world = World(gravity=(0, 0))
        body = world.create_dynamic_body(0, 0)
        parent = Node(body=body)
        decoration = Node(x=10, y=0)
        parent.add_child(decoration)

        body.position = (50, 50)
        parent.update(0)

        self.assertAlmostEqual(decoration.world_position.x, 60, places=3)
        self.assertAlmostEqual(decoration.world_position.y, 50, places=3)

    def test_remove_child(self) -> None:
        parent = Node()
        child = Node()
        parent.add_child(child)
        parent.remove_child(child)
        self.assertIsNone(child.parent)
        self.assertNotIn(child, parent.children)

    def test_update_recurses_into_children(self) -> None:
        world = World(gravity=(0, 900))
        body = world.create_dynamic_body(0, 0, CircleShape(radius=5))
        root = Node()
        child = Node(body=body)
        root.add_child(child)

        world.fixed_update()
        root.update(1 / 60)

        self.assertAlmostEqual(child.world_position.y, body.position.y)


if __name__ == "__main__":
    unittest.main()
