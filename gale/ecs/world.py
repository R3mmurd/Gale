"""
This file contains the implementation of the class World: a Data-Oriented
Design (ECS) store of entities (plain integer ids) and the components
(plain Python objects) attached to them, plus the queries a System needs
to find every entity that has a given combination of components.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Dict, Iterator, Optional, Tuple, Type

Entity = int


class World:
    """
    A Data-Oriented Design (ECS) store: entities are just integer ids,
    components are plain Python objects the game defines itself (a
    dataclass such as ``Position(x, y)`` or ``Fatigue(stamina)``), and a
    System (see gale.ecs.system) is whatever code queries the world for a
    combination of components and does something with them every frame.

    This is meant for scenarios where a lot of similar entities (the
    ball, every player on the pitch, every collider) need the same kind
    of processing (physics integration, fatigue decay, collision
    checks) applied to all of them in a batch, which a plain
    object-oriented "one class per entity with its own update method"
    design tends to make either rigid (every entity needs every
    behavior it could ever use) or entangled (behaviors reach into each
    other directly). Storing components by type instead of by entity
    keeps each system's data ready to be iterated over in one pass, and
    keeps behaviors decoupled: a MovementSystem only needs to know about
    Position and Velocity, never about Fatigue or the ball at all.

    Usage example:

        from dataclasses import dataclass

        @dataclass
        class Position:
            x: float
            y: float

        @dataclass
        class Velocity:
            dx: float
            dy: float

        world = World()
        player = world.create_entity()
        world.add_component(player, Position(0, 0))
        world.add_component(player, Velocity(10, 0))

        for entity, position, velocity in world.query(Position, Velocity):
            position.x += velocity.dx
            position.y += velocity.dy

        world.destroy_entity(player)  # drops Position and Velocity too
    """

    def __init__(self) -> None:
        self._next_entity_id: int = 0
        self._entities: set = set()
        self._components: Dict[Type, Dict[Entity, Any]] = {}

    def create_entity(self) -> Entity:
        """
        :returns: A new entity id, unique for the lifetime of this world.
        """
        entity = self._next_entity_id
        self._next_entity_id += 1
        self._entities.add(entity)
        return entity

    def destroy_entity(self, entity: Entity) -> None:
        """
        Remove entity and every component attached to it. Does nothing if
        entity does not exist (or was already destroyed).

        :param entity: The entity to destroy.
        """
        self._entities.discard(entity)

        for components in self._components.values():
            components.pop(entity, None)

    def has_entity(self, entity: Entity) -> bool:
        """
        :param entity: The entity to look for.
        :returns: Whether entity currently exists in this world.
        """
        return entity in self._entities

    def add_component(self, entity: Entity, component: Any) -> None:
        """
        Attach component to entity, keyed by its type. Attaching another
        component of the same type replaces the previous one.

        :param entity: The entity to attach the component to.
        :param component: The component instance to attach.
        :raises KeyError: If entity does not exist.
        """
        if entity not in self._entities:
            raise KeyError(entity)

        self._components.setdefault(type(component), {})[entity] = component

    def remove_component(self, entity: Entity, component_type: Type) -> None:
        """
        Detach the component of the given type from entity. Does nothing
        if entity has no component of that type.

        :param entity: The entity to detach the component from.
        :param component_type: The type of the component to detach.
        """
        self._components.get(component_type, {}).pop(entity, None)

    def get_component(self, entity: Entity, component_type: Type) -> Optional[Any]:
        """
        :param entity: The entity to look up.
        :param component_type: The type of the component to fetch.
        :returns: The component of that type attached to entity, or None if it has none.
        """
        return self._components.get(component_type, {}).get(entity)

    def has_component(self, entity: Entity, component_type: Type) -> bool:
        """
        :param entity: The entity to look up.
        :param component_type: The type of the component to check for.
        :returns: Whether entity has a component of that type attached.
        """
        return entity in self._components.get(component_type, {})

    def query(self, *component_types: Type) -> Iterator[Tuple[Any, ...]]:
        """
        Find every entity that has all of the given component types.
        This is the hot path a System calls every frame, so it iterates
        the smallest of the requested component stores (fewer candidate
        entities to check against the others) instead of every entity in
        the world.

        :param component_types: One or more component types an entity must have all of.
        :returns: An iterator of tuples ``(entity, component1, component2, ...)``, one per matching entity, with the components in the same order as component_types.
        :raises ValueError: If called with no component types.
        """
        if not component_types:
            raise ValueError("query requires at least one component type")

        stores = [
            self._components.get(component_type, {})
            for component_type in component_types
        ]
        smallest_store = min(stores, key=len)

        for entity in smallest_store:
            if all(entity in store for store in stores):
                yield (entity,) + tuple(store[entity] for store in stores)
