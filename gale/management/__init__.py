"""
gale.management: the gale-admin command-line tool's entry point,
scaffolding a new project's directory structure (create-project) and
new BaseState subclasses inside one (create-state).

See docs/examples/project_template.rst for a walkthrough.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from . import gale_admin


def execute_from_command_line():
    gale_admin.execute()
