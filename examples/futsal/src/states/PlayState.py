import pygame

from gale.ai.blackboard import Blackboard
from gale.ecs import SystemScheduler, World
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

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
from src.entities import PlayerAI
from src.systems import BallSystem, CollisionSystem, FatigueSystem, MovementSystem

# (team, role, home_position, base_max_speed), mirrored left/right for team B.
_ROSTER = [
    (
        "goalkeeper",
        (settings.COURT_LEFT + 18, settings.COURT_CENTER_Y),
        settings.GOALKEEPER_SPEED,
    ),
    (
        "defender",
        (settings.COURT_LEFT + 120, settings.COURT_CENTER_Y),
        settings.DEFENDER_SPEED,
    ),
    (
        "attacker",
        (settings.COURT_CENTER_X - 60, settings.COURT_CENTER_Y),
        settings.ATTACKER_SPEED,
    ),
]

# Small per-role vertical offsets from COURT_CENTER_Y (goalkeepers
# excluded -- they belong on the goal line), the SAME for both teams
# so neither gets a positional edge. Every dribble/shot aims at
# COURT_CENTER_Y exactly, so leaving every player's home row on that
# same line makes a head-on standoff likely: two opposing outfield
# players plus the ball all sitting on one perfectly straight,
# perfectly horizontal line have no sideways room to route around each
# other. Offsetting by role keeps that exact line from forming at
# kickoff without favoring either side (an earlier version of this
# used different offsets per team, which quietly gave one team a
# structural edge -- team B outscored team A roughly 5 to 1 over ten
# simulated matches).
_HOME_Y_OFFSET = {
    "defender": -18,
    "attacker": 12,
}


class PlayState(BaseState):
    def enter(self) -> None:
        self.world = World()
        self.blackboard = Blackboard(
            {
                "score_a": 0,
                "score_b": 0,
                "possession_entity": None,
                "possession_team": None,
                "ball_position": (settings.COURT_CENTER_X, settings.COURT_CENTER_Y),
            }
        )
        self.blackboard.observe("score_a", self._on_goal)
        self.blackboard.observe("score_b", self._on_goal)
        self.goal_flash_timer = 0.0
        self.goal_flash_team = None

        self.ball_entity = self.world.create_entity()
        self.world.add_component(
            self.ball_entity, Position(settings.COURT_CENTER_X, settings.COURT_CENTER_Y)
        )
        self.world.add_component(self.ball_entity, Velocity())
        self.world.add_component(self.ball_entity, Radius(settings.BALL_RADIUS))
        self.world.add_component(self.ball_entity, BallTag())

        self.players = []

        for team in ("A", "B"):
            team_players = []

            for role, home_position, base_max_speed in _ROSTER:
                x, y = home_position
                y += _HOME_Y_OFFSET.get(role, 0)

                if team == "B":
                    x = settings.COURT_LEFT + settings.COURT_RIGHT - x

                entity = self.world.create_entity()
                self.world.add_component(entity, Position(x, y))
                self.world.add_component(entity, Velocity())
                self.world.add_component(entity, Radius(settings.PLAYER_RADIUS))
                self.world.add_component(
                    entity,
                    Fatigue(
                        stamina=settings.MAX_STAMINA,
                        max_stamina=settings.MAX_STAMINA,
                        base_max_speed=base_max_speed,
                        effective_max_speed=base_max_speed,
                    ),
                )
                self.world.add_component(entity, TeamId(team))
                self.world.add_component(entity, PlayerTag(role))

                player_ai = PlayerAI(
                    entity,
                    self.ball_entity,
                    team,
                    role,
                    (x, y),
                    base_max_speed,
                    self.world,
                    self.blackboard,
                )
                team_players.append(player_ai)

            for player_ai in team_players:
                self.players.append(player_ai)

        # Goalkeepers step() (and so may touch the ball, via
        # PlayerAI._make_save) before defenders and attackers of
        # either team, regardless of which team is which: a save and
        # an attacker's still-dribbling kick can both fire in the very
        # same tick (the ball is in reach of both at once for a
        # moment), and PlayerAI._kick_ball_towards only lets the first
        # touch of the tick count. Ordering by role instead of by team
        # means a successful save always locks in before the shooter's
        # stale "I still have possession" kick can un-do it, and vice
        # versa is never possible -- rather than one team's goalkeeper
        # always winning that race and the other's always losing it
        # purely because of which team happened to be built first.
        role_priority = {"goalkeeper": 0, "defender": 1, "attacker": 2}
        self.players.sort(key=lambda player_ai: role_priority[player_ai.role])

        for player_ai in self.players:
            teammates = [
                other
                for other in self.players
                if other.team == player_ai.team and other is not player_ai
            ]
            player_ai.wire_teammates(teammates)
            player_ai.wire_all_players(
                [other for other in self.players if other is not player_ai]
            )

        self.scheduler = SystemScheduler(
            [
                MovementSystem(),
                BallSystem(self.blackboard),
                CollisionSystem(self.blackboard),
                FatigueSystem(),
            ]
        )

        self.match_time = settings.MATCH_DURATION

    def _on_goal(self, key, old_value, new_value) -> None:
        self.goal_flash_timer = settings.GOAL_FLASH_DURATION
        self.goal_flash_team = "A" if key == "score_a" else "B"
        self._reset_kickoff()

    def _reset_kickoff(self) -> None:
        """
        BallSystem already recentres the ball on a goal, but every
        player's Position/Velocity is left exactly where it was --
        typically with the scoring team's attacker deep in the
        opponent's half and, since defenders/goalkeepers push up while
        their own team attacks, the conceding team's own players
        scattered out of position too. With nobody actually back
        defending, whichever side's players happen to average closer
        to the recentred ball wins an uncontested race to it and
        immediately counter-attacks -- in practice this produced an
        almost metronomic goal every few seconds, alternating ends,
        rather than a real match. Snapping every player back to its
        home_position (and zeroing velocity/fatigue drain) is the
        standard football kickoff reset that prevents that.
        """
        for player_ai in self.players:
            position = self.world.get_component(player_ai.entity, Position)
            velocity = self.world.get_component(player_ai.entity, Velocity)
            position.x, position.y = player_ai.home_position
            velocity.dx = velocity.dy = 0.0

    def update(self, dt: float) -> None:
        # Reset once per tick so PlayerAI._kick_ball_towards can tell
        # whether the ball has already been touched this tick -- see
        # its docstring for why a second same-tick touch (e.g. a save
        # racing a dribble) must not silently overwrite the first.
        self.blackboard.set("ball_touched_this_tick", False)

        for player_ai in self.players:
            player_ai.step(dt)

        self.scheduler.update(self.world, dt)

        if self.goal_flash_timer > 0:
            self.goal_flash_timer -= dt

        self.match_time -= dt

        if self.match_time <= 0:
            self.state_machine.change(
                "fulltime",
                score_a=self.blackboard.get("score_a"),
                score_b=self.blackboard.get("score_b"),
            )

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self._render_court(surface)

        for entity, position, radius, team, tag in self.world.query(
            Position, Radius, TeamId, PlayerTag
        ):
            color = settings.COLOR_TEAM_A if team.team == "A" else settings.COLOR_TEAM_B
            center = (round(position.x), round(position.y))
            pygame.draw.circle(surface, color, center, round(radius.value))

            if tag.role == "goalkeeper":
                pygame.draw.circle(
                    surface,
                    settings.COLOR_GOALKEEPER_RING,
                    center,
                    round(radius.value) + 3,
                    1,
                )

            if self.blackboard.get("possession_entity") == entity:
                pygame.draw.circle(
                    surface, settings.COLOR_LINES, center, round(radius.value) + 5, 1
                )

        for entity, position, radius, _ in self.world.query(Position, Radius, BallTag):
            pygame.draw.circle(
                surface,
                settings.COLOR_BALL,
                (round(position.x), round(position.y)),
                round(radius.value),
            )

        self._render_hud(surface)

    def _render_court(self, surface: pygame.Surface) -> None:
        court_rect = pygame.Rect(
            settings.COURT_LEFT,
            settings.COURT_TOP,
            settings.COURT_RIGHT - settings.COURT_LEFT,
            settings.COURT_BOTTOM - settings.COURT_TOP,
        )
        pygame.draw.rect(surface, settings.COLOR_COURT, court_rect)
        pygame.draw.rect(surface, settings.COLOR_LINES, court_rect, 2)
        pygame.draw.line(
            surface,
            settings.COLOR_LINES,
            (settings.COURT_CENTER_X, settings.COURT_TOP),
            (settings.COURT_CENTER_X, settings.COURT_BOTTOM),
            2,
        )
        pygame.draw.circle(
            surface,
            settings.COLOR_LINES,
            (settings.COURT_CENTER_X, settings.COURT_CENTER_Y),
            36,
            2,
        )

        for goal_x in (settings.COURT_LEFT, settings.COURT_RIGHT):
            pygame.draw.line(
                surface,
                settings.COLOR_LINES,
                (goal_x, settings.GOAL_Y_TOP),
                (goal_x, settings.GOAL_Y_BOTTOM),
                4,
            )

    def _render_hud(self, surface: pygame.Surface) -> None:
        score_a = self.blackboard.get("score_a")
        score_b = self.blackboard.get("score_b")
        render_text(
            surface,
            f"A {score_a} - {score_b} B",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            14,
            settings.COLOR_TEXT,
            center=True,
        )
        render_text(
            surface,
            f"{max(0, self.match_time):.0f}s",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH / 2,
            32,
            settings.COLOR_TEXT,
            center=True,
        )

        if self.goal_flash_timer > 0:
            render_text(
                surface,
                f"GOAL! Team {self.goal_flash_team}",
                settings.FONTS["large"],
                settings.VIRTUAL_WIDTH / 2,
                settings.VIRTUAL_HEIGHT / 2,
                settings.COLOR_FLASH,
                center=True,
            )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        pass
