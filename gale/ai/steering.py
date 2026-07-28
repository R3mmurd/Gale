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

from typing import Callable, Optional, Sequence, Tuple

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

        if distance == 0 or distance < self.target_radius:
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

        if rotation_size == 0 or rotation_size < self.target_radius:
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


class LookWhereYoureGoing(Align):
    """
    Steers the character to face the direction it is currently moving
    in, by reusing Align with a virtual target oriented towards the
    character's own velocity. Complements Face (which orients towards
    a target's position instead) and is typically combined with
    Arrive/Seek/Wander, all of which only steer the linear motion and
    leave orientation to whatever else is driving it.
    """

    def __init__(
        self,
        character: Kinematic,
        target_radius: float = 0.05,
        slow_radius: float = 0.5,
        time_to_target: float = 0.1,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param target_radius: Angle (in radians) below which the character is considered aligned.
        :param slow_radius: Angle (in radians) below which the character starts to slow down its rotation.
        :param time_to_target: Time in which the character should reach its target rotation.
        """
        super().__init__(
            character, character, target_radius, slow_radius, time_to_target
        )

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        if self.character.velocity.length_squared() == 0:
            return SteeringOutput()

        facing_target = Kinematic(
            self.character.position.x,
            self.character.position.y,
            orientation=Kinematic.vector_to_orientation(self.character.velocity),
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


class CollisionAvoidance(SteeringBehavior):
    """
    Steers the character away from other moving characters it is on a
    collision course with, by predicting the time of closest approach
    to each and, for whichever is soonest and close enough, steering
    away from its predicted position at that time. Complements
    Separation (which only reacts to how close targets already are,
    ignoring where they're headed) and ObstacleAvoidance/WallAvoidance
    (which are for static geometry, not other moving characters).
    """

    def __init__(
        self,
        character: Kinematic,
        targets: Sequence[Kinematic],
        collision_radius: float = 20,
        max_prediction: float = 2,
        max_acceleration: Optional[float] = None,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param targets: The other moving kinematics to avoid colliding with.
        :param collision_radius: Combined radius below which two kinematics are considered to collide.
        :param max_prediction: Maximum time (in seconds) ahead to look for a collision.
        :param max_acceleration: Acceleration applied away from the predicted collision. The default value is character.max_acceleration.
        """
        self.character: Kinematic = character
        self.targets: Sequence[Kinematic] = targets
        self.collision_radius: float = collision_radius
        self.max_prediction: float = max_prediction
        self.max_acceleration: float = (
            character.max_acceleration if max_acceleration is None else max_acceleration
        )

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        shortest_time = self.max_prediction
        first_target: Optional[Kinematic] = None
        first_relative_position: Optional[pygame.Vector2] = None

        for target in self.targets:
            if target is self.character:
                continue

            relative_position = target.position - self.character.position
            relative_velocity = target.velocity - self.character.velocity
            relative_speed_squared = relative_velocity.length_squared()

            if relative_speed_squared == 0:
                continue

            time_to_closest = (
                -relative_position.dot(relative_velocity) / relative_speed_squared
            )

            if time_to_closest <= 0 or time_to_closest >= shortest_time:
                continue

            closest_distance = (
                relative_position + relative_velocity * time_to_closest
            ).length()

            if closest_distance < self.collision_radius:
                shortest_time = time_to_closest
                first_target = target
                first_relative_position = relative_position

        if first_target is None or first_relative_position is None:
            return SteeringOutput()

        relative_position_at_closest = (
            first_relative_position
            + (first_target.velocity - self.character.velocity) * shortest_time
        )

        if relative_position_at_closest.length_squared() == 0:
            heading = self.character.velocity
            avoidance_direction = (
                pygame.Vector2(-heading.y, heading.x)
                if heading.length_squared() > 0
                else pygame.Vector2(1, 0)
            )
        else:
            avoidance_direction = -relative_position_at_closest

        avoidance_direction.scale_to_length(self.max_acceleration)
        return SteeringOutput(linear=avoidance_direction)


class Wall:
    """
    A straight wall segment to be used with WallAvoidance.
    """

    def __init__(self, start: Tuple[float, float], end: Tuple[float, float]) -> None:
        """
        :param start: One endpoint of the wall segment.
        :param end: The other endpoint of the wall segment.
        """
        self.start: pygame.Vector2 = pygame.Vector2(start)
        self.end: pygame.Vector2 = pygame.Vector2(end)

    def normal(self) -> pygame.Vector2:
        """
        :returns: A unit vector perpendicular to this wall.
        """
        direction = self.end - self.start

        if direction.length_squared() == 0:
            return pygame.Vector2(0, -1)

        direction = direction.normalize()
        return pygame.Vector2(-direction.y, direction.x)


class WallAvoidance(SteeringBehavior):
    """
    Steers the character away from walls by casting a short whisker
    ahead of it (along its current velocity) and, if the whisker
    crosses a wall, steering along that wall's normal -- the classic
    whisker-based avoidance for straight geometry, as opposed to the
    circular obstacles ObstacleAvoidance handles.
    """

    def __init__(
        self,
        character: Kinematic,
        walls: Sequence[Wall],
        whisker_length: float = 40,
        max_acceleration: Optional[float] = None,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param walls: The wall segments to avoid.
        :param whisker_length: How far ahead of the character to check for a wall crossing.
        :param max_acceleration: Acceleration applied away from the wall. The default value is character.max_acceleration.
        """
        self.character: Kinematic = character
        self.walls: Sequence[Wall] = walls
        self.whisker_length: float = whisker_length
        self.max_acceleration: float = (
            character.max_acceleration if max_acceleration is None else max_acceleration
        )

    @staticmethod
    def _segment_intersection(
        p1: pygame.Vector2,
        p2: pygame.Vector2,
        p3: pygame.Vector2,
        p4: pygame.Vector2,
    ) -> Optional[pygame.Vector2]:
        r = p2 - p1
        s = p4 - p3
        denominator = r.x * s.y - r.y * s.x

        if denominator == 0:
            return None

        diff = p3 - p1
        t = (diff.x * s.y - diff.y * s.x) / denominator
        u = (diff.x * r.y - diff.y * r.x) / denominator

        if 0 <= t <= 1 and 0 <= u <= 1:
            return p1 + r * t

        return None

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        if self.character.velocity.length_squared() == 0:
            return SteeringOutput()

        heading = self.character.velocity.normalize()
        whisker_end = self.character.position + heading * self.whisker_length

        closest_point: Optional[pygame.Vector2] = None
        closest_distance = self.whisker_length
        closest_wall: Optional[Wall] = None

        for wall in self.walls:
            point = self._segment_intersection(
                self.character.position, whisker_end, wall.start, wall.end
            )

            if point is None:
                continue

            distance = (point - self.character.position).length()

            if distance < closest_distance:
                closest_distance = distance
                closest_point = point
                closest_wall = wall

        if closest_point is None or closest_wall is None:
            return SteeringOutput()

        avoidance_direction = closest_wall.normal()
        avoidance_direction.scale_to_length(self.max_acceleration)
        return SteeringOutput(linear=avoidance_direction)


class PathFollow(SteeringBehavior):
    """
    Steers the character to follow a path (an ordered sequence of
    points, such as one obtained from gale.ai.search over a
    gale.ai.graph.NavGraph) by predicting the character's future
    position, finding the closest point on the path to it, and Seeking
    a target a fixed distance further along the path -- so the
    character cuts corners smoothly instead of visiting every point
    exactly.
    """

    def __init__(
        self,
        character: Kinematic,
        path: Sequence[Tuple[float, float]],
        path_offset: float = 30,
        prediction_time: float = 0.2,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param path: Ordered points describing the path to follow.
        :param path_offset: Distance, measured along the path, to look ahead of the closest point when picking the Seek target.
        :param prediction_time: How far ahead (in seconds) to predict the character's position before projecting it onto the path.
        """
        self.character: Kinematic = character
        self.path: Sequence[Tuple[float, float]] = path
        self.path_offset: float = path_offset
        self.prediction_time: float = prediction_time
        self._seek = Seek(character, Kinematic())

    def _closest_param(self, position: pygame.Vector2) -> Tuple[int, float, float]:
        best_segment = 0
        best_distance_along = 0.0
        best_distance_squared = float("inf")
        cumulative = 0.0

        for i in range(len(self.path) - 1):
            start = pygame.Vector2(self.path[i])
            end = pygame.Vector2(self.path[i + 1])
            segment = end - start
            segment_length_squared = segment.length_squared()

            if segment_length_squared == 0:
                t = 0.0
            else:
                t = max(
                    0.0,
                    min(1.0, (position - start).dot(segment) / segment_length_squared),
                )

            closest_point = start + segment * t
            distance_squared = (position - closest_point).length_squared()

            if distance_squared < best_distance_squared:
                best_distance_squared = distance_squared
                best_segment = i
                best_distance_along = cumulative + segment.length() * t

            cumulative += segment.length()

        return best_segment, best_distance_along, cumulative

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        if len(self.path) < 2:
            return SteeringOutput()

        future_position = (
            self.character.position + self.character.velocity * self.prediction_time
        )
        _, distance_along, _ = self._closest_param(future_position)
        target_distance = distance_along + self.path_offset

        cumulative = 0.0
        target_point = pygame.Vector2(self.path[-1])

        for i in range(len(self.path) - 1):
            start = pygame.Vector2(self.path[i])
            end = pygame.Vector2(self.path[i + 1])
            segment_length = (end - start).length()

            if cumulative + segment_length >= target_distance:
                t = (
                    (target_distance - cumulative) / segment_length
                    if segment_length > 0
                    else 0.0
                )
                target_point = start.lerp(end, max(0.0, min(1.0, t)))
                break

            cumulative += segment_length

        self._seek.target.position = target_point
        return self._seek.get_steering(dt)


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


def _default_score(steering: SteeringOutput) -> float:
    return steering.linear.length_squared() + steering.angular**2


class CooperativeArbitration(SteeringBehavior):
    """
    Blends each group of behaviors independently (like PrioritySteering
    does), but -- unlike it -- evaluates every group instead of
    stopping at the first meaningful one, and returns whichever scores
    highest under score. Useful when the "best" behavior isn't simply
    the highest-priority one that happens to produce output, but
    whichever actually addresses the situation the most (for instance,
    preferring a strong flanking maneuver over a weak direct approach
    even though both fire at once).
    """

    def __init__(
        self,
        character: Kinematic,
        groups: Sequence[Sequence[Tuple[SteeringBehavior, float]]],
        score: Callable[[SteeringOutput], float] = _default_score,
    ) -> None:
        """
        :param character: The kinematic that will be steered.
        :param groups: Sequence of groups, each one a sequence of pairs (behavior, weight).
        :param score: Callable ranking a candidate SteeringOutput; the group with the highest score wins. The default value scores by squared magnitude.
        """
        self.character: Kinematic = character
        self.groups: Sequence[Sequence[Tuple[SteeringBehavior, float]]] = groups
        self.score: Callable[[SteeringOutput], float] = score

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        best_steering = SteeringOutput()
        best_score = self.score(best_steering)

        for group in self.groups:
            steering = BlendedSteering(self.character, group).get_steering(dt)
            candidate_score = self.score(steering)

            if candidate_score > best_score:
                best_score = candidate_score
                best_steering = steering

        return best_steering


class OutputFilter(SteeringBehavior):
    """
    Wraps another steering behavior and smooths its output over time
    (exponential smoothing) instead of applying it outright, to avoid
    jittery, frame-to-frame-inconsistent motor output from a noisy
    underlying behavior.
    """

    def __init__(self, behavior: SteeringBehavior, smoothing: float = 0.2) -> None:
        """
        :param behavior: The steering behavior to filter.
        :param smoothing: How much of the new output to blend in each call, between 0 (output never changes) and 1 (no filtering at all). The default value is 0.2.
        """
        self.behavior: SteeringBehavior = behavior
        self.smoothing: float = smoothing
        self._filtered: SteeringOutput = SteeringOutput()

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        raw = self.behavior.get_steering(dt)
        self._filtered = SteeringOutput(
            linear=self._filtered.linear.lerp(raw.linear, self.smoothing),
            angular=self._filtered.angular
            + (raw.angular - self._filtered.angular) * self.smoothing,
        )
        return self._filtered


class CapabilityFilter(SteeringBehavior):
    """
    Wraps another steering behavior and clamps its output to a set of
    capabilities that may be more restrictive than the character's own
    Kinematic limits -- for instance, reusing the same targeting logic
    across a fast scout and a slow, heavy tank sharing the same
    character.max_acceleration, but where the tank's turret should
    still turn slower than its chassis's own limits allow.
    """

    def __init__(
        self,
        behavior: SteeringBehavior,
        max_acceleration: float,
        max_angular_acceleration: float,
    ) -> None:
        """
        :param behavior: The steering behavior to filter.
        :param max_acceleration: Maximum linear acceleration magnitude to allow through.
        :param max_angular_acceleration: Maximum angular acceleration magnitude to allow through.
        """
        self.behavior: SteeringBehavior = behavior
        self.max_acceleration: float = max_acceleration
        self.max_angular_acceleration: float = max_angular_acceleration

    def get_steering(self, dt: float = 0) -> SteeringOutput:
        raw = self.behavior.get_steering(dt)
        angular = raw.angular

        if abs(angular) > self.max_angular_acceleration:
            angular = math.copysign(self.max_angular_acceleration, angular)

        return SteeringOutput(
            linear=_clamp_to_length(raw.linear, self.max_acceleration), angular=angular
        )
