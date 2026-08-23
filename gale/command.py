"""
This file contains Command, a stateless, reusable action executed
against a receiver passed in on every call (so a single instance can
be shared as a singleton across every entity that performs it) whose
__call__ alias lets it double as a plain callable(receiver, dt) leaf
for gale.ai's behavior/decision trees; CommandBindings, mapping an
InputHandler input_id to the pair of commands run on press/release;
and CommandControlled, an InputListener mixin that registers itself
and routes on_input straight into a CommandBindings.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Any, Dict, Optional, Tuple

from gale.input_handler import InputData, InputHandler, InputListener


class Command:
    """
    Base class for the Command pattern. A Command holds no state of
    its own: everything it acts upon is the receiver passed into
    execute, never the constructor, so the same instance can be reused
    (even kept as a module-level singleton) across a player and any
    number of autonomous creatures that perform the same action.
    """

    def execute(self, receiver: Any, dt: float = 0.0) -> None:
        """
        Perform this command against receiver.

        :param receiver: The object this command acts upon.
        :param dt: Time elapsed (in seconds) since the last execution. Defaults to 0.0, which is fine for one-shot commands, such as those fired from a press/release, that don't need it.
        """
        raise NotImplementedError()

    def __call__(self, receiver: Any, dt: float = 0.0) -> None:
        """
        Alias for execute, so a Command instance can be passed
        directly wherever a plain callable(receiver, dt) is expected —
        for instance, driven from an AI loop — without wrapping it
        first.
        """
        self.execute(receiver, dt)


class CommandBindings:
    """
    Maps an InputHandler input_id to the pair of commands that should
    run when that input is pressed and when it is released.
    """

    def __init__(self) -> None:
        self._bindings: Dict[str, Tuple[Optional[Command], Optional[Command]]] = {}

    def bind(
        self,
        input_id: str,
        press: Optional[Command] = None,
        release: Optional[Command] = None,
    ) -> None:
        """
        :param input_id: The InputHandler action id this binding reacts to.
        :param press: Command executed when the dispatched input_data reports pressed. The default value is None, meaning a press is ignored.
        :param release: Command executed when the dispatched input_data reports released. The default value is None, meaning a release is ignored.
        """
        self._bindings[input_id] = (press, release)

    def dispatch(
        self, receiver: Any, input_id: str, input_data: InputData, dt: float = 0.0
    ) -> None:
        """
        Look up input_id and execute whichever of its commands matches
        input_data, if any.

        :param receiver: The object the resolved command, if any, is executed against.
        :param input_id: The action id reported by InputHandler, typically forwarded straight from on_input.
        :param input_data: The data reported alongside input_id. Only pressed/released are inspected, read through getattr with a False default since some variants (GamepadAxisData, for instance) don't carry either attribute at all.
        :param dt: Time elapsed (in seconds) since the last dispatch, forwarded to the resolved command's execute.
        """
        binding = self._bindings.get(input_id)

        if binding is None:
            return

        press, release = binding

        if getattr(input_data, "pressed", False) and press is not None:
            press.execute(receiver, dt)
        elif getattr(input_data, "released", False) and release is not None:
            release.execute(receiver, dt)


class CommandControlled(InputListener):
    """
    Mixin that registers itself with InputHandler and routes every
    on_input notification into a CommandBindings. Combine it by
    multiple inheritance with any entity class (Entity, Kinematic, and
    so on) to make that entity respond to input purely through
    Command objects, the same way plain InputListener is combined
    today.
    """

    def __init__(
        self, command_bindings: CommandBindings, *args: Any, **kwargs: Any
    ) -> None:
        """
        :param command_bindings: The bindings used to resolve on_input notifications into commands.
        """
        super().__init__(*args, **kwargs)
        self._command_bindings = command_bindings
        InputHandler.register_listener(self)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self._command_bindings.dispatch(self, input_id, input_data)
