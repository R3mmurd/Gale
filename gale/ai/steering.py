"""
This file contains steering behaviors to compute the linear and angular
acceleration that autonomous characters (vehicles, people, animals, or
any kind of creature) need to move and orientate themselves, following
the classic formulation described by Ian Millington in "Artificial
Intelligence for Games".

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math
import random

from typing import Optional, Sequence, Tuple

import pygame


class SteeringOutput:
    """
    Groups the linear and angular acceleration produced by a steering
    behavior.
    """

    def __init__(
        self, linear: Optional[pygame.Vector2] = None, angular: float = 0
    ) -> None:
        """
        :param linear: Linear acceleration. The default value is a zero vector.
        :param angular: Angular acceleration (in radians per second squared).
        """
        self.linear: pygame.Vector2 = (
            pygame.Vector2() if linear is None else pygame.Vector2(linear)
        )
        self.angular: float = angular

    def __add__(self, other: "SteeringOutput") -> "SteeringOutput":
        return SteeringOutput(self.linear + other.linear, self.angular + other.angular)

    def __mul__(self, scalar: float) -> "SteeringOutput":
        return SteeringOutput(self.linear * scalar, self.angular * scalar)

    __rmul__ = __mul__

    def is_zero(self) -> bool:
        """
        :returns: Whether this steering does not produce any acceleration.
        """
        return self.linear.length_squared() == 0 and self.angular == 0


def _clamp_to_length(vector: pygame.Vector2, max_length: float) -> pygame.Vector2:
    if max_length <= 0:
        return pygame.Vector2()

    if vector.length_squared() > max_length * max_length:
        result = pygame.Vector2(vector)
        result.scale_to_length(max_length)
        return result

    return pygame.Vector2(vector)


class Kinematic:
    """
    Groups the physical state of a moving character: its position and
    orientation (in radians), together with their first derivatives,
    velocity and rotation (angular speed).
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        orientation: float = 0,
        max_speed: float = 200,
        max_acceleration: float = 200,
        max_rotation: float = math.pi * 2,
        max_angular_acceleration: float = math.pi * 4,
    ) -> None:
        """
        :param x: Initial x component of the position.
        :param y: Initial y component of the position.
        :param orientation: Initial orientation, in radians.
        :param max_speed: Maximum speed this kinematic can reach.
        :param max_acceleration: Maximum linear acceleration this kinematic can receive.
        :param max_rotation: Maximum angular speed this kinematic can reach.
        :param max_angular_acceleration: Maximum angular acceleration this kinematic can receive.
        """
        self.position: pygame.Vector2 = pygame.Vector2(x, y)
        self.velocity: pygame.Vector2 = pygame.Vector2()
        self.orientation: float = orientation
        self.rotation: float = 0
        self.max_speed: float = max_speed
        self.max_acceleration: float = max_acceleration
        self.max_rotation: float = max_rotation
        self.max_angular_acceleration: float = max_angular_acceleration

    @property
    def x(self) -> float:
        return self.position.x

    @property
    def y(self) -> float:
        return self.position.y

    def orientation_as_vector(self) -> pygame.Vector2:
        """
        :returns: A unit vector pointing towards the current orientation.
        """
        return pygame.Vector2(math.cos(self.orientation), math.sin(self.orientation))

    @staticmethod
    def vector_to_orientation(vector: pygame.Vector2) -> float:
        """
        :param vector: The vector to get the orientation from.
        :returns: The orientation, in radians, represented by the given vector. Zero if the vector has no length.
        """
        if vector.length_squared() == 0:
            return 0

        return math.atan2(vector.y, vector.x)

    def update(self, steering: SteeringOutput, dt: float) -> None:
        """
        Integrate this kinematic one time step forward by using the given
        steering output.

        :param steering: The linear and angular acceleration to apply.
        :param dt: Time elapsed (in seconds) since the last update.
        """
        self.position += self.velocity * dt
        self.orientation += self.rotation * dt

        self.velocity += steering.linear * dt
        self.rotation += steering.angular * dt

        if self.velocity.length_squared() > self.max_speed * self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        if abs(self.rotation) > self.max_rotation:
            self.rotation = math.copysign(self.max_rotation, self.rotation)


class SteeringBehavior:
    """
    Base class for any steering behavior. A steering behavior computes the
    linear and angular acceleration that a character should have to
    fulfil a movement goal, for instance, reaching a target, avoiding an
    obstacle, or wandering around.
    """

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        """
        Compute the steering output of this behavior.

        :param dt: Time elapsed (in seconds) since the last call. Only used by time-dependent behaviors, such as Wander.
        :returns: The computed steering output.
        """
        raise NotImplementedError()


class Seek(SteeringBehavior):
    """
    Steers the character to move towards the target as fast as possible.
    """

    def __init__(self, character: Kinematic, target: Kinematic) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target: The kinematic to move towards.
        """
        self.character: Kinematic = character
        self.target: Kinematic = target

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        direction = self.target.position - self.character.position

        if direction.length_squared() == 0:
            return SteeringOutput()

        direction.scale_to_length(self.character.max_acceleration)
        return SteeringOutput(linear=direction)


class Flee(Seek):
    """
    Steers the character to move away from the target as fast as
    possible.
    """

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        return Seek.get_steering(self, dt) * -1


class Arrive(SteeringBehavior):
    """
    Steers the character to reach the target and stop right there,
    slowing down as it approaches to avoid overshooting it.
    """

    def __init__(
        self,
        character: Kinematic,
        target: Kinematic,
        target_radius: float = 5,
        slow_radius: float = 100,
        time_to_target: float = 0.1,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target: The kinematic to arrive at.
        :param target_radius: Distance to the target below which the character is considered to have arrived.
        :param slow_radius: Distance to the target below which the character starts to slow down.
        :param time_to_target: Time in which the character should reach its target speed.
        """
        self.character: Kinematic = character
        self.target: Kinematic = target
        self.target_radius: float = target_radius
        self.slow_radius: float = slow_radius
        self.time_to_target: float = time_to_target

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        direction = self.target.position - self.character.position
        distance = direction.length()

        if distance < self.target_radius:
            return SteeringOutput()

        if distance > self.slow_radius:
            target_speed = self.character.max_speed
        else:
            target_speed = self.character.max_speed * distance / self.slow_radius

        direction.scale_to_length(target_speed)
        acceleration = (direction - self.character.velocity) / self.time_to_target
        return SteeringOutput(
            linear=_clamp_to_length(acceleration, self.character.max_acceleration)
        )


class Align(SteeringBehavior):
    """
    Steers the character to match its orientation with the target's
    orientation, slowing down its rotation as it gets close.
    """

    def __init__(
        self,
        character: Kinematic,
        target: Kinematic,
        target_radius: float = 0.05,
        slow_radius: float = 0.5,
        time_to_target: float = 0.1,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target: The kinematic to match the orientation of.
        :param target_radius: Angle (in radians) below which the character is considered aligned.
        :param slow_radius: Angle (in radians) below which the character starts to slow down its rotation.
        :param time_to_target: Time in which the character should reach its target rotation.
        """
        self.character: Kinematic = character
        self.target: Kinematic = target
        self.target_radius: float = target_radius
        self.slow_radius: float = slow_radius
        self.time_to_target: float = time_to_target

    @staticmethod
    def _map_to_range(angle: float) -> float:
        angle %= 2 * math.pi

        if angle > math.pi:
            angle -= 2 * math.pi

        return angle

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        rotation = self._map_to_range(
            self.target.orientation - self.character.orientation
        )
        rotation_size = abs(rotation)

        if rotation_size < self.target_radius:
            return SteeringOutput()

        if rotation_size > self.slow_radius:
            target_rotation = self.character.max_rotation
        else:
            target_rotation = (
                self.character.max_rotation * rotation_size / self.slow_radius
            )

        target_rotation *= rotation / rotation_size

        angular = (target_rotation - self.character.rotation) / self.time_to_target
        max_acceleration = self.character.max_angular_acceleration

        if abs(angular) > max_acceleration:
            angular = math.copysign(max_acceleration, angular)

        return SteeringOutput(angular=angular)


class Face(Align):
    """
    Steers the character to face towards the target's position, by
    reusing Align with a virtual target that has the required
    orientation.
    """

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        direction = self.target.position - self.character.position

        if direction.length_squared() == 0:
            return SteeringOutput()

        facing_target = Kinematic(
            self.target.position.x,
            self.target.position.y,
            orientation=Kinematic.vector_to_orientation(direction),
        )
        original_target, self.target = self.target, facing_target
        try:
            return super().get_steering(dt)
        finally:
            self.target = original_target


class VelocityMatch(SteeringBehavior):
    """
    Steers the character to match the target's velocity.
    """

    def __init__(
        self, character: Kinematic, target: Kinematic, time_to_target: float = 0.1
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target: The kinematic to match the velocity of.
        :param time_to_target: Time in which the character should reach the target velocity.
        """
        self.character: Kinematic = character
        self.target: Kinematic = target
        self.time_to_target: float = time_to_target

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        acceleration = (
            self.target.velocity - self.character.velocity
        ) / self.time_to_target
        return SteeringOutput(
            linear=_clamp_to_length(acceleration, self.character.max_acceleration)
        )


def _predict_position(
    character: Kinematic, real_target: Kinematic, max_prediction: float
) -> pygame.Vector2:
    direction = real_target.position - character.position
    distance = direction.length()
    speed = character.velocity.length()

    if speed == 0 or distance / speed > max_prediction:
        prediction = max_prediction
    else:
        prediction = distance / speed

    return real_target.position + real_target.velocity * prediction


class Pursue(Seek):
    """
    Steers the character to intercept the target by seeking its
    predicted future position instead of its current one.
    """

    def __init__(
        self, character: Kinematic, target: Kinematic, max_prediction: float = 1
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target: The kinematic to intercept.
        :param max_prediction: Maximum time (in seconds) used to predict the target's future position.
        """
        super().__init__(character, Kinematic())
        self._real_target: Kinematic = target
        self.max_prediction: float = max_prediction

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        self.target.position = _predict_position(
            self.character, self._real_target, self.max_prediction
        )
        return super().get_steering(dt)


class Evade(Flee):
    """
    Steers the character away from the predicted future position of the
    target, instead of its current one.
    """

    def __init__(
        self, character: Kinematic, target: Kinematic, max_prediction: float = 1
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target: The kinematic to evade.
        :param max_prediction: Maximum time (in seconds) used to predict the target's future position.
        """
        super().__init__(character, Kinematic())
        self._real_target: Kinematic = target
        self.max_prediction: float = max_prediction

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        self.target.position = _predict_position(
            self.character, self._real_target, self.max_prediction
        )
        return super().get_steering(dt)


class Wander(SteeringBehavior):
    """
    Steers the character to wander around by continuously seeking a
    moving target placed a fixed distance ahead of it that randomly
    drifts around a circle.
    """

    def __init__(
        self,
        character: Kinematic,
        offset: float = 50,
        radius: float = 30,
        rate: float = math.pi,
        max_acceleration: Optional[float] = None,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param offset: Distance ahead of the character where the wander circle is centered.
        :param radius: Radius of the wander circle.
        :param rate: Maximum angle (in radians per second) the wander orientation may change.
        :param max_acceleration: Acceleration applied towards the wander target. The default value is character.max_acceleration.
        """
        self.character: Kinematic = character
        self.offset: float = offset
        self.radius: float = radius
        self.rate: float = rate
        self.max_acceleration: float = (
            character.max_acceleration if max_acceleration is None else max_acceleration
        )
        self.wander_orientation: float = 0

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        self.wander_orientation += random.uniform(-1, 1) * self.rate * dt

        target_orientation = self.wander_orientation + self.character.orientation
        target = (
            self.character.position
            + self.character.orientation_as_vector() * self.offset
        )
        target += (
            pygame.Vector2(math.cos(target_orientation), math.sin(target_orientation))
            * self.radius
        )

        direction = target - self.character.position

        if direction.length_squared() == 0:
            return SteeringOutput()

        direction.scale_to_length(self.max_acceleration)
        return SteeringOutput(linear=direction)


class Separation(SteeringBehavior):
    """
    Steers the character away from a group of nearby targets. Useful to
    implement flocking or crowd behaviors together with VelocityMatch and
    a cohesion-like Seek towards the group's center.
    """

    def __init__(
        self,
        character: Kinematic,
        targets: Sequence[Kinematic],
        threshold: float = 50,
        max_acceleration: Optional[float] = None,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param targets: The other kinematics to keep distance from.
        :param threshold: Distance below which a target starts to push the character away.
        :param max_acceleration: Acceleration applied away from close targets. The default value is character.max_acceleration.
        """
        self.character: Kinematic = character
        self.targets: Sequence[Kinematic] = targets
        self.threshold: float = threshold
        self.max_acceleration: float = (
            character.max_acceleration if max_acceleration is None else max_acceleration
        )

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        linear = pygame.Vector2()

        for target in self.targets:
            if target is self.character:
                continue

            direction = self.character.position - target.position
            distance = direction.length()

            if distance == 0 or distance >= self.threshold:
                continue

            strength = (
                self.max_acceleration * (self.threshold - distance) / self.threshold
            )
            linear += direction.normalize() * strength

        return SteeringOutput(linear=_clamp_to_length(linear, self.max_acceleration))


class Obstacle:
    """
    A simple circular obstacle to be used with ObstacleAvoidance.
    """

    def __init__(self, x: float, y: float, radius: float) -> None:
        """
        :param x: X component of the obstacle's position.
        :param y: Y component of the obstacle's position.
        :param radius: Radius of the obstacle.
        """
        self.position: pygame.Vector2 = pygame.Vector2(x, y)
        self.radius: float = radius


class ObstacleAvoidance(SteeringBehavior):
    """
    Steers the character away from the nearest obstacle that lies ahead
    of it, based on a simple lookahead check along its current velocity.
    """

    def __init__(
        self,
        character: Kinematic,
        obstacles: Sequence[Obstacle],
        avoid_margin: float = 20,
        lookahead: float = 100,
        max_acceleration: Optional[float] = None,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param obstacles: The obstacles to avoid.
        :param avoid_margin: Extra distance to keep from the surface of an obstacle.
        :param lookahead: Distance ahead of the character to check for collisions.
        :param max_acceleration: Acceleration applied to avoid the obstacle. The default value is character.max_acceleration.
        """
        self.character: Kinematic = character
        self.obstacles: Sequence[Obstacle] = obstacles
        self.avoid_margin: float = avoid_margin
        self.lookahead: float = lookahead
        self.max_acceleration: float = (
            character.max_acceleration if max_acceleration is None else max_acceleration
        )

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        if self.character.velocity.length_squared() == 0:
            return SteeringOutput()

        heading = self.character.velocity.normalize()
        closest_obstacle: Optional[Obstacle] = None
        closest_distance = self.lookahead

        for obstacle in self.obstacles:
            to_obstacle = obstacle.position - self.character.position
            forward_distance = to_obstacle.dot(heading)

            if forward_distance <= 0 or forward_distance > closest_distance:
                continue

            closest_point = self.character.position + heading * forward_distance
            offset = (obstacle.position - closest_point).length()

            if offset < obstacle.radius + self.avoid_margin:
                closest_distance = forward_distance
                closest_obstacle = obstacle

        if closest_obstacle is None:
            return SteeringOutput()

        closest_point = self.character.position + heading * closest_distance
        avoidance_direction = closest_point - closest_obstacle.position

        if avoidance_direction.length_squared() == 0:
            avoidance_direction = pygame.Vector2(-heading.y, heading.x)

        avoidance_direction.scale_to_length(self.max_acceleration)
        return SteeringOutput(linear=avoidance_direction)


class BlendedSteering(SteeringBehavior):
    """
    Combines several steering behaviors by adding their weighted outputs
    together, then clamping the result to the character's limits.
    """

    def __init__(
        self,
        character: Kinematic,
        behaviors: Sequence[Tuple[SteeringBehavior, float]],
    ) -> None:
        """
        :param character: The kinematic that will be steered. Used to clamp the combined output to its limits.
        :param behaviors: Sequence of pairs (behavior, weight) to combine.
        """
        self.character: Kinematic = character
        self.behaviors: Sequence[Tuple[SteeringBehavior, float]] = behaviors

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        linear = pygame.Vector2()
        angular = 0.0

        for behavior, weight in self.behaviors:
            steering = behavior.get_steering(dt)
            linear += steering.linear * weight
            angular += steering.angular * weight

        linear = _clamp_to_length(linear, self.character.max_acceleration)

        if abs(angular) > self.character.max_angular_acceleration:
            angular = math.copysign(self.character.max_angular_acceleration, angular)

        return SteeringOutput(linear=linear, angular=angular)


class PrioritySteering(SteeringBehavior):
    """
    Tries each group of behaviors (blended together) in order and returns
    the first one that produces a meaningful steering output. Useful to
    make urgent behaviors, such as obstacle avoidance, override lower
    priority ones, such as seeking a target.
    """

    def __init__(
        self,
        character: Kinematic,
        groups: Sequence[Sequence[Tuple[SteeringBehavior, float]]],
        epsilon: float = 1e-3,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param groups: Sequence of groups, each one a sequence of pairs (behavior, weight), ordered from highest to lowest priority.
        :param epsilon: Minimum magnitude a steering output must have to be considered meaningful.
        """
        self.character: Kinematic = character
        self.groups: Sequence[Sequence[Tuple[SteeringBehavior, float]]] = groups
        self.epsilon: float = epsilon

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        for group in self.groups:
            steering = BlendedSteering(self.character, group).get_steering(dt)

            if (
                steering.linear.length_squared() > self.epsilon**2
                or abs(steering.angular) > self.epsilon
            ):
                return steering

        return SteeringOutput()
