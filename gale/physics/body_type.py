"""
This file contains the implementation of the class BodyType.

Author: Alejandro Mujica (aledrums@gmail.com)
"""


class BodyType:
    """
    Identifies how a Body is simulated.

    - STATIC: never moves, infinite mass. Use it for the ground,
      walls, and any other fixed level geometry.
    - DYNAMIC: fully simulated, affected by gravity, forces, and
      collisions. Use it for anything that should move and react
      realistically, such as a player or a projectile.
    - KINEMATIC: moves exactly according to the velocity you set on
      it, is not affected by gravity/forces/collisions with other
      bodies, but does push dynamic bodies resting on it. Use it for
      moving platforms, elevators, or anything else whose motion is
      scripted rather than simulated.
    """

    STATIC: int = 0
    DYNAMIC: int = 1
    KINEMATIC: int = 2
