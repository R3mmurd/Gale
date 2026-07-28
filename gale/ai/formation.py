"""
This file contains support for coordinated group movement: a
FormationPattern gives each slot in a formation an offset relative to
an anchor point (LineFormation, WedgeFormation, CircleFormation are
fixed patterns; ScalableFormationPattern adapts one to however many
members currently occupy it), SlotAssignment assigns characters to
slots minimizing total movement, and FormationManager ties it all
together as "two-level" steering: the anchor moves on its own (driven
by whatever steering behavior you give it, e.g. Arrive at a
destination), and each member is steered towards anchor.position +
pattern.slot_offset(slot, member_count) -- so members follow the
anchor's motion for free, without each one needing to know where the
group as a whole is going.

Note that "emergent" formations (a flock/crowd that stays together
without any explicit pattern) don't need any of this: they fall out of
combining Separation, a cohesion Seek towards the group's centroid, and
VelocityMatch (alignment) with BlendedSteering, all of which already
exist in gale.ai.steering.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import math

from typing import Dict, Hashable, List, Optional, Sequence

import pygame

from .steering import Kinematic


class FormationPattern:
    """
    Base class for a formation pattern: gives the offset, relative to
    the formation's anchor, that a given slot should occupy.
    """

    def slot_offset(self, slot: int, member_count: int) -> pygame.Vector2:
        """
        :param slot: Index of the slot to get the offset of.
        :param member_count: How many members currently occupy the formation.
        :returns: The offset, relative to the anchor's position, slot should be placed at.
        """
        raise NotImplementedError()


class LineFormation(FormationPattern):
    """
    Slots placed in a straight line, spaced spacing apart, centered on
    the anchor.
    """

    def __init__(self, spacing: float = 40) -> None:
        """
        :param spacing: Distance between consecutive slots.
        """
        self.spacing: float = spacing

    def slot_offset(self, slot: int, member_count: int) -> pygame.Vector2:
        centered_slot = slot - (member_count - 1) / 2
        return pygame.Vector2(centered_slot * self.spacing, 0)


class WedgeFormation(FormationPattern):
    """
    Slots placed in a V shape opening behind the anchor (slot 0), two
    per following row, spreading out and back.
    """

    def __init__(self, spacing: float = 40, depth: float = 40) -> None:
        """
        :param spacing: Horizontal distance between the two slots of a row.
        :param depth: Distance each row sits behind the previous one.
        """
        self.spacing: float = spacing
        self.depth: float = depth

    def slot_offset(self, slot: int, member_count: int) -> pygame.Vector2:
        if slot == 0:
            return pygame.Vector2(0, 0)

        row = (slot + 1) // 2
        side = 1 if slot % 2 == 1 else -1
        return pygame.Vector2(side * row * self.spacing / 2, row * self.depth)


class CircleFormation(FormationPattern):
    """
    Slots placed evenly around a circle centered on the anchor.
    """

    def __init__(self, radius: float = 60) -> None:
        """
        :param radius: Radius of the circle.
        """
        self.radius: float = radius

    def slot_offset(self, slot: int, member_count: int) -> pygame.Vector2:
        if member_count <= 0:
            return pygame.Vector2(0, 0)

        angle = 2 * math.pi * slot / member_count
        return pygame.Vector2(math.cos(angle), math.sin(angle)) * self.radius


class ScalableFormationPattern(FormationPattern):
    """
    Wraps another FormationPattern and scales its spacing so the whole
    formation's footprint stays close to a target size regardless of
    how many members currently occupy it, instead of growing without
    bound as members are added.
    """

    def __init__(
        self, base_pattern: FormationPattern, reference_count: int = 4
    ) -> None:
        """
        :param base_pattern: The pattern whose offsets get scaled.
        :param reference_count: Member count at which base_pattern's offsets are used unscaled.
        """
        self.base_pattern: FormationPattern = base_pattern
        self.reference_count: int = reference_count

    def slot_offset(self, slot: int, member_count: int) -> pygame.Vector2:
        offset = self.base_pattern.slot_offset(slot, member_count)

        if member_count <= 0:
            return offset

        scale = math.sqrt(self.reference_count / member_count)
        return offset * scale


class SlotAssignment:
    """
    Assigns characters to formation slots minimizing total movement,
    by greedily giving each character the closest still-available slot
    -- not globally optimal, but cheap and good enough to avoid members
    crossing paths on every reassignment, and stable enough that a
    member usually keeps its slot across calls.
    """

    @staticmethod
    def assign(
        characters: Sequence[Kinematic],
        pattern: FormationPattern,
        anchor: pygame.Vector2,
    ) -> Dict[int, Kinematic]:
        """
        :param characters: The characters to assign to slots.
        :param pattern: The formation pattern to assign slots from.
        :param anchor: The formation's current anchor position.
        :returns: A mapping from slot index to the character assigned to it, for slots 0..len(characters) - 1.
        """
        member_count = len(characters)
        slot_positions = {
            slot: anchor + pattern.slot_offset(slot, member_count)
            for slot in range(member_count)
        }

        remaining_slots = set(slot_positions.keys())
        assignment: Dict[int, Kinematic] = {}

        for character in characters:
            best_slot = min(
                remaining_slots,
                key=lambda slot: (
                    character.position - slot_positions[slot]
                ).length_squared(),
            )
            assignment[best_slot] = character
            remaining_slots.remove(best_slot)

        return assignment


class FormationManager:
    """
    Drives a group of characters as a formation: an anchor Kinematic
    represents the group's overall position/orientation (steer it
    yourself with any SteeringBehavior, e.g. Arrive at a destination),
    and each member gets a per-slot target Kinematic positioned at
    anchor.position + pattern.slot_offset(slot, member_count) for you
    to steer the member towards (e.g. with Arrive). Call update() once
    a frame after moving the anchor, and add_member/remove_member as
    the group's membership changes -- both trigger a fresh
    SlotAssignment so slots stay filled without gaps.

    Usage example:

        anchor = Kinematic(x=0, y=0)
        manager = FormationManager(anchor, WedgeFormation())
        manager.add_member(soldier_1)
        manager.add_member(soldier_2)

        # In the game loop, after steering the anchor with your own
        # behavior (e.g. anchor_arrive.get_steering() then anchor.update(...)):
        manager.update()
        for member in manager.members:
            slot_target = manager.slot_kinematic(member)
            Arrive(member, slot_target).get_steering(dt)
    """

    def __init__(self, anchor: Kinematic, pattern: FormationPattern) -> None:
        """
        :param anchor: The Kinematic representing the formation's overall position.
        :param pattern: The formation pattern to arrange members in.
        """
        self.anchor: Kinematic = anchor
        self.pattern: FormationPattern = pattern
        self.members: List[Kinematic] = []
        self.roles: Dict[int, str] = {}
        self._slot_kinematics: Dict[Hashable, Kinematic] = {}
        self._assignment: Dict[int, Kinematic] = {}

    def set_pattern(self, pattern: FormationPattern) -> None:
        """
        Switch to a different formation pattern (e.g. a different
        tactical "play"), reassigning slots on the next update().

        :param pattern: The new pattern to arrange members in.
        """
        self.pattern = pattern

    def add_member(self, character: Kinematic, role: Optional[str] = None) -> None:
        """
        :param character: The character to add to the formation.
        :param role: An optional label for whichever slot this character ends up assigned to (e.g. "leader", "flank"). The default value is None.
        """
        self.members.append(character)

        if role is not None:
            self.roles[id(character)] = role

    def remove_member(self, character: Kinematic) -> None:
        """
        :param character: The character to remove from the formation.
        """
        self.members.remove(character)
        self.roles.pop(id(character), None)
        self._slot_kinematics.pop(id(character), None)

    def update(self) -> None:
        """
        Reassign slots (via SlotAssignment) and refresh each member's
        slot-target Kinematic position/orientation. Call this once a
        frame, after moving self.anchor.
        """
        self._assignment = SlotAssignment.assign(
            self.members, self.pattern, self.anchor.position
        )
        member_count = len(self.members)

        for slot, character in self._assignment.items():
            target = self._slot_kinematics.setdefault(id(character), Kinematic())
            target.position = self.anchor.position + self.pattern.slot_offset(
                slot, member_count
            )
            target.orientation = self.anchor.orientation

    def slot_kinematic(self, character: Kinematic) -> Kinematic:
        """
        :param character: A member of this formation.
        :returns: The Kinematic representing character's current slot target, to be steered towards (e.g. with Arrive). Only valid after update() has been called at least once since character was added.
        :raises KeyError: If character has never been assigned a slot yet.
        """
        return self._slot_kinematics[id(character)]

    def role_of(self, character: Kinematic) -> Optional[str]:
        """
        :param character: A member of this formation.
        :returns: The role character was added with, or None if it wasn't given one.
        """
        return self.roles.get(id(character))
