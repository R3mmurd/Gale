"""
This file contains the implementation of the class Agent, a modular and
reusable base to build autonomous characters (vehicles, people, animals,
or any kind of creature) by composing a Kinematic body with steering
behaviors, a behavior tree, and/or a decision tree.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Optional

import pygame

from .behavior_tree import BehaviorTree
from .decision_tree import DecisionTree
from .steering import Kinematic, SteeringBehavior, SteeringOutput


class Agent:
    """
    Base class for an autonomous character.

    An agent is a Kinematic body (position, orientation, velocity, and
    rotation) driven by up to two independent, swappable pieces:

    - A steering behavior that produces the linear and angular
      acceleration used to move and orientate the agent on every update.
    - A "brain" (a BehaviorTree or a DecisionTree) that decides which
      steering behavior, or any other property, the agent should be
      using at any given moment.

    Both pieces are optional and can be replaced at any time through
    set_steering_behavior and set_brain. That keeps agents personalizable
    and reusable: the same Agent (or a subclass of it) can drive a
    chaser, a wanderer, or a guard just by plugging different steering
    behaviors and/or brains, and it plays nicely with gale.factory.Factory
    since its constructor accepts x and y as its first two parameters.

    Usage example:

        agent = Agent(x=10, y=10, max_speed=150)
        target = Kinematic(x=200, y=80)
        agent.set_steering_behavior(Seek(agent.kinematic, target))

        # In the game loop:
        agent.update(dt)
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        orientation: float = 0,
        max_speed: float = 200,
        max_acceleration: float = 200,
        max_rotation: float = 6.283185307179586,
        max_angular_acceleration: float = 12.566370614359172,
        face_movement_direction: bool = True,
        steering_behavior: Optional[SteeringBehavior] = None,
        brain: Optional[Any] = None,
    ) -> None:
        """
        :param x: Initial x component of the position.
        :param y: Initial y component of the position.
        :param orientation: Initial orientation, in radians.
        :param max_speed: Maximum speed the agent can reach.
        :param max_acceleration: Maximum linear acceleration the agent can receive.
        :param max_rotation: Maximum angular speed the agent can reach.
        :param max_angular_acceleration: Maximum angular acceleration the agent can receive.
        :param face_movement_direction: Whether the agent should automatically rotate to face its current velocity when its steering behavior does not produce an explicit angular acceleration. The default value is True.
        :param steering_behavior: The steering behavior driving the agent's movement. The default value is None, so the agent does not accelerate until one is set with set_steering_behavior.
        :param brain: A BehaviorTree or a DecisionTree (or any object exposing a compatible tick/make_decision interface) used to decide the agent's behavior on every update. The default value is None.
        """
        self.kinematic: Kinematic = Kinematic(
            x,
            y,
            orientation=orientation,
            max_speed=max_speed,
            max_acceleration=max_acceleration,
            max_rotation=max_rotation,
            max_angular_acceleration=max_angular_acceleration,
        )
        self.face_movement_direction: bool = face_movement_direction
        self.steering_behavior: Optional[SteeringBehavior] = steering_behavior
        self.brain: Optional[Any] = brain

    @property
    def position(self) -> pygame.Vector2:
        return self.kinematic.position

    @property
    def orientation(self) -> float:
        return self.kinematic.orientation

    @property
    def velocity(self) -> pygame.Vector2:
        return self.kinematic.velocity

    def set_steering_behavior(
        self, steering_behavior: Optional[SteeringBehavior]
    ) -> None:
        """
        Replace the steering behavior driving this agent's movement.

        :param steering_behavior: The new steering behavior. Use None to stop applying acceleration (the agent keeps moving with its current velocity).
        """
        self.steering_behavior = steering_behavior

    def set_brain(self, brain: Optional[Any]) -> None:
        """
        Replace the brain deciding this agent's behavior.

        :param brain: A BehaviorTree, a DecisionTree, or any object exposing a compatible tick(agent, dt)/make_decision(agent) method. Use None to disable decision making.
        """
        self.brain = brain

    def think(self, dt: float) -> None:
        """
        Run the agent's brain, if any, typically to update its steering
        behavior and/or any other of its properties.

        :param dt: Time elapsed (in seconds) since the last update.
        :raises TypeError: If brain is set and it is not a BehaviorTree nor a DecisionTree.
        """
        if self.brain is None:
            return

        if isinstance(self.brain, BehaviorTree):
            self.brain.tick(self, dt)
        elif isinstance(self.brain, DecisionTree):
            self.brain.make_decision(self)
        else:
            raise TypeError("brain must be a BehaviorTree, a DecisionTree, or None")

    def update(self, dt: float) -> None:
        """
        Update the agent for one time step: run its brain, compute its
        steering, and integrate its movement.

        :param dt: Time elapsed (in seconds) since the last update.
        """
        self.think(dt)

        steering = (
            self.steering_behavior.get_steering(dt)
            if self.steering_behavior is not None
            else SteeringOutput()
        )

        self.kinematic.update(steering, dt)

        if (
            self.face_movement_direction
            and steering.angular == 0
            and self.kinematic.velocity.length_squared() > 0
        ):
            self.kinematic.orientation = Kinematic.vector_to_orientation(
                self.kinematic.velocity
            )
