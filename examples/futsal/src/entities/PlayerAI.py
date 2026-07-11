"""
PlayerAI drives one player entity's tactical decisions. It reuses
gale.ai.agent.Agent purely for its composition (a Kinematic body, a
swappable steering behavior, a behavior tree "brain", and a shared
Blackboard) -- but, unlike a plain Agent, it never integrates its own
position: gale.ecs.MovementSystem owns that. Every frame, step() syncs
this Kinematic from the entity's ECS Position/Fatigue components,
ticks the behavior tree (which picks a steering behavior and a
target), turns that into a new *desired* velocity, and writes it back
into the entity's Velocity component -- the ECS's MovementSystem is
what actually moves the entity next. That split is deliberate: the
behavior tree/steering stack is the OOP "brain" layer, gale.ecs is the
bulk "body" layer, and Velocity is the seam between them.

Every role's tree is a Selector of Sequences, re-evaluated fresh every
tick (every Action below returns Status.SUCCESS, never RUNNING, the
same reason given in nightwatch's Guard), and every Condition reads or
compares against the match-wide Blackboard's "possession_entity" /
"possession_team" / "ball_position" -- the same "coordinate through
shared state, not direct references" rationale nightwatch's guards use
to react to each other's sightings.
"""

import random

from typing import List, Tuple

import pygame

from gale.ai.agent import Agent
from gale.ai.behavior_tree import (
    Action,
    BehaviorTree,
    Condition,
    Selector,
    Sequence,
    Status,
)
from gale.ai.blackboard import Blackboard
from gale.ai.steering import (
    Arrive,
    BlendedSteering,
    Kinematic,
    Separation,
    SteeringOutput,
)
from gale.ecs import Entity, World

import settings
from src.components import Fatigue, PlayerTag, Position, TeamId, Velocity

Point = Tuple[float, float]


class PlayerAI(Agent):
    def __init__(
        self,
        entity: Entity,
        ball_entity: Entity,
        team: str,
        role: str,
        home_position: Point,
        base_max_speed: float,
        world: World,
        blackboard: Blackboard,
    ) -> None:
        super().__init__(
            x=home_position[0],
            y=home_position[1],
            max_speed=base_max_speed,
            max_acceleration=settings.PLAYER_ACCELERATION,
            blackboard=blackboard,
        )
        self.entity: Entity = entity
        self.ball_entity: Entity = ball_entity
        self.team: str = team
        self.role: str = role
        self.home_position: pygame.Vector2 = pygame.Vector2(home_position)
        self.world: World = world
        self.teammates: List["PlayerAI"] = []
        # Seconds until this goalkeeper may roll its save chance again
        # (see _make_save) -- sub-zero means a roll is due right now.
        # A cooldown, not a one-shot flag: a single failed/blocked
        # attempt must not permanently give up on a ball that's still
        # sitting right next to the keeper (nobody else has any reason
        # to touch a ball the keeper is closest to, so it would
        # otherwise never move again).
        self._save_cooldown: float = 0.0

        self._target: Kinematic = Kinematic()
        self._arrive: Arrive = Arrive(
            self.kinematic,
            self._target,
            target_radius=6,
            slow_radius=70,
            time_to_target=0.12,
        )
        self._separation: Separation = Separation(self.kinematic, [], threshold=26)
        self._arrive_and_spread: BlendedSteering = BlendedSteering(
            self.kinematic, [(self._arrive, 1.0), (self._separation, 0.5)]
        )
        # Ball-contesting actions (_rush_ball/_challenge_ball/_chase_ball)
        # blend in Separation too: without it, two players from opposing
        # teams both racing for the exact same ball position converge to
        # (near) the same point, which CollisionSystem then has to shove
        # apart every single frame -- a tug-of-war where the push-apart
        # exactly cancels each frame's approach, freezing both players
        # (and the ball, since possession/kicks flicker between them
        # every tick as "closest" keeps flipping) in place.
        #
        # This uses Arrive, not Seek, for the "approach" half of the
        # blend: Seek always commands full acceleration towards the
        # target no matter how close it already is, so two players
        # both Seeking the ball keep slamming into each other at full
        # power right up to (and past) the point of contact --
        # Separation's modest push is rarely enough to out-muscle that.
        # Arrive behaves identically to Seek from a distance (both
        # target max speed), but decelerates within slow_radius, so as
        # two challengers close in on the ball their forward drive
        # tapers off well before they'd otherwise collide, giving
        # Separation actual room to steer them around each other
        # instead of just resisting a head-on charge.
        self._approach_and_spread: BlendedSteering = BlendedSteering(
            self.kinematic, [(self._arrive, 1.0), (self._separation, 0.6)]
        )

        if role == "goalkeeper":
            tree = Selector(
                [
                    Sequence(
                        [
                            Condition(self._ball_within_save_range),
                            Action(self._make_save),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._not_kickoff_restricted),
                            Condition(self._ball_in_defensive_third),
                            Condition(self._ball_close_enough_to_rush),
                            Action(self._rush_ball),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._feels_safe),
                            Action(self._sweep),
                        ]
                    ),
                    Action(self._guard_goal_line),
                ]
            )
        elif role == "defender":
            tree = Selector(
                [
                    Sequence(
                        [
                            Condition(self._has_possession),
                            Action(self._advance_ball),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._not_kickoff_restricted),
                            Condition(self._ball_loose_in_own_half),
                            Action(self._challenge_ball),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._team_has_possession),
                            Action(self._support_attack),
                        ]
                    ),
                    Action(self._hold_defensive_position),
                ]
            )
        else:  # attacker
            tree = Selector(
                [
                    Sequence(
                        [
                            Condition(self._is_kickoff_first_touch),
                            Action(self._kickoff_pass),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._has_possession),
                            Action(self._dribble_and_shoot),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._team_has_possession),
                            Action(self._seek_open_space),
                        ]
                    ),
                    Sequence(
                        [
                            Condition(self._not_kickoff_restricted),
                            Action(self._chase_ball),
                        ]
                    ),
                    Action(self._hold_position),
                ]
            )

        self.set_brain(BehaviorTree(tree))

    def wire_teammates(self, teammates: List["PlayerAI"]) -> None:
        """
        :param teammates: The other two PlayerAI on the same team, kept for any team-specific logic that needs them later.
        """
        self.teammates = teammates

    def wire_all_players(self, others: List["PlayerAI"]) -> None:
        """
        :param others: Every other PlayerAI on the pitch, teammates and opponents alike, so this player's Separation steering keeps its distance from all of them -- not just its own team -- instead of just from the ball. Without opponents included, two players from opposing teams both racing for the same ball converge on (near) the same point, which CollisionSystem then has to shove apart every frame, freezing both of them in a tug-of-war (see _approach_and_spread's docstring).
        """
        self._separation.targets = [other.kinematic for other in others]

    @property
    def own_goal_x(self) -> float:
        return settings.COURT_LEFT if self.team == "A" else settings.COURT_RIGHT

    @property
    def opponent_goal_x(self) -> float:
        return settings.COURT_RIGHT if self.team == "A" else settings.COURT_LEFT

    def ball_position(self) -> pygame.Vector2:
        position = self.world.get_component(self.ball_entity, Position)
        return pygame.Vector2(position.x, position.y)

    def step(self, dt: float) -> None:
        """
        Sync this Kinematic from the ECS world, run the behavior tree
        to decide a steering behavior/target, turn that into a new
        velocity, and write it back to the entity's Velocity
        component for MovementSystem to integrate.
        """
        position = self.world.get_component(self.entity, Position)
        velocity = self.world.get_component(self.entity, Velocity)
        fatigue = self.world.get_component(self.entity, Fatigue)
        self.kinematic.position.x, self.kinematic.position.y = position.x, position.y
        # Re-sync velocity too, not just position: CollisionSystem can
        # cancel part of it (the component driving two players into each
        # other) after MovementSystem runs. Without reading that
        # correction back here, this Kinematic's own private velocity
        # would just keep accumulating from last tick's pre-correction
        # value every frame, silently undoing the correction and letting
        # steering re-drive the players straight back into each other.
        self.kinematic.velocity.x, self.kinematic.velocity.y = velocity.dx, velocity.dy
        self.kinematic.max_speed = fatigue.effective_max_speed

        if self.role == "goalkeeper":
            # Ticks down every real frame regardless of whether
            # _make_save actually runs this tick (Condition predicates
            # don't receive dt, so it can't live there) -- otherwise,
            # if _ball_within_save_range only holds intermittently
            # (the ball drifting in and out of range rather than
            # staying put), the cooldown would only ever advance on
            # those sparse ticks, taking far longer than
            # GK_SAVE_COOLDOWN of *wall-clock* time to reach zero again
            # and leaving the keeper essentially unable to ever
            # attempt a second save for the rest of the match.
            self._save_cooldown -= dt

        self.think(dt)

        steering = (
            self.steering_behavior.get_steering(dt)
            if self.steering_behavior is not None
            else SteeringOutput()
        )
        self.kinematic.velocity += steering.linear * dt

        if self.kinematic.velocity.length_squared() > self.kinematic.max_speed**2:
            self.kinematic.velocity.scale_to_length(self.kinematic.max_speed)

        velocity.dx, velocity.dy = self.kinematic.velocity.x, self.kinematic.velocity.y

    def _kick_ball_towards(self, target: pygame.Vector2, speed: float) -> None:
        # Only the first kick in a given tick actually moves the ball.
        # All players' step() run before MovementSystem integrates
        # anything, so if e.g. an attacker's dribble and the opposing
        # goalkeeper's save both fire in the same tick (the ball can
        # legitimately be in reach of both at once), whichever one
        # happens to be later in PlayState.players would silently
        # overwrite the earlier one's kick every single time -- since
        # that list always orders the same team first, one team's
        # saves/shots would *always* lose that race and the other's
        # would *always* win it, a permanent, order-driven advantage
        # having nothing to do with actual play.
        if self.blackboard.get("ball_touched_this_tick", False):
            return

        ball_velocity = self.world.get_component(self.ball_entity, Velocity)
        direction = target - self.ball_position()

        if direction.length_squared() == 0:
            return

        direction.scale_to_length(speed)
        ball_velocity.dx, ball_velocity.dy = direction.x, direction.y
        self.blackboard.set("ball_touched_this_tick", True)

    # -- Blackboard-driven conditions, shared by every role --------------

    def _has_possession(self, agent: "PlayerAI") -> bool:
        return self.blackboard.get("possession_entity") == self.entity

    def _team_has_possession(self, agent: "PlayerAI") -> bool:
        return self.blackboard.get(
            "possession_team"
        ) == self.team and not self._has_possession(agent)

    def _not_kickoff_restricted(self, agent: "PlayerAI") -> bool:
        """
        The real football/futsal kickoff rule: the team that didn't
        take the kickoff may not approach/challenge for the ball until
        two of the kicking team's players have touched it (tracked and
        actually enforced in CollisionSystem -- this Condition just
        keeps a restricted team's own players from uselessly running
        at a ball they mechanically cannot gain possession of anyway).
        """
        return not (
            self.blackboard.get("kickoff_active", False)
            and self.blackboard.get("kickoff_team") != self.team
        )

    # -- Goalkeeper --------------------------------------------------------

    def _ball_in_defensive_third(self, agent: "PlayerAI") -> bool:
        ball_x = self.ball_position().x

        if self.team == "A":
            return ball_x < settings.COURT_LEFT + settings.DEFENSIVE_THIRD_DEPTH

        return ball_x > settings.COURT_RIGHT - settings.DEFENSIVE_THIRD_DEPTH

    def _ball_close_enough_to_rush(self, agent: "PlayerAI") -> bool:
        return (
            self.ball_position() - self.kinematic.position
        ).length() < settings.GK_RUSH_RADIUS

    def _ball_within_save_range(self, agent: "PlayerAI") -> bool:
        return (
            self.ball_position() - self.kinematic.position
        ).length() < settings.GK_SAVE_RADIUS

    def _make_save(self, agent: "PlayerAI", dt: float) -> Status:
        """
        A shot has reached the goalkeeper's outstretched reach: instead
        of just standing there (guard_goal_line never touches the
        ball, and rush_ball only chases it), attempt to stop it --
        punch it away from this goalkeeper's own goal, out towards the
        middle of the pitch at the same height it arrived at, the way
        a real keeper parries a shot rather than letting it drift
        through untouched. Not every attempt succeeds (see
        settings.GK_SAVE_SUCCESS_CHANCE): a keeper that saves every
        single shot within reach is an impenetrable wall, not a
        goalkeeper.

        The chance is only rolled once per GK_SAVE_COOLDOWN seconds
        (see _save_cooldown), not on every tick the ball happens to
        stay in range: a close-quarters contest can last dozens of
        ticks, and re-rolling on each one turns a 55% per-shot save
        rate into a near-100% chance within a fraction of a second (the
        odds of missing every single one of thirty independent
        45%-to-fail rolls in a row are astronomically small) -- an
        unbeatable keeper, not a fallible one.

        This must be a cooldown, not a one-shot-per-approach flag: if
        an attempt fails (or is blocked by
        PlayerAI._kick_ball_towards's one-touch-per-tick rule) and the
        ball just sits there afterwards, nothing else will ever kick it
        away -- attackers only dribble/shoot while they hold
        possession, which the keeper is hogging just by being closest
        to a ball nobody's contesting -- so a one-shot flag would leave
        the keeper standing frozen on top of a dead ball forever,
        having permanently used up its only chance to clear it. Retrying
        periodically guarantees it eventually does.
        """
        self._target.position = self.ball_position()
        self.set_steering_behavior(self._arrive)

        if self._save_cooldown <= 0:
            self._save_cooldown = settings.GK_SAVE_COOLDOWN

            if random.random() < settings.GK_SAVE_SUCCESS_CHANCE:
                clear_target = pygame.Vector2(
                    settings.COURT_CENTER_X, self.ball_position().y
                )
                self._kick_ball_towards(clear_target, settings.GK_CLEAR_SPEED)

        return Status.SUCCESS

    def _rush_ball(self, agent: "PlayerAI", dt: float) -> Status:
        self._target.position = self.ball_position()
        self.set_steering_behavior(self._approach_and_spread)
        return Status.SUCCESS

    def _guard_goal_line(self, agent: "PlayerAI", dt: float) -> Status:
        ball = self.ball_position()
        goal_line_x = (
            settings.COURT_LEFT + settings.PLAYER_RADIUS * 2
            if self.team == "A"
            else settings.COURT_RIGHT - settings.PLAYER_RADIUS * 2
        )
        target_y = max(
            settings.GOAL_Y_TOP + settings.PLAYER_RADIUS,
            min(settings.GOAL_Y_BOTTOM - settings.PLAYER_RADIUS, ball.y),
        )
        self._target.position = pygame.Vector2(goal_line_x, target_y)
        self.set_steering_behavior(self._arrive)
        return Status.SUCCESS

    def _feels_safe(self, agent: "PlayerAI") -> bool:
        """
        Whether this goalkeeper can afford to step off the goal line: the
        ball isn't in his own defensive third, and no opponent is
        lurking close enough to his goal to punish him for coming out
        (a fútbol sala keeper often plays like an extra outfield player
        -- a sweeper -- once the danger has genuinely passed, rather
        than always gluing himself to the line).
        """
        if self._ball_in_defensive_third(agent):
            return False

        own_goal = pygame.Vector2(self.own_goal_x, settings.COURT_CENTER_Y)
        nearest_opponent_distance = min(
            (pygame.Vector2(position.x, position.y) - own_goal).length()
            for _, position, team, _ in self.world.query(Position, TeamId, PlayerTag)
            if team.team != self.team
        )
        return nearest_opponent_distance > settings.GK_SAFE_OPPONENT_RADIUS

    def _sweep(self, agent: "PlayerAI", dt: float) -> Status:
        """
        It's safe to leave the goal line: push up to a modest advanced
        position (nowhere near as far forward as an outfield player)
        so the keeper is a supporting outlet instead of standing idle
        in an empty defensive third.
        """
        ball = self.ball_position()
        advance = settings.GK_RUSH_RADIUS
        sweep_x = (
            self.home_position.x + advance
            if self.team == "A"
            else self.home_position.x - advance
        )
        target_y = self.home_position.y + (ball.y - self.home_position.y) * 0.3
        target_y = max(
            settings.COURT_TOP + settings.PLAYER_RADIUS,
            min(settings.COURT_BOTTOM - settings.PLAYER_RADIUS, target_y),
        )
        self._target.position = pygame.Vector2(sweep_x, target_y)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    # -- Defender ------------------------------------------------------

    def _ball_loose_in_own_half(self, agent: "PlayerAI") -> bool:
        ball_x = self.ball_position().x
        in_own_half = (
            ball_x < settings.COURT_CENTER_X
            if self.team == "A"
            else ball_x > settings.COURT_CENTER_X
        )
        return in_own_half and self.blackboard.get("possession_team") != self.team

    def _challenge_ball(self, agent: "PlayerAI", dt: float) -> Status:
        self._target.position = self.ball_position()
        self.set_steering_behavior(self._approach_and_spread)
        return Status.SUCCESS

    def _advance_ball(self, agent: "PlayerAI", dt: float) -> Status:
        """
        Once this defender has the ball under control (having won a
        challenge, or received a kickoff's mandatory backward pass),
        knock it forward to the nearest attacking teammate instead of
        just standing on it -- without this, the ball would sit dead at
        the defender's feet forever (no other Condition/Action here
        ever has a defender in possession do anything with the ball),
        letting the opponent stroll up and retake it for free every
        single time play restarts through this defender.
        """
        attacking_teammates = [
            teammate for teammate in self.teammates if teammate.role == "attacker"
        ]

        if attacking_teammates:
            target = min(
                attacking_teammates,
                key=lambda mate: (
                    mate.kinematic.position - self.kinematic.position
                ).length(),
            ).kinematic.position
        else:
            target = pygame.Vector2(self.opponent_goal_x, self.kinematic.position.y)

        self._kick_ball_towards(target, settings.PASS_SPEED)
        self._target.position = pygame.Vector2(self.kinematic.position)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    def _support_attack(self, agent: "PlayerAI", dt: float) -> Status:
        ball = self.ball_position()
        target_x = (
            self.home_position.x + (self.opponent_goal_x - self.home_position.x) * 0.25
        )
        target_y = self.home_position.y + (ball.y - self.home_position.y) * 0.4
        self._target.position = pygame.Vector2(target_x, target_y)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    def _hold_defensive_position(self, agent: "PlayerAI", dt: float) -> Status:
        ball = self.ball_position()
        target_y = self.home_position.y + (ball.y - self.home_position.y) * 0.3
        self._target.position = pygame.Vector2(self.home_position.x, target_y)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    # -- Attacker --------------------------------------------------------

    def _is_kickoff_first_touch(self, agent: "PlayerAI") -> bool:
        # kickoff_touches is bumped to 1 by CollisionSystem the very
        # same tick it first registers this player as closest to the
        # ball -- one tick *before* this Condition ever gets to see it
        # (PlayerAI.step() runs, then CollisionSystem runs, then next
        # tick's step() finally reads the new blackboard state). So by
        # the time _has_possession is true here, kickoff_touches is
        # already 1, never 0: checking for the *count* of exactly one
        # touch, made by *this* player, is what actually identifies "my
        # own first touch" rather than an unreachable touches == 0.
        return (
            self.blackboard.get("kickoff_active", False)
            and self.blackboard.get("kickoff_team") == self.team
            and self.blackboard.get("kickoff_touches", 0) == 1
            and self.blackboard.get("kickoff_last_toucher") == self.entity
            and self._has_possession(agent)
        )

    def _kickoff_pass(self, agent: "PlayerAI", dt: float) -> Status:
        """
        Real football/futsal kickoff rule: the kicking team must pass
        backward to a teammate first, rather than driving the ball
        straight at goal themselves. That teammate is specifically the
        goalkeeper, not just whoever is nearest: an earlier version
        passed to the nearest teammate, which in this 3-a-side roster
        is always the defender -- dragging them out of their defensive
        station right as the kickoff restriction lifts and the
        opponent is freed to press. The instant the (now undermanned,
        missing its defender) defense got dispossessed, the opponent
        countered into a huge numerical advantage; the kicking team
        conceded almost every single time, regardless of random
        chance, because it was a structural flaw, not bad luck.
        Passing to the goalkeeper instead -- who is never needed to
        press higher up and already covers exactly the ground a
        backward pass travels to -- keeps the defender at home the
        whole time. The second touch (ending the opponent's kickoff
        restriction) is tracked and enforced in CollisionSystem, not
        here.
        """
        goalkeeper = next(
            (mate for mate in self.teammates if mate.role == "goalkeeper"), None
        )

        if goalkeeper is not None:
            self._kick_ball_towards(goalkeeper.kinematic.position, settings.PASS_SPEED)

        self._target.position = pygame.Vector2(self.kinematic.position)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    def _hold_position(self, agent: "PlayerAI", dt: float) -> Status:
        self._target.position = pygame.Vector2(self.home_position)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    def _dribble_and_shoot(self, agent: "PlayerAI", dt: float) -> Status:
        goal = pygame.Vector2(self.opponent_goal_x, settings.COURT_CENTER_Y)

        if (goal - self.kinematic.position).length() < settings.SHOOT_RADIUS:
            self._kick_ball_towards(goal, settings.SHOT_SPEED)
            # Shoot from here -- don't keep Arriving at goal center
            # itself once in shooting range. goal center is usually
            # exactly where the goalkeeper stands guard, and Arrive is
            # *designed* to stop once it gets within target_radius of
            # wherever it's aimed: literally walking the attacker into
            # the keeper's spot and then halting there, permanently
            # parked nose-to-nose (Separation alone can't rescue this,
            # since the attacker isn't being pushed off course, it's
            # deliberately driving to that exact point and arriving).
            # Standing its ground and just striking the ball is both
            # more realistic and avoids the freeze entirely.
            self._target.position = pygame.Vector2(self.kinematic.position)
        else:
            self._kick_ball_towards(goal, settings.DRIBBLE_SPEED)
            self._target.position = goal

        # _arrive_and_spread, not bare _arrive: without Separation here,
        # an attacker driving straight at goal (right where the
        # goalkeeper usually stands guard) and the keeper closing in to
        # save/challenge can end up perfectly nose-to-nose with no
        # sideways force to break the standoff -- frozen together the
        # same way the opening kickoff used to be before the roster's
        # home positions were staggered.
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    def _seek_open_space(self, agent: "PlayerAI", dt: float) -> Status:
        ball = self.ball_position()
        advanced_x = (
            self.home_position.x + (self.opponent_goal_x - self.home_position.x) * 0.5
        )
        target_y = self.home_position.y - (ball.y - self.home_position.y) * 0.5
        target_y = max(
            settings.COURT_TOP + settings.PLAYER_RADIUS,
            min(settings.COURT_BOTTOM - settings.PLAYER_RADIUS, target_y),
        )
        self._target.position = pygame.Vector2(advanced_x, target_y)
        self.set_steering_behavior(self._arrive_and_spread)
        return Status.SUCCESS

    def _chase_ball(self, agent: "PlayerAI", dt: float) -> Status:
        self._target.position = self.ball_position()
        self.set_steering_behavior(self._approach_and_spread)
        return Status.SUCCESS
