import unittest

from gale.ai.minimax import best_move, minimax

WINS = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]


def winner(board):
    for a, b, c in WINS:
        if board[a] is not None and board[a] == board[b] == board[c]:
            return board[a]

    return None


def is_terminal(state):
    board, _ = state
    return winner(board) is not None or all(cell is not None for cell in board)


def get_children(state):
    board, turn = state
    for i in range(9):
        if board[i] is None:
            next_board = list(board)
            next_board[i] = turn
            next_turn = "O" if turn == "X" else "X"
            yield i, (tuple(next_board), next_turn)


def evaluate(state):
    board, _ = state
    result = winner(board)
    remaining = board.count(None)

    if result == "X":
        return 10 + remaining
    if result == "O":
        return -(10 + remaining)

    return 0


def empty_state(turn="X"):
    return (tuple([None] * 9), turn)


class MinimaxTicTacToeTestCase(unittest.TestCase):
    def test_finds_winning_move_in_one_ply(self) -> None:
        # X to move, can win at index 2 to complete the top row.
        board = ("X", "X", None, "O", "O", None, None, None, None)
        state = (board, "X")

        move = best_move(state, 9, True, get_children, evaluate, is_terminal)

        self.assertEqual(move, 2)

    def test_blocks_opponent_winning_move(self) -> None:
        # O threatens to win at index 5 (middle row). X must block there.
        board = ("X", None, None, "O", "O", None, None, None, None)
        state = (board, "X")

        move = best_move(state, 9, True, get_children, evaluate, is_terminal)

        self.assertEqual(move, 5)

    def test_alpha_beta_matches_unbounded_bounds(self) -> None:
        state = empty_state("X")

        pruned_score, _ = minimax(
            state, 9, True, get_children, evaluate, is_terminal, alpha=-5, beta=5
        )
        unbounded_score, _ = minimax(
            state, 9, True, get_children, evaluate, is_terminal
        )

        self.assertEqual(pruned_score, unbounded_score)

    def test_optimal_play_from_empty_board_always_draws(self) -> None:
        state = empty_state("X")
        maximizing = True

        while not is_terminal(state):
            move = best_move(state, 9, maximizing, get_children, evaluate, is_terminal)
            self.assertIsNotNone(move)

            board, turn = state
            next_board = list(board)
            next_board[move] = turn
            state = (tuple(next_board), "O" if turn == "X" else "X")
            maximizing = not maximizing

        self.assertIsNone(winner(state[0]))
        self.assertTrue(all(cell is not None for cell in state[0]))


if __name__ == "__main__":
    unittest.main()
