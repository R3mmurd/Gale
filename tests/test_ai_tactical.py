import unittest

import pygame

from gale.ai.tactical import InfluenceMap, best_position


class InfluenceMapTestCase(unittest.TestCase):
    def test_value_peaks_at_the_source(self) -> None:
        influence_map = InfluenceMap(400, 400, cell_size=20)
        influence_map.add_influence(pygame.Vector2(100, 100), strength=1.0, radius=100)
        near = influence_map.value_at(pygame.Vector2(100, 100))
        far = influence_map.value_at(pygame.Vector2(390, 390))
        self.assertGreater(near, far)

    def test_dominance_favors_the_stronger_team(self) -> None:
        influence_map = InfluenceMap(400, 400, cell_size=20)
        influence_map.add_influence(
            pygame.Vector2(50, 50), strength=1.0, radius=200, team="ally"
        )
        influence_map.add_influence(
            pygame.Vector2(350, 350), strength=1.0, radius=200, team="enemy"
        )
        self.assertGreater(influence_map.dominance_at(pygame.Vector2(50, 50)), 0)
        self.assertLess(influence_map.dominance_at(pygame.Vector2(350, 350)), 0)

    def test_clear_removes_every_source(self) -> None:
        influence_map = InfluenceMap(400, 400, cell_size=20)
        influence_map.add_influence(pygame.Vector2(50, 50), strength=1.0, radius=100)
        influence_map.clear()
        self.assertEqual(influence_map.value_at(pygame.Vector2(50, 50)), 0.0)

    def test_propagate_spreads_influence_to_neighboring_cells(self) -> None:
        influence_map = InfluenceMap(400, 400, cell_size=20)
        influence_map.add_influence(pygame.Vector2(50, 50), strength=1.0, radius=5)
        before = influence_map.value_at(pygame.Vector2(70, 50))
        influence_map.propagate(iterations=2)
        after = influence_map.value_at(pygame.Vector2(70, 50))
        self.assertGreaterEqual(after, before)


class BestPositionTestCase(unittest.TestCase):
    def test_returns_the_highest_scoring_candidate(self) -> None:
        candidates = [pygame.Vector2(0, 0), pygame.Vector2(10, 0), pygame.Vector2(5, 0)]
        result = best_position(candidates, score=lambda p: p.x)
        self.assertEqual(result, pygame.Vector2(10, 0))

    def test_none_for_empty_candidates(self) -> None:
        self.assertIsNone(best_position([], score=lambda p: 0))


if __name__ == "__main__":
    unittest.main()
