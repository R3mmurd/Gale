"""
This file contains utility classes that perform as timers.

Author: Alejandro Mujica (aledrums@gmail.com)
"""


class TimerItemBase:
    def __init__(self, time, on_finish=None):
        self.timer = 0
        self.time = time
        self.on_finish = (lambda: None) if on_finish is None else on_finish
        self.to_remove = False
    
    def remove(self):
        self.to_remove = True


class Every(TimerItemBase):
    def __init__(self, time, function, limit=None, on_finish=None):
        super().__init__(time, on_finish=on_finish)
        self.function = function
        self.limit = limit

    def finish(self, on_finish):
        self.on_finish = on_finish   

    def update(self, dt):
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
    def __init__(self, time, function):
        super().__init__(time, on_finish=function)
    
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.time:
            self.on_finish()
            self.remove()


class Tween(TimerItemBase):
    def __init__(self, time, params, on_finish=lambda: None):
        super().__init__(time, on_finish=on_finish)
        self.objs = {}

        for obj, attrs in params.items():
            self.objs[obj] = {
                var: {
                    'target': val,
                    'velocity': (val - getattr(obj, var))/time
                }
                for var, val in attrs.items()
            }

    def finish(self, on_finish):
        self.on_finish = on_finish

    def update(self, dt):
        self.timer += dt

        for obj, attrs in self.objs.items():    
            for var, val in attrs.items():
                setattr(
                    obj, var, getattr(obj, var) + val['velocity']*dt
                )

        if self.timer >= self.time:
            for obj, attrs in self.objs.items():    
                for var, val in attrs.items():
                    setattr(
                        obj, var, val['target']
                    )

            self.on_finish()
            self.remove()


class Timer:
    items = []

    @classmethod
    def update(cls, dt):
        for item in cls.items:
            item.update(dt)
        
        cls.items = [item for item in cls.items if not item.to_remove]

    @classmethod
    def every(cls, time, function, limit=None, on_finish=None):
        cls.items.append(
            Every(time, function, limit=limit, on_finish=on_finish)
        )
        return cls.items[-1]
    
    @classmethod
    def after(cls, time, function):
        cls.items.append(
            After(time, function)
        )
        return cls.items[-1]

    @classmethod
    def tween(cls, time, objs, on_finish=None):
        cls.items.append(Tween(time, objs, on_finish=on_finish))
        return cls.items[-1]

