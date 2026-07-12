import unittest

import pygame

from gale.animation import Animation
from gale.cutscene import (
    Cutscene,
    Dialogue,
    MoveActor,
    PlayAnimation,
    SetActorAnimation,
    ShowImage,
    Wait,
)


class Actor:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.animation = None
        self.update_calls = 0
        self.render_calls = 0

    def update(self, dt):
        self.update_calls += 1

    def render(self, surface):
        self.render_calls += 1


class WaitTestCase(unittest.TestCase):
    def test_behaves_like_a_plain_step(self):
        step = Wait(duration=1.0)
        step.enter()
        step._tick(1.0)
        self.assertTrue(step.is_complete())


class ShowImageTestCase(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((1, 1))

    def tearDown(self):
        pygame.display.quit()

    def test_renders_image_at_position(self):
        image = pygame.Surface((10, 10))
        image.fill((255, 0, 0))
        step = ShowImage(image, position=(5, 5), duration=1.0)
        surface = pygame.Surface((20, 20))
        step.render(surface)
        self.assertEqual(surface.get_at((6, 6)), pygame.Color(255, 0, 0))


class PlayAnimationTestCase(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((1, 1))

    def tearDown(self):
        pygame.display.quit()

    def _frames(self):
        frame_a = pygame.Surface((4, 4))
        frame_a.fill((255, 0, 0))
        frame_b = pygame.Surface((4, 4))
        frame_b.fill((0, 255, 0))
        return [frame_a, frame_b]

    def test_completes_once_loops_run_out(self):
        animation = Animation(self._frames(), time_interval=1.0, loops=1)
        step = PlayAnimation(animation)
        step.enter()
        step._tick(1.0)
        self.assertFalse(step.is_complete())
        step._tick(1.0)
        self.assertTrue(step.is_complete())

    def test_infinite_loop_only_completes_via_duration(self):
        animation = Animation(self._frames(), time_interval=1.0, loops=None)
        step = PlayAnimation(animation, duration=5.0)
        step.enter()
        step._tick(4.0)
        self.assertFalse(step.is_complete())
        step._tick(1.0)
        self.assertTrue(step.is_complete())

    def test_resets_animation_on_enter(self):
        animation = Animation(self._frames(), time_interval=1.0, loops=None)
        step = PlayAnimation(animation)
        step.enter()
        step._tick(1.0)
        self.assertEqual(animation.current_frame_index, 1)
        step.enter()
        self.assertEqual(animation.current_frame_index, 0)


class MoveActorTestCase(unittest.TestCase):
    def test_interpolates_position_over_duration(self):
        actor = Actor(0, 0)
        step = MoveActor(actor, target=(10, 0), duration=2.0)
        step.enter()
        step._tick(1.0)
        self.assertAlmostEqual(actor.position.x, 5.0)
        step._tick(1.0)
        self.assertAlmostEqual(actor.position.x, 10.0)
        self.assertTrue(step.is_complete())

    def test_starts_from_actors_position_at_enter_time(self):
        actor = Actor(3, 4)
        step = MoveActor(actor, target=(3, 14), duration=1.0)
        step.enter()
        step._tick(0.5)
        self.assertAlmostEqual(actor.position.y, 9.0)


class SetActorAnimationTestCase(unittest.TestCase):
    def test_completes_immediately_by_default(self):
        actor = Actor(0, 0)
        animation = Animation([1, 2, 3])
        step = SetActorAnimation(actor, animation)
        step.enter()
        self.assertTrue(step.is_complete())
        self.assertIs(actor.animation, animation)

    def test_can_be_held_with_duration(self):
        actor = Actor(0, 0)
        step = SetActorAnimation(actor, Animation([1]), duration=1.0)
        step.enter()
        self.assertFalse(step.is_complete())
        step._tick(1.0)
        self.assertTrue(step.is_complete())


class DialogueTestCase(unittest.TestCase):
    def setUp(self):
        pygame.font.init()

    def test_renders_without_error(self):
        font = pygame.font.Font(None, 16)
        step = Dialogue("Elder", "Hello there.", font, advance_on_input="confirm")
        surface = pygame.Surface((200, 100))
        step.render(surface)


class CutsceneTestCase(unittest.TestCase):
    def test_ticks_and_renders_actors_every_frame(self):
        actor = Actor(0, 0)
        cutscene = Cutscene([Wait(duration=1.0)], actors=[actor])
        cutscene.update(0.5)
        cutscene.render(pygame.Surface((10, 10)))
        self.assertEqual(actor.update_calls, 1)
        self.assertEqual(actor.render_calls, 1)

    def test_finishes_and_calls_on_finished(self):
        finished = []
        cutscene = Cutscene(
            [MoveActor(Actor(0, 0), (1, 1), duration=0.5)],
            on_finished=lambda: finished.append(True),
        )
        cutscene.update(0.5)
        self.assertTrue(cutscene.finished)
        self.assertEqual(finished, [True])

    def test_actors_missing_update_or_render_are_skipped(self):
        cutscene = Cutscene([Wait(duration=1.0)], actors=[object()])
        cutscene.update(0.1)
        cutscene.render(pygame.Surface((10, 10)))


if __name__ == "__main__":
    unittest.main()
