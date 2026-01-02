import config

class Vector2:
    def __init__(self, y: int, x: int):
        self.y = int(y)
        self.x = int(x)

    def copy(self):
        return Vector2(self.y, self.x)

    def add(self, y: int, x: int):
        return Vector2(self.y + y, self.x + x)

    def mul(self, multiplier: float):
        return Vector2((self.y * multiplier).__round__(), (self.x * multiplier).__round__())

class GameObject:
    def __init__(self, pos: Vector2, type: str, symbol: str, hidden: bool = False):
        self.pos = pos
        self.type = type
        self.symbol = symbol
        self.hidden = hidden

class Event:
    def __init__(self, name: str, delay_seconds: float = 0, params = None):
        self.name = name
        self.params = params
        # delay is in ticks
        self.delay = (delay_seconds * config.TICKRATE).__ceil__()
        self.initial_delay = self.delay