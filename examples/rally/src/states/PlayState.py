import time

import pygame

from gale.input_handler import InputData
from gale.net.protocol import Channel
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src.Ball import Ball
from src.Paddle import Paddle
from src.snapshot_buffer import SnapshotBuffer

# How far in the past (beyond the render delay already implied by
# half the RTT) the joining client samples its SnapshotBuffer, to
# smooth over jitter in packet arrival times.
INTERP_DELAY: float = 0.05


class PlayState(BaseState):
    """
    The host simulates the ball and both paddles authoritatively and
    broadcasts the result; the joining client renders its own paddle
    immediately from local input and interpolates the ball/opponent
    paddle from the snapshots it receives (see src/snapshot_buffer.py).
    """

    def enter(self, is_host: bool, server=None, client=None) -> None:
        self.is_host = is_host
        self.server = server
        self.client = client
        self.ended = False
        self.score_left = 0
        self.score_right = 0

        left_x = settings.PADDLE_MARGIN
        right_x = (
            settings.VIRTUAL_WIDTH - settings.PADDLE_MARGIN - settings.PADDLE_WIDTH
        )
        mid_y = settings.VIRTUAL_HEIGHT / 2 - settings.PADDLE_HEIGHT / 2
        self.left_paddle = Paddle(left_x, mid_y)
        self.right_paddle = Paddle(right_x, mid_y)
        self.my_paddle = self.left_paddle if is_host else self.right_paddle

        if self.is_host:
            self.ball = Ball()
            self.server.on_message("input", self._on_remote_input)
            self.server.on_disconnect(self._on_opponent_left)
        else:
            self.ball_position = (
                settings.VIRTUAL_WIDTH / 2 - settings.BALL_SIZE / 2,
                settings.VIRTUAL_HEIGHT / 2 - settings.BALL_SIZE / 2,
            )
            self.opponent_snapshot = SnapshotBuffer()
            self.client.on_message("snapshot", self._on_snapshot)
            self.client.on_message("score", self._on_score)
            self.client.on_message("game_over", self._on_game_over)
            self.client.on_disconnect(self._on_host_disconnected)

    def exit(self) -> None:
        Timer.clear()

    def update(self, dt: float) -> None:
        if self.ended:
            return

        if self.is_host:
            self._update_host(dt)
        else:
            self._update_joiner(dt)

    def _update_host(self, dt: float) -> None:
        self.server.update(dt)
        self.left_paddle.update(dt)
        self.right_paddle.update(dt)
        scorer = self.ball.update(dt, self.left_paddle, self.right_paddle)

        if scorer:
            if scorer == 1:
                self.score_left += 1
            else:
                self.score_right += 1

            self.server.broadcast(
                "score",
                {"left": self.score_left, "right": self.score_right},
                channel=Channel.RELIABLE_UNORDERED,
            )
            self.ball.reset(direction=-1 if scorer == 1 else 1)

            if (
                self.score_left >= settings.WIN_SCORE
                or self.score_right >= settings.WIN_SCORE
            ):
                self._end_game(
                    "left" if self.score_left > self.score_right else "right"
                )
                return

        self.server.broadcast(
            "snapshot",
            {
                "ball": {"x": self.ball.x, "y": self.ball.y},
                "left_paddle": {"y": self.left_paddle.y},
            },
            channel=Channel.UNRELIABLE,
        )

    def _update_joiner(self, dt: float) -> None:
        self.client.update(dt)
        self.right_paddle.update(dt)

        render_delay = INTERP_DELAY + (self.client.get_rtt() or 0.0) / 2
        sample = self.opponent_snapshot.sample(time.monotonic() - render_delay)

        if sample is not None:
            self.left_paddle.y = sample["left_paddle"]["y"]
            self.ball_position = (sample["ball"]["x"], sample["ball"]["y"])

    def _end_game(self, winner: str) -> None:
        self.ended = True
        self.server.broadcast(
            "game_over", {"winner": winner}, channel=Channel.RELIABLE_UNORDERED
        )
        Timer.after(0.1, lambda: self._go_to_game_over(winner))

    def _go_to_game_over(self, winner: str) -> None:
        self.state_machine.change(
            "game_over",
            is_host=self.is_host,
            server=self.server,
            client=self.client,
            winner=winner,
            score_left=self.score_left,
            score_right=self.score_right,
        )

    def _on_remote_input(self, peer, payload) -> None:
        self.right_paddle.vy = payload["vy"]

    def _on_snapshot(self, payload) -> None:
        self.opponent_snapshot.add(payload)

    def _on_score(self, payload) -> None:
        self.score_left = payload["left"]
        self.score_right = payload["right"]

    def _on_game_over(self, payload) -> None:
        if not self.ended:
            self.ended = True
            Timer.after(0.1, lambda: self._go_to_game_over(payload["winner"]))

    def _on_opponent_left(self, peer) -> None:
        if self.ended:
            return

        self.ended = True
        self.status_message = "Opponent disconnected."
        Timer.after(2.0, self._return_to_title)

    def _on_host_disconnected(self, reason: str) -> None:
        if self.ended:
            return

        self.ended = True
        self.status_message = "Lost connection to host."
        Timer.after(2.0, self._return_to_title)

    def _return_to_title(self) -> None:
        if self.client is not None:
            self.client.close()

        if self.server is not None:
            self.server.close()

        self.state_machine.change("title")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)
        self._render_net(surface)
        self.left_paddle.render(surface)
        self.right_paddle.render(surface)

        if self.is_host:
            self.ball.render(surface)
        else:
            ball_rect = pygame.Rect(
                int(self.ball_position[0]),
                int(self.ball_position[1]),
                settings.BALL_SIZE,
                settings.BALL_SIZE,
            )
            pygame.draw.rect(surface, settings.COLOR_BALL, ball_rect)

        render_text(
            surface,
            f"{self.score_left}   {self.score_right}",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            20,
            settings.COLOR_TEXT,
            center=True,
        )

        rtt = self.client.get_rtt() if self.client is not None else None
        ping_text = f"ping: {int(rtt * 1000)} ms" if rtt is not None else "ping: --"
        render_text(
            surface,
            ping_text,
            settings.FONTS["small"],
            8,
            settings.VIRTUAL_HEIGHT - 20,
            settings.COLOR_TEXT,
        )

        if self.ended and hasattr(self, "status_message"):
            render_text(
                surface,
                self.status_message,
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH / 2,
                settings.VIRTUAL_HEIGHT / 2,
                settings.COLOR_TEXT,
                center=True,
            )

    def _render_net(self, surface: pygame.Surface) -> None:
        x = settings.VIRTUAL_WIDTH // 2
        for y in range(0, settings.VIRTUAL_HEIGHT, 12):
            pygame.draw.rect(surface, settings.COLOR_NET, (x - 1, y, 2, 6))

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if self.ended:
            return

        if input_id == "move_up":
            if input_data.pressed:
                self.my_paddle.vy = -settings.PADDLE_SPEED
            elif input_data.released and self.my_paddle.vy < 0:
                self.my_paddle.vy = 0
        elif input_id == "move_down":
            if input_data.pressed:
                self.my_paddle.vy = settings.PADDLE_SPEED
            elif input_data.released and self.my_paddle.vy > 0:
                self.my_paddle.vy = 0
        else:
            return

        if not self.is_host:
            self.client.send(
                "input", {"vy": self.my_paddle.vy}, channel=Channel.UNRELIABLE
            )
