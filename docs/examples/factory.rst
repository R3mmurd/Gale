`← Back to the main README <../../README.rst>`_

gale.factory
=============

``Factory`` builds instances of a given class from an ``(x, y)`` position
plus an optional dictionary of extra properties. ``AbstractFactory`` goes
one step further: it looks up the class by name inside a module, useful
to build the right kind of game object from data (for instance, a level
loaded from a file).

.. code-block:: python

   from gale.factory import AbstractFactory, Factory


   class Enemy:
       def __init__(self, x: float, y: float, texture_name: str = "enemy.png") -> None:
           self.x = x
           self.y = y
           self.texture_name = texture_name


   enemy_factory = Factory(Enemy)
   enemy = enemy_factory.create(100, 200, {"texture_name": "goblin.png"})

   # Look up the class by name, for instance from level data such as
   # {"type": "Enemy", "x": 100, "y": 200}.
   abstract_factory = AbstractFactory(__name__)
   enemy_factory = abstract_factory.get_factory("Enemy")
   enemy = enemy_factory.create(100, 200)

``AbstractFactory`` takes the dotted name of a module, which must already
be imported (i.e. present in ``sys.modules``) before you construct it —
if the classes you want to build live in a different module than the one
constructing the factory, import that module first, even if you don't use
it directly:

.. code-block:: python

   import src.enemies  # registers the module so AbstractFactory can find it

   abstract_factory = AbstractFactory("src.enemies")
