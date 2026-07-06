"""
A headless, pygame-free dedicated server for Rally: only ever imports
gale.net, never pygame, so it can run on a machine with no display at
all (a cloud VM, a Raspberry Pi headless, ...). It runs its own
authoritative simulation for two remote players (neither is a local
player the way LobbyState's "Host Game" is), which is a different,
independent little protocol from the one PlayState/LobbyState speak
for player-hosted games — see examples/rally/README.md for how the
two topologies differ and how you'd wire the second one into the
example's states if you wanted a "Join dedicated server" menu entry.

Usage:
    python dedicated_server.py [port]
"""

import sys
import time

from gale.net.protocol import Channel
from gale.net.server import Server

VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 300
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 60
PADDLE_MARGIN = 20
PADDLE_SPEED = 220
BALL_SIZE = 8
BALL_SPEED = 160
WIN_SCORE = 5
TICK_RATE = 60


class Match:
    def __init__(self) -> None:
        self.left_y = VIRTUAL_HEIGHT / 2 - PADDLE_HEIGHT / 2
        self.right_y = VIRTUAL_HEIGHT / 2 - PADDLE_HEIGHT / 2
        self.left_vy = 0.0
        self.right_vy = 0.0
        self.score_left = 0
        self.score_right = 0
        self.reset_ball(1)

    def reset_ball(self, direction: int) -> None:
        self.ball_x = VIRTUAL_WIDTH / 2 - BALL_SIZE / 2
        self.ball_y = VIRTUAL_HEIGHT / 2 - BALL_SIZE / 2
        self.ball_vx = direction * BALL_SPEED
        self.ball_vy = BALL_SPEED * 0.3

    def update(self, dt: float) -> int:
        self.left_y = max(
            0, min(VIRTUAL_HEIGHT - PADDLE_HEIGHT, self.left_y + self.left_vy * dt)
        )
        self.right_y = max(
            0, min(VIRTUAL_HEIGHT - PADDLE_HEIGHT, self.right_y + self.right_vy * dt)
        )
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y + BALL_SIZE >= VIRTUAL_HEIGHT:
            self.ball_y = VIRTUAL_HEIGHT - BALL_SIZE
            self.ball_vy = -abs(self.ball_vy)

        left_wall = PADDLE_MARGIN + PADDLE_WIDTH
        right_wall = VIRTUAL_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH

        if (
            self.ball_vx < 0
            and self.ball_x <= left_wall
            and self.left_y <= self.ball_y + BALL_SIZE
            and self.ball_y <= self.left_y + PADDLE_HEIGHT
        ):
            self.ball_x = left_wall
            self.ball_vx = abs(self.ball_vx) * 1.05
        elif (
            self.ball_vx > 0
            and self.ball_x + BALL_SIZE >= right_wall
            and self.right_y <= self.ball_y + BALL_SIZE
            and self.ball_y <= self.right_y + PADDLE_HEIGHT
        ):
            self.ball_x = right_wall - BALL_SIZE
            self.ball_vx = -abs(self.ball_vx) * 1.05

        if self.ball_x + BALL_SIZE < 0:
            return 2

        if self.ball_x > VIRTUAL_WIDTH:
            return 1

        return 0


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    server = Server(port=port, max_peers=2)
    server.enable_lan_discovery("Rally Dedicated Server")
    match = Match()
    sides = {}
    ended = False

    def on_connect(peer) -> None:
        side = "left" if "left" not in sides.values() else "right"
        sides[peer.peer_id] = side
        server.send_to(peer.peer_id, "assign_side", {"side": side})
        print(f"peer {peer.peer_id} connected as {side}")

    def on_disconnect(peer) -> None:
        sides.pop(peer.peer_id, None)
        print(f"peer {peer.peer_id} disconnected")

    def on_input(peer, payload) -> None:
        side = sides.get(peer.peer_id)

        if side == "left":
            match.left_vy = payload["vy"]
        elif side == "right":
            match.right_vy = payload["vy"]

    server.on_connect(on_connect)
    server.on_disconnect(on_disconnect)
    server.on_message("input", on_input)

    print(f"Rally dedicated server listening on port {server.port}")
    dt = 1.0 / TICK_RATE

    while True:
        server.update(dt)

        if not ended and len(sides) == 2:
            scorer = match.update(dt)

            if scorer:
                if scorer == 1:
                    match.score_left += 1
                else:
                    match.score_right += 1

                server.broadcast(
                    "score",
                    {"left": match.score_left, "right": match.score_right},
                    channel=Channel.RELIABLE_UNORDERED,
                )
                match.reset_ball(direction=-1 if scorer == 1 else 1)

                if match.score_left >= WIN_SCORE or match.score_right >= WIN_SCORE:
                    winner = "left" if match.score_left > match.score_right else "right"
                    server.broadcast(
                        "game_over",
                        {"winner": winner},
                        channel=Channel.RELIABLE_UNORDERED,
                    )
                    ended = True

            server.broadcast(
                "snapshot",
                {
                    "ball": {"x": match.ball_x, "y": match.ball_y},
                    "left_paddle": {"y": match.left_y},
                    "right_paddle": {"y": match.right_y},
                },
                channel=Channel.UNRELIABLE,
            )

        time.sleep(dt)


if __name__ == "__main__":
    main()
