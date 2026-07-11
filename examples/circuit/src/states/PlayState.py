import math
import time

import pygame

from gale.input_handler import InputData
from gale.net.interpolation import SnapshotInterpolator, lag_compensated_position
from gale.net.prediction import PredictionBuffer
from gale.net.protocol import Channel
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src import car, track
from src.ai_car import AICar


class PlayState(BaseState):
    """
    The host simulates every car authoritatively (its own, the
    joiner's, and the AI's) and broadcasts a "snapshot" every tick. Each
    car demonstrates a different piece of gale.net's networking recipes:

    - The host's own car needs neither prediction nor interpolation: it
      is already authoritative and updated every local frame, exactly
      like examples/rally's host paddle.
    - The joiner's own car is predicted immediately from local input
      via gale.net.PredictionBuffer, then reconciled against the
      host's authoritative echo of it when each snapshot arrives -
      fixing the exact limitation examples/rally's README calls out
      ("No client-side prediction/reconciliation").
    - The host car and AI car, as seen by the joiner, are buffered and
      smoothed with gale.net.SnapshotInterpolator instead of snapping
      to the latest UDP packet.
    - The AI car is simulated on the host with steering path-following
      (see src/ai_car.py) and broadcast exactly like a human car.
    - gale.net.lag_compensated_position is used in _on_bump_attempt to
      check a laggy joiner's "bump" against the AI car's rewound,
      rather than current, position.
    """

    def enter(self, is_host: bool, server=None, client=None) -> None:
        self.is_host = is_host
        self.server = server
        self.client = client
        self.ended = False
        self.laps = {"host": 0, "joiner": 0, "ai": 0}
        self.bump_flash_timer = 0.0

        start_x, start_y = track.WAYPOINTS[0]
        next_x, next_y = track.WAYPOINTS[1]
        heading = math.atan2(next_y - start_y, next_x - start_x)

        self.host_car = car.new_state(start_x - 10, start_y - 8, heading)
        self.joiner_car = car.new_state(start_x - 10, start_y + 8, heading)
        self.ai_car_state = car.new_state(start_x + 10, start_y, heading)

        self.host_input = {"throttle": 0.0, "steer": 0.0}
        self.joiner_input = {"throttle": 0.0, "steer": 0.0}

        if self.is_host:
            self.ai_car = AICar(start_x + 10, start_y, heading)
            self.joiner_peer_id = None
            self.last_processed_sequence = 0
            self.latest_joiner_input = {"throttle": 0.0, "steer": 0.0}
            # The host's own timeline of the AI car's authoritative
            # position, so a laggy joiner's "bump" attempt can be
            # checked against where the AI was when they saw it (see
            # _on_bump_attempt).
            self.ai_lag_history = SnapshotInterpolator()
            self.server.on_connect(self._on_joiner_connected)
            self.server.on_disconnect(self._on_joiner_left)
            self.server.on_message("input", self._on_remote_input)
            self.server.on_message("bump_attempt", self._on_bump_attempt)
        else:
            self.sequence = 0
            self.prediction = PredictionBuffer()
            self.predicted_state = dict(self.joiner_car)
            self.host_render_history = SnapshotInterpolator()
            self.ai_render_history = SnapshotInterpolator()
            self.status_message = None
            self.client.on_message("snapshot", self._on_snapshot)
            self.client.on_message("bumped", self._on_bumped)
            self.client.on_message("game_over", self._on_game_over)
            self.client.on_disconnect(self._on_host_disconnected)

    def exit(self) -> None:
        Timer.clear()

    # -- update -----------------------------------------------------

    def update(self, dt: float) -> None:
        if self.ended:
            return

        if self.is_host:
            self._update_host(dt)
        else:
            self._update_joiner(dt)

    def _update_host(self, dt: float) -> None:
        self.server.update(dt)

        previous = (self.host_car["x"], self.host_car["y"])
        self.host_car = car.apply_input(self.host_car, self.host_input, dt)
        if track.crosses_finish_line(
            previous, (self.host_car["x"], self.host_car["y"])
        ):
            self.laps["host"] += 1

        if self.joiner_peer_id is not None:
            previous = (self.joiner_car["x"], self.joiner_car["y"])
            self.joiner_car = car.apply_input(
                self.joiner_car, self.latest_joiner_input, dt
            )
            if track.crosses_finish_line(
                previous, (self.joiner_car["x"], self.joiner_car["y"])
            ):
                self.laps["joiner"] += 1

        self.ai_car.update(dt)
        self.laps["ai"] = self.ai_car.laps
        self.ai_lag_history.add(self.ai_car.to_state())

        winner = None
        if self.laps["host"] >= settings.LAPS_TO_WIN:
            winner = "host"
        elif (
            self.joiner_peer_id is not None
            and self.laps["joiner"] >= settings.LAPS_TO_WIN
        ):
            winner = "joiner"
        elif self.laps["ai"] >= settings.LAPS_TO_WIN:
            winner = "ai"

        if winner is not None:
            self._end_game(winner)
            return

        self.server.broadcast(
            "snapshot",
            {
                "last_processed_sequence": self.last_processed_sequence,
                "host_car": self.host_car,
                "joiner_car": self.joiner_car,
                "ai_car": self.ai_car.to_state(),
                "laps": self.laps,
            },
            channel=Channel.UNRELIABLE,
        )

    def _update_joiner(self, dt: float) -> None:
        self.client.update(dt)

        self.sequence += 1
        predicted = car.apply_input(self.predicted_state, self.joiner_input, dt)
        self.prediction.record(self.sequence, self.joiner_input, predicted, dt=dt)
        self.predicted_state = predicted
        self.joiner_car = predicted
        self.client.send(
            "input",
            {"sequence": self.sequence, **self.joiner_input},
            channel=Channel.UNRELIABLE,
        )

        render_delay = settings.INTERP_DELAY + (self.client.get_rtt() or 0.0) / 2
        render_time = time.monotonic() - render_delay

        host_sample = self.host_render_history.sample(render_time)
        if host_sample is not None:
            self.host_car = host_sample

        ai_sample = self.ai_render_history.sample(render_time)
        if ai_sample is not None:
            self.ai_car_state = ai_sample

        if self.bump_flash_timer > 0:
            self.bump_flash_timer = max(0.0, self.bump_flash_timer - dt)

    # -- host-side networking callbacks ------------------------------

    def _on_joiner_connected(self, peer) -> None:
        self.joiner_peer_id = peer.peer_id

    def _on_joiner_left(self, peer) -> None:
        if peer.peer_id == self.joiner_peer_id:
            self.joiner_peer_id = None
            self.latest_joiner_input = {"throttle": 0.0, "steer": 0.0}

    def _on_remote_input(self, peer, payload) -> None:
        if peer.peer_id != self.joiner_peer_id:
            return

        self.latest_joiner_input = {
            "throttle": payload.get("throttle", 0.0),
            "steer": payload.get("steer", 0.0),
        }
        sequence = payload.get("sequence")

        if sequence is not None:
            self.last_processed_sequence = sequence

    def _on_bump_attempt(self, peer, payload) -> None:
        """
        The joiner believes they just bumped the AI car, based on their
        own (interpolated, and therefore latency-old) view of it.
        Checking that against the AI car's *current* authoritative
        position would be unfair to a laggy joiner: by the time their
        "bump_attempt" packet reaches the host, the AI has already
        moved on from where they actually saw it. Instead, rewind the
        AI's recorded history back to approximately when the joiner
        saw what they reacted to (their one-way trip to the host plus
        their own render delay) and check the bump against that.
        """
        if peer.peer_id != self.joiner_peer_id:
            return

        rtt = self.server.get_rtt(peer.peer_id) or 0.0
        rewind_time = rtt / 2 + settings.INTERP_DELAY
        ai_state = lag_compensated_position(self.ai_lag_history, rewind_time)

        if ai_state is None:
            return

        dx = ai_state["x"] - self.joiner_car["x"]
        dy = ai_state["y"] - self.joiner_car["y"]

        if math.hypot(dx, dy) <= settings.BUMP_RADIUS:
            self.ai_car.kinematic.velocity *= 0.2
            self.server.broadcast(
                "bumped", {"target": "ai"}, channel=Channel.RELIABLE_UNORDERED
            )

    # -- joiner-side networking callbacks ----------------------------

    def _on_snapshot(self, payload) -> None:
        self.host_render_history.add(payload["host_car"])
        self.ai_render_history.add(payload["ai_car"])
        self.laps = payload["laps"]
        reconciled = self.prediction.reconcile(
            payload["last_processed_sequence"], payload["joiner_car"], car.apply_input
        )
        self.predicted_state = reconciled
        self.joiner_car = reconciled

    def _on_bumped(self, payload) -> None:
        self.bump_flash_timer = 0.3

    def _on_host_disconnected(self, reason: str) -> None:
        if self.ended:
            return

        self.ended = True
        self.status_message = "Lost connection to host."
        Timer.after(2.0, self._return_to_title)

    # -- end of race --------------------------------------------------

    def _end_game(self, winner: str) -> None:
        self.ended = True

        if self.is_host:
            self.server.broadcast(
                "game_over",
                {"winner": winner, "laps": self.laps},
                channel=Channel.RELIABLE_UNORDERED,
            )

        Timer.after(0.1, lambda: self._go_to_game_over(winner))

    def _on_game_over(self, payload) -> None:
        if self.ended:
            return

        self.ended = True
        self.laps = payload["laps"]
        Timer.after(0.1, lambda: self._go_to_game_over(payload["winner"]))

    def _go_to_game_over(self, winner: str) -> None:
        self.state_machine.change(
            "game_over",
            is_host=self.is_host,
            server=self.server,
            client=self.client,
            winner=winner,
            laps=self.laps,
        )

    def _return_to_title(self) -> None:
        if self.client is not None:
            self.client.close()

        if self.server is not None:
            self.server.close()

        self.state_machine.change("title")

    # -- rendering ------------------------------------------------------

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        track.render(surface)

        car.render(surface, self.host_car, settings.COLOR_HOST_CAR)

        joiner_present = self.joiner_peer_id is not None if self.is_host else True
        if joiner_present:
            car.render(surface, self.joiner_car, settings.COLOR_JOINER_CAR)

        ai_state = self.ai_car.to_state() if self.is_host else self.ai_car_state
        ai_color = settings.COLOR_AI_CAR
        if self.bump_flash_timer > 0:
            ai_color = settings.COLOR_TEXT
        car.render(surface, ai_state, ai_color)

        render_text(
            surface,
            f"laps  you: {self._my_laps()}/{settings.LAPS_TO_WIN}"
            f"   ai: {self.laps.get('ai', 0)}/{settings.LAPS_TO_WIN}",
            settings.FONTS["small"],
            8,
            8,
            settings.COLOR_TEXT,
        )

        if not self.is_host:
            rtt = self.client.get_rtt()
            ping_text = f"ping: {int(rtt * 1000)} ms" if rtt is not None else "ping: --"
            render_text(
                surface,
                f"{ping_text}   pending: {self.prediction.pending_count}",
                settings.FONTS["small"],
                8,
                settings.VIRTUAL_HEIGHT - 20,
                settings.COLOR_TEXT,
            )
        elif self.joiner_peer_id is None:
            render_text(
                surface,
                "Practicing solo - waiting for a challenger to join...",
                settings.FONTS["small"],
                8,
                settings.VIRTUAL_HEIGHT - 20,
                settings.COLOR_TEXT,
            )

        if self.ended and not self.is_host and self.status_message:
            render_text(
                surface,
                self.status_message,
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH / 2,
                settings.VIRTUAL_HEIGHT / 2,
                settings.COLOR_TEXT,
                center=True,
            )

    def _my_laps(self) -> int:
        return self.laps.get("host" if self.is_host else "joiner", 0)

    # -- input ------------------------------------------------------

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.ended:
            return

        controls = self.host_input if self.is_host else self.joiner_input

        if input_id == "throttle_up":
            if input_data.pressed:
                controls["throttle"] = 1.0
            elif input_data.released and controls["throttle"] > 0:
                controls["throttle"] = 0.0
        elif input_id == "throttle_down":
            if input_data.pressed:
                controls["throttle"] = -1.0
            elif input_data.released and controls["throttle"] < 0:
                controls["throttle"] = 0.0
        elif input_id == "steer_left":
            if input_data.pressed:
                controls["steer"] = -1.0
            elif input_data.released and controls["steer"] < 0:
                controls["steer"] = 0.0
        elif input_id == "steer_right":
            if input_data.pressed:
                controls["steer"] = 1.0
            elif input_data.released and controls["steer"] > 0:
                controls["steer"] = 0.0
        elif input_id == "bump" and input_data.pressed and not self.is_host:
            self.client.send("bump_attempt", {}, channel=Channel.RELIABLE_UNORDERED)
