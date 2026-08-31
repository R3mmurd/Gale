"""
This file contains Every/After/Tween/During (a repeating callback, a
one-shot delayed callback, an eased attribute interpolation, and a
continuous per-frame callback fed dt/progress until a cutoff,
respectively) and the class Timer, a process-wide scheduler managing
all of them — call Timer.every/after/tween/during to start one, and
Timer.update(dt) once a frame to drive them all.

Every item can optionally be tagged with a group (any hashable — a
string tag or an owning object both work) so a subset can be
paused/resumed/cleared independently of the rest: Timer.pause(group=
"enemies") stops only that group, Timer.clear(group=level_object)
drops everything tagged with it, the same "kill everything belonging
to X" DOTween's Kill(target) gives. An item can also be paused on its
own through item.pause()/item.resume(), and set to ignore_global_pause
so a global Timer.pause() (say, from a pause menu) leaves it running —
useful for a UI's own timers/tweens, which usually shouldn't freeze
just because gameplay did (the same thing Godot's Timer.process_mode
gives per-node).

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, List, Optional, Any, Sequence, Tuple, Dict, Set, Union

from .ease_functions import EASE_FUNCTIONS


class TimerItemBase:
    def __init__(
        self,
        time: float,
        on_finish: Optional[Callable[[], None]] = None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> None:
        self.timer: float = 0
        self.time: float = time
        self.on_finish: Callable[[], None] = (
            (lambda: None) if on_finish is None else on_finish
        )
        self.to_remove: bool = False
        self.group: Optional[Any] = group
        self.ignore_global_pause: bool = ignore_global_pause
        self.paused: bool = False

    def finish(self, on_finish: Callable[[], None]) -> None:
        self.on_finish = on_finish

    def remove(self) -> None:
        self.to_remove = True

    def pause(self) -> None:
        """Pause this item alone, independently of Timer.pause()/Timer.pause(group=...)."""
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    @property
    def progress(self) -> float:
        """How far along [0, 1] this item is towards `time`. 1.0 for a non-positive time, which never has any distance left to cover."""
        if self.time <= 0:
            return 1.0

        return min(self.timer / self.time, 1.0)


class Every(TimerItemBase):
    def __init__(
        self,
        time: float,
        function: Callable[[], None],
        limit: Optional[int] = None,
        on_finish: Optional[Callable[[], None]] = None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> None:
        super().__init__(
            time,
            on_finish=on_finish,
            group=group,
            ignore_global_pause=ignore_global_pause,
        )
        self.function: Callable[[], None] = function
        self.limit: Optional[int] = limit

    def update(self, dt: float) -> None:
        self.timer += dt

        if self.timer >= self.time:
            self.timer %= self.time
            self.function()
            if self.limit:
                if self.limit == 1:
                    self.on_finish()
                    self.remove()
                else:
                    self.limit -= 1


class After(TimerItemBase):
    def __init__(
        self,
        time: float,
        function: Callable[[], None],
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> None:
        super().__init__(
            time,
            on_finish=function,
            group=group,
            ignore_global_pause=ignore_global_pause,
        )

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.time:
            self.on_finish()
            self.remove()


class Tween(TimerItemBase):
    def __init__(
        self,
        time: float,
        params: Sequence[Tuple[Any, Dict[str, Any]]],
        ease_function_name: str = "linear",
        on_finish: Optional[Callable[[], None]] = lambda: None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> None:
        super().__init__(
            time,
            on_finish=on_finish,
            group=group,
            ignore_global_pause=ignore_global_pause,
        )

        self.ease_function = EASE_FUNCTIONS.get(ease_function_name)

        if self.ease_function is None:
            raise RuntimeError(
                f"{ease_function_name} is not a valid ease function for tween"
            )

        self.plan: Sequence[Tuple[Any, Dict[str, Any]]] = []

        for obj, attrs in params:
            for key, final in attrs.items():
                initial = getattr(obj, key)

                self.plan.append(
                    (
                        obj,
                        {
                            "key": key,
                            "initial": initial,
                            "final": final,
                            "change": final - initial,
                        },
                    )
                )

    def update(self, dt: float) -> None:
        self.timer += dt

        if self.timer >= self.time:
            for obj, data in self.plan:
                setattr(obj, data["key"], data["final"])
            self.on_finish()
            self.remove()
            return

        for obj, data in self.plan:
            setattr(
                obj,
                data["key"],
                data["initial"]
                + data["change"] * self.ease_function(self.timer / self.time),
            )


class During(TimerItemBase):
    """
    Calls function(dt, progress) every update() for `time` seconds,
    then on_finish() once. Useful for a per-frame effect that isn't
    "interpolate this object's attribute towards a final value" (what
    Tween is for), such as a camera shake, a shader uniform, or
    anything else driven by a raw callback instead.
    """

    def __init__(
        self,
        time: float,
        function: Callable[[float, float], None],
        on_finish: Optional[Callable[[], None]] = None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> None:
        super().__init__(
            time,
            on_finish=on_finish,
            group=group,
            ignore_global_pause=ignore_global_pause,
        )
        self.function: Callable[[float, float], None] = function

    def update(self, dt: float) -> None:
        self.timer += dt
        self.function(dt, self.progress)

        if self.timer >= self.time:
            self.on_finish()
            self.remove()


class Timer:
    items: List[Union[Every, After, Tween, During]] = []
    paused: bool = False
    paused_groups: Set[Any] = set()

    @classmethod
    def update(cls, dt: float) -> None:
        for item in cls.items:
            if item.paused:
                continue

            if cls.paused and not item.ignore_global_pause:
                continue

            if item.group is not None and item.group in cls.paused_groups:
                continue

            item.update(dt)

        cls.items = [item for item in cls.items if not item.to_remove]

    @classmethod
    def every(
        cls,
        time: float,
        function: Callable[[], None],
        limit: Optional[int] = None,
        on_finish: Optional[Callable[[], None]] = None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> Every:
        cls.items.append(
            Every(
                time,
                function,
                limit=limit,
                on_finish=on_finish,
                group=group,
                ignore_global_pause=ignore_global_pause,
            )
        )
        return cls.items[-1]

    @classmethod
    def after(
        cls,
        time: float,
        function: Callable[[], None],
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> After:
        cls.items.append(
            After(time, function, group=group, ignore_global_pause=ignore_global_pause)
        )
        return cls.items[-1]

    @classmethod
    def tween(
        cls,
        time: float,
        objs: Sequence[Tuple[Any, Dict[str, Any]]],
        ease_function_name: str = "linear",
        on_finish: Optional[Callable[[], None]] = None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> Tween:
        cls.items.append(
            Tween(
                time,
                objs,
                ease_function_name=ease_function_name,
                on_finish=on_finish,
                group=group,
                ignore_global_pause=ignore_global_pause,
            )
        )
        return cls.items[-1]

    @classmethod
    def during(
        cls,
        time: float,
        function: Callable[[float, float], None],
        on_finish: Optional[Callable[[], None]] = None,
        group: Optional[Any] = None,
        ignore_global_pause: bool = False,
    ) -> During:
        cls.items.append(
            During(
                time,
                function,
                on_finish=on_finish,
                group=group,
                ignore_global_pause=ignore_global_pause,
            )
        )
        return cls.items[-1]

    @classmethod
    def clear(cls, group: Optional[Any] = None) -> None:
        """
        :param group: The single group to drop every item from (and unpause). The default value is None, clearing every item, unpausing everything, and dropping every group-level pause.
        """
        if group is None:
            cls.items = []
            cls.paused = False
            cls.paused_groups = set()
        else:
            cls.items = [item for item in cls.items if item.group != group]
            cls.paused_groups.discard(group)

    @classmethod
    def pause(cls, group: Optional[Any] = None) -> None:
        """
        :param group: The single group to pause. The default value is None, pausing every item that doesn't have ignore_global_pause set.
        """
        if group is None:
            cls.paused = True
        else:
            cls.paused_groups.add(group)

    @classmethod
    def resume(cls, group: Optional[Any] = None) -> None:
        """
        :param group: The single group to resume. The default value is None, resuming every item paused through a groupless Timer.pause().
        """
        if group is None:
            cls.paused = False
        else:
            cls.paused_groups.discard(group)
