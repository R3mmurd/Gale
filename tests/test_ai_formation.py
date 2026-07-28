import unittest

import pygame

from gale.ai.formation import (
    CircleFormation,
    FormationManager,
    LineFormation,
    ScalableFormationPattern,
    SlotAssignment,
    WedgeFormation,
)
from gale.ai.steering import Kinematic


class LineFormationTestCase(unittest.TestCase):
    def test_slots_are_centered_and_evenly_spaced(self) -> None:
        pattern = LineFormation(spacing=10)
        offsets = [pattern.slot_offset(i, 3) for i in range(3)]
        self.assertAlmostEqual(offsets[0].x, -10)
        self.assertAlmostEqual(offsets[1].x, 0)
        self.assertAlmostEqual(offsets[2].x, 10)


class WedgeFormationTestCase(unittest.TestCase):
    def test_slot_zero_is_the_anchor_itself(self) -> None:
        pattern = WedgeFormation()
        offset = pattern.slot_offset(0, 3)
        self.assertEqual(offset, pygame.Vector2(0, 0))

    def test_later_slots_spread_further_back(self) -> None:
        pattern = WedgeFormation(spacing=10, depth=10)
        first_row = pattern.slot_offset(1, 5)
        second_row = pattern.slot_offset(3, 5)
        self.assertGreater(second_row.y, first_row.y)


class CircleFormationTestCase(unittest.TestCase):
    def test_slots_are_at_the_given_radius(self) -> None:
        pattern = CircleFormation(radius=50)
        offset = pattern.slot_offset(0, 4)
        self.assertAlmostEqual(offset.length(), 50)


class ScalableFormationPatternTestCase(unittest.TestCase):
    def test_scales_down_with_more_members_than_reference(self) -> None:
        pattern = ScalableFormationPattern(LineFormation(spacing=10), reference_count=4)
        offset_at_reference = pattern.slot_offset(3, 4)
        offset_with_more_members = pattern.slot_offset(3, 16)
        self.assertLess(
            offset_with_more_members.length(), offset_at_reference.length() * 2
        )


class SlotAssignmentTestCase(unittest.TestCase):
    def test_assigns_each_character_its_closest_available_slot(self) -> None:
        near = Kinematic(9, 0)
        far = Kinematic(-9, 0)
        pattern = LineFormation(spacing=10)
        assignment = SlotAssignment.assign([far, near], pattern, pygame.Vector2(0, 0))
        # Slots for 2 members are at x=-5 and x=5.
        self.assertIs(assignment[1], near)
        self.assertIs(assignment[0], far)


class FormationManagerTestCase(unittest.TestCase):
    def test_update_assigns_slot_kinematics_to_every_member(self) -> None:
        anchor = Kinematic(0, 0)
        manager = FormationManager(anchor, LineFormation(spacing=10))
        member_a = Kinematic(5, 0)
        member_b = Kinematic(-5, 0)
        manager.add_member(member_a)
        manager.add_member(member_b)
        manager.update()

        self.assertIn(manager.slot_kinematic(member_a).position.x, (-5, 5))
        self.assertIn(manager.slot_kinematic(member_b).position.x, (-5, 5))

    def test_remove_member_drops_its_slot(self) -> None:
        anchor = Kinematic(0, 0)
        manager = FormationManager(anchor, LineFormation())
        member = Kinematic(0, 0)
        manager.add_member(member)
        manager.update()
        manager.remove_member(member)
        self.assertNotIn(member, manager.members)
        self.assertRaises(KeyError, manager.slot_kinematic, member)

    def test_role_of_returns_the_registered_role(self) -> None:
        anchor = Kinematic(0, 0)
        manager = FormationManager(anchor, LineFormation())
        member = Kinematic(0, 0)
        manager.add_member(member, role="leader")
        self.assertEqual(manager.role_of(member), "leader")

    def test_set_pattern_changes_slot_offsets_on_next_update(self) -> None:
        anchor = Kinematic(0, 0)
        manager = FormationManager(anchor, LineFormation(spacing=10))
        member = Kinematic(0, 0)
        manager.add_member(member)
        manager.update()
        manager.set_pattern(CircleFormation(radius=50))
        manager.update()
        self.assertAlmostEqual(manager.slot_kinematic(member).position.length(), 50)


if __name__ == "__main__":
    unittest.main()
