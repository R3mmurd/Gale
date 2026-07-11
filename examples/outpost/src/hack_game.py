"""
"Hack the terminal": a 3x3 tic-tac-toe board the player must beat or
draw (never lose) against a defense AI that plays every move optimally,
found with gale.ai.minimax.best_move. The board is a plain 9-tuple of
"X" (the player)/"O" (the terminal's defense AI)/None (empty) -- a
minimal, hashable state representation, exactly the shape
gale.ai.minimax's get_children/evaluate/is_terminal callables expect.
"""

from typing import Iterable, Optional, Tuple

from gale.ai.minimax import best_move

PLAYER_SYMBOL = "X"
AI_SYMBOL = "O"

Board = Tuple[Optional[str], ...]

_WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def empty_board() -> Board:
    return (None,) * 9


def winner(board: Board) -> Optional[str]:
    """
    :returns: "X", "O", or None if there is no three-in-a-row yet.
    """
    for a, b, c in _WIN_LINES:
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a]

    return None


def is_full(board: Board) -> bool:
    return all(cell is not None for cell in board)


def is_terminal(board: Board) -> bool:
    return winner(board) is not None or is_full(board)


def turn(board: Board) -> str:
    """
    :returns: The symbol to move next. X always moves first, so it moves again whenever an even number of cells are filled.
    """
    filled = sum(1 for cell in board if cell is not None)
    return PLAYER_SYMBOL if filled % 2 == 0 else AI_SYMBOL


def evaluate(board: Board) -> float:
    """
    Score from X's (the player's) perspective, as gale.ai.minimax
    expects: positive is good for X, negative good for O. A win is
    worth more the more empty cells are left, so minimax prefers
    winning sooner and losing later, not just winning/losing eventually.
    """
    empties = sum(1 for cell in board if cell is None)
    win = winner(board)

    if win == PLAYER_SYMBOL:
        return 10 + empties

    if win == AI_SYMBOL:
        return -10 - empties

    return 0


def get_children(board: Board) -> Iterable[Tuple[int, Board]]:
    """
    :returns: Every (cell_index, resulting_board) pair reachable from board by whoever's turn it is placing their symbol in an empty cell.
    """
    symbol = turn(board)

    for i in range(9):
        if board[i] is None:
            yield i, board[:i] + (symbol,) + board[i + 1 :]


def apply_move(board: Board, index: int, symbol: str) -> Board:
    """
    :param board: The board to play on.
    :param index: The (empty) cell to place symbol at.
    :param symbol: PLAYER_SYMBOL or AI_SYMBOL.
    :returns: The resulting board.
    :raises ValueError: If index is already occupied.
    """
    if board[index] is not None:
        raise ValueError(f"Cell {index} is already occupied")

    return board[:index] + (symbol,) + board[index + 1 :]


def ai_move(board: Board) -> Optional[int]:
    """
    Find the terminal defense AI's optimal move with a full-depth
    (depth=9, i.e. to the end of the game) alpha-beta minimax search.
    The AI (O) is the minimizing player, since evaluate scores the board
    from X's perspective.

    :param board: The board to move on. Must not already be terminal, and it must be O's turn.
    :returns: The cell index O should play, or None if the board has no empty cell left.
    """
    return best_move(
        board,
        depth=9,
        maximizing=False,
        get_children=get_children,
        evaluate=evaluate,
        is_terminal=is_terminal,
    )
