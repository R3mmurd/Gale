"""
This file contains a generic minimax search with alpha-beta pruning for
turn-based adversarial games, such as a tactical hacking terminal
minigame inside a stealth game, or the classic tic-tac-toe. It works
over any state exposing (move, next_state) transitions and a leaf
evaluation, such as a gale.ai.graph.StateGraph (whose edges already
carry an action/move label) or a plain callable, so it is not tied to
any single game representation.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Callable, Iterable, Optional, Tuple, TypeVar

T = TypeVar("T")

ChildrenFn = Callable[[T], Iterable[Tuple[Any, T]]]
EvaluateFn = Callable[[T], float]
IsTerminalFn = Callable[[T], bool]


def minimax(
    state: T,
    depth: int,
    maximizing: bool,
    get_children: ChildrenFn,
    evaluate: EvaluateFn,
    is_terminal: IsTerminalFn,
    alpha: float = float("-inf"),
    beta: float = float("inf"),
) -> Tuple[float, Optional[Any]]:
    """
    Find the optimal move from state by exploring depth plies ahead
    (or until a terminal state is reached), alternating between the
    maximizing and minimizing player and pruning branches with
    alpha-beta that cannot affect the final decision.

    :param state: The state to search from.
    :param depth: How many plies ahead to explore. 0 evaluates state directly without expanding it.
    :param maximizing: Whether the player to move at state is the maximizing player.
    :param get_children: Callable state -> iterable of (move, next_state) pairs describing every move available at state, such as a StateGraph's edges out of state paired with their action.
    :param evaluate: Callable state -> heuristic/terminal score from the maximizing player's perspective. Larger is better for the maximizing player.
    :param is_terminal: Callable state -> whether state is a terminal state (win/loss/draw, or no more moves), regardless of depth.
    :returns: A pair (best_score, best_move), where best_move is the move leading to best_score, or None if depth is 0, state is terminal, or get_children yields nothing.
    """
    if depth == 0 or is_terminal(state):
        return evaluate(state), None

    best_move: Optional[Any] = None

    if maximizing:
        best_score = float("-inf")

        for move, child in get_children(state):
            score, _ = minimax(
                child,
                depth - 1,
                False,
                get_children,
                evaluate,
                is_terminal,
                alpha,
                beta,
            )

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

            if alpha >= beta:
                break
    else:
        best_score = float("inf")

        for move, child in get_children(state):
            score, _ = minimax(
                child, depth - 1, True, get_children, evaluate, is_terminal, alpha, beta
            )

            if score < best_score:
                best_score = score
                best_move = move

            beta = min(beta, best_score)

            if alpha >= beta:
                break

    if best_move is None:
        return evaluate(state), None

    return best_score, best_move


def best_move(
    state: T,
    depth: int,
    maximizing: bool,
    get_children: ChildrenFn,
    evaluate: EvaluateFn,
    is_terminal: IsTerminalFn,
) -> Any:
    """
    :param state: The state to search from.
    :param depth: How many plies ahead to explore. 0 evaluates state directly without expanding it.
    :param maximizing: Whether the player to move at state is the maximizing player.
    :param get_children: Callable state -> iterable of (move, next_state) pairs describing every move available at state.
    :param evaluate: Callable state -> heuristic/terminal score from the maximizing player's perspective.
    :param is_terminal: Callable state -> whether state is a terminal state.
    :returns: The move minimax deems best from state, or None if there is none.
    """
    _, move = minimax(state, depth, maximizing, get_children, evaluate, is_terminal)
    return move
