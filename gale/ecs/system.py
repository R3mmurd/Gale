"""
This file contains the implementation of the class System, the base for
any piece of per-frame logic that operates on a gale.ecs.World's
entities, and SystemScheduler, a small orchestrator that runs an
ordered list of systems every frame.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import List

from .world import World


class System:
    """
    Base class for any system: a piece of logic that queries a World for
    entities with a given combination of components and does something
    with them every frame, such as integrating physics, decaying
    fatigue, or checking collisions. Subclasses should override update.
    """

    def update(self, world: World, dt: float) -> None:
        """
        Run this system's logic once over world.

        :param world: The world to query and mutate.
        :param dt: Time elapsed, in seconds, since the last call.
        """
        raise NotImplementedError()


class SystemScheduler:
    """
    Runs an ordered list of systems against a World every frame, mirroring
    how gale.state.StateMachine is a separate small orchestrator instead
    of baking dispatch into BaseState: SystemScheduler only knows how to
    run systems in order, it does not own or know anything about the
    World's storage.

    Usage example:

        scheduler = SystemScheduler([MovementSystem(), FatigueSystem()])

        # Every frame:
        scheduler.update(world, dt)
    """

    def __init__(self, systems: List[System]) -> None:
        """
        :param systems: The systems to run, in order, on every update.
        """
        self.systems: List[System] = list(systems)

    def add_system(self, system: System) -> None:
        """
        Append a system to run after every system already scheduled.

        :param system: The system to add.
        """
        self.systems.append(system)

    def update(self, world: World, dt: float) -> None:
        """
        Run every scheduled system, in order, against world.

        :param world: The world to pass to each system's update.
        :param dt: Time elapsed, in seconds, since the last call.
        """
        for system in self.systems:
            system.update(world, dt)
