import unittest

import pygame

from gale.particle_system import (
    PARTICLE_SHAPES,
    SHAPE_CIRCLE,
    SHAPE_SQUARE,
    SHAPE_STAR,
    SHAPE_TRIANGLE,
    Particle,
    ParticleSystem,
)


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

    def test_defaults_match_the_original_circle_only_behavior(self) -> None:
        particle = Particle(0, 0, ax=0, ay=0, life_time=1.0, color=(255, 0, 0, 255))
        self.assertEqual(particle.shape, SHAPE_CIRCLE)
        self.assertIsNone(particle.texture)
        self.assertEqual(particle.size, 4.0)
        self.assertEqual(particle.angular_velocity, 0.0)
        self.assertEqual(particle.angle, 0.0)

    def test_default_render_draws_the_same_circle_the_original_implementation_did(
        self,
    ) -> None:
        # Backward compatibility, at the pixel level, for every pixel
        # the original circle-only Particle actually drew opaque or
        # transparent: a particle created without any of the new
        # shape/texture/size/rotation arguments still draws the exact
        # same 2px-radius circle in the exact same spot.
        #
        # The one deliberate difference: the original implementation
        # built its circle on a surface with only a whole-surface
        # alpha (no per-pixel alpha), which left the four corners
        # just outside the circle a solid, semi-transparent black
        # instead of transparent -- invisible at a 4px scale, but
        # exactly the defect that made a rotated shape (a new
        # feature, with much more of its bounding box left undrawn)
        # show an opaque black box around it. Fixed by drawing on a
        # per-pixel-alpha (SRCALPHA) surface instead, so this test
        # checks the circle itself pixel-for-pixel, and the corners
        # separately, for what they now correctly are: transparent.
        particle = Particle(5, 5, ax=0, ay=0, life_time=1.0, color=(255, 0, 0, 255))
        surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        particle.render(surface)

        expected_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(expected_surface, (255, 0, 0, 255), (5 + 2, 5 + 2), 2)

        for x in range(20):
            for y in range(20):
                self.assertEqual(
                    surface.get_at((x, y)), expected_surface.get_at((x, y))
                )

        for corner in ((5, 5), (8, 5), (5, 8), (8, 8)):
            self.assertEqual(surface.get_at(corner).a, 0)

    def test_every_registered_shape_renders_without_raising(self) -> None:
        surface = pygame.Surface((20, 20))
        for shape in PARTICLE_SHAPES:
            particle = Particle(
                5, 5, ax=0, ay=0, life_time=1.0, color=(0, 255, 0, 255), shape=shape
            )
            particle.render(surface)

    def test_unknown_shape_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            Particle(
                0, 0, ax=0, ay=0, life_time=1.0, color=(255, 0, 0, 255), shape="hexagon"
            )

    def test_texture_takes_precedence_over_shape_when_both_are_given(self) -> None:
        texture = pygame.Surface((8, 8), pygame.SRCALPHA)
        texture.fill((10, 20, 30, 255))
        particle = Particle(
            0,
            0,
            ax=0,
            ay=0,
            life_time=1.0,
            color=(255, 255, 255, 255),
            shape=SHAPE_SQUARE,
            texture=texture,
        )
        surface = pygame.Surface((20, 20))
        surface.fill((0, 0, 0))
        particle.render(surface)
        # A square shape would have painted every pixel in its 8x8
        # box; the texture instead only paints its own (tinted) pixels
        # at full opacity, both cases distinguishable by exact color.
        self.assertEqual(surface.get_at((0, 0))[:3], (10, 20, 30))

    def test_angular_velocity_accumulates_into_angle(self) -> None:
        particle = Particle(
            0,
            0,
            ax=0,
            ay=0,
            life_time=1.0,
            color=(255, 0, 0, 255),
            angular_velocity=90.0,
        )
        particle.update(1.0)
        self.assertEqual(particle.angle, 90.0)

    def test_render_with_rotation_does_not_raise(self) -> None:
        particle = Particle(
            5,
            5,
            ax=0,
            ay=0,
            life_time=1.0,
            color=(255, 0, 0, 255),
            angular_velocity=45.0,
        )
        particle.update(1.0)
        surface = pygame.Surface((20, 20))
        particle.render(surface)

    def test_a_rotated_particle_does_not_paint_an_opaque_box_around_its_shape(
        self,
    ) -> None:
        # Regression test: a shape rarely fills its whole size x size
        # box (a square is the only one that does), and rotating it
        # exposes that box's corners even wider -- both must stay
        # transparent rather than show up as a solid, semi-transparent
        # black square behind/around the shape.
        particle = Particle(
            5,
            5,
            ax=0,
            ay=0,
            life_time=1.0,
            color=(255, 0, 0, 255),
            shape=SHAPE_TRIANGLE,
            size=10,
            angular_velocity=45.0,
        )
        particle.update(1.0)
        surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        particle.render(surface)

        corner_alphas = {surface.get_at((x, y)).a for x in (0, 29) for y in (0, 29)}
        self.assertEqual(corner_alphas, {0})


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

    def test_defaults_generate_only_circle_particles_with_no_texture(self) -> None:
        # Backward compatibility: a system that never calls
        # set_shapes/set_textures/set_size/set_angular_velocity
        # generates exactly what it always generated.
        self.system.generate()
        for particle in self.system.particles:
            self.assertEqual(particle.shape, SHAPE_CIRCLE)
            self.assertIsNone(particle.texture)
            self.assertEqual(particle.size, 4.0)
            self.assertEqual(particle.angular_velocity, 0.0)

    def test_set_shapes_makes_generated_particles_draw_from_that_pool(self) -> None:
        self.system.set_shapes([SHAPE_SQUARE, SHAPE_STAR])
        self.system.generate()
        for particle in self.system.particles:
            self.assertIn(particle.shape, (SHAPE_SQUARE, SHAPE_STAR))
            self.assertIsNone(particle.texture)

    def test_set_textures_makes_generated_particles_use_a_texture(self) -> None:
        texture_a = pygame.Surface((4, 4))
        texture_b = pygame.Surface((4, 4))
        self.system.set_textures([texture_a, texture_b])
        self.system.generate()
        for particle in self.system.particles:
            self.assertIn(particle.texture, (texture_a, texture_b))

    def test_shapes_and_textures_can_be_combined_in_the_same_burst(self) -> None:
        star_texture = pygame.Surface((4, 4))
        system = ParticleSystem(0, 0, n=200)
        system.set_life_time(1.0, 1.0)
        system.set_linear_acceleration(0, 0, 0, 0)
        system.set_colors([(255, 255, 255, 255)])
        system.set_area_spread(0, 0)
        system.set_shapes([SHAPE_TRIANGLE])
        system.set_textures([star_texture])

        system.generate()

        shaped = [p for p in system.particles if p.texture is None]
        textured = [p for p in system.particles if p.texture is not None]
        self.assertTrue(shaped)
        self.assertTrue(textured)
        self.assertTrue(all(p.shape == SHAPE_TRIANGLE for p in shaped))
        self.assertTrue(all(p.texture is star_texture for p in textured))

    def test_set_size_controls_the_generated_particle_size(self) -> None:
        self.system.set_size(2.0, 2.0)
        self.system.generate()
        for particle in self.system.particles:
            self.assertEqual(particle.size, 2.0)

    def test_set_angular_velocity_controls_the_generated_spin(self) -> None:
        self.system.set_angular_velocity(30.0, 30.0)
        self.system.generate()
        for particle in self.system.particles:
            self.assertEqual(particle.angular_velocity, 30.0)


if __name__ == "__main__":
    unittest.main()
