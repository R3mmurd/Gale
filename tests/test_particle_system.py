import unittest

import pygame

from gale.particle_system import Particle, ParticleSystem


class ParticleTestCase(unittest.TestCase):
    def test_update_integrates_velocity_and_position(self) -> None:
        particle = Particle(0, 0, ax=10, ay=0, life_time=1.0, color=(255, 0, 0, 255))
        particle.update(1.0)
        self.assertEqual(particle.vx, 10)
        self.assertEqual(particle.x, 10)

    def test_render_does_not_raise(self) -> None:
        particle = Particle(5, 5, ax=0, ay=0, life_time=1.0, color=(255, 0, 0, 255))
        surface = pygame.Surface((20, 20))
        particle.render(surface)


class ParticleSystemTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.system = ParticleSystem(100, 100, n=20)
        self.system.set_life_time(0.5, 1.0)
        self.system.set_linear_acceleration(-10, -10, 10, 10)
        self.system.set_colors([(255, 0, 0, 255), (0, 255, 0, 255)])
        self.system.set_area_spread(5, 5)

    def test_generate_creates_the_requested_number_of_particles(self) -> None:
        self.system.generate()
        self.assertEqual(len(self.system.particles), 20)

    def test_generated_particles_use_the_given_colors(self) -> None:
        self.system.generate()
        colors = {tuple(p.color) for p in self.system.particles}
        self.assertTrue(colors.issubset({(255, 0, 0, 255), (0, 255, 0, 255)}))

    def test_generated_particles_life_time_is_within_range(self) -> None:
        self.system.generate()
        for particle in self.system.particles:
            self.assertGreaterEqual(particle.life_time, 0.5)
            self.assertLessEqual(particle.life_time, 1.0)

    def test_update_with_no_particles_does_not_raise(self) -> None:
        self.system.update(0.1)

    def test_update_stops_updating_particles_past_their_own_life_time(self) -> None:
        self.system.set_life_time(0.1, 1.0)
        self.system.generate()
        short_lived = min(self.system.particles, key=lambda p: p.life_time)
        short_lived.life_time = 0.05
        original_x = short_lived.x

        self.system.update(0.2)

        self.assertEqual(short_lived.x, original_x)

    def test_update_clears_particles_and_calls_on_finish_past_max_life_time(
        self,
    ) -> None:
        finished = []
        self.system.on_finish = lambda: finished.append(1)
        self.system.generate()

        self.system.update(2.0)

        self.assertEqual(len(self.system.particles), 0)
        self.assertEqual(len(finished), 1)

    def test_render_does_not_raise(self) -> None:
        self.system.generate()
        surface = pygame.Surface((200, 200))
        self.system.render(surface)

    def test_default_on_finish_is_a_no_op(self) -> None:
        system = ParticleSystem(0, 0, n=1)
        system.set_life_time(0.1, 0.1)
        system.set_colors([(255, 255, 255, 255)])
        system.generate()
        system.update(1.0)  # should not raise


if __name__ == "__main__":
    unittest.main()
