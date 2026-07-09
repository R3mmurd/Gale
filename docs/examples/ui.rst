`← Back to the main README <../../README.rst>`_

gale.ui
========

``gale.ui`` is a small widget toolkit for menus, HUDs, and forms:
``Panel``, ``Label``, ``Button``, ``ProgressBar``, ``Checkbox``,
``ListView``, ``Container``, ``Window``, ``TextBox``,
``PaginatedTextBox``, ``TextInput``, and ``Cursor``, styled through a
shared ``Theme`` and driven by ``gale.input_handler`` through a
``UIManager``. See ``examples/rally`` for a full game built with it
(menus, a "host:port" text field, buttons) alongside ``gale.net``.

A simple menu
--------------

.. code-block:: python

   from gale.ui.container import Container
   from gale.ui.list_view import ListView
   from gale.ui.manager import UIManager
   from gale.ui.panel import Panel

   def start_game() -> None:
       ...

   menu = Container(40, 40, 240, 120, children=[
       Panel(40, 40, 240, 120),
       ListView(48, 48, 224, 104, items=[
           ("Start", start_game),
           ("Quit", quit_game),
       ]),
   ])

   ui = UIManager(
       menu,
       virtual_width=settings.VIRTUAL_WIDTH,
       window_width=settings.WINDOW_WIDTH,
       virtual_height=settings.VIRTUAL_HEIGHT,
       window_height=settings.WINDOW_HEIGHT,
       confirm_action="confirm",
       navigate_actions={"move_up": (0, -1), "move_down": (0, 1)},
   )

   # In your state:
   def update(self, dt): self.ui.update(dt)
   def render(self, surface): self.ui.render(surface)
   def on_input(self, input_id, input_data): self.ui.on_input(input_id, input_data)

A ``Container`` is a real scene-graph node: any mix of widgets, in any
combination, not just this fixed "background panel + list" shape.
Wire mouse motion into ``UIManager`` too so hovering highlights items —
see the "Mouse support" section below, it needs one extra binding.

Widget list
------------

.. list-table::
   :header-rows: 1

   * - Widget
     - Use it for
   * - ``Panel``
     - Background chrome behind other widgets.
   * - ``Label``
     - Static or programmatically updated text (``set_text``).
   * - ``Button``
     - A clickable action, fires ``on_click`` on click or ``on_confirm``.
   * - ``ProgressBar``
     - A health/loading bar; ``value``/``max_value`` are plain attributes so ``Timer.tween`` can animate them directly.
   * - ``Checkbox``
     - A toggle, fires ``on_change(checked)``.
   * - ``ListView``
     - A vertical selectable list — the generalization of a classic "menu": mouse hover/click and keyboard up/down both work.
   * - ``Container``
     - Groups any number of children; handles z-order, input dispatch, and focus movement between them.
   * - ``TextBox``
     - Click/Enter-to-continue dialogue/hint text; ``advance()`` moves a page at a time, ``on_close`` fires after the last one.
   * - ``PaginatedTextBox``
     - The same paginated text, but navigated with explicit "Previous"/"Next" buttons instead (e.g. a rules/help screen) — the buttons enable/disable themselves at the first/last page.
   * - ``TextInput``
     - A single-line editable field (a player name, a chat message, a "join code"/server address).
   * - ``Cursor``
     - A custom OS pointer (``set_as_system_cursor``) or a keyboard-navigation indicator sprite (passed to ``ListView(cursor=...)``).
   * - ``Window``
     - A ``Panel`` + optional title + optional close ("X") button, docked at the top-right corner, wrapped around any children — an inventory, a pause menu, a dismissible dialog.

Mouse support
--------------

``gale.input_handler``'s mouse-motion binding matches an *exact*
relative-motion vector by default (meant for discrete swipe-style
actions), which real mouse movement essentially never produces. Bind
the wildcard fallback once in your ``settings.py`` so hover tracking
actually receives every motion event:

.. code-block:: python

   from gale import input_handler

   input_handler.InputHandler.set_mouse_click_action(input_handler.MOUSE_BUTTON_1, "click")
   input_handler.InputHandler.set_mouse_motion_action(None, "mouse_move")

``UIManager.on_input`` already knows what to do with both once they're
bound — clicks and motion just need to reach it through your state's
``on_input``, same as any other input.

Customizing look and feel
----------------------------

Pass a ``Theme`` to any widget, or replace the process-wide default:

.. code-block:: python

   import pygame
   from gale.ui.theme import Theme, set_default_theme

   set_default_theme(Theme(
       font=pygame.font.Font(None, 22),
       accent_color=pygame.Color(255, 90, 90),
   ))

Widgets read their theme fresh on every ``render()`` call, so swapping
the default theme (or a widget's own, via its ``theme`` attribute)
takes effect immediately — no need to rebuild the widget tree.

Cursors from settings.py
---------------------------

Following the same convention as ``TEXTURES``/``FONTS``/``SOUNDS``:

.. code-block:: python

   import pygame
   from gale.ui.cursor import Cursor

   CURSORS = {
       "pointer": Cursor(pygame.image.load(BASE_DIR / "assets" / "graphics" / "cursor.png"), hotspot=(2, 2)),
   }

.. code-block:: python

   # In a state's enter(), to use it as the OS pointer:
   settings.CURSORS["pointer"].set_as_system_cursor()

   # Or pass it to a ListView for the keyboard-navigation indicator instead:
   ListView(..., cursor=settings.CURSORS["pointer"])

Paginated text: click-through or buttons
--------------------------------------------

``TextBox`` word-wraps and paginates ``text`` on its own
(``lines_per_page`` lines at a time) and is meant to be clicked or
confirmed through, RPG-dialogue style — ``advance()`` moves to the
next page, or, on the last one, hides the box and calls ``on_close``:

.. code-block:: python

   from gale.ui.text_box import TextBox

   dialogue = TextBox(40, 120, 240, 48, "A long line of dialogue...", on_close=close_dialogue)
   # advance() is wired to on_mouse_click/on_confirm already; call it
   # yourself too if you want another input (e.g. Space) to work.

For content the player should page through at their own pace with
explicit buttons instead — a rules or help screen, where jumping back
and forth matters — use ``PaginatedTextBox``, which wires up
"Previous"/"Next" buttons under the text and keeps them
enabled/disabled at the first/last page for you. Unlike ``TextBox``,
it never auto-hides itself:

.. code-block:: python

   from gale.ui.text_box import PaginatedTextBox

   help_box = PaginatedTextBox(160, 90, 320, 220, long_help_text)
   # help_box.text_box.page_index / .page_count if you want to render
   # a "page 2 of 5" indicator alongside it.

Closable windows
------------------

``Window`` wraps a ``Panel``, an optional title, an optional close
("X") button docked at the top-right corner, and any children you pass
it, into a single ``Container``:

.. code-block:: python

   from gale.ui.window import Window
   from gale.ui.text_box import PaginatedTextBox

   def close_help() -> None:
       menu.remove_child(help_window)  # or just help_window.visible = False

   help_window = Window(
       160, 90, 320, 220, title="How to play", on_close=close_help,
       children=[PaginatedTextBox(160, 114, 320, 172, long_help_text)],
   )

Set ``closable=False`` to skip the close button (e.g. a modal the
player must resolve by clicking something inside it instead), or call
``window.close()`` yourself — from a keyboard shortcut, another
widget's ``on_click``, whatever — to trigger the same hide-and-call-
``on_close`` behavior the button does.

Known limitations
-------------------

- ``TextInput`` only supports ASCII-range input (``pygame.KEYDOWN``'s
  ``unicode``), not full IME/composed-character entry — enough for
  names, chat, and join codes, not every language. Full Unicode
  support would need ``pygame.TEXTINPUT`` events wired into
  ``gale.input_handler``, which is a separate, bigger change to that
  module.
- No built-in widget animation: drive a plain attribute (``value``,
  ``x``, ...) with ``gale.timer.Timer.tween`` instead, the same way
  the existing examples already animate everything else.
- No ``Slider`` widget yet — add one when a real use case needs it.
