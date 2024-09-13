"""
This file contains utility classes that perform as timers.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

from typing import Optional, Sequence, Union

from .ease_functions import EASE_FUNCTIONS


class TimerItemBase:
    def __init__(self, time: float, on_finish: Optional[callable] = None) -> None:
        self.timer: float = 0
        self.time: float = time
        self.on_finish: callable = (lambda: None) if on_finish is None else on_finish
        self.to_remove: bool = False

    def finish(self, on_finish: callable) -> None:
        self.on_finish = on_finish

    def remove(self) -> None:
        self.to_remove = True


class Every(TimerItemBase):
    def __init__(
        self,
        time: float,
        function: callable,
        limit: Optional[int] = None,
        on_finish: Optional[callable] = None,
    ) -> None:
        super().__init__(time, on_finish=on_finish)
        self.function: callable = function
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
    def __init__(self, time: float, function: callable) -> None:
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
        params: Sequence[tuple[any, dict[str, any]]],
        ease_function_name: str = "linear",
        on_finish: Optional[callable] = lambda: None,
    ) -> None:
        super().__init__(time, on_finish=on_finish)

        self.ease_function = EASE_FUNCTIONS.get(ease_function_name)

        if self.ease_function is None:
            raise RuntimeError(
                f"{ease_function_name} is not a valid ease function for tween"
            )

        self.plan: list[tuple[any, dict[str, any]]] = []

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


class Timer:
    items: list[Union[Every, After, Tween]] = []
    paused: bool = False

    @classmethod
    def update(cls, dt: float) -> None:
        if cls.paused:
            return

        for item in cls.items:
            item.update(dt)

        cls.items = [item for item in cls.items if not item.to_remove]

    @classmethod
    def every(
        cls,
        time: float,
        function: callable,
        limit: Optional[int] = None,
        on_finish: Optional[callable] = None,
    ) -> Every:
        cls.items.append(Every(time, function, limit=limit, on_finish=on_finish))
        return cls.items[-1]

    @classmethod
    def after(cls, time: float, function: callable) -> After:
        cls.items.append(After(time, function))
        return cls.items[-1]

    @classmethod
    def tween(
        cls,
        time: float,
        objs: Sequence[tuple[any, dict[str, any]]],
        ease_function_name: str = "linear",
        on_finish: Optional[callable] = None,
    ) -> Tween:
        cls.items.append(
            Tween(
                time, objs, ease_function_name=ease_function_name, on_finish=on_finish
            )
        )
        return cls.items[-1]

    @classmethod
    def clear(cls) -> None:
        cls.items = []
        cls.paused = False

    @classmethod
    def pause(cls) -> None:
        cls.paused = True

    @classmethod
    def resume(cls) -> None:
        cls.paused = False
