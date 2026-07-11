`← Back to the main README <../../README.rst>`_

gale.ecs
=========

``gale.ecs`` is a Data-Oriented Design (ECS) toolkit for managing large
numbers of similar entities efficiently: the ball, every player on the
pitch, every collider in a match. An ``Entity`` is just an integer id, a
component is any plain Python object the game defines itself (typically
a small ``@dataclass``), and a ``System`` queries the ``World`` for a
combination of components and processes every matching entity in one
pass, instead of each entity carrying its own update method.

World, entities, and components
--------------------------------

.. code-block:: python

   from dataclasses import dataclass

   from gale.ecs import World


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


   world = World()

   ball = world.create_entity()
   world.add_component(ball, Position(0, 0))
   world.add_component(ball, Velocity(120, 0))

   player = world.create_entity()
   world.add_component(player, Position(10, 10))
   world.add_component(player, Velocity(0, 0))
   world.add_component(player, Fatigue(stamina=100))

``get_component``, ``has_component``, and ``remove_component`` round out
the basic storage API, and ``destroy_entity`` removes an entity together
with every component attached to it:

.. code-block:: python

   world.has_component(player, Fatigue)  # True
   world.get_component(player, Fatigue)  # Fatigue(stamina=100)

   world.destroy_entity(ball)  # ball's Position and Velocity are gone too

Querying entities
------------------

``World.query`` yields ``(entity, component1, component2, ...)`` tuples
for every entity that has *all* of the requested component types, which
is exactly what a system needs to process a batch of similar entities
without caring about anything else attached to them:

.. code-block:: python

   for entity, position, fatigue in world.query(Position, Fatigue):
       print(entity, position, fatigue)  # only entities with both components

Systems
-------

A ``System`` is a small class with an ``update(world, dt)`` method that
queries the world and mutates whatever components it cares about.
``SystemScheduler`` runs an ordered list of systems every frame, the same
way ``gale.state.StateMachine`` is a small orchestrator kept separate
from the states it drives:

.. code-block:: python

   from gale.ecs import System, SystemScheduler


   class MovementSystem(System):
       def update(self, world, dt) -> None:
           for entity, position, velocity in world.query(Position, Velocity):
               position.x += velocity.dx * dt
               position.y += velocity.dy * dt


   class FatigueSystem(System):
       def update(self, world, dt) -> None:
           for entity, fatigue, velocity in world.query(Fatigue, Velocity):
               moving = velocity.dx != 0 or velocity.dy != 0
               fatigue.stamina -= (5 if moving else -2) * dt
               fatigue.stamina = max(0, min(100, fatigue.stamina))


   scheduler = SystemScheduler([MovementSystem(), FatigueSystem()])

   # In your game loop:
   scheduler.update(world, dt)

Systems stay decoupled from one another this way: ``MovementSystem``
only ever looks at ``Position``/``Velocity`` and ``FatigueSystem`` only
at ``Fatigue``/``Velocity`` — neither one needs to know the other
exists, or anything about the ball versus a player, only about the
components they agree to operate on.
