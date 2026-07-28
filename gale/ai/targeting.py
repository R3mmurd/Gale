"""
This file contains helpers to aim projectiles: predict_intercept_time
solves the classic "lead the target" problem for a constant-speed,
drag-free projectile; ballistic_position gives a projectile's position
under gravity alone; simulate_drag_trajectory numerically integrates
one under gravity and linear drag, for which no closed-form solution
exists; and iterative_targeting_angle searches for the launch angle
that hits a target under either model.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math

from typing import List, Optional

import pygame


def predict_intercept_time(
    shooter_position: pygame.Vector2,
    target_position: pygame.Vector2,
    target_velocity: pygame.Vector2,
    projectile_speed: float,
) -> Optional[float]:
    """
    Solve for how long a constant-speed, drag-free, gravity-free
    projectile fired now would take to reach a target moving at a
    constant velocity -- the smallest positive root of the quadratic
    formed by requiring the projectile's and target's distance to
    close exactly as fast as the projectile can travel.

    :param shooter_position: Position the projectile is fired from.
    :param target_position: The target's current position.
    :param target_velocity: The target's current velocity.
    :param projectile_speed: Speed of the projectile.
    :returns: Time (in seconds) until interception, or None if the target cannot be intercepted (it outruns the projectile in every direction, or projectile_speed is not positive).
    """
    if projectile_speed <= 0:
        return None

    to_target = target_position - shooter_position
    a = target_velocity.length_squared() - projectile_speed * projectile_speed
    b = 2 * to_target.dot(target_velocity)
    c = to_target.length_squared()

    if abs(a) < 1e-9:
        if abs(b) < 1e-9:
            return None

        t = -c / b
        return t if t > 0 else None

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return None

    sqrt_discriminant = math.sqrt(discriminant)
    t1 = (-b - sqrt_discriminant) / (2 * a)
    t2 = (-b + sqrt_discriminant) / (2 * a)
    candidates = sorted(t for t in (t1, t2) if t > 0)
    return candidates[0] if candidates else None


def ballistic_position(
    origin: pygame.Vector2,
    velocity: pygame.Vector2,
    gravity: pygame.Vector2,
    t: float,
) -> pygame.Vector2:
    """
    :param origin: The projectile's launch position.
    :param velocity: The projectile's initial velocity.
    :param gravity: Constant acceleration applied to the projectile (typically pointing down).
    :param t: Time (in seconds) since launch.
    :returns: The projectile's position at time t, assuming no drag.
    """
    return origin + velocity * t + gravity * (0.5 * t * t)


def simulate_drag_trajectory(
    origin: pygame.Vector2,
    velocity: pygame.Vector2,
    gravity: pygame.Vector2,
    drag: float,
    dt: float,
    steps: int,
) -> List[pygame.Vector2]:
    """
    Numerically integrate a projectile's trajectory under constant
    gravity and linear drag (a deceleration proportional to speed),
    for which no closed-form position formula exists.

    :param origin: The projectile's launch position.
    :param velocity: The projectile's initial velocity.
    :param gravity: Constant acceleration applied to the projectile (typically pointing down).
    :param drag: Linear drag coefficient; the deceleration applied each step is -drag * velocity.
    :param dt: Time step (in seconds) used for the integration.
    :param steps: Number of steps to simulate.
    :returns: The projectile's position at launch and after each of the steps that follow (steps + 1 points in total).
    """
    position = pygame.Vector2(origin)
    current_velocity = pygame.Vector2(velocity)
    positions = [pygame.Vector2(position)]

    for _ in range(steps):
        current_velocity += (gravity - current_velocity * drag) * dt
        position += current_velocity * dt
        positions.append(pygame.Vector2(position))

    return positions


def iterative_targeting_angle(
    origin: pygame.Vector2,
    target_position: pygame.Vector2,
    speed: float,
    gravity: pygame.Vector2,
    drag: float = 0.0,
    dt: float = 1.0 / 60.0,
    max_time: float = 5.0,
    iterations: int = 8,
) -> Optional[float]:
    """
    Search for the launch angle (relative to the direction facing the
    target) that lands a projectile of the given speed on target_position,
    by ternary-searching between that direction and straight up
    (-gravity) and simulating each candidate trajectory (via
    simulate_drag_trajectory) to see how close it lands. Works with or
    without drag, which is the point: unlike a closed-form ballistic
    solution, this keeps working once drag makes one unavailable.

    :param origin: The projectile's launch position.
    :param target_position: The position to hit.
    :param speed: Speed of the projectile.
    :param gravity: Constant acceleration applied to the projectile (typically pointing down).
    :param drag: Linear drag coefficient. The default value is 0 (no drag).
    :param dt: Time step used to simulate each candidate trajectory. The default value is 1/60.
    :param max_time: Maximum flight time to simulate per candidate, in seconds. The default value is 5.
    :param iterations: Number of ternary-search refinements to perform. The default value is 8.
    :returns: The launch angle (in radians, measured from the straight line to target_position, rotating towards -gravity) that comes closest to hitting target_position, or None if origin and target_position coincide.
    """
    to_target = target_position - origin
    distance = to_target.length()

    if distance == 0:
        return None

    base_orientation = math.atan2(to_target.y, to_target.x)
    up = -gravity.normalize() if gravity.length_squared() > 0 else pygame.Vector2(0, -1)
    up_angle = math.atan2(up.y, up.x) - base_orientation

    # Normalize to (-pi, pi] so the search range below always spans
    # the short way from "aimed straight at the target" to "aimed
    # straight up", regardless of which way base_orientation happens
    # to point.
    up_angle = (up_angle + math.pi) % (2 * math.pi) - math.pi

    def landing_distance(angle: float) -> float:
        direction = pygame.Vector2(
            math.cos(base_orientation + angle), math.sin(base_orientation + angle)
        )
        velocity = direction * speed
        steps = int(max_time / dt)
        trajectory = simulate_drag_trajectory(
            origin, velocity, gravity, drag, dt, steps
        )

        closest = min(trajectory, key=lambda point: (point - target_position).length())
        return (closest - target_position).length()

    # Ternary search assuming landing_distance is unimodal over the
    # candidate range, which holds for the usual case of a target
    # within reach: distance-to-target first decreases as the launch
    # angle rises from flat towards the target, then increases again
    # once it overshoots into too steep an arc. The range always goes
    # from 0 (aimed straight at the target) towards up_angle (aimed
    # straight up), whichever sign that turns out to have.
    low, high = (0.0, up_angle) if up_angle >= 0 else (up_angle, 0.0)

    for _ in range(iterations):
        first_third = low + (high - low) / 3
        second_third = high - (high - low) / 3

        if landing_distance(first_third) < landing_distance(second_third):
            high = second_third
        else:
            low = first_third

    return (low + high) / 2
