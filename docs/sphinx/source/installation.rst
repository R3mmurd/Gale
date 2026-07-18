Installation
=============

Gale is published on PyPI as ``gale-engine``:

.. code-block:: bash

   pip install gale-engine

Requirements
------------

* Python 3.7+
* pygame
* Box2D (``Box2D``)
* numpy

These are installed automatically as dependencies of the ``gale-engine``
package.

From source
------------

To work against the latest development version instead:

.. code-block:: bash

   git clone https://github.com/R3mmurd/Gale.git
   cd Gale
   pip install -e .

Starting a new project
------------------------

Gale ships a ``gale-admin`` command-line tool that scaffolds a new
game project:

.. code-block:: bash

   gale-admin startproject my_game

See :doc:`examples/project_template` for details on the generated
layout.
