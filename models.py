import config
import math

class Vector2:
    def __init__(self, y: int, x: int):
        self.y = int(y)
        self.x = int(x)

    def copy(self):
        return Vector2(self.y, self.x)

    def add(self, y: int, x: int):
        return Vector2(self.y + y, self.x + x)

    def mul(self, multiplier: float):
        return Vector2(round(self.y * multiplier), round(self.x * multiplier))

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
        self.delay = math.ceil(delay_seconds * config.TICKRATE)
        self.initial_delay = self.delay

class GameLevel:
    def __init__(self, num: int, name: str, starting_ammo: int, objects: list[GameObject]):
        self.num = num
        self.name = name
        self.starting_ammo = starting_ammo
        self.objects = objects[:] # shallow copy
        self._spawn = [obj for obj in objects if obj.type == "Spawn"][0]
        self._flag = [obj for obj in objects if obj.type == "Flag"][0]
    
    @property
    def spawn(self):
        return self._spawn

    @property
    def flag(self):
        return self._flag
    
    @property
    def player(self):
        return self._player
    
    @player.setter
    def player(self, player):
        self._player = player
    
