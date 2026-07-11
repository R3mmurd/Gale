from dataclasses import dataclass
import unittest

from gale.ecs import System, SystemScheduler, World


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Velocity:
    dx: float
    dy: float


@dataclass
class Fatigue:
    stamina: float


class WorldTestCase(unittest.TestCase):
    def test_create_entity_returns_unique_ids(self) -> None:
        world = World()
        a = world.create_entity()
        b = world.create_entity()
        self.assertNotEqual(a, b)
        self.assertTrue(world.has_entity(a))
        self.assertTrue(world.has_entity(b))

    def test_destroy_entity_removes_its_components(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(0, 0))
        world.add_component(entity, Velocity(1, 1))

        world.destroy_entity(entity)

        self.assertFalse(world.has_entity(entity))
        self.assertFalse(world.has_component(entity, Position))
        self.assertFalse(world.has_component(entity, Velocity))
        self.assertIsNone(world.get_component(entity, Position))

    def test_destroy_entity_does_not_raise_if_already_gone(self) -> None:
        world = World()
        entity = world.create_entity()
        world.destroy_entity(entity)
        world.destroy_entity(entity)  # should not raise

    def test_add_get_has_remove_component_round_trip(self) -> None:
        world = World()
        entity = world.create_entity()

        self.assertFalse(world.has_component(entity, Position))
        self.assertIsNone(world.get_component(entity, Position))

        world.add_component(entity, Position(3, 4))
        self.assertTrue(world.has_component(entity, Position))
        self.assertEqual(world.get_component(entity, Position), Position(3, 4))

        world.remove_component(entity, Position)
        self.assertFalse(world.has_component(entity, Position))
        self.assertIsNone(world.get_component(entity, Position))

    def test_add_component_raises_for_unknown_entity(self) -> None:
        world = World()
        with self.assertRaises(KeyError):
            world.add_component(999, Position(0, 0))

    def test_query_returns_only_entities_with_all_component_types(self) -> None:
        world = World()

        ball = world.create_entity()
        world.add_component(ball, Position(0, 0))
        world.add_component(ball, Velocity(5, 0))

        player = world.create_entity()
        world.add_component(player, Position(10, 10))
        world.add_component(player, Velocity(0, 1))
        world.add_component(player, Fatigue(100))

        spectator = world.create_entity()
        world.add_component(spectator, Position(20, 20))  # no Velocity

        results = {
            entity: (position, velocity)
            for entity, position, velocity in world.query(Position, Velocity)
        }

        self.assertEqual(set(results.keys()), {ball, player})
        self.assertEqual(results[ball], (Position(0, 0), Velocity(5, 0)))
        self.assertEqual(results[player], (Position(10, 10), Velocity(0, 1)))

        fatigue_results = list(world.query(Fatigue))
        self.assertEqual(len(fatigue_results), 1)
        self.assertEqual(fatigue_results[0], (player, Fatigue(100)))

    def test_query_yields_tuples_in_requested_order(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(1, 2))
        world.add_component(entity, Velocity(3, 4))

        (result,) = list(world.query(Velocity, Position))
        self.assertEqual(result, (entity, Velocity(3, 4), Position(1, 2)))

    def test_query_requires_at_least_one_component_type(self) -> None:
        world = World()
        with self.assertRaises(ValueError):
            list(world.query())

    def test_destroying_one_entity_does_not_affect_query_over_others(self) -> None:
        world = World()

        entities = []
        for i in range(5):
            entity = world.create_entity()
            world.add_component(entity, Position(i, i))
            entities.append(entity)

        world.destroy_entity(entities[2])

        remaining = {entity for entity, _ in world.query(Position)}
        self.assertEqual(remaining, set(entities) - {entities[2]})


class MovementSystem(System):
    def update(self, world: World, dt: float) -> None:
        for entity, position, velocity in world.query(Position, Velocity):
            position.x += velocity.dx * dt
            position.y += velocity.dy * dt


class SystemSchedulerTestCase(unittest.TestCase):
    def test_update_runs_scheduled_systems_and_mutates_world(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(0, 0))
        world.add_component(entity, Velocity(10, -5))

        scheduler = SystemScheduler([MovementSystem()])
        scheduler.update(world, dt=2.0)

        position = world.get_component(entity, Position)
        self.assertEqual(position, Position(20, -10))

    def test_add_system_appends_after_existing_ones(self) -> None:
        world = World()
        entity = world.create_entity()
        world.add_component(entity, Position(0, 0))
        world.add_component(entity, Velocity(1, 0))

        scheduler = SystemScheduler([])
        scheduler.add_system(MovementSystem())
        scheduler.update(world, dt=1.0)

        self.assertEqual(world.get_component(entity, Position), Position(1, 0))

    def test_base_system_update_raises_not_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            System().update(World(), 0.1)


if __name__ == "__main__":
    unittest.main()
