"""
The bulk, data-oriented half of the match: gale.ecs.System subclasses
that process every matching entity in one pass every frame, run in
order by a gale.ecs.SystemScheduler. They know nothing about "team AI"
or "roles" -- MovementSystem only ever looks at Position/Velocity,
FatigueSystem only at Fatigue/Velocity, and so on. Team AI (see
src/entities/PlayerAI.py) writes the *desired* Velocity for each player
every frame; these systems are what actually turns that intent into
simulated movement, fatigue, ball physics, and possession/collisions.
"""

import math

from gale.ai.blackboard import Blackboard
from gale.ecs import System, World

import settings
from src.components import (
    BallTag,
    Fatigue,
    PlayerTag,
    Position,
    Radius,
    TeamId,
    Velocity,
)


class MovementSystem(System):
    """
    Integrates every Position/Velocity entity (the ball and every
    player alike) one time step forward. This is the only place
    Velocity actually becomes movement.
    """

    def update(self, world: World, dt: float) -> None:
        for entity, position, velocity in world.query(Position, Velocity):
            position.x += velocity.dx * dt
            position.y += velocity.dy * dt


class FatigueSystem(System):
    """
    Drains stamina while a player runs above a jog threshold (faster
    while sprinting above a second, higher threshold), regenerates it
    while idle/walking, and recomputes the effective max speed the
    team AI's steering is allowed to reach: base_max_speed scaled down
    towards FATIGUE_MIN_SPEED_RATIO as stamina runs out. Velocity is
    also clamped to that cap here, in case a gust of steering
    acceleration briefly pushed it over.
    """

    def update(self, world: World, dt: float) -> None:
        for entity, fatigue, velocity in world.query(Fatigue, Velocity):
            speed = math.hypot(velocity.dx, velocity.dy)
            sprint_threshold = fatigue.base_max_speed * settings.SPRINT_SPEED_RATIO
            jog_threshold = fatigue.base_max_speed * settings.JOG_SPEED_RATIO

            if speed > sprint_threshold:
                fatigue.stamina -= settings.FATIGUE_DRAIN_RATE * dt
            elif speed > jog_threshold:
                fatigue.stamina -= settings.FATIGUE_JOG_DRAIN_RATE * dt
            else:
                fatigue.stamina += settings.FATIGUE_REGEN_RATE * dt

            fatigue.stamina = max(0.0, min(fatigue.max_stamina, fatigue.stamina))
            stamina_ratio = fatigue.stamina / fatigue.max_stamina
            fatigue.effective_max_speed = fatigue.base_max_speed * (
                settings.FATIGUE_MIN_SPEED_RATIO
                + (1 - settings.FATIGUE_MIN_SPEED_RATIO) * stamina_ratio
            )

            if speed > fatigue.effective_max_speed and speed > 0:
                scale = fatigue.effective_max_speed / speed
                velocity.dx *= scale
                velocity.dy *= scale


class BallSystem(System):
    """
    The ball's own simple physics: friction slows it down every frame,
    it bounces off the court's top/bottom walls and off the left/right
    walls (unless it is passing through a goal mouth), and crossing
    fully past a goal line inside the goal mouth scores for the
    attacking team, posts the new score to the shared Blackboard (so
    PlayState's goal-flash observer can react to it), and resets the
    ball to the center spot.
    """

    def __init__(self, blackboard: Blackboard) -> None:
        self.blackboard: Blackboard = blackboard

    def update(self, world: World, dt: float) -> None:
        for entity, position, velocity, _ in world.query(Position, Velocity, BallTag):
            velocity.dx *= settings.BALL_FRICTION
            velocity.dy *= settings.BALL_FRICTION

            if position.y < settings.COURT_TOP:
                position.y = settings.COURT_TOP
                velocity.dy *= -1
            elif position.y > settings.COURT_BOTTOM:
                position.y = settings.COURT_BOTTOM
                velocity.dy *= -1

            in_goal_mouth = settings.GOAL_Y_TOP <= position.y <= settings.GOAL_Y_BOTTOM

            if position.x < settings.COURT_LEFT:
                if (
                    in_goal_mouth
                    and position.x < settings.COURT_LEFT - settings.GOAL_DEPTH
                ):
                    self._score("B", world, position, velocity)
                elif not in_goal_mouth:
                    position.x = settings.COURT_LEFT
                    velocity.dx *= -1
            elif position.x > settings.COURT_RIGHT:
                if (
                    in_goal_mouth
                    and position.x > settings.COURT_RIGHT + settings.GOAL_DEPTH
                ):
                    self._score("A", world, position, velocity)
                elif not in_goal_mouth:
                    position.x = settings.COURT_RIGHT
                    velocity.dx *= -1

    def _score(self, scoring_team: str, world: World, position, velocity) -> None:
        key = "score_a" if scoring_team == "A" else "score_b"
        self.blackboard.set(key, self.blackboard.get(key, 0) + 1)
        position.x, position.y = settings.COURT_CENTER_X, settings.COURT_CENTER_Y
        velocity.dx = velocity.dy = 0.0
        self.blackboard.set("possession_entity", None)
        self.blackboard.set("possession_team", None)


class CollisionSystem(System):
    """
    Two unrelated kinds of "collision" a real match needs, both simple
    proximity checks over Position/Radius:

    - Ball vs player: whichever player is close enough to the ball is
      posted as "possession_entity"/"possession_team" on the shared
      Blackboard, which is exactly what the Condition nodes in every
      player's behavior tree (has_possession/team_has_possession)
      branch on.
    - Player vs player: overlapping players (regardless of team) are
      pushed apart along the line joining their centers, a minimal
      separation so the six players don't stack on top of each other.
    """

    def __init__(self, blackboard: Blackboard) -> None:
        self.blackboard: Blackboard = blackboard

    def update(self, world: World, dt: float) -> None:
        ball = None

        for entity, position, radius, _ in world.query(Position, Radius, BallTag):
            ball = (position, radius)

        players = list(world.query(Position, Radius, TeamId, PlayerTag, Velocity))

        if ball is not None:
            ball_position, ball_radius = ball
            self.blackboard.set("ball_position", (ball_position.x, ball_position.y))

            current_entity = self.blackboard.get("possession_entity")
            current_distance = None
            closest_entity = None
            closest_team = None
            closest_distance = None

            for entity, position, radius, team, tag, _ in players:
                distance = math.hypot(
                    position.x - ball_position.x, position.y - ball_position.y
                )

                if (
                    distance
                    > radius.value + ball_radius.value + settings.POSSESSION_MARGIN
                ):
                    continue

                if entity == current_entity:
                    current_distance = distance

                if closest_distance is None or distance < closest_distance:
                    closest_entity, closest_team, closest_distance = (
                        entity,
                        team,
                        distance,
                    )

            if (
                current_distance is not None
                and closest_entity != current_entity
                and closest_distance
                >= current_distance - settings.POSSESSION_STICKINESS
            ):
                # The current possessor is still within range and no
                # rival is decisively closer (by more than
                # POSSESSION_STICKINESS) -- keep possession with them.
                # Without this, two players contesting the exact same
                # spot flip "closest" (and therefore possession) every
                # single tick from a hair's-width difference, which
                # never lets either of them actually settle into
                # dribbling/passing.
                pass
            elif closest_entity is not None:
                self.blackboard.set("possession_entity", closest_entity)
                self.blackboard.set("possession_team", closest_team.team)
            else:
                self.blackboard.set("possession_entity", None)
                self.blackboard.set("possession_team", None)

        for i in range(len(players)):
            entity_a, position_a, radius_a, _, _, velocity_a = players[i]

            for j in range(i + 1, len(players)):
                entity_b, position_b, radius_b, _, _, velocity_b = players[j]

                dx = position_a.x - position_b.x
                dy = position_a.y - position_b.y
                distance = math.hypot(dx, dy)
                min_distance = radius_a.value + radius_b.value

                if distance <= 0 or distance >= min_distance:
                    continue

                overlap = (min_distance - distance) / 2
                nx, ny = dx / distance, dy / distance
                position_a.x += nx * overlap
                position_a.y += ny * overlap
                position_b.x -= nx * overlap
                position_b.y -= ny * overlap

                # Cancel whichever part of each player's velocity still
                # points into the other, along the separation normal.
                # Correcting position alone isn't enough: steering keeps
                # re-accelerating both of them right back into each
                # other every frame (e.g. two players both driving
                # straight for a contested ball), so the position push
                # and the steering's approach exactly cancel out frame
                # after frame -- freezing both players in place, glued
                # together, even though they never stop "trying" to
                # move. Removing the approaching component (not the
                # whole velocity) leaves any genuine sideways/separating
                # motion untouched.
                a_normal = velocity_a.dx * nx + velocity_a.dy * ny
                if a_normal < 0:
                    velocity_a.dx -= a_normal * nx
                    velocity_a.dy -= a_normal * ny

                b_normal = velocity_b.dx * nx + velocity_b.dy * ny
                if b_normal > 0:
                    velocity_b.dx -= b_normal * nx
                    velocity_b.dy -= b_normal * ny
