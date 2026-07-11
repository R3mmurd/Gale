"""
The shared car model: a tiny state dict {"x", "y", "heading", "speed"}
and apply_input, the pure function that advances it one step. Kept as
plain data + a pure function (rather than a stateful class) on purpose:
it is exactly the shape gale.net.PredictionBuffer expects (see its
usage in src/states/PlayState.py), since PredictionBuffer.reconcile
replays apply_input, possibly several times in a row, on top of
whatever authoritative state the host last sent.
"""

import math
from typing import Any, Dict

import pygame

import settings
from src import track

State = Dict[str, Any]


def new_state(x: float, y: float, heading: float) -> State:
    return {"x": x, "y": y, "heading": heading, "speed": 0.0}


def apply_input(state: State, input_payload: Dict[str, Any], dt: float) -> State:
    """
    Advance one car state one step, given an input of {"throttle":
    -1..1, "steer": -1..1}. Pure: depends only on its arguments, so it
    can be replayed identically by PredictionBuffer.reconcile.

    :param state: The car's state before this step.
    :param input_payload: The input applied over dt.
    :param dt: Time elapsed, in seconds, over which the input is applied.
    :returns: The resulting state.
    """
    throttle = input_payload.get("throttle", 0.0)
    steer = input_payload.get("steer", 0.0)

    speed = state["speed"] + throttle * settings.CAR_ACCELERATION * dt
    speed *= max(0.0, 1.0 - settings.CAR_FRICTION * dt)
    speed = max(settings.CAR_MIN_SPEED, min(settings.CAR_MAX_SPEED, speed))

    heading = state["heading"]
    if abs(speed) > 1.0:
        turn_factor = speed / settings.CAR_MAX_SPEED
        heading += steer * settings.CAR_TURN_RATE * dt * turn_factor

    x = state["x"] + math.cos(heading) * speed * dt
    y = state["y"] + math.sin(heading) * speed * dt

    if not track.is_on_track(x, y):
        speed *= settings.OFFTRACK_DAMPING

    return {"x": x, "y": y, "heading": heading, "speed": speed}


def render(surface: pygame.Surface, state: State, color) -> None:
    x, y, heading = state["x"], state["y"], state["heading"]
    length = settings.CAR_RADIUS * 1.8
    width = settings.CAR_RADIUS
    forward = pygame.Vector2(math.cos(heading), math.sin(heading))
    side = pygame.Vector2(-forward.y, forward.x)
    nose = pygame.Vector2(x, y) + forward * length / 2
    tail_left = pygame.Vector2(x, y) - forward * length / 2 + side * width / 2
    tail_right = pygame.Vector2(x, y) - forward * length / 2 - side * width / 2
    pygame.draw.polygon(surface, color, [nose, tail_left, tail_right])
