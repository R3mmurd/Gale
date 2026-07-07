`← Back to the main README <../../README.rst>`_

gale.physics
=============

``gale.physics`` is 2D physics for gale games, backed by Box2D — but
you never import or touch Box2D directly: everything here works in
plain pixel units and gale's own vocabulary (``World``, ``Body``,
``BodyType``, shapes, joints), plus a lightweight scene graph
(``Node``) for organizing physics entities. See ``examples/leap`` (a
platformer using all three body types) and ``examples/hillclimb`` (a
vehicle demo built on joints) for full games built on it.

Creating a world and bodies
-----------------------------

.. code-block:: python

   from gale.physics.world import World
   from gale.physics.shapes import BoxShape, CircleShape

   world = World(gravity=(0, 900))  # positive y points down the screen

   ground = world.create_static_body(200, 280, BoxShape(400, 20))
   ball = world.create_dynamic_body(200, 50, CircleShape(radius=10, restitution=0.6))

   # In your state:
   def update(self, dt: float) -> None:
       self.world.update(dt)

   def render(self, surface) -> None:
       pygame.draw.circle(surface, "white", ball.position, 10)

There are three body types, created through ``create_static_body``/
``create_dynamic_body``/``create_kinematic_body``:

.. list-table::
   :header-rows: 1

   * - Body type
     - Use it for
   * - Static
     - Fixed level geometry — the ground, walls, platforms that never move.
   * - Dynamic
     - Anything fully simulated — affected by gravity, forces, and collisions (a player, a projectile).
   * - Kinematic
     - Scripted motion — moves exactly per its own set velocity, unaffected by gravity/forces, but pushes dynamic bodies resting on it (a moving platform, an elevator).

``BoxShape``/``CircleShape``/``PolygonShape`` (``gale.physics.shapes``)
describe a fixture — friction, density, restitution, whether it's a
sensor — and can be passed to ``create_*_body(shape=...)`` immediately
or attached later with ``body.add_box``/``add_circle``/``add_polygon``.

Stepping the simulation: update vs. fixed_update
---------------------------------------------------

Box2D's solver wants a fixed timestep for stable results, but your
game loop's ``dt`` is real and variable. ``World`` follows the same
split Unity uses: call ``update(dt)`` once a frame, same as every
other gale subsystem; it accumulates that time and calls
``fixed_update()`` (a real Box2D step, at ``fixed_timestep``, default
``1/60``) as many times as needed to consume it. ``fixed_update()`` is
itself a normal public method, useful in tests (or the rare game) that
want to drive the simulation one fixed step at a time directly:

.. code-block:: python

   world = World(fixed_timestep=1 / 60)
   world.update(dt)       # what your state calls every frame
   world.fixed_update()   # what update() calls internally, 0+ times

Reading and driving a body
-----------------------------

.. code-block:: python

   body.position          # pygame.Vector2, in pixels
   body.angle              # radians
   body.velocity           # pygame.Vector2, pixels/second
   body.set_velocity(vx, vy)
   body.apply_force(fx, fy)     # continuous, call every frame
   body.apply_impulse(ix, iy)   # instantaneous, e.g. a jump
   body.apply_torque(t)

Collision: callbacks vs. touching_bodies
--------------------------------------------

For discrete events (a pickup, a goal, a hazard), register callbacks:

.. code-block:: python

   def on_begin(body_a, body_b) -> None:
       ...

   world.on_collision_begin(on_begin)
   world.on_collision_end(lambda body_a, body_b: ...)

For a per-frame check (e.g. "is the player standing on something" to
decide if it can jump), poll instead — cheaper, no bookkeeping:

.. code-block:: python

   is_grounded = any(b.user_data == "ground" for b in player.touching_bodies)

Joints
-------

Two joint types are wired up, exactly what gale's own examples need:
``RevoluteJoint`` (a motorized pin/pivot) and ``WheelJoint`` (a
motorized wheel with a spring/damper suspension) — see
``examples/hillclimb`` for a full car built from two of the latter.

.. code-block:: python

   joint = world.create_wheel_joint(
       chassis, wheel, wheel.position, axis=(0, 1),
       frequencyHz=4, dampingRatio=0.7,
   )
   joint.enable_motor = True
   joint.motor_speed = 20        # positive drives toward +x
   joint.max_motor_torque = 2000

Scene graph
------------

``Node`` organizes physics entities: every node has an absolute
position; if it owns a ``Body``, that position (and angle) are pulled
from the body every ``update()`` (physics is the source of truth for
anything simulated); children exist for grouping and for attaching a
decoration to a body that should follow it around:

.. code-block:: python

   from gale.physics.node import Node

   chassis_node = Node(body=chassis_body)
   exhaust_node = Node(x=-20, y=0)  # a decoration, no body of its own
   chassis_node.add_child(exhaust_node)

   chassis_node.update(dt)
   exhaust_node.world_position  # chassis_body.position + (-20, 0)

Debug rendering
-----------------

.. code-block:: python

   world.render_debug(surface)  # draws every fixture's outline, no assets needed

Handy while building a level; both ``examples/leap`` and
``examples/hillclimb`` draw their own shapes instead for a nicer look,
but ``render_debug`` is there whenever you just need to see the raw
physics.
