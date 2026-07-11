"""
Plain dataclasses attached to gale.ecs.World entities. gale.ecs itself
defines no components -- these are the ones this game needs: the ball
and every player are Position/Velocity entities, players additionally
carry Fatigue (stamina that drains/regenerates and caps their
effective max speed), TeamId, and PlayerTag (their tactical role).
"""

from dataclasses import dataclass


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Velocity:
    dx: float = 0.0
    dy: float = 0.0


@dataclass
class Radius:
    value: float


@dataclass
class Fatigue:
    stamina: float
    max_stamina: float
    base_max_speed: float
    effective_max_speed: float


@dataclass
class TeamId:
    team: str  # "A" or "B"


@dataclass
class PlayerTag:
    role: str  # "goalkeeper", "defender", or "attacker"


@dataclass
class BallTag:
    pass
