"""
This file contains utility classes that perform as timers.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Callable, Optional, Any, Sequence, Tuple, Dict, Union


class TimerItemBase:
    def __init__(
        self, time: float, on_finish: Optional[Callable[[], None]] = None
    ) -> None:
        self.timer: float = 0
        self.time: float = time
        self.on_finish: Callable[[], None] = (
            (lambda: None) if on_finish is None else on_finish
        )
        self.to_remove: bool = False

    def remove(self) -> None:
        self.to_remove = True


class Every(TimerItemBase):
    def __init__(
        self,
        time: float,
        function: Callable[[], None],
        limit: Optional[int] = None,
        on_finish: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(time, on_finish=on_finish)
        self.function: Callable[[], None] = function
        self.limit: Optional[int] = limit

    def finish(self, on_finish: Callable[[], None]) -> None:
        self.on_finish = on_finish

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
    def __init__(self, time: float, function: Callable[[], None]) -> None:
        super().__init__(time, on_finish=function)

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
        on_finish: Optional[Callable[[], None]] = lambda: None,
    ) -> None:
        super().__init__(time, on_finish=on_finish)
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

    def finish(self, on_finish: Callable[[], None]) -> None:
        self.on_finish = on_finish

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
                data["change"] * self.timer / self.time + data["initial"],
            )


class Timer:
    items: Union[Every, After, Tween] = []

    @classmethod
    def update(cls, dt: float) -> None:
        for item in cls.items:
            item.update(dt)

        cls.items = [item for item in cls.items if not item.to_remove]

    @classmethod
    def every(
        cls,
        time: float,
        function: Callable[[], None],
        limit: Optional[int] = None,
        on_finish: Optional[Callable[[], None]] = None,
    ) -> Every:
        cls.items.append(Every(time, function, limit=limit, on_finish=on_finish))
        return cls.items[-1]

    @classmethod
    def after(cls, time: float, function: Callable[[], None]) -> After:
        cls.items.append(After(time, function))
        return cls.items[-1]

    @classmethod
    def tween(
        cls,
        time: float,
        objs: Sequence[Tuple[Any, Dict[str, Any]]],
        on_finish: Optional[Callable[[], None]] = None,
    ) -> Tween:
        cls.items.append(Tween(time, objs, on_finish=on_finish))
        return cls.items[-1]

    @classmethod
    def clear(cls) -> None:
        cls.items = []
