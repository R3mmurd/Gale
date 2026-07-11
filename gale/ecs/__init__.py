"""
gale.ecs: a Data-Oriented Design (ECS) toolkit for managing large numbers
of similar entities efficiently — entities are plain integer ids,
components are plain Python objects the game defines itself, and a
System queries the World for a combination of components to process
every frame (physics integration, fatigue decay, collision checks, ...).

See docs/examples/ecs.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from .world import Entity, World
from .system import System, SystemScheduler
