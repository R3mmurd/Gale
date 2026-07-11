from typing import Tuple

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src import hack_game

CELL_PIXELS = 64
BOARD_TOP_LEFT = (
    settings.VIRTUAL_WIDTH // 2 - CELL_PIXELS * 3 // 2,
    settings.VIRTUAL_HEIGHT // 2 - CELL_PIXELS * 3 // 2,
)

MOVE_CURSOR = {
    "move_left": (0, -1),
    "move_right": (0, 1),
    "move_up": (-1, 0),
    "move_down": (1, 0),
}


class TerminalHackState(BaseState):
    """
    "Hack the terminal": a 3x3 tic-tac-toe board (see src/hack_game.py)
    against a defense AI that always plays the move
    gale.ai.minimax.best_move deems optimal. The player (X) must win or
    draw to open the terminal; losing just denies access, so the level
    stays intact to try again.
    """

    def enter(self) -> None:
        self.board = hack_game.empty_board()
        self.cursor: Tuple[int, int] = (1, 1)
        self.result = None  # None while playing, else "won"/"draw"/"lost"

    def _cell_index(self) -> int:
        row, col = self.cursor
        return row * 3 + col

    def _resolve_if_terminal(self) -> None:
        winner = hack_game.winner(self.board)

        if winner == hack_game.PLAYER_SYMBOL:
            self.result = "won"
        elif winner == hack_game.AI_SYMBOL:
            self.result = "lost"
        elif hack_game.is_full(self.board):
            self.result = "draw"

    def _play_player_move(self) -> None:
        index = self._cell_index()

        if self.board[index] is not None:
            return

        self.board = hack_game.apply_move(self.board, index, hack_game.PLAYER_SYMBOL)
        self._resolve_if_terminal()

        if self.result is not None:
            return

        ai_index = hack_game.ai_move(self.board)

        if ai_index is not None:
            self.board = hack_game.apply_move(self.board, ai_index, hack_game.AI_SYMBOL)
            self._resolve_if_terminal()

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if not input_data.pressed:
            return

        if self.result is not None:
            if input_id == "confirm":
                self.state_machine.change(
                    "victory" if self.result != "lost" else "play"
                )

            return

        if input_id in MOVE_CURSOR:
            d_row, d_col = MOVE_CURSOR[input_id]
            row, col = self.cursor
            self.cursor = ((row + d_row) % 3, (col + d_col) % 3)
        elif input_id == "confirm":
            self._play_player_move()

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)

        render_text(
            surface,
            "HACK THE TERMINAL",
            settings.FONTS["large"],
            settings.VIRTUAL_WIDTH // 2,
            60,
            settings.COLOR_TERMINAL_EDGE,
            center=True,
        )
        render_text(
            surface,
            "Arrows: move cursor   Enter: place X   Beat or draw the AI",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            95,
            settings.COLOR_TEXT,
            center=True,
        )

        left, top = BOARD_TOP_LEFT

        for row in range(3):
            for col in range(3):
                rect = pygame.Rect(
                    left + col * CELL_PIXELS,
                    top + row * CELL_PIXELS,
                    CELL_PIXELS,
                    CELL_PIXELS,
                )
                pygame.draw.rect(surface, settings.COLOR_FLOOR, rect)
                pygame.draw.rect(surface, settings.COLOR_FLOOR_EDGE, rect, 2)

                mark = self.board[row * 3 + col]

                if mark is not None:
                    color = (
                        settings.COLOR_PLAYER
                        if mark == hack_game.PLAYER_SYMBOL
                        else settings.COLOR_GUARD_ALERTED
                    )
                    render_text(
                        surface,
                        mark,
                        settings.FONTS["large"],
                        rect.centerx,
                        rect.centery,
                        color,
                        center=True,
                    )

                if self.result is None and (row, col) == self.cursor:
                    pygame.draw.rect(surface, settings.COLOR_TERMINAL_EDGE, rect, 3)

        if self.result is not None:
            message, color = {
                "won": ("ACCESS GRANTED", settings.COLOR_GOOD_TEXT),
                "draw": ("ACCESS GRANTED (draw)", settings.COLOR_GOOD_TEXT),
                "lost": ("ACCESS DENIED", settings.COLOR_ALERT_TEXT),
            }[self.result]
            render_text(
                surface,
                message,
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH // 2,
                top + 3 * CELL_PIXELS + 30,
                color,
                center=True,
            )
            render_text(
                surface,
                "Enter to continue",
                settings.FONTS["small"],
                settings.VIRTUAL_WIDTH // 2,
                top + 3 * CELL_PIXELS + 55,
                settings.COLOR_TEXT,
                center=True,
            )
