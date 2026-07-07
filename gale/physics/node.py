"""
This file contains the implementation of the class Node.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional, Sequence

import pygame

from .body import Body


class Node:
    """
    A lightweight scene graph node for organizing physics entities:
    every node has an absolute position (matching how everything else
    in gale already works), optionally owns a Body (in which case its
    position/angle are pulled from the body every update, since
    physics is the source of truth for anything simulated), and can
    have children for grouping/attachment — a decorative or dependent
    node that should follow its parent's body around, or just a way
    to destroy a group of related nodes together.

    This mirrors gale.ui.Container's parent/children/add_order-render
    pattern, applied to physics entities instead of widgets.

    Usage example:

        chassis_node = Node(body=chassis_body)
        exhaust_node = Node(offset=(-20, 0))  # a decoration, no body of its own
        chassis_node.add_child(exhaust_node)

        # Every frame, after world.update(dt):
        chassis_node.update(dt)
        chassis_node.render(surface)
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        body: Optional[Body] = None,
        children: Optional[Sequence["Node"]] = None,
    ) -> None:
        """
        :param x: Initial x position. If body is set, overwritten every update() with the body's own absolute position (Box2D bodies have no concept of a parent-relative transform). Otherwise, this is a fixed offset from this node's parent (or an absolute position, if it has none). The default value is 0.
        :param y: Initial y position, same rules as x. The default value is 0.
        :param body: The Body driving this node's transform. The default value is None, meaning this node's position is either fixed (no parent) or a fixed offset from its parent.
        :param children: Child nodes to add immediately. The default value is None.
        """
        self.x: float = x
        self.y: float = y
        self.angle: float = 0.0
        self.body: Optional[Body] = body
        self.parent: Optional["Node"] = None
        self.children: list = []
        self.visible: bool = True

        for child in children or []:
            self.add_child(child)

    def add_child(self, node: "Node") -> None:
        """
        :param node: The child to add. Rendered/updated after every previously added child (add-order is z-order, as in gale.ui.Container).
        """
        node.parent = self
        self.children.append(node)

    def remove_child(self, node: "Node") -> None:
        """
        :param node: The child to remove.
        """
        if node in self.children:
            node.parent = None
            self.children.remove(node)

    @property
    def world_position(self) -> pygame.Vector2:
        """
        :returns: This node's absolute position. A node with a body already has an absolute position (Box2D bodies are always in world coordinates); otherwise, this composes every ancestor's position with this node's own offset.
        """
        if self.body is not None or self.parent is None:
            return pygame.Vector2(self.x, self.y)

        return pygame.Vector2(self.x, self.y) + self.parent.world_position

    def update(self, dt: float) -> None:
        """
        :param dt: Time elapsed, in seconds, since the last call.
        """
        if self.body is not None:
            self.x, self.y = self.body.position
            self.angle = self.body.angle

        for child in self.children:
            child.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        :param surface: The surface to draw this node (and its children) on. The base Node itself draws nothing — subclasses/games draw whatever they want at self.world_position.
        """
        if not self.visible:
            return

        for child in self.children:
            child.render(surface)
